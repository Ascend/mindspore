/**
 * Copyright 2022 Huawei Technologies Co., Ltd
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
#include "src/runtime/cxx_api/model_pool/model_pool.h"
#include <unistd.h>
#include <future>
#include "src/common/log_adapter.h"
#include "include/lite_types.h"
#include "src/runtime/inner_allocator.h"
#include "src/common/file_utils.h"
#include "src/runtime/pack_weight_manager.h"
#include "src/runtime/numa_adapter.h"
#include "src/common/common.h"
namespace mindspore {
namespace {
constexpr int kNumDeviceInfo = 2;
constexpr int kNumIndex = 2;
constexpr int kNumCoreDataLen = 3;
constexpr int kNumMaxTaskQueueSize = 1000;
constexpr int kNumPhysicalCoreThreshold = 16;
constexpr int kDefaultWorkerNumPerPhysicalCpu = 2;
constexpr int kDefaultThreadsNum = 8;
constexpr int kInvalidNumaId = -1;
int GetCoreNum() {
  int core_num = 1;
#if defined(_MSC_VER) || defined(_WIN32)
  SYSTEM_INFO sysinfo;
  GetSystemInfo(&sysinfo);
  core_num = sysinfo.dwNumberOfProcessors;
#else
  core_num = sysconf(_SC_NPROCESSORS_CONF);
#endif
  return core_num;
}

Status DistinguishPhysicalAndLogical(std::vector<int> *physical_list, std::vector<int> *logical_list) {
  int processor_id = -1;
  int physical_id = -1;
  int core_id = -1;
  // physical id <=> one physical cpu core id
  std::unordered_map<int, std::vector<int>> ids;
  std::ifstream infile("/proc/cpuinfo", std::ios::in);
  std::string line;
  int data_size = 0;
  while (getline(infile, line)) {
    auto line_size = line.size();
    if (line.find("processor") != std::string::npos) {
      auto it = line.find(": ") + kNumIndex;
      processor_id = std::atoi(line.substr(it, line_size - 1).c_str());
      data_size++;
    }
    if (line.find("physical id") != std::string::npos) {
      auto it = line.find(": ") + kNumIndex;
      physical_id = std::atoi(line.substr(it, line_size - 1).c_str());
      data_size++;
    }
    if (line.find("core id") != std::string::npos) {
      auto it = line.find(": ") + kNumIndex;
      core_id = std::atoi(line.substr(it, line_size - 1).c_str());
      data_size++;
    }
    if (data_size == kNumCoreDataLen) {
      if (core_id == -1 && physical_id == -1) {
        MS_LOG(DEBUG) << "All cores are physical cores.";
        int core_size = GetCoreNum();
        for (int core_num = 0; core_num < core_size; core_num++) {
          physical_list->push_back(core_num);
        }
        return kSuccess;
      }
      data_size = 0;
      if (ids.find(physical_id) == ids.end()) {
        std::vector<int> core_id_list = {core_id};
        ids.insert(std::make_pair(physical_id, core_id_list));
        physical_list->push_back(processor_id);
        continue;
      }
      if (find(ids[physical_id].begin(), ids[physical_id].end(), core_id) == ids[physical_id].end()) {
        ids[physical_id].push_back(core_id);
        physical_list->push_back(processor_id);
        continue;
      } else {
        logical_list->push_back(processor_id);
      }
    }
  }
  return kSuccess;
}

int GetDefaultThreadNum() {
  std::vector<int> physical_core_lite;
  std::vector<int> logical_core_list;
  auto status = DistinguishPhysicalAndLogical(&physical_core_lite, &logical_core_list);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "DistinguishPhysicalAndLogical failed.";
    return 0;
  }
  auto physical_core_size = physical_core_lite.size();
  if (physical_core_lite.size() <= kNumPhysicalCoreThreshold) {
    return physical_core_size / kDefaultWorkerNumPerPhysicalCpu;
  } else {
    return kDefaultThreadsNum;
  }
}
}  // namespace

Status ModelPool::DistinguishPhysicalAndLogicalByNuma(const std::vector<int> &physical_core_list,
                                                      const std::vector<int> &logical_core_list) {
  std::vector<std::vector<int>> all_numa_core_list;
  auto numa_num = numa::NUMAAdapter::GetInstance()->NodesNum();
  for (int i = 0; i < numa_num; i++) {
    std::vector<int> numa_cpu_list = numa::NUMAAdapter::GetInstance()->GetCPUList(i);
    if (numa_cpu_list.empty()) {
      MS_LOG(ERROR) << i << "-th numa node does not exist";
      return kLiteError;
    }
    all_numa_core_list.push_back(numa_cpu_list);
  }
  MS_CHECK_TRUE_MSG(!all_numa_core_list.empty(), kLiteError, "numa core list is empty.");
  for (auto one_numa_list : all_numa_core_list) {
    MS_CHECK_TRUE_MSG(!one_numa_list.empty(), kLiteError, "one numa core list is empty.");
    std::vector<int> physical_cores;
    std::vector<int> logical_cores;
    for (auto core_id : one_numa_list) {
      if (find(physical_core_list.begin(), physical_core_list.end(), core_id) != physical_core_list.end()) {
        physical_cores.push_back(core_id);
      } else if (find(logical_core_list.begin(), logical_core_list.end(), core_id) != logical_core_list.end()) {
        logical_cores.push_back(core_id);
      } else {
        MS_LOG(ERROR) << "core id not belong physical/logical core id.";
        return kLiteError;
      }
    }
    numa_physical_cores_.push_back(physical_cores);
    numa_logical_cores_.push_back(logical_cores);
  }
  return kSuccess;
}

/*
 * bind numa:
 *      worker 1    worker 2    worker 3    worker 4
 *         |           |           |          |
 *       numa 0  ->  numa 1  ->  numa 0  ->  numa 1
 *
 *  core num: 16          worker num: 4          thread num: 4
 *  physical core id: 0,2,4,6,8,10,12,14    logic core id: 1,3,5,7,9,11,13,15
 *  numa 0: 0,1,2,3,4,5,6,7    numa 1: 8,9,10,11,12,13,14,15
 *
 * result of bind numa:
 *                physical                 logic
 *  numa 0:   worker1: 0,2,4,6       worker3: 1,3,5,7
 *  numa 1:   worker2: 8,10,12,14    worker4: 9,11,13,15
 *
 * */
