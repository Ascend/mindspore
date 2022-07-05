/**
 * Copyright 2020 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#define USE_DEPRECATED_API
#include "tools/converter/converter.h"
#include <memory>
#include <vector>
#include <set>
#include <algorithm>
#include "src/common/log_adapter.h"
#include "tools/common/meta_graph_serializer.h"
#include "tools/lite_exporter/anf_exporter.h"
#include "tools/graph_kernel/converter/graph_kernel_optimization.h"
#ifdef SUPPORT_TRAIN
#include "src/train/train_populate_parameter.h"
#endif
#include "include/registry/model_parser_registry.h"
#include "src/common/dynamic_library_loader.h"
#include "src/common/log_util.h"
#include "tools/converter/parser/parser_utils.h"
#include "tools/converter/import/mindspore_importer.h"
#include "nnacl/op_base.h"
#include "tools/converter/micro/coder/coder.h"
#include "src/common/prim_util.h"
#include "src/common/version_manager.h"
#include "tools/common/tensor_util.h"
#include "include/api/model.h"
#include "tools/mindir_exporter/mindir_serializer.h"
#include "src/common/primitive_t_utils.h"
#include "tools/converter/config_parser/acl_option_param_parser.h"
#include "tools/converter/config_parser/micro_param_parser.h"
#include "tools/converter/config_parser/preprocess_parser.h"
#include "tools/converter/config_parser/quant_param_parser.h"
#include "tools/common/string_util.h"
#include "src/common/file_utils.h"

namespace mindspore {
extern "C" {
void common_log_init();
}
namespace lite {
namespace {
constexpr size_t kMaxNum1024 = 1024;
constexpr size_t kPluginPathMaxNum = 10;
constexpr int kPathLengthUpperLimit = 1024;
constexpr size_t kEncMaxLen = 16;
constexpr size_t kFlatbuffersBuilderInitSize = 1024;

FuncGraphPtr ConvertGraph(const api::FuncGraphPtr &func_graph) {
  auto impl = func_graph->impl();
  return std::dynamic_pointer_cast<FuncGraph>(impl);
}
}  // namespace

FuncGraphPtr ConverterImpl::BuildFuncGraph(const std::shared_ptr<ConverterPara> &param) {
  api::FuncGraphPtr func_graph_base = nullptr;
  if (param->fmk_type == converter::FmkType::kFmkTypeMs) {
#ifdef SUPPORT_TRAIN
    kernel::PopulateTrainParameters();
#endif
    MindsporeImporter ms_import;
    func_graph_base = api::MakeShared<api::FuncGraph>(ms_import.ImportMindIR(param));
  } else {
    model_parser_ = registry::ModelParserRegistry::GetModelParser(param->fmk_type);
    if (model_parser_ == nullptr) {
      MS_LOG(ERROR) << "Unsupported to converter models with fmk: " << param->fmk_type;
      return nullptr;
    }
    converter::ConverterParameters converter_parameters;
    converter_parameters.fmk = param->fmk_type;
    converter_parameters.model_file = param->model_file;
    converter_parameters.weight_file = param->weight_file;
    func_graph_base = model_parser_->Parse(converter_parameters);
  }
  if (func_graph_base == nullptr) {
    MS_LOG(ERROR) << "Get funcGraph failed for fmk: " << param->fmk_type;
    ReturnCode::GetSingleReturnCode()->UpdateReturnCode(RET_NOT_SUPPORT);
    return nullptr;
  }
  auto func_graph = ConvertGraph(func_graph_base);
  if (func_graph == nullptr) {
    MS_LOG(ERROR) << "func graph is invalid.";
    return nullptr;
  }
  if (UpdateFuncGraphInputsAndOutputsDtype(func_graph) != RET_OK) {
    MS_LOG(ERROR) << "Update graph inputs and outputs dtype failed.";
    return nullptr;
  }
  return func_graph;
}

FuncGraphPtr ConverterImpl::BuildFuncGraph(const std::shared_ptr<ConverterPara> &param, const void *buf,
                                           const size_t &size) {
  MindsporeImporter ms_import;
  FuncGraphPtr func_graph = ms_import.ImportMindIR(param, buf, size);
  if (func_graph == nullptr) {
    MS_LOG(ERROR) << "Get funcGraph failed.";
    return nullptr;
  }

  if (UpdateFuncGraphInputsAndOutputsDtype(func_graph) != RET_OK) {
    MS_LOG(ERROR) << "Update graph inputs and outputs dtype failed.";
    return nullptr;
  }

  return func_graph;
}

schema::MetaGraphT *ConverterImpl::Convert(const std::shared_ptr<ConverterPara> &param, const void *buf,
                                           const size_t &size) {
  if (param == nullptr || buf == nullptr) {
    MS_LOG(ERROR) << "Input param is nullptr";
    return nullptr;
  }
  auto graph = BuildFuncGraph(param, buf, size);
  if (graph == nullptr) {
    MS_LOG(ERROR) << "Parser/Import model return nullptr";
    return nullptr;
  }
  MS_CHECK_TRUE_MSG(funcgraph_transform_ != nullptr, nullptr, "funcgraph_transform init failed.");
  // funcgraph_transform
  graph = funcgraph_transform_->Transform(graph, param);
  MS_CHECK_TRUE_MSG(graph != nullptr, nullptr, "Transform anf graph return nullptr.");
  // export protobuf
  auto status = MindIRSerialize(param, graph);
  if (status != RET_OK) {
    MS_LOG(WARNING) << "Export to mindir proto return nullptr.";
  }
  return TransferFuncGraph(param, graph);
}

schema::MetaGraphT *ConverterImpl::Convert(const std::shared_ptr<ConverterPara> &param) {
  if (param == nullptr) {
    MS_LOG(ERROR) << "Input param is nullptr";
    return nullptr;
  }

  param->aclModelOptionCfgParam.om_file_path = param->output_file;
  param->aclModelOptionCfgParam.offline = true;

  if (!param->config_file.empty() || !param->config_param.empty()) {
    auto ret = InitConfigParam(param);
    if (ret != RET_OK) {
      std::cerr << "Init config file failed." << std::endl;
      return nullptr;
    }
  }

  // load plugin
  static std::vector<std::shared_ptr<DynamicLibraryLoader>> dl_loaders;
  if (!param->plugins_path.empty()) {
    for (auto &path : param->plugins_path) {
      auto dl_loader = std::make_shared<DynamicLibraryLoader>();
      MS_CHECK_TRUE_RET(dl_loader != nullptr, nullptr);
      auto status = dl_loader->Open(path);
      if (status != RET_OK) {
        MS_LOG(ERROR) << "open dynamic library failed. " << path;
        return nullptr;
      }
      dl_loaders.emplace_back(dl_loader);
    }
  }

  auto graph = BuildFuncGraph(param);
  if (graph == nullptr) {
    MS_LOG(ERROR) << "Parser/Import model return nullptr";
    return nullptr;
  }

  MS_CHECK_TRUE_MSG(funcgraph_transform_ != nullptr, nullptr, "funcgraph_transform init failed");
  // funcgraph transform
  graph = funcgraph_transform_->Transform(graph, param);
  if (graph == nullptr) {
    MS_LOG(ERROR) << "Transform anf graph return nullptr";
    return nullptr;
  }

  // export protobuf
  auto status = MindIRSerialize(param, graph);
  if (status != RET_OK) {
    MS_LOG(WARNING) << "Export to mindir proto return nullptr.";
  }

  return TransferFuncGraph(param, graph);
}

schema::MetaGraphT *ConverterImpl::TransferFuncGraph(const std::shared_ptr<ConverterPara> &param,
                                                     FuncGraphPtr func_graph) {
  MS_CHECK_TRUE_MSG(metagraph_transform_ != nullptr, nullptr, "metagraph_transform_ init failed");
#ifdef MSLITE_ENABLE_GRAPH_KERNEL
  graphkernel::GraphKernelOptimize(func_graph, param);
#endif

  // protobuf -> flatbuffer
  auto meta_graph = Export(func_graph, false, false, param->train_model);
  if (meta_graph == nullptr) {
    MS_LOG(ERROR) << "Export to meta graph return nullptr";
    return nullptr;
  }

  // metagraph compile
  metagraph_transform_->SetGraphDef(meta_graph);
  auto status = metagraph_transform_->Transform(param);
  if (status != RET_OK) {
    MS_LOG(ERROR) << "Transform meta graph failed " << status;
    ReturnCode::GetSingleReturnCode()->UpdateReturnCode(status);
    delete meta_graph;
    return nullptr;
  }

  status = UpdateGraphOutputName(meta_graph);
  if (status != RET_OK) {
    MS_LOG(ERROR) << "UpdateGraphOutputName failed.";
    ReturnCode::GetSingleReturnCode()->UpdateReturnCode(RET_ERROR);
    delete meta_graph;
    return nullptr;
  }

  return meta_graph;
}

int CheckExistCustomOps(const schema::MetaGraphT *meta_graph, bool *exist_custom_nodes) {
  MS_CHECK_TRUE_MSG(meta_graph != nullptr && exist_custom_nodes != nullptr, RET_ERROR, "input params contain nullptr.");
  flatbuffers::FlatBufferBuilder fbb(kMaxNum1024);
  for (const auto &node : meta_graph->nodes) {
    auto prim = ConvertToPrimitive(node->primitive.get(), &fbb);
    if (prim == nullptr) {
      MS_LOG(ERROR) << "get primitive failed.";
      fbb.Clear();
      return RET_ERROR;
    }
    if (IsCustomNode(prim, static_cast<int>(SCHEMA_CUR))) {
      *exist_custom_nodes = true;
      break;
    }
  }
  fbb.Clear();
  return RET_OK;
}

int PreInference(const schema::MetaGraphT &meta_graph, bool train_model) {
  if (train_model) {
    MS_LOG(WARNING) << "train model dont support pre-infer.";
    return RET_OK;
  }

  bool exist_custom_nodes = false;
  auto check_ret = CheckExistCustomOps(&meta_graph, &exist_custom_nodes);
  if (check_ret == RET_ERROR) {
    MS_LOG(ERROR) << "CheckExistCustomOps failed.";
    return RET_ERROR;
  }
  if (exist_custom_nodes) {
    MS_LOG(WARNING) << "exist custom nodes and will not be pre-infer.";
    return RET_OK;
  }
  mindspore::Model model;
  flatbuffers::FlatBufferBuilder builder(kMaxNum1024);
  auto offset = schema::MetaGraph::Pack(builder, &meta_graph);
  builder.Finish(offset);
  schema::FinishMetaGraphBuffer(builder, offset);
  int size = builder.GetSize();
  auto content = builder.GetBufferPointer();
  if (content == nullptr) {
    MS_LOG(ERROR) << "GetBufferPointer nullptr";
    return RET_ERROR;
  }
  auto context = std::make_shared<mindspore::Context>();
  if (context == nullptr) {
    MS_LOG(ERROR) << "New context failed while running ";
    std::cerr << "New context failed while running " << std::endl;
    return RET_ERROR;
  }
  std::shared_ptr<CPUDeviceInfo> device_info = std::make_shared<CPUDeviceInfo>();
  auto &device_list = context->MutableDeviceInfo();
  device_list.push_back(device_info);

  auto ret = model.Build(content, size, kMindIR, context);
  if (ret != kSuccess) {
    MS_LOG(ERROR) << "Build error ";
    std::cerr << "Build error " << std::endl;
    return RET_ERROR;
  }
  for (auto &tensor : model.GetInputs()) {
    if (tensor.Shape().empty() || tensor.DataSize() <= 0 ||
        std::find(tensor.Shape().begin(), tensor.Shape().end(), -1) != tensor.Shape().end()) {
      MS_LOG(WARNING) << tensor.Name() << " is dynamic shape and will not be pre-infer.";
      return RET_OK;
    }
    auto status = GenerateRandomData(&tensor);
    if (status != RET_OK) {
      MS_LOG(ERROR) << tensor.Name() << "GenerateRandomData failed.";
      return status;
    }
  }
  std::vector<MSTensor> outputs;
  ret = model.Predict(model.GetInputs(), &outputs);
  if (ret != kSuccess) {
    MS_LOG(ERROR) << "Inference error ";
    std::cerr << "Inference error " << std::endl;
    return RET_ERROR;
  }
  return RET_OK;
}

int ConverterImpl::InitConfigParam(const std::shared_ptr<ConverterPara> &param) {
  lite::ConfigFileParser config_parser;
  auto ret = RET_OK;
  if (!param->config_file.empty()) {
    ret = config_parser.ParseConfigFile(param->config_file);
  } else {
    ret = config_parser.ParseConfigParam(&param->config_param);
  }
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse config param failed.";
    return ret;
  }
  ret = lite::PreprocessParser::ParsePreprocess(config_parser.GetDataPreProcessString(), &param->dataPreProcessParam);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse preprocess failed.";
    return ret;
  }
  ret = lite::QuantParamParser::ParseCommonQuant(config_parser.GetCommonQuantString(), &param->commonQuantParam);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse common quant param failed.";
    return ret;
  }
  ret = lite::QuantParamParser::ParseFullQuant(config_parser.GetFullQuantString(), &param->fullQuantParam);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse full quant param failed.";
    return ret;
  }
  ret = lite::QuantParamParser::ParseMixedBitWeightQuant(config_parser.GetMixedBitWeightQuantString(),
                                                         &param->mixedBitWeightQuantParam);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse mixed bit weight quant param failed.";
    return ret;
  }
  ret = InitExtendedIntegrationInfo(param, config_parser);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse extended integration info failed.";
    return ret;
  }

  lite::AclOptionParamParser acl_param_parser;
  ret = acl_param_parser.ParseAclOptionCfg(config_parser.GetAclOptionCfgString(), &param->aclModelOptionCfgParam);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse acl option param failed.";
    return ret;
  }
  if (!param->config_file.empty()) {
    (void)CheckOfflineParallelConfig(param->config_file, &param->parallel_split_config);
  }
  lite::MicroParamParser micro_param_parser;
  ret = micro_param_parser.ParseMicroParam(config_parser.GetMicroParamString(), &param->microParam);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "Parse micro param failed.";
    return ret;
  }
  return RET_OK;
}

int ConverterImpl::InitExtendedIntegrationInfo(const std::shared_ptr<ConverterPara> &param,
                                               const lite::ConfigFileParser &config_parser) {
  auto extended_info = config_parser.GetRegistryInfoString();
  if (!extended_info.plugin_path.empty()) {
    const char delimiter = ';';
    auto relative_path = lite::SplitStringToVector(extended_info.plugin_path, delimiter);
    if (relative_path.size() > kPluginPathMaxNum) {
      MS_LOG(ERROR) << "extended plugin library's num is too big, which shouldn't be larger than " << kPluginPathMaxNum;
      return RET_INPUT_PARAM_INVALID;
    }
    for (auto &i : relative_path) {
      param->plugins_path.push_back(lite::RealPath(i.c_str()));
    }
  }

  if (!extended_info.disable_fusion.empty()) {
    if (extended_info.disable_fusion == "on") {
      param->no_fusion = true;
    } else if (extended_info.disable_fusion == "off") {
      param->no_fusion = false;
    } else {
      std::cerr << "CONFIG SETTING ILLEGAL: disable_fusion should be on/off" << std::endl;
      return RET_INPUT_PARAM_INVALID;
    }
  }

  if (!extended_info.fusion_blacklists.empty()) {
    std::vector<std::string> fusions = SplitStringToVector(extended_info.fusion_blacklists, ",");
    for (const auto &fusion : fusions) {
      param->fusion_blacklists.insert(fusion);
    }
  }
  return RET_OK;
}

bool ConverterImpl::CheckOfflineParallelConfig(const std::string &file, ParallelSplitConfig *parallel_split_config) {
  // device: [device0 device1] ---> {cpu, gpu}
  // computeRate: [x: y] x >=0 && y >=0 && x/y < 10
  MS_ASSERT(parallel_split_config != nullptr);
  std::vector<std::string> config_devices = {"cpu", "gpu", "npu"};
  auto compute_rate_result = GetStrFromConfigFile(file, kComputeRate);
  if (compute_rate_result.empty()) {
    return false;
  }
  std::string device0_result = GetStrFromConfigFile(file, kSplitDevice0);
  if (device0_result.empty()) {
    return false;
  }
  std::string device1_result = GetStrFromConfigFile(file, kSplitDevice1);
  if (device1_result.empty()) {
    return false;
  }
  bool device0_flag = false;
  bool device1_flag = false;
  for (const auto &device : config_devices) {
    if (device == device0_result) {
      device0_flag = true;
    }
    if (device == device1_result) {
      device1_flag = true;
    }
  }
  if (!device0_flag || !device1_flag) {
    return false;
  }
  const char delimiter = ';';
  std::vector<std::string> device_rates = lite::SplitStringToVector(compute_rate_result, delimiter);
  const char colon = ':';
  for (const auto &device : device_rates) {
    std::vector<std::string> rate = lite::SplitStringToVector(device, colon);
    int64_t compute_rate = 0;
    try {
      compute_rate = std::stoi(rate.back());
    } catch (const std::exception &e) {
      MS_LOG(ERROR) << "Get compute rate failed: " << e.what();
      return false;
    }
    parallel_split_config->parallel_compute_rates_.push_back(compute_rate);
  }
  const size_t support_rates_num = 2;
  if (parallel_split_config->parallel_compute_rates_.size() != support_rates_num) {
    return false;
  }
  int64_t bigger_rate = INT32_MIN;
  int64_t smaller_rate = INT32_MAX;
  for (const auto &rate : parallel_split_config->parallel_compute_rates_) {
    if (rate <= 0 || rate > INT32_MAX) {
      return false;
    }
    bigger_rate = std::max(rate, bigger_rate);
    smaller_rate = std::min(rate, smaller_rate);
  }
  parallel_split_config->parallel_devices_.push_back(device0_result);
  parallel_split_config->parallel_devices_.push_back(device1_result);
  // parall_split_type will extend by other user's attr
  parallel_split_config->parallel_split_type_ = SplitByUserRatio;
  if (smaller_rate == 0) {
    MS_LOG(ERROR) << "smaller_rate is zero";
    return false;
  }
  return bigger_rate / smaller_rate <= kMaxSplitRatio;
}

std::string ConverterImpl::GetStrFromConfigFile(const std::string &file, const std::string &target_key) {
  std::string res;
  if (file.empty()) {
    MS_LOG(ERROR) << "file is nullptr";
    return res;
  }
  auto resolved_path = std::make_unique<char[]>(PATH_MAX);
  if (resolved_path == nullptr) {
    MS_LOG(ERROR) << "new resolved_path failed";
    return "";
  }

#ifdef _WIN32
  auto *real_path = _fullpath(resolved_path.get(), file.c_str(), kPathLengthUpperLimit);
#else
  char *real_path = realpath(file.c_str(), resolved_path.get());
#endif
  if (real_path == nullptr || strlen(real_path) == 0) {
    MS_LOG(ERROR) << "file path is not valid : " << file;
    return "";
  }
  std::ifstream ifs(resolved_path.get());
  if (!ifs.good()) {
    MS_LOG(ERROR) << "file: " << real_path << " is not exist";
    return res;
  }
  if (!ifs.is_open()) {
    MS_LOG(ERROR) << "file: " << real_path << "open failed";
    return res;
  }
  std::string line;
  while (std::getline(ifs, line)) {
    lite::Trim(&line);
    if (line.empty() || line.at(0) == '#' || line.at(0) == '[') {
      continue;
    }
    auto index = line.find('=');
    if (index == std::string::npos) {
      MS_LOG(ERROR) << "the config file is invalid, can not find '=', please check";
      return "";
    }
    auto key = line.substr(0, index);
    auto value = line.substr(index + 1);
    lite::Trim(&key);
    lite::Trim(&value);
    if (key == target_key) {
      return value;
    }
  }
  return res;
}

int RunConverter(const std::shared_ptr<ConverterPara> &param, void **model_data, size_t *data_size, bool not_save) {
  mindspore::common_log_init();

  ConverterImpl converter_impl;
  auto meta_graph = converter_impl.Convert(param);
  NotSupportOp::GetInstance()->PrintOps();
  int status = ReturnCode::GetSingleReturnCode()->status_code();
  std::ostringstream oss;
  if (meta_graph == nullptr) {
    oss.clear();
    oss << "CONVERT RESULT FAILED:" << status << " " << GetErrorInfo(status);
    MS_LOG(ERROR) << oss.str();
    std::cout << oss.str() << std::endl;
    status = RET_ERROR;
    return status;
  }
  //   save graph to file
  meta_graph->version = Version();

  if (param->pre_infer) {
    status = PreInference(*meta_graph, param->train_model);
    if (status != RET_OK) {
      oss.clear();
      oss << "PRE INFERENCE FAILED:" << status << " " << GetErrorInfo(status);
      MS_LOG(ERROR) << oss.str();
      std::cout << oss.str() << std::endl;
      delete meta_graph;
      return status;
    }
  }

  if (param->microParam.enable_micro) {
    status = micro::Coder::MicroSourceCodeGeneration(*meta_graph, param->output_file, param->microParam.codegen_mode,
                                                     param->microParam.target, param->microParam.support_parallel,
                                                     param->microParam.debug_mode);
    if (status != RET_OK) {
      delete meta_graph;
      oss.clear();
      oss << "MICRO CODEGEN FAILED:" << status << " " << GetErrorInfo(status);
      MS_LOG(ERROR) << oss.str();
      std::cout << oss.str() << std::endl;
      return status;
    }
  } else {
    unsigned char encKey[kEncMaxLen] = {0};
    size_t keyLen = 0;
    if (param->enable_encryption) {
      if (!param->encrypt_key.empty()) {
        keyLen = lite::Hex2ByteArray(param->encrypt_key, encKey, kEncMaxLen);
        if (keyLen != kEncMaxLen) {
          MS_LOG(ERROR) << "enc_key must expressed in hexadecimal characters "
                        << " and only support AES-GCM method and the key length is 16.";
          return RET_INPUT_PARAM_INVALID;
        }
      } else {
        MS_LOG(ERROR) << "If you don't need to use model encryption, please set --encryption=false.";
        return RET_INPUT_PARAM_INVALID;
      }
    }
    if (not_save) {
      flatbuffers::FlatBufferBuilder builder(kFlatbuffersBuilderInitSize);
      *model_data = static_cast<void *>(MetaGraphSerializer::GetMetaGraphPackedBuff(&builder, *meta_graph, data_size));
    } else {
      status = MetaGraphSerializer::Save(*meta_graph, param->output_file, encKey, keyLen, param->encrypt_mode);
    }
    if (memset_s(encKey, kEncMaxLen, 0, kEncMaxLen) != EOK) {
      MS_LOG(ERROR) << "memset failed.";
      delete meta_graph;
      return RET_ERROR;
    }
    if (status != RET_OK) {
      delete meta_graph;
      oss.clear();
      oss << "SAVE GRAPH FAILED:" << status << " " << GetErrorInfo(status);
      MS_LOG(ERROR) << oss.str();
      std::cout << oss.str() << std::endl;
      return status;
    }
  }
  delete meta_graph;
  oss.clear();
  oss << "CONVERT RESULT SUCCESS:" << status;
  MS_LOG(INFO) << oss.str();
  std::cout << oss.str() << std::endl;
  return status;
}
}  // namespace lite
}  // namespace mindspore
