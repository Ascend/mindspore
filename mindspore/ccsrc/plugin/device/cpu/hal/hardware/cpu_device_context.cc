/**
 * Copyright 2021-2022 Huawei Technologies Co., Ltd
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

#include "plugin/device/cpu/hal/hardware/cpu_device_context.h"
#include <string>
#include "plugin/device/cpu/hal/device/cpu_device_address.h"
#include "plugin/device/cpu/hal/device/cpu_memory_manager.h"
#ifdef ENABLE_AKG
#include "plugin/device/cpu/kernel/akg/akg_cpu_kernel_build.h"
#endif
#include "plugin/factory/ms_factory.h"
#include "plugin/device/cpu/kernel/cpu_kernel.h"
#include "kernel/kernel_build_info.h"
#include "plugin/device/cpu/hal/device/kernel_select_cpu.h"
#include "utils/trace_base.h"
#include "common/graph_kernel/graph_kernel_flags.h"
#include "backend/common/optimizer/optimizer.h"
#include "backend/common/optimizer/pass_manager.h"
#include "backend/common/optimizer/common_backend_optimization.h"
#include "backend/common/optimizer/dynamic_shape/dynamic_shape_helper.h"
#include "plugin/device/cpu/optimizer/insert_cast_cpu.h"
#include "plugin/device/cpu/optimizer/insert_format_transform_op.h"
#include "backend/common/pass/communication_op_fusion.h"
#include "backend/common/pass/replace_node_by_proxy.h"
#include "backend/common/pass/erase_visit_attr.h"
#include "common/graph_kernel/adapter/graph_kernel_optimization.h"
#include "common/graph_kernel/adapter/expander.h"
#include "common/graph_kernel/value_graph_binder.h"
#include "backend/common/session/anf_runtime_algorithm.h"
#include "include/common/utils/anfalgo.h"
#include "profiler/device/cpu/cpu_profiling.h"
#ifdef WITH_BACKEND
#include "plugin/device/cpu/hal/hardware/ms_collective_comm_lib.h"
#endif
#ifndef ENABLE_SECURITY
#include "debug/data_dump/dump_json_parser.h"
#endif

namespace mindspore {
namespace device {
namespace cpu {
using mindspore::kernel::KernelBuildInfo;

void CPUDeviceContext::Initialize() {
  if (initialized_) {
    return;
  }
  device_res_manager_->Initialize();

#ifndef ENABLE_SECURITY
  // Dump json config file if dump is enabled.
  auto rank_id = 0;
  auto &json_parser = DumpJsonParser::GetInstance();
  json_parser.Parse();
  json_parser.CopyDumpJsonToDir(rank_id);
  json_parser.CopyMSCfgJsonToDir(rank_id);
#endif

  initialized_ = true;
}

void CPUDeviceContext::Destroy() { device_res_manager_->Destroy(); }

void CPUDeviceResManager::Initialize() {
  mem_manager_ = std::make_shared<CPUMemoryManager>();
  MS_EXCEPTION_IF_NULL(mem_manager_);
}

void CPUDeviceResManager::Destroy() {
  // Release memory.
  if (mem_manager_ != nullptr) {
    mem_manager_->Finalize();
    mem_manager_ = nullptr;
  }
}

void *CPUDeviceResManager::AllocateMemory(size_t size) const {
  MS_EXCEPTION_IF_NULL(mem_manager_);
  return mem_manager_->MallocMemFromMemPool(size, false);
}

void CPUDeviceResManager::FreeMemory(void *ptr) const {
  MS_EXCEPTION_IF_NULL(ptr);
  MS_EXCEPTION_IF_NULL(mem_manager_);
  mem_manager_->FreeMemFromMemPool(ptr);
}

std::vector<void *> CPUDeviceResManager::AllocateContinuousMemory(const std::vector<size_t> &size_list) const {
  return mem_manager_->MallocContinuousMemFromMemPool(size_list);
}

DeviceAddressPtr CPUDeviceResManager::CreateDeviceAddress(void *const device_ptr, size_t device_size,
                                                          const string &format, TypeId type_id,
                                                          const ShapeVector &shape) const {
  auto device_address = std::make_shared<CPUDeviceAddress>(device_ptr, device_size, format, type_id,
                                                           device_context_->device_context_key().device_name_,
                                                           device_context_->device_context_key().device_id_);
  device_address->set_host_shape(shape);
  return device_address;
}

void CPUKernelExecutor::OptimizeGraph(const FuncGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  auto kernel_graph = graph->cast<KernelGraphPtr>();
  MS_EXCEPTION_IF_NULL(kernel_graph);
  if (kernel_graph->is_from_single_op()) {
    SetOperatorInfo(kernel_graph);
    OptimizeGraphImpl(kernel_graph);
    UpdateKernelRefInfo(kernel_graph);
  } else {
    // Update Graph Dynamic Shape Attr.
    opt::AddDynamicShapeAttrPass(kernel_graph);

    SetOperatorInfo(kernel_graph);
    OptimizeGraphImpl(kernel_graph);

    // Run final optimization.
    opt::CommonFinalOptimization(kernel_graph);

#ifdef ENABLE_AKG
    // Run graph kernel fusion optimization
    if (graphkernel::GraphKernelFlags::GetInstance().IsEnableGraphKernel()) {
      graphkernel::GraphKernelOptimize(kernel_graph);
      kernel_graph->SetExecOrderByDefault();
    }
#endif
  }
}

void CPUKernelExecutor::UpdateKernelRefInfo(const KernelGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  const std::vector<CNodePtr> &kernels = graph->execution_order();
  for (const auto &kernel : kernels) {
    MS_EXCEPTION_IF_NULL(kernel);
    const std::string &op_name = common::AnfAlgo::GetCNodeName(kernel);

    auto kernel_attr_list = kernel::NativeCpuKernelMod::GetCpuSupportedList(op_name);
    if (kernel_attr_list.empty()) {
      MS_LOG(DEBUG) << "kernel_attr_list is empty";
      return;
    }

    auto kernel_info = dynamic_cast<device::KernelInfo *>(kernel->kernel_info());
    MS_EXCEPTION_IF_NULL(kernel_info);
    kernel_info->set_ref_map(kernel_attr_list[0].GetAllOutInRef(), kernel_attr_list[0].GetOutInRefMap());
  }
}

void CPUKernelExecutor::OptimizeGraphImpl(const KernelGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  auto optimizer = std::make_shared<opt::GraphOptimizer>();
  auto pm = std::make_shared<opt::PassManager>();
  pm->AddPass(std::make_shared<opt::InsertFormatTransformOpCPU>("insert_format_transform_op_cpu"));
  pm->AddPass(std::make_shared<opt::AllReduceFusion>());
  pm->AddPass(std::make_shared<opt::InsertCastCPU>("insert_cast"));
  pm->AddPass(std::make_shared<opt::EraseVisitAttr>());
  optimizer->AddPassManager(pm);
  (void)optimizer->Optimize(graph);
  graph->SetExecOrderByDefault();
}

namespace {
void SetControlOpInfo(const CNodePtr &kernel_node) {
  MS_EXCEPTION_IF_NULL(kernel_node);
  std::vector<std::string> inputs_format;
  std::vector<TypeId> inputs_type;
  size_t input_num = common::AnfAlgo::GetInputTensorNum(kernel_node);
  for (size_t input_index = 0; input_index < input_num; ++input_index) {
    (void)inputs_format.emplace_back(kOpFormat_DEFAULT);
    inputs_type.push_back(common::AnfAlgo::GetPrevNodeOutputInferDataType(kernel_node, input_index));
  }
  std::vector<std::string> outputs_format;
  std::vector<TypeId> outputs_type;
  size_t output_num = common::AnfAlgo::GetOutputTensorNum(kernel_node);
  for (size_t output_index = 0; output_index < output_num; ++output_index) {
    (void)outputs_format.emplace_back(kOpFormat_DEFAULT);
    outputs_type.push_back(common::AnfAlgo::GetOutputInferDataType(kernel_node, output_index));
  }

  auto builder = std::make_shared<KernelBuildInfo::KernelBuildInfoBuilder>();
  builder->SetInputsFormat(inputs_format);
  builder->SetInputsDeviceType(inputs_type);
  builder->SetOutputsFormat(outputs_format);
  builder->SetOutputsDeviceType(outputs_type);

  AnfAlgo::SetSelectKernelBuildInfo(builder->Build(), kernel_node.get());
}

// Before creating the kernel, check whether the node has completed the operator selection. If not, the operator
// selection needs to be performed to set kernel info.
void SetKernelInfoBeforeCreateKernel(const std::vector<CNodePtr> &nodes) {
  // Check whether the node has completed operator selection.
  for (const auto &node : nodes) {
    if (AnfAlgo::GetSelectKernelBuildInfo(node) != nullptr) {
      continue;
    }

    // Kernel selection process for non control op.
    if (!common::AnfAlgo::IsControlOpExecInBackend(node)) {
      auto [msg, etype] = SetKernelInfoWithMsg(node);
      if (!msg.empty()) {
        MS_EXCEPTION(etype) << msg;
      }
    } else {
      // Kernel selection process for control op.
      SetControlOpInfo(node);
    }
  }
}
}  // namespace

void CPUKernelExecutor::SetOperatorInfo(const KernelGraphPtr &graph) const {
#ifdef ENABLE_AKG
  bool do_expand = false;
  auto mng = graph->manager();
  if (mng == nullptr) {
    mng = Manage(graph, true);
    graph->set_manager(mng);
  }
#endif
  auto &node_list = graph->execution_order();
  for (auto &node : node_list) {
    if (!common::AnfAlgo::IsControlOpExecInBackend(node)) {
      auto [msg, etype] = SetKernelInfoWithMsg(node);
      if (msg.empty()) {
        continue;
      }
#ifdef ENABLE_AKG
      auto f = [](const CNodePtr &n) {
        auto res = SetKernelInfoWithMsg(n);
        return res.first.empty();
      };
      auto cnode = graphkernel::TryExpandCNode(node, f);
      if (cnode == nullptr) {
        MS_EXCEPTION(etype) << msg;
      }
      (void)mng->Replace(node, cnode);
      MS_LOG(INFO) << msg << " but expand success.";
      auto expand_fg = GetCNodeFuncGraph(cnode);
      graphkernel::InlineExpandFuncGraph(cnode, expand_fg);
      do_expand = true;
#else
      MS_EXCEPTION(etype) << msg;
#endif
    } else {
      SetControlOpInfo(node);
    }
  }
#ifdef ENABLE_AKG
  if (do_expand) {
    graphkernel::BindValueToGraph().Run(graph);
    graph->SetExecOrderByDefault();
  }
#endif
}
void CPUKernelExecutor::CreateKernel(const std::vector<CNodePtr> &nodes) const {
  SetKernelInfoBeforeCreateKernel(nodes);

  kernel::KernelMeta *bin_map = kernel::KernelMeta::GetInstance();
  MS_EXCEPTION_IF_NULL(bin_map);
  std::vector<AnfNodePtr> akg_nodes;
  for (const auto &node : nodes) {
    MS_EXCEPTION_IF_NULL(node);
    if (common::AnfAlgo::IsControlOpExecInBackend(node)) {
      continue;
    }
    if (session::AnfRuntimeAlgorithm::GetKernelType(node) == KernelType::AKG_KERNEL) {
      if (!bin_map->initialized()) {
        bin_map->Initialize();
      }
      akg_nodes.push_back(node);
      continue;
    }
    std::string kernel_name = common::AnfAlgo::GetCNodeName(node);

    std::shared_ptr<kernel::NativeCpuKernelMod> cpu_kernel =
      kernel::Factory<kernel::NativeCpuKernelMod>::Instance().Create(kernel_name);

    if (!cpu_kernel) {
      MS_LOG(EXCEPTION) << "Build cpu operator[" << node->fullname_with_scope() << "] failed";
    }

    // This branch would be removed When KernelMode rectification is complete
    auto discard_cpu_kernel_mod = std::dynamic_pointer_cast<kernel::DeprecatedNativeCpuKernelMod>(cpu_kernel);
    if (discard_cpu_kernel_mod) {
      discard_cpu_kernel_mod->SetCpuRefMapToKernelInfo(node);
      discard_cpu_kernel_mod->Init(node);
      AnfAlgo::SetKernelMod(discard_cpu_kernel_mod, node.get());
    } else {
      auto kernel_attrs = cpu_kernel->GetOpSupport();
      kernel::SetCpuRefMapToKernelInfo(node, kernel_attrs);
      auto thread_pool = kernel::GetActorMgrInnerThreadPool();
      cpu_kernel->SetThreadPool(thread_pool);
      auto args = kernel::AbstractArgsFromCNode(node);
      auto ret = cpu_kernel->Init(args.op, args.inputs, args.outputs);
      if (!ret) {
        MS_LOG(EXCEPTION) << trace::DumpSourceLines(node);
      }
      if (cpu_kernel->Resize(args.op, args.inputs, args.outputs, kernel::GetKernelDepends(node)) ==
          kernel::KRET_RESIZE_FAILED) {
        MS_LOG(EXCEPTION) << "CPU kernel op [" << node->fullname_with_scope() << "] Resize failed.";
      }
      AnfAlgo::SetKernelMod(cpu_kernel, node.get());
    }
  }
#ifdef ENABLE_AKG
  kernel::AkgCpuKernelBuilder akg_cpu_kernel_builder;
  (void)akg_cpu_kernel_builder.AkgKernelParallelBuild(akg_nodes);
#endif
}

void CPUKernelExecutor::PreprocessBeforeRun(const FuncGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  auto kernel_graph = graph->cast<KernelGraphPtr>();
  MS_EXCEPTION_IF_NULL(kernel_graph);
  auto profiler_inst = profiler::cpu::CPUProfiler::GetInstance();
  MS_EXCEPTION_IF_NULL(profiler_inst);
  if (kernel_graph->is_dynamic_shape()) {
    profiler_inst->SetNetDynamicShapeStatus();
  }
  if (!kernel_graph->is_from_single_op()) {
    // Remove reorder after PS feature finish adapting push/pull in auto_monad.
    auto execution_order = kernel_graph->execution_order();
    common::AnfAlgo::ReorderPosteriorExecList(NOT_NULL(&execution_order));
    kernel_graph->set_execution_order(execution_order);
  }
}

bool CPUKernelExecutor::LaunchKernel(const CNodePtr &kernel, const std::vector<AddressPtr> &inputs,
                                     const std::vector<AddressPtr> &workspace,
                                     const std::vector<AddressPtr> &outputs) const {
  MS_EXCEPTION_IF_NULL(kernel);
  MS_LOG(DEBUG) << "Launch kernel: " << kernel->fullname_with_scope();
  auto kernel_mod = AnfAlgo::GetKernelMod(kernel);
  MS_EXCEPTION_IF_NULL(kernel_mod);

  // Some CPU kernels can't initialize kernel and launch kernel in different thread, so reinitialize the kernels before
  // launch.
  if (kOpNotSupportMultiThreadExecList.find(common::AnfAlgo::GetCNodeName(kernel)) !=
      kOpNotSupportMultiThreadExecList.end()) {
    auto cpu_kernel_mod = dynamic_cast<kernel::DeprecatedNativeCpuKernelMod *>(kernel_mod);
    MS_EXCEPTION_IF_NULL(cpu_kernel_mod);
    cpu_kernel_mod->InitKernel(kernel);
  }
#ifndef ENABLE_SECURITY
  const auto &profiler_inst = profiler::cpu::CPUProfiler::GetInstance();
  MS_EXCEPTION_IF_NULL(profiler_inst);
  if (profiler_inst->GetEnableFlag()) {
    return LaunchKernelWithProfiling(kernel, inputs, workspace, outputs);
  }
#endif
  return DoLaunchKernel(kernel_mod, inputs, workspace, outputs);
}

bool CPUDeviceResManager::LoadCollectiveCommLib() {
  bool using_mpi = common::UseMPI();
  if (using_mpi) {
    std::string mpi_comm_lib_name = "libmpi_collective.so";
    auto loader = std::make_shared<CollectiveCommLibLoader>(mpi_comm_lib_name);
    MS_EXCEPTION_IF_NULL(loader);
    if (!loader->Initialize()) {
      MS_LOG(EXCEPTION) << "Failed to load mpi collective library.";
      return false;
    }

    void *collective_comm_lib_handle = loader->collective_comm_lib_ptr();
    MS_EXCEPTION_IF_NULL(collective_comm_lib_handle);

    auto instance_func = DlsymFuncObj(communication_lib_instance, collective_comm_lib_handle);
    collective_comm_lib_ = instance_func();
    MS_EXCEPTION_IF_NULL(collective_comm_lib_);
  } else {
#ifdef WITH_BACKEND
    collective_comm_lib_ = &MsCollectiveCommLib::GetInstance();
    MS_EXCEPTION_IF_NULL(collective_comm_lib_);
#endif
  }
  return true;
}

bool CPUKernelExecutor::LaunchKernelWithProfiling(const CNodePtr &kernel, const std::vector<AddressPtr> &inputs,
                                                  const std::vector<AddressPtr> &workspace,
                                                  const std::vector<AddressPtr> &outputs) const {
  MS_EXCEPTION_IF_NULL(kernel);

  auto profiler_inst = profiler::cpu::CPUProfiler::GetInstance();
  MS_EXCEPTION_IF_NULL(profiler_inst);

  auto kernel_mod = AnfAlgo::GetKernelMod(kernel);
  MS_EXCEPTION_IF_NULL(kernel_mod);

  uint32_t pid = IntToUint(getpid());
  // cpu support multi-thread with mindrt for profiling.
  profiler_inst->OpDataProducerBeginParallel(kernel->fullname_with_scope(), pid);
  bool ret = DoLaunchKernel(kernel_mod, inputs, workspace, outputs);
  profiler_inst->OpDataProducerEndParallel(kernel->fullname_with_scope());
  profiler_inst->RecordFrameWorkInfo(kernel);
  return ret;
}

bool CPUKernelExecutor::DoLaunchKernel(KernelMod *const kernel_mod, const std::vector<AddressPtr> &inputs,
                                       const std::vector<AddressPtr> &workspace,
                                       const std::vector<AddressPtr> &outputs) const {
  MS_EXCEPTION_IF_NULL(kernel_mod);
  return kernel_mod->Launch(inputs, workspace, outputs, nullptr);
}

MS_REGISTER_DEVICE(kCPUDevice, CPUDeviceContext);
}  // namespace cpu
}  // namespace device
}  // namespace mindspore