Status ModelPool::SetNumaBindStrategy(std::vector<std::vector<int>> *all_worker_bind_list,
                                      std::vector<int> *numa_node_id, int thread_num) {
  if (MS_UNLIKELY(thread_num == 0)) {
    MS_LOG(ERROR) << "thread num is zero.";
    return kLiteError;
  }
  if (numa_physical_cores_.empty()) {
    MS_LOG(ERROR) << "numa physical cores is empty.";
    return kLiteError;
  }
  if (numa_physical_cores_.front().size() < static_cast<size_t>(thread_num)) {
    MS_LOG(ERROR) << "thread num more than physical core num. one numa physical core size: "
                  << numa_physical_cores_.front().size();
    return kLiteError;
  }
  std::vector<int> physical_index(numa_physical_cores_.size(), 0);  // numa node size
  std::vector<int> logical_index(numa_logical_cores_.size(), 0);
  size_t bind_numa_id = 0;
  for (size_t i = 0; i < workers_num_; i++) {
    if (bind_numa_id >= numa_physical_cores_.size()) {
      used_numa_node_num_ = bind_numa_id;
      bind_numa_id = 0;
    }
    std::vector<int> worker_bind_list;
    if (physical_index[bind_numa_id] + static_cast<size_t>(thread_num) <= numa_physical_cores_[bind_numa_id].size()) {
      worker_bind_list.insert(worker_bind_list.begin(),
                              numa_physical_cores_[bind_numa_id].begin() + physical_index[bind_numa_id],
                              numa_physical_cores_[bind_numa_id].begin() + physical_index[bind_numa_id] + thread_num);
      physical_index[bind_numa_id] += thread_num;
    } else if (logical_index[bind_numa_id] + static_cast<size_t>(thread_num) <=
               numa_logical_cores_[bind_numa_id].size()) {
      worker_bind_list.insert(worker_bind_list.begin(),
                              numa_logical_cores_[bind_numa_id].begin() + logical_index[bind_numa_id],
                              numa_logical_cores_[bind_numa_id].begin() + logical_index[bind_numa_id] + thread_num);
      logical_index[bind_numa_id] += thread_num;
    } else {
      MS_LOG(ERROR) << "not find core id in physical and logical.";
      return kLiteError;
    }
    all_worker_bind_list->push_back(worker_bind_list);
    numa_node_id->push_back(bind_numa_id);
    bind_numa_id++;
  }
  used_numa_node_num_ = used_numa_node_num_ != 0 ? used_numa_node_num_ : bind_numa_id;
  return kSuccess;
}

Status ModelPool::SetBindStrategy(std::vector<std::vector<int>> *all_model_bind_list, std::vector<int> *numa_node_id,
                                  int thread_num) {
  if (thread_num == 0) {
    MS_LOG(ERROR) << "thread num is zero.";
    return kLiteError;
  }
  std::vector<int> physical_core_lite;
  std::vector<int> logical_core_list;
  auto status = DistinguishPhysicalAndLogical(&physical_core_lite, &logical_core_list);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "distinguish physical and logical failed.";
    return kLiteError;
  }
  std::vector<int> all_core_list = physical_core_lite;
  all_core_list.insert(all_core_list.end(), logical_core_list.begin(), logical_core_list.end());
  size_t core_id = 0;
  for (size_t i = 0; i < workers_num_; i++) {
    std::vector<int> bind_id;
    for (int j = 0; j < thread_num; j++) {
      if (core_id >= all_core_list.size()) {
        core_id = 0;
      }
      bind_id.push_back(all_core_list[core_id]);
      core_id++;
    }
    all_model_bind_list->push_back(bind_id);
    numa_node_id->push_back(kInvalidNumaId);
  }
  return kSuccess;
}

Status ModelPool::SetDefaultOptimalModelNum(int thread_num) {
  if (thread_num <= 0) {
    MS_LOG(ERROR) << "the number of threads set in the context is less than 1.";
    return kLiteError;
  }
  if (numa_available_) {
    // now only supports the same number of cores per numa node
    // do not use if there are extra cores
    auto worker_num = 0;
    for (auto one_numa_physical : numa_physical_cores_) {
      worker_num += (one_numa_physical.size() / thread_num);
    }
    for (auto one_numa_logical : numa_logical_cores_) {
      worker_num += (one_numa_logical.size() / thread_num);
    }
    workers_num_ = worker_num;
  } else {
    // each worker binds all available cores in order
    workers_num_ = GetCoreNum() / thread_num;
  }
  return kSuccess;
}

std::shared_ptr<mindspore::Context> ModelPool::GetDefaultContext() {
  MS_LOG(DEBUG) << "use default config.";
  auto context = std::make_shared<Context>();
  if (context == nullptr) {
    MS_LOG(ERROR) << "create default context failed.";
    return nullptr;
  }
  auto thread_num = GetDefaultThreadNum();
  if (thread_num == 0) {
    MS_LOG(ERROR) << "computer thread num failed.";
    return nullptr;
  }
  context->SetThreadNum(thread_num);
  auto &device_list = context->MutableDeviceInfo();
  auto device_info = std::make_shared<CPUDeviceInfo>();
  if (device_info == nullptr) {
    MS_LOG(ERROR) << "device_info is nullptr.";
    return nullptr;
  }
  device_info->SetEnableFP16(false);
  device_list.push_back(device_info);
  return context;
}

Status ModelPool::CheckAffinityCoreList(const std::shared_ptr<RunnerConfig> &runner_config) {
  auto context = runner_config->GetContext();
  auto all_bind_core_list = context->GetThreadAffinityCoreList();
  auto worker_num = runner_config->GetWorkersNum();
  if (worker_num != 0 && !all_bind_core_list.empty() &&
      static_cast<int>(all_bind_core_list.size()) != context->GetThreadNum() * worker_num) {
    MS_LOG(ERROR) << "user set core list size != " << context->GetThreadNum() * worker_num
                  << " If the user sets the Bind core list, the size must be equal to the number of threads "
                     "multiplied by the number of workers";
    return kLiteError;
  }
  if (worker_num != 0 && !all_bind_core_list.empty() &&
      static_cast<int>(all_bind_core_list.size()) == context->GetThreadNum() * worker_num) {
    // Use the core id set by the user. Currently, this function can only be enabled when the worker num is not 0.
    auto max_core_id = GetCoreNum();
    for (size_t i = 0; i < all_bind_core_list.size(); i++) {
      if (all_bind_core_list[i] < 0 || all_bind_core_list[i] >= max_core_id) {
        MS_LOG(ERROR) << "Please set correct core id, core id should be less than " << max_core_id
                      << "and greater than 0";
        return kLiteError;
      }
    }
    is_user_core_list_ = true;
  }
  return kSuccess;
}

std::shared_ptr<Context> ModelPool::GetUserDefineContext(const std::shared_ptr<RunnerConfig> &runner_config) {
  auto context = runner_config->GetContext();
  if (context == nullptr) {
    MS_LOG(ERROR) << "user set config context nullptr.";
    return nullptr;
  }
  if (context->GetThreadNum() < 0) {
    MS_LOG(ERROR) << "Invalid thread num " << context->GetThreadNum();
    return nullptr;
  }
  if (context->GetThreadNum() == 0) {
    // Defaults are automatically adjusted based on computer performance
    auto thread_num = GetDefaultThreadNum();
    if (thread_num == 0) {
      MS_LOG(ERROR) << "computer thread num failed.";
      return nullptr;
    }
    context->SetThreadNum(thread_num);
  }
  auto status = CheckAffinityCoreList(runner_config);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "user set core list failed.";
    return nullptr;
  }
  auto device_list = context->MutableDeviceInfo();
  if (device_list.size() > kNumDeviceInfo) {
    MS_LOG(ERROR) << "model pool only support device CPU or GPU.";
    return nullptr;
  }
  for (size_t i = 0; i < device_list.size(); i++) {
    auto device = device_list[i];
    if (device->GetDeviceType() != kCPU && device->GetDeviceType() != kGPU) {
      MS_LOG(ERROR) << "model pool only support cpu or gpu type.";
      return nullptr;
    }
    if (device->GetDeviceType() == kGPU && device_list.size() == kNumDeviceInfo) {
      return context;
    } else if (device->GetDeviceType() == kCPU) {
      auto cpu_context = device->Cast<CPUDeviceInfo>();
      auto enable_fp16 = cpu_context->GetEnableFP16();
      if (enable_fp16) {
        MS_LOG(ERROR) << "model pool not support enable fp16.";
        return nullptr;
      }
    } else {
      MS_LOG(ERROR) << "context is invalid; If you want run in GPU, you must set gpu device first, and then set cpu "
                       "device";
      return nullptr;
    }
  }
  return context;
}

std::shared_ptr<Context> ModelPool::GetInitContext(const std::shared_ptr<RunnerConfig> &runner_config) {
  std::shared_ptr<mindspore::Context> context = nullptr;
  if (runner_config != nullptr && runner_config->GetContext() != nullptr) {
    use_numa_bind_mode_ = numa_available_ && runner_config->GetContext()->GetThreadAffinityMode() == lite::HIGHER_CPU;
    context = GetUserDefineContext(runner_config);
  } else {
    context = GetDefaultContext();
  }
  if (context == nullptr) {
    MS_LOG(ERROR) << "Init context failed. status=" << kLiteNullptr;
    return nullptr;
  }
  return context;
}

Status ModelPool::SetModelBindMode(std::vector<std::vector<int>> *all_worker_bind_list, std::vector<int> *numa_node_id,
                                   std::shared_ptr<Context> model_context) {
  Status status;
  if (numa_available_) {
    status = SetNumaBindStrategy(all_worker_bind_list, numa_node_id, static_cast<int>(model_context->GetThreadNum()));
  } else {
    status = SetBindStrategy(all_worker_bind_list, numa_node_id, static_cast<int>(model_context->GetThreadNum()));
  }
  if (status != kSuccess) {
    MS_LOG(ERROR) << "Set  bind strategy failed.";
    return kLiteError;
  }
  return kSuccess;
}

Status ModelPool::SetWorkersNum(const std::shared_ptr<RunnerConfig> &runner_config,
                                const std::shared_ptr<Context> &context) {
  if ((runner_config != nullptr && runner_config->GetWorkersNum() == 0) || runner_config == nullptr) {
    // the user does not define the number of models, the default optimal number of models is used
    auto status = SetDefaultOptimalModelNum(context->GetThreadNum());
    if (status != kSuccess) {
      MS_LOG(ERROR) << "SetDefaultOptimalModelNum failed.";
      return kLiteError;
    }
  } else if (runner_config != nullptr && runner_config->GetWorkersNum() > 0) {
    // User defined number of models
    workers_num_ = runner_config->GetWorkersNum();
  } else {
    MS_LOG(ERROR) << "user set worker num " << runner_config->GetWorkersNum() << " < 0";
    return kLiteError;
  }
  return kSuccess;
}

Status ModelPool::SetWorkersNumaId(std::vector<int> *numa_node_id) {
  if (!numa_available_) {
    MS_LOG(WARNING) << "numa is not available.";
    numa_node_id->resize(workers_num_, kInvalidNumaId);
  } else {
    size_t numa_id = 0;
    for (size_t i = 0; i < workers_num_; i++) {
      if (numa_id == numa_node_num_) {
        numa_id = 0;
      }
      numa_node_id->push_back(numa_id);
      numa_id++;
    }
    used_numa_node_num_ = workers_num_ < numa_node_num_ ? workers_num_ : numa_node_num_;
  }
  return kSuccess;
}

ModelPoolConfig ModelPool::CreateGpuModelPoolConfig(const std::shared_ptr<RunnerConfig> &runner_config,
                                                    const std::shared_ptr<Context> &init_context) {
  ModelPoolConfig model_pool_gpu_config;
  auto worker_config = std::make_shared<WorkerConfig>();
  if (worker_config == nullptr) {
    MS_LOG(ERROR) << "new worker config failed.";
    return {};
  }
  if (runner_config != nullptr) {
    worker_config->config_info = runner_config->GetConfigInfo();
  }
  worker_config->worker_id = 0;
  worker_config->context = init_context;
  worker_config->numa_id = -1;
  used_numa_node_num_ = 1;
  workers_num_ = 1;
  model_pool_gpu_config.push_back(worker_config);
  return model_pool_gpu_config;
}

ModelPoolConfig ModelPool::CreateCpuModelPoolConfig(const std::shared_ptr<RunnerConfig> &runner_config,
                                                    const std::shared_ptr<Context> &init_context,
                                                    const std::vector<std::vector<int>> &all_worker_bind_list,
                                                    const std::vector<int> &numa_node_id) {
  ModelPoolConfig model_pool_config;
  for (size_t i = 0; i < workers_num_; i++) {
    auto context = std::make_shared<Context>();
    if (context == nullptr) {
      MS_LOG(ERROR) << "New Context failed.";
      return {};
    }
    auto worker_config = std::make_shared<WorkerConfig>();
    if (worker_config == nullptr) {
      MS_LOG(ERROR) << "new worker config failed.";
      return {};
    }
    context->SetThreadNum(init_context->GetThreadNum());
    context->SetEnableParallel(init_context->GetEnableParallel());
    context->SetInterOpParallelNum(init_context->GetInterOpParallelNum());
    if (init_context->GetThreadAffinityMode() != lite::NO_BIND) {
      // bind by core id
      context->SetThreadAffinity(all_worker_bind_list[i]);
    } else {
      // not bind core , not use numa
      context->SetThreadAffinity(init_context->GetThreadAffinityMode());
    }
    worker_config->numa_id = numa_node_id[i];
    auto &new_device_list = context->MutableDeviceInfo();
    std::shared_ptr<CPUDeviceInfo> device_info = std::make_shared<CPUDeviceInfo>();
    if (device_info == nullptr) {
      MS_LOG(ERROR) << "device_info is nullptr.";
      return {};
    }
    std::shared_ptr<Allocator> allocator = nullptr;
    if (init_context->MutableDeviceInfo().front()->GetAllocator() == nullptr) {
      allocator = std::make_shared<DynamicMemAllocator>(worker_config->numa_id);
    } else {
      allocator = init_context->MutableDeviceInfo().front()->GetAllocator();
    }
    if (allocator == nullptr) {
      MS_LOG(ERROR) << "new allocator failed.";
      return {};
    }
    if (numa_allocator_.find(worker_config->numa_id) == numa_allocator_.end()) {
      numa_allocator_.insert(std::make_pair(worker_config->numa_id, allocator));
    }
    device_info->SetAllocator(allocator);
    device_info->SetEnableFP16(false);
    new_device_list.push_back(device_info);
    if (runner_config != nullptr) {
      worker_config->config_info = runner_config->GetConfigInfo();
    }
    worker_config->context = context;
    worker_config->worker_id = i;
    model_pool_config.push_back(worker_config);
  }
  return model_pool_config;
}

Status ModelPool::InitModelPoolBindList(const std::shared_ptr<Context> &init_context,
                                        std::vector<std::vector<int>> *bind_core_list,
                                        std::vector<int> *bind_numa_list) {
  if (init_context->GetThreadAffinityMode() == lite::HIGHER_CPU) {
    // The user specified the id of the bundled core
    if (is_user_core_list_) {
      auto user_core_list = init_context->GetThreadAffinityCoreList();
      auto thread_num = init_context->GetThreadNum();
      for (size_t work_index = 0; work_index < workers_num_; work_index++) {
        std::vector<int> core_list;
        core_list.insert(core_list.end(), user_core_list.begin() + work_index * thread_num,
                         user_core_list.begin() + work_index * thread_num + thread_num);
        bind_core_list->push_back(core_list);
        bind_numa_list->push_back(kInvalidNumaId);
      }
      return kSuccess;
    }
    auto status = SetModelBindMode(bind_core_list, bind_numa_list, init_context);
    if (status != kSuccess) {
      MS_LOG(ERROR) << "SetModelBindMode failed.";
      return kLiteError;
    }
  } else if (init_context->GetThreadAffinityMode() == lite::NO_BIND) {
    auto status = SetWorkersNumaId(bind_numa_list);
    if (status != kSuccess) {
      MS_LOG(ERROR) << "set worker numa id failed in NO_BIND";
      return kLiteError;
    }
  } else {
    MS_LOG(ERROR) << "not support bind MID_CPU.";
    return kLiteError;
  }
  return kSuccess;
}

ModelPoolConfig ModelPool::CreateModelPoolConfig(const std::shared_ptr<RunnerConfig> &runner_config) {
  auto init_context = GetInitContext(runner_config);
  if (init_context == nullptr) {
    MS_LOG(ERROR) << "context is nullptr.";
    return {};
  }
  auto status = SetWorkersNum(runner_config, init_context);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "set worker num failed.";
    return {};
  }
  // init all bind list
  std::vector<std::vector<int>> bind_core_list;
  std::vector<int> bind_numa_list;
  status = InitModelPoolBindList(init_context, &bind_core_list, &bind_numa_list);
  // if numa is not applicable or numa is not available, numa id is -1
  if (status != kSuccess || bind_numa_list.empty()) {
    MS_LOG(ERROR) << "init model pool bind list failed.";
    return {};
  }
  auto device_num = init_context->MutableDeviceInfo().size();
  if (device_num == 0) {
    MS_LOG(ERROR) << "device_info is null.";
    return {};
  }
  if (device_num > 1) {
    return CreateGpuModelPoolConfig(runner_config, init_context);
  }
  // create all worker config
  ModelPoolConfig model_pool_config =
    CreateCpuModelPoolConfig(runner_config, init_context, bind_core_list, bind_numa_list);
  if (model_pool_config.empty()) {
    MS_LOG(ERROR) << "create cpu model pool config failed.";
    return {};
  }
  return model_pool_config;
}

std::vector<MSTensor> ModelPool::GetInputs() {
  std::vector<MSTensor> inputs;
  if (model_pool_inputs_.empty()) {
    MS_LOG(ERROR) << "model input is empty.";
    return {};
  }
  for (size_t i = 0; i < model_pool_inputs_.size(); i++) {
    auto tensor = mindspore::MSTensor::CreateTensor(model_pool_inputs_.at(i).Name(),
                                                    model_pool_inputs_.at(i).DataType(), {}, nullptr, 0);
    if (tensor == nullptr) {
      MS_LOG(ERROR) << "create tensor failed.";
      return {};
    }
    tensor->SetShape(model_pool_inputs_.at(i).Shape());
    inputs.push_back(*tensor);
    delete tensor;
  }
  return inputs;
}

std::vector<MSTensor> ModelPool::GetOutputs() {
  std::vector<MSTensor> outputs;
  if (model_pool_outputs_.empty()) {
    MS_LOG(ERROR) << "model output is empty.";
    return {};
  }
  for (size_t i = 0; i < model_pool_outputs_.size(); i++) {
    auto tensor = mindspore::MSTensor::CreateTensor(model_pool_outputs_.at(i).Name(),
                                                    model_pool_outputs_.at(i).DataType(), {}, nullptr, 0);
    if (tensor == nullptr) {
      MS_LOG(ERROR) << "create tensor failed.";
      return {};
    }
    outputs.push_back(*tensor);
    delete tensor;
  }
  return outputs;
}

Status ModelPool::InitNumaParameter(const std::shared_ptr<RunnerConfig> &runner_config) {
  numa_available_ = numa::NUMAAdapter::GetInstance()->Available();
  if (!numa_available_ && runner_config->GetWorkersNum() != 0 &&
      runner_config->GetContext()->GetThreadAffinityCoreList().size() != 0) {
    MS_LOG(DEBUG) << "numa node is unavailable.";
    return kSuccess;
  }
  if (runner_config != nullptr && runner_config->GetWorkersNum() != 0 && runner_config->GetContext() != nullptr &&
      runner_config->GetContext()->GetThreadAffinityCoreList().size() != 0) {
    MS_LOG(DEBUG) << "If the user explicitly sets the core list, the numa binding is not performed by default.";
    numa_available_ = false;
    return kSuccess;
  }
  numa_node_num_ = numa::NUMAAdapter::GetInstance()->NodesNum();
  std::vector<int> physical_core_lite;
  std::vector<int> logical_core_list;
  auto status = DistinguishPhysicalAndLogical(&physical_core_lite, &logical_core_list);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "distinguish physical and logical failed.";
    return kLiteError;
  }
  status = DistinguishPhysicalAndLogicalByNuma(physical_core_lite, logical_core_list);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "distinguish physical and logical by numa failed.";
    return kLiteError;
  }
  return kSuccess;
}

Status ModelPool::CreateWorkers(char *graph_buf, size_t size, const ModelPoolConfig &model_pool_config) {
  std::shared_ptr<ModelWorker> model_worker = nullptr;
  if (model_pool_config.size() != workers_num_) {
    MS_LOG(ERROR) << "model pool config size is wrong.";
    return kLiteError;
  }
  bool create_worker_success = true;
  for (size_t i = 0; i < workers_num_; i++) {
    int numa_node_id = model_pool_config[i]->numa_id;
    auto ret = lite::PackWeightManager::GetInstance()->InitPackWeight(graph_buf, size, numa_node_id);
    MS_CHECK_FALSE_MSG(ret != kSuccess, kLiteError, "InitWeightManagerByBuf failed.");
    auto new_model_buf = lite::PackWeightManager::GetInstance()->GetNumaModelBuf(graph_buf, numa_node_id);
    MS_CHECK_TRUE_MSG(new_model_buf != nullptr, kLiteError, "get model buf is nullptr from PackWeightManager");
    model_worker = std::make_shared<ModelWorker>();
    if (model_worker == nullptr) {
      MS_LOG(ERROR) << "model worker is nullptr.";
      return kLiteNullptr;
    }
    int task_queue_id = numa_node_id != -1 ? numa_node_id : 0;
    predict_task_queue_->IncreaseWaitModelNum(1, task_queue_id);
    worker_thread_vec_.push_back(std::thread(&ModelWorker::CreateThreadWorker, model_worker, new_model_buf, size,
                                             model_pool_config[i], predict_task_queue_, &create_worker_success));
    if (all_model_workers_.find(task_queue_id) != all_model_workers_.end()) {
      all_model_workers_[task_queue_id].push_back(model_worker);
    } else {
      all_model_workers_[task_queue_id] = {model_worker};
    }
  }
  // wait for all workers to be created successfully
  for (auto &item : all_model_workers_) {
    auto &workers = item.second;
    for (auto &worker : workers) {
      worker->WaitCreateWorkerDone();
      if (!create_worker_success) {
        MS_LOG(ERROR) << "worker init failed.";
        return kLiteError;
      }
    }
  }
  // init model pool input and output
  if (model_worker != nullptr) {
    model_pool_inputs_ = model_worker->GetInputs();
    model_pool_outputs_ = model_worker->GetOutputs();
  }
  return kSuccess;
}

Status ModelPool::Init(const std::string &model_path, const std::shared_ptr<RunnerConfig> &runner_config) {
  Status status = InitNumaParameter(runner_config);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "Init numa parameter failed.";
    return kLiteError;
  }
  // create model pool config
  auto model_pool_config = CreateModelPoolConfig(runner_config);
  if (model_pool_config.empty()) {
    MS_LOG(ERROR) << "CreateModelPoolConfig failed, context is empty.";
    return kLiteError;
  }
  // create task queue for model pool
  predict_task_queue_ = std::make_shared<PredictTaskQueue>();
  if (predict_task_queue_ == nullptr) {
    MS_LOG(ERROR) << "create PredictTaskQueue failed, predict task queue is nullptr.";
    return kLiteNullptr;
  }
  if (numa_available_) {
    status = predict_task_queue_->InitTaskQueue(used_numa_node_num_, kNumMaxTaskQueueSize);
  } else {
    status = predict_task_queue_->InitTaskQueue(1, kNumMaxTaskQueueSize);
  }
  if (status != kSuccess) {
    MS_LOG(ERROR) << "predict task queue init failed, status=" << status;
    return kLiteError;
  }
  // read model by path and init packed weight by buffer
  size_t size = 0;
  auto graph_buf = lite::ReadFile(model_path.c_str(), &size);
  if (graph_buf == nullptr) {
    MS_LOG(ERROR) << "read file failed.";
    return kLiteNullptr;
  }
  status = CreateWorkers(graph_buf, size, model_pool_config);
  if (status != kSuccess) {
    delete[] graph_buf;
    graph_buf = nullptr;
    MS_LOG(ERROR) << "create worker failed.";
    return kLiteError;
  }
  if (graph_buf != nullptr) {
    delete[] graph_buf;
    graph_buf = nullptr;
  }
  // initialize the task pool
  tasks_ = new (std::nothrow) PredictTask[kNumMaxTaskQueueSize]();
  if (tasks_ == nullptr) {
    MS_LOG(ERROR) << "new task failed.";
    return kLiteNullptr;
  }
  for (size_t i = 0; i < kNumMaxTaskQueueSize; i++) {
    free_tasks_id_.push(i);
  }
  return kSuccess;
}

Status ModelPool::UpdateConfig(const std::string &section, const std::pair<std::string, std::string> &config) {
  for (auto &item : all_model_workers_) {
    auto &workers = item.second;
    for (auto &worker : workers) {
      auto status = worker->UpdateConfig(section, config);
      if (status != kSuccess) {
        MS_LOG(ERROR) << "model pool update config failed, status=" << status;
        return status;
      }
    }
  }
  return kSuccess;
}

std::shared_ptr<ModelWorker> ModelPool::GetMaxWaitWorkerNum(int *max_wait_worker_node_id, int *max_wait_worker_num) {
  *max_wait_worker_node_id = 0;
  *max_wait_worker_num = predict_task_queue_->GetWaitModelNum(0);
  for (size_t i = 1; i < used_numa_node_num_; i++) {
    int worker_num = predict_task_queue_->GetWaitModelNum(i);
    if (*max_wait_worker_num < worker_num) {
      *max_wait_worker_num = worker_num;
      *max_wait_worker_node_id = i;
    }
  }
  if (*max_wait_worker_num > 0) {
    auto &workers = all_model_workers_[*max_wait_worker_node_id];
    auto task_queue_id = *max_wait_worker_node_id;
    for (auto &worker : workers) {
      if (worker->IsAvailable()) {
        *max_wait_worker_num = predict_task_queue_->GetWaitModelNum(task_queue_id);
        *max_wait_worker_node_id = task_queue_id;
        return worker;
      }
    }
  }
  return nullptr;
}

PredictTask *ModelPool::CreatePredictTask(const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs,
                                          const MSKernelCallBack &before, const MSKernelCallBack &after,
                                          size_t *task_id) {
  std::lock_guard<std::mutex> lock(task_id_mutex_);
  if (!free_tasks_id_.empty()) {
    auto item = free_tasks_id_.front();
    *task_id = item;
    free_tasks_id_.pop();
    PredictTask *task = &tasks_[*task_id];
    task->inputs = &inputs;
    task->outputs = outputs;
    task->before = before;
    task->after = after;
    return task;
  } else {
    return nullptr;
  }
}

void ModelPool::UpdateFreeTaskId(size_t id) {
  std::lock_guard<std::mutex> lock(task_id_mutex_);
  free_tasks_id_.push(id);
}

Status ModelPool::Predict(const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs,
                          const MSKernelCallBack &before, const MSKernelCallBack &after) {
  predict_task_mutex_.lock();
  int max_wait_worker_node_id = 0;
  int max_wait_worker_num = 0;
  auto available_worker = GetMaxWaitWorkerNum(&max_wait_worker_node_id, &max_wait_worker_num);
  if (inputs.size() == 0) {
    predict_task_mutex_.unlock();
    MS_LOG(ERROR) << "inputs is invalid. input size: " << inputs.size();
    return kLiteError;
  }
  if (available_worker != nullptr) {
    predict_task_queue_->DecreaseWaitModelNum(1, max_wait_worker_node_id);
    // dispatch tasks directly to workers
    predict_task_mutex_.unlock();
    auto ret = available_worker->Predict(inputs, outputs, before, after);
    if (ret != kSuccess) {
      MS_LOG(ERROR) << "direct predict failed.";
      return kLiteError;
    }
    predict_task_queue_->IncreaseWaitModelNum(1, max_wait_worker_node_id);
    return kSuccess;
  } else {
    // push task to task queue
    size_t task_id;
    auto task = CreatePredictTask(inputs, outputs, before, after, &task_id);
    if (task == nullptr) {
      MS_LOG(ERROR) << "The number of waiting tasks in the queue exceeds the limit, ret=" << kLiteServiceDeny;
      predict_task_mutex_.unlock();
      return kLiteServiceDeny;
    }
    predict_task_queue_->PushPredictTask(task, max_wait_worker_node_id);
    predict_task_mutex_.unlock();
    predict_task_queue_->WaitUntilPredictActive(task, max_wait_worker_node_id);
    UpdateFreeTaskId(task_id);
  }
  return kSuccess;
}

ModelPool::~ModelPool() {
  if (predict_task_queue_ != nullptr) {
    predict_task_queue_->SetPredictTaskDone();
  }
  if (tasks_ != nullptr) {
    delete[] tasks_;
    tasks_ = nullptr;
  }
  for (auto &th : worker_thread_vec_) {
    if (th.joinable()) {
      th.join();
    }
  }
}
}  // namespace mindspore
