/**
 * Copyright 2021-2022 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License"){}
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

#include "plugin/device/gpu/hal/hardware/gpu_device_context.h"
#include <dlfcn.h>
#include <utility>
#include "plugin/device/gpu/hal/device/kernel_info_setter.h"
#include "plugin/device/gpu/hal/device/gpu_kernel_build.h"
#include "plugin/device/gpu/hal/device/gpu_device_address.h"
#include "plugin/device/gpu/hal/device/gpu_memory_manager.h"
#include "plugin/device/gpu/hal/device/gpu_memory_allocator.h"
#include "plugin/device/gpu/hal/device/gpu_stream_assign.h"
#include "plugin/device/gpu/hal/device/distribution/collective_init.h"
#include "plugin/device/gpu/hal/device/gpu_device_manager.h"
#include "runtime/data_queue/data_queue_mgr.h"
#include "kernel/common_utils.h"
#include "plugin/device/gpu/hal/device/gpu_common.h"
#include "plugin/device/gpu/kernel/cuda_impl/cuda_ops/cuda_common.h"
#include "plugin/device/gpu/hal/hardware/optimizer.h"
#include "runtime/device/ms_device_shape_transfer.h"
#include "common/graph_kernel/graph_kernel_flags.h"
#include "plugin/device/gpu/hal/device/gpu_bucket.h"
#include "profiler/device/gpu/gpu_profiling.h"
#include "profiler/device/gpu/gpu_profiling_utils.h"
#include "backend/common/session/kernel_graph.h"
#include "plugin/device/gpu/kernel/gpu_kernel.h"
#include "plugin/device/gpu/kernel/gpu_kernel_factory.h"
#include "backend/common/optimizer/common_backend_optimization.h"
#include "backend/common/optimizer/dynamic_shape/dynamic_shape_helper.h"
#ifdef ENABLE_DUMP_IR
#include "include/common/debug/rdr/recorder_manager.h"
#include "debug/rdr/mem_address_recorder.h"
#endif
#include "include/common/utils/comm_manager.h"
#ifdef ENABLE_DEBUGGER
#include "debug/debugger/debugger.h"
#endif
#ifndef ENABLE_SECURITY
#include "debug/data_dump/dump_json_parser.h"
#endif
#include "backend/common/pass/optimize_updatestate.h"
#include "abstract/ops/primitive_infer_map.h"
#include "common/graph_kernel/adapter/expander.h"
#include "common/graph_kernel/value_graph_binder.h"

namespace mindspore {
namespace device {
namespace gpu {
using KernelGraph = mindspore::session::KernelGraph;

static thread_local bool cur_thread_device_inited{false};

void GPUDeviceContext::Initialize() {
  if (initialized_ == true) {
    if (!device_res_manager_->BindDeviceToCurrentThread()) {
      MS_LOG(EXCEPTION) << "BindDeviceToCurrentThread failed.";
    }
    GPUMemoryAllocator::GetInstance().CheckMaxDeviceMemory();
    return;
  }

  device_res_manager_->Initialize();
  auto gpu_kernel_executor = dynamic_cast<GPUKernelExecutor *>(kernel_executor_.get());
  MS_EXCEPTION_IF_NULL(gpu_kernel_executor);
  gpu_kernel_executor->Initialize();

#ifndef ENABLE_SECURITY
  // Dump json config file if dump is enabled.
  auto rank_id = gpu_kernel_executor->GetRankID();
  auto &json_parser = DumpJsonParser::GetInstance();
  json_parser.Parse();
  json_parser.CopyDumpJsonToDir(rank_id);
  json_parser.CopyMSCfgJsonToDir(rank_id);
#endif
  initialized_ = true;
}

void GPUDeviceResManager::Initialize() {
  // Set device id
  if (CollectiveInitializer::instance().collective_inited()) {
    DeviceContextKey old_key = device_context_->device_context_key();
    device_context_->device_context_key_.device_id_ = CollectiveInitializer::instance().local_rank_id();

    DeviceContextManager::GetInstance().UpdateDeviceContextKey(old_key, device_context_->device_context_key());

    auto ms_context = MsContext::GetInstance();
    MS_EXCEPTION_IF_NULL(ms_context);
    ms_context->set_param<uint32_t>(MS_CTX_DEVICE_ID, device_context_->device_context_key().device_id_);
  }

  MS_LOG(INFO) << "Set GPU device id index " << device_context_->device_context_key().device_id_;
  // Set device id and initialize device resource.
  if (!InitDevice()) {
    MS_LOG(EXCEPTION) << "GPU InitDevice failed.";
  }

  // Initialize memory pool.
  mem_manager_ = std::make_shared<GPUMemoryManager>();
  MS_EXCEPTION_IF_NULL(mem_manager_);
  mem_manager_->Initialize();

  // Initialize NCCL.
  if (CollectiveInitializer::instance().collective_inited()) {
    auto collective_handle = CollectiveInitializer::instance().collective_handle();
    if (collective_handle != nullptr) {
      MS_LOG(INFO) << "Start initializing NCCL communicator for device "
                   << device_context_->device_context_key().device_id_;
      auto init_nccl_comm_funcptr =
        reinterpret_cast<InitNCCLComm>(dlsym(const_cast<void *>(collective_handle), "InitNCCLComm"));
      MS_EXCEPTION_IF_NULL(init_nccl_comm_funcptr);
      (*init_nccl_comm_funcptr)();
      MS_LOG(INFO) << "End initializing NCCL communicator.";
    }
  }
}

bool GPUDeviceResManager::InitDevice() {
  if (GPUDeviceManager::GetInstance().device_count() <= 0) {
    MS_LOG(ERROR) << "No GPU device found.";
    return false;
  }

  if (!GPUDeviceManager::GetInstance().is_device_id_init()) {
    if (!GPUDeviceManager::GetInstance().set_cur_device_id(device_context_->device_context_key().device_id_)) {
      MS_LOG(ERROR) << "Failed to set current device id: "
                    << SizeToInt(device_context_->device_context_key().device_id_);
      return false;
    }
  }
  // Check the Cuda capability
  const float cuda_cap = GET_CUDA_CAP;
  if (cuda_cap < SUPPORTED_CAP) {
    MS_LOG(WARNING) << "The device with Cuda compute capability " << cuda_cap
                    << " is lower than the minimum required capability " << SUPPORTED_CAP
                    << ", this may cause some unexpected problems and severely affect the results. "
                    << "Eg: the outputs are all zeros.\n"
                    << "Device with a compute capability > " << SUPPORTED_CAP << " is required, "
                    << "and it is recommended to use devices with a compute capability >= " << RECOMMEND_SM;
  }

  // Initialize device resource, such as stream, cudnn and cublas handle.
  GPUDeviceManager::GetInstance().InitDevice();

  auto stream = GPUDeviceManager::GetInstance().default_stream();
  MS_ERROR_IF_NULL(stream);
  streams_.push_back(stream);

  void *communication_stream = nullptr;
  GPUDeviceManager::GetInstance().CreateStream(&communication_stream);
  MS_ERROR_IF_NULL(communication_stream);
  streams_.push_back(communication_stream);

  return true;
}

void GPUDeviceResManager::Destroy() {
  if (DataQueueMgr::GetInstance().IsInit()) {
    if (!DataQueueMgr::GetInstance().IsClosed() && !DataQueueMgr::GetInstance().CloseNotify()) {
      MS_LOG(ERROR) << "Could not close gpu data queue.";
    }
    CHECK_OP_RET_WITH_ERROR(DataQueueMgr::GetInstance().Destroy(), "Could not destroy gpu data queue.");
  }

  // Release stream, cudnn and cublas handle, etc.
  GPUDeviceManager::GetInstance().ReleaseDevice();

  // Release device memory
  if (mem_manager_ != nullptr) {
    mem_manager_->Finalize();
    mem_manager_ = nullptr;
  }
}

void GPUDeviceContext::Destroy() {
#ifdef ENABLE_DEBUGGER
  auto debugger = Debugger::GetInstance();
  if (debugger && debugger->debugger_enabled()) {
    debugger->SetTrainingDone(true);
    bool ret = debugger->SendMetadata(false);
    if (!ret) {
      MS_LOG(ERROR) << "Failed to SendMetadata when finalize";
    }
  }
#endif
  auto gpu_kernel_executor = dynamic_cast<GPUKernelExecutor *>(kernel_executor_.get());
  gpu_kernel_executor->Destroy();
  device_res_manager_->Destroy();
}

void *GPUDeviceResManager::AllocateMemory(size_t size) const {
  MS_EXCEPTION_IF_NULL(mem_manager_);
  if (!BindDeviceToCurrentThread()) {
    return nullptr;
  }
  return mem_manager_->MallocMemFromMemPool(size, false);
}

void GPUDeviceResManager::FreeMemory(void *ptr) const {
  MS_EXCEPTION_IF_NULL(mem_manager_);
  MS_EXCEPTION_IF_NULL(ptr);
  mem_manager_->FreeMemFromMemPool(ptr);
}

bool GPUDeviceResManager::AllocateMemory(DeviceAddress *const &address) const {
  MS_EXCEPTION_IF_NULL(address);
  auto device_name_in_address = GetDeviceNameByType(static_cast<const DeviceType>(address->GetDeviceType()));
  if (device_name_in_address != device_context_->device_context_key().device_name_) {
    MS_LOG(EXCEPTION) << "The device address type is wrong: type name in address:" << device_name_in_address
                      << ", type name in context:" << device_context_->device_context_key().device_name_;
  }

  if (address->GetPtr() != nullptr) {
    MS_LOG(ERROR) << "Memory leak detected!";
    return false;
  }

  if (!BindDeviceToCurrentThread()) {
    return false;
  }
  auto device_ptr = mem_manager_->MallocMemFromMemPool(address->GetSize(), address->from_persistent_mem());
  if (!device_ptr) {
    return false;
  }

  address->set_ptr(device_ptr);
  address->set_from_mem_pool(true);
  return true;
}

std::vector<void *> GPUDeviceResManager::AllocateContinuousMemory(const std::vector<size_t> &size_list) const {
  if (!BindDeviceToCurrentThread()) {
    std::vector<void *> ptr_list;
    return ptr_list;
  }
  return mem_manager_->MallocContinuousMemFromMemPool(size_list);
}

DeviceAddressPtr GPUDeviceResManager::CreateDeviceAddress(void *const device_ptr, size_t device_size,
                                                          const string &format, TypeId type_id,
                                                          const ShapeVector &shape) const {
  auto device_address = std::make_shared<GPUDeviceAddress>(device_ptr, device_size, format, type_id,
                                                           device_context_->device_context_key().device_name_,
                                                           device_context_->device_context_key().device_id_);
  device_address->set_host_shape(shape);
  return device_address;
}

void GPUKernelExecutor::PreprocessBeforeRun(const FuncGraphPtr &graph) const {
  auto kernel_graph = graph->cast<KernelGraphPtr>();
  MS_EXCEPTION_IF_NULL(kernel_graph);
  auto profiler_inst = profiler::gpu::GPUProfiler::GetInstance();
  MS_EXCEPTION_IF_NULL(profiler_inst);
  if (kernel_graph->is_dynamic_shape()) {
    profiler_inst->SetNetDynamicShapeStatus();
  }
}

void GPUKernelExecutor::OptimizeGraphWithoutDeviceInfo(const KernelGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  // Operator fusion optimization.
  FuseOperators(graph);
}

void GPUKernelExecutor::OptimizeGraphWithDeviceInfo(const KernelGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  auto ms_context = MsContext::GetInstance();
  MS_EXCEPTION_IF_NULL(ms_context);
  // Graph optimization relevant to device data format
  auto optimizer = std::make_shared<opt::GraphOptimizer>();
  auto pm = std::make_shared<opt::PassManager>();
  pm->AddPass(std::make_shared<opt::BatchNormReluFusion>());
  pm->AddPass(std::make_shared<opt::BatchNormReluGradFusion>());
  pm->AddPass(std::make_shared<opt::BatchNormAddReluFusion>());
  pm->AddPass(std::make_shared<opt::PostBatchNormAddReluFusion>());
  pm->AddPass(std::make_shared<opt::BatchNormAddReluGradFusion>());
  pm->AddPass(std::make_shared<opt::InsertFormatTransformOp>());
  pm->AddPass(std::make_shared<opt::RemoveFormatTransformPair>());
  pm->AddPass(std::make_shared<opt::RemoveRedundantFormatTransform>());
  if (ms_context->get_param<int>(MS_CTX_EXECUTION_MODE) == kGraphMode) {
    // Remove node only used by UpdateState, in order to ensure the correct execution sequence in CudnnInplaceAggregate.
    pm->AddPass(std::make_shared<opt::OptimizeUpdateState>());
    pm->AddPass(std::make_shared<opt::CudnnInplaceAggregate>());
  }
  pm->AddPass(std::make_shared<opt::ReluV2Pass>());
  pm->AddPass(std::make_shared<opt::AddReluV2Fusion>());
  pm->AddPass(std::make_shared<opt::AddReluGradV2Fusion>());
  pm->AddPass(std::make_shared<opt::AllReduceFusion>());
  pm->AddPass(std::make_shared<opt::AdjustDependForParallelOptimizerRecomputeAllGather>());
  pm->AddPass(std::make_shared<opt::AllGatherFusion>());
  pm->AddPass(std::make_shared<opt::ConcatOutputsForAllGather>());
  pm->AddPass(std::make_shared<opt::GetitemTuple>());
  pm->AddPass(std::make_shared<opt::ReducePrecisionFusion>("reduce_precision"));
  optimizer->AddPassManager(pm);
  (void)optimizer->Optimize(graph);
  graph->SetExecOrderByDefault();
}

void GPUKernelExecutor::FuseOperators(const KernelGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  auto optimizer = std::make_shared<opt::GraphOptimizer>();
  auto pm = std::make_shared<opt::PassManager>();
  // In the dynamic shape scene, the infershape stage needs to call the primitive infer function.
  // When the fusion operator generates a new primitive, but there
  // is no corresponding primitive infer function, an error will occur.
  // Therefore, this kind of scene does not support dynamic shape.
  if (graph->is_dynamic_shape()) {
    MS_LOG(INFO) << "Dynamic shape skip some fusion pass";
    pm->AddPass(std::make_shared<opt::PrintReduceFusion>("print_reduce"));
  } else {
    pm->AddPass(std::make_shared<opt::MatMulBiasAddFusion>());
    pm->AddPass(std::make_shared<opt::AdamWeightDecayFusion>());
    pm->AddPass(std::make_shared<opt::AdamFusion>());
    pm->AddPass(std::make_shared<opt::AllToAllFusion>());
    pm->AddPass(std::make_shared<opt::ApplyMomentumWeightDecayScaleFusion>());
    pm->AddPass(std::make_shared<opt::ApplyMomentumScaleFusion>());
    pm->AddPass(std::make_shared<opt::ApplyMomentumWeightDecayFusion>());
    if (!graphkernel::GraphKernelFlags::GetInstance().IsEnableGraphKernel()) {
      pm->AddPass(std::make_shared<opt::CastAllFusion>("cast_all"));
    }
    pm->AddPass(std::make_shared<opt::CombineMomentumFusion>("combine_momentum"));
    pm->AddPass(std::make_shared<opt::ReplaceMomentumCastFusion>());
    pm->AddPass(std::make_shared<opt::ReplaceAddNFusion>());
    pm->AddPass(std::make_shared<opt::PrintReduceFusion>("print_reduce"));
    pm->AddPass(std::make_shared<opt::BCEWithLogitsLossFusion>());
    pm->AddPass(std::make_shared<opt::InsertCastGPU>("insert_cast_gpu"));
    pm->AddPass(std::make_shared<opt::NeighborExchangeV2Fusion>());
    pm->AddPass(std::make_shared<opt::NeighborExchangeV2GradFusion>());
  }
  optimizer->AddPassManager(pm);
  (void)optimizer->Optimize(graph);
  graph->SetExecOrderByDefault();
}

namespace {
void RunOpOptimize(const KernelGraphPtr &kernel_graph) {
  MS_EXCEPTION_IF_NULL(kernel_graph);
  auto optimizer = std::make_shared<opt::GraphOptimizer>();
  auto pm = std::make_shared<opt::PassManager>();
  pm->AddPass(std::make_shared<opt::BCEWithLogitsLossFusion>());
  pm->AddPass(std::make_shared<opt::InsertCastGPU>("insert_cast_gpu"));
  optimizer->AddPassManager(pm);
  (void)optimizer->Optimize(kernel_graph);
  kernel_graph->SetExecOrderByDefault();
}

void RunOpHardwareOptimize(const KernelGraphPtr &kernel_graph) {
  MS_EXCEPTION_IF_NULL(kernel_graph);
  auto optimizer = std::make_shared<opt::GraphOptimizer>();
  auto pm = std::make_shared<opt::PassManager>();
  pm->AddPass(std::make_shared<opt::ReducePrecisionFusion>("reduce_precision"));
  optimizer->AddPassManager(pm);
  (void)optimizer->Optimize(kernel_graph);
  kernel_graph->SetExecOrderByDefault();
}

void RunOpHideNopNode(const KernelGraphPtr &kernel_graph) {
  auto ms_context = MsContext::GetInstance();
  MS_EXCEPTION_IF_NULL(ms_context);
  if (!ms_context->get_param<bool>(MS_CTX_ENABLE_PYNATIVE_INFER)) {
    opt::HideNopNode(kernel_graph.get());
  }
}

void RunOpRemoveNopNode(const KernelGraphPtr &kernel_graph) {
  auto ms_context = MsContext::GetInstance();
  MS_EXCEPTION_IF_NULL(ms_context);
  if (!ms_context->get_param<bool>(MS_CTX_ENABLE_PYNATIVE_INFER)) {
    opt::RemoveNopNode(kernel_graph.get());
  }
}

// Before creating the kernel, check whether the node has completed the operator selection. If not, the operator
// selection needs to be performed to set kernel info.
void SetKernelInfoBeforeCreateKernel(const std::vector<CNodePtr> &nodes) {
  // Check whether the node has completed operator selection.
  for (const auto &node : nodes) {
    if (AnfAlgo::GetSelectKernelBuildInfo(node) != nullptr) {
      continue;
    }

    // Kernel selection process.
    auto [msg, etype] = SetKernelInfoWithMsg(node);
    if (!msg.empty()) {
      MS_EXCEPTION(etype) << msg;
    }
  }
}

// Check whether mutex exists for a stream.
std::pair<bool, std::mutex *> CheckStreamMutexExist(
  const void *stream, const mindspore::HashMap<const void *, std::shared_ptr<std::mutex>> &mtxs_for_streams,
  std::shared_mutex *shd_mtx) {
  MS_EXCEPTION_IF_NULL(stream);
  MS_EXCEPTION_IF_NULL(shd_mtx);
  std::shared_lock<std::shared_mutex> shd_lock(*shd_mtx);
  auto iter = mtxs_for_streams.find(stream);
  if (iter != mtxs_for_streams.end()) {
    MS_EXCEPTION_IF_NULL(iter->second);
    return std::make_pair(true, iter->second.get());
  }
  return std::make_pair(false, nullptr);
}

// Create a mutex for stream.
std::mutex *CreateStreamMutex(const void *stream, std::shared_mutex *shd_mtx,
                              mindspore::HashMap<const void *, std::shared_ptr<std::mutex>> *mtxs_for_streams) {
  MS_EXCEPTION_IF_NULL(stream);
  MS_EXCEPTION_IF_NULL(shd_mtx);
  MS_EXCEPTION_IF_NULL(mtxs_for_streams);

  std::unique_lock<std::shared_mutex> unq_lock(*shd_mtx);
  auto ret_pair = mtxs_for_streams->emplace(stream, std::make_shared<std::mutex>());

  MS_EXCEPTION_IF_NULL(ret_pair.first->second);
  return ret_pair.first->second.get();
}

// The launch kernel is thread-unsafe, and the behavior of delivering the kernel launch to the same stream requires
// lock protection, need to create a separate lock for each stream.
// for GPU, The cublas handle is not thread safety specifically, it is not recommended that multiple threads access the
// same cublas handle at the same time, so need the launch mutex when multiple threads launch the cublas kernels.
std::lock_guard<std::mutex> LockLaunchKernel(const void *stream) {
  MS_EXCEPTION_IF_NULL(stream);
  // Read-write lock for accessing mtxs_for_streams map.
  // When the lock of each stream is created, mtxs_for_streams can be accessed concurrently to improve performance.
  static std::shared_mutex shd_mtx;
  static mindspore::HashMap<const void *, std::shared_ptr<std::mutex>> mtxs_for_streams;

  std::mutex *stream_mtx;
  // Check whether mutex exists for a stream.
  std::pair<bool, std::mutex *> ret_pair = CheckStreamMutexExist(stream, mtxs_for_streams, &shd_mtx);
  if (ret_pair.first) {
    stream_mtx = ret_pair.second;
  } else {
    // Create a mutex for stream.
    stream_mtx = CreateStreamMutex(stream, &shd_mtx, &mtxs_for_streams);
  }

  MS_EXCEPTION_IF_NULL(stream_mtx);
  // Lock kernel launch for the stream.
  return std::lock_guard<std::mutex>(*stream_mtx);
}
}  // namespace

void GPUKernelExecutor::Initialize() {
  res_manager_ = dynamic_cast<GPUDeviceResManager *>(device_context_->device_res_manager_.get());
  MS_EXCEPTION_IF_NULL(res_manager_);
}

void GPUKernelExecutor::Destroy() { res_manager_ = nullptr; }

void GPUKernelExecutor::OptimizeGraph(const FuncGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  auto kernel_graph = graph->cast<KernelGraphPtr>();
  MS_EXCEPTION_IF_NULL(kernel_graph);
  if (kernel_graph->is_from_single_op()) {
    RunOpOptimize(kernel_graph);

    FormatTransformChecker::GetInstance().CheckSupportFormatTransform(kernel_graph);
    SetOperatorInfo(kernel_graph);

    RunOpHardwareOptimize(kernel_graph);

    RunOpHideNopNode(kernel_graph);
    RunOpRemoveNopNode(kernel_graph);
    UpdateKernelRefInfo(kernel_graph);
  } else {
    // Optimization pass which is irrelevant to device type or format.
    OptimizeGraphWithoutDeviceInfo(kernel_graph);

    FormatTransformChecker::GetInstance().CheckSupportFormatTransform(kernel_graph);
    SetOperatorInfo(kernel_graph);

    // Optimization pass which is relevant to device type or format.
    OptimizeGraphWithDeviceInfo(kernel_graph);

    // Run final optimization.
    opt::CommonFinalOptimization(kernel_graph);

    // Graph kernel fusion optimization
    if (graphkernel::GraphKernelFlags::GetInstance().IsEnableGraphKernel()) {
      graphkernel::GraphKernelOptimize(kernel_graph);
      kernel_graph->SetExecOrderByDefault();
    }

    // Assign the stream and insert the send/recv node for all reduce kernel, so must be the last in the optimizer.
    device::gpu::AssignGpuStream(kernel_graph);
  }
}

void GPUKernelExecutor::UpdateKernelRefInfo(const KernelGraphPtr &graph) const {
  MS_EXCEPTION_IF_NULL(graph);
  const std::vector<CNodePtr> &kernels = graph->execution_order();
  for (const auto &kernel : kernels) {
    MS_EXCEPTION_IF_NULL(kernel);
    const std::string &op_name = common::AnfAlgo::GetCNodeName(kernel);

    auto kernel_attr_list = kernel::NativeGpuKernelModFactory::GetInstance().GetGpuSupportedList(op_name);
    if (kernel_attr_list.empty()) {
      MS_LOG(DEBUG) << "kernel_attr_list is empty";
      return;
    }

    auto kernel_info = dynamic_cast<device::KernelInfo *>(kernel->kernel_info());
    MS_EXCEPTION_IF_NULL(kernel_info);
    // For the same kernel, there are currently no multiple Ref info.
    kernel_info->set_ref_map(kernel_attr_list[0].GetAllOutInRef(), kernel_attr_list[0].GetOutInRefMap());
  }
}

void GPUKernelExecutor::SetOperatorInfo(const KernelGraphPtr &graph) const {
  auto mng = graph->manager();
  if (mng == nullptr) {
    mng = Manage(graph, true);
    graph->set_manager(mng);
  }
  bool do_expand = false;
  auto &node_list = graph->execution_order();
  for (auto &node : node_list) {
    auto [msg, etype] = SetKernelInfoWithMsg(node);
    if (msg.empty()) {
      continue;
    }
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
  }
  if (do_expand) {
    graphkernel::BindValueToGraph().Run(graph);
    graph->SetExecOrderByDefault();
  }
}

void GPUKernelExecutor::CreateKernel(const std::vector<CNodePtr> &nodes) const {
  SetKernelInfoBeforeCreateKernel(nodes);
  CreateGPUKernel(nodes);
}

bool GPUKernelExecutor::LaunchKernel(const CNodePtr &kernel, const std::vector<AddressPtr> &inputs,
                                     const std::vector<AddressPtr> &workspace,
                                     const std::vector<AddressPtr> &outputs) const {
  MS_EXCEPTION_IF_NULL(kernel);
  if (!res_manager_->BindDeviceToCurrentThread()) {
    return false;
  }
  bool ret = true;

  auto stream = GetLaunchKernelStream(kernel);
  MS_EXCEPTION_IF_NULL(stream);

#ifndef ENABLE_SECURITY
  const auto &profiler_inst = profiler::gpu::GPUProfiler::GetInstance();
  MS_EXCEPTION_IF_NULL(profiler_inst);

  if (!profiler_inst->GetEnableFlag()) {
#endif
    auto lock = LockLaunchKernel(stream);
    MS_LOG(DEBUG) << "Launch kernel: " << kernel->fullname_with_scope();
    ret = DoLaunchKernel(kernel, inputs, workspace, outputs, stream);
#ifndef ENABLE_SECURITY
  } else {
    auto lock = LockLaunchKernel(stream);
    MS_LOG(DEBUG) << "Launch kernel: " << kernel->fullname_with_scope();
    ret = LaunchKernelWithProfiling(kernel, inputs, workspace, outputs, stream);
  }
#endif
  if (!ret) {
    MS_LOG(ERROR) << "Launch kernel failed, kernel full name: " << kernel->fullname_with_scope();
    return false;
  }

  // Sync running.
  auto ms_context = MsContext::GetInstance();
  MS_EXCEPTION_IF_NULL(ms_context);
  if ((ms_context->get_param<int>(MS_CTX_EXECUTION_MODE) == kPynativeMode) &&
      ms_context->get_param<bool>(MS_CTX_ENABLE_PYNATIVE_SYNCHRONIZE) && !res_manager_->SyncStream()) {
    return false;
  }

  return ret;
}
#ifndef ENABLE_SECURITY
bool GPUKernelExecutor::LaunchKernelWithProfiling(const CNodePtr &kernel, const std::vector<AddressPtr> &inputs,
                                                  const std::vector<AddressPtr> &workspace,
                                                  const std::vector<AddressPtr> &outputs, void *stream) const {
  MS_EXCEPTION_IF_NULL(kernel);
  MS_EXCEPTION_IF_NULL(stream);

  auto kernel_graph = std::dynamic_pointer_cast<KernelGraph>(kernel->func_graph());
  MS_EXCEPTION_IF_NULL(kernel_graph);

  auto profiler_inst = profiler::gpu::GPUProfiler::GetInstance();
  MS_EXCEPTION_IF_NULL(profiler_inst);

  if (profiler::gpu::ProfilingUtils::IsFirstStep(kernel_graph->graph_id())) {
    profiler::gpu::ProfilingTraceInfo profiling_trace =
      profiler::gpu::ProfilingUtils::GetProfilingTraceFromEnv(NOT_NULL(kernel_graph.get()));
    profiler_inst->SetStepTraceOpName(profiling_trace);
  }

  profiler_inst->OpDataProducerBegin(kernel->fullname_with_scope(), res_manager_->streams_.front());
  bool ret = DoLaunchKernel(kernel, inputs, workspace, outputs, stream);
  profiler_inst->OpDataProducerEnd();
  profiler_inst->RecordFrameWorkInfo(kernel);

  auto op_launch_start_end_time = profiler_inst->GetSingleOpLaunchTime();
  MS_LOG(DEBUG) << "Launch kernel:" << kernel->fullname_with_scope() << " cost:"
                << (op_launch_start_end_time.second - op_launch_start_end_time.first) / kBasicTimeTransferUnit;

  if (profiler_inst->GetSyncEnableFlag()) {
    CHECK_RET_WITH_RETURN_ERROR(res_manager_->SyncStream(), "Profiler SyncStream failed.");
  }
  return ret;
}
#endif
bool GPUKernelExecutor::DoLaunchKernel(const CNodePtr &kernel, const std::vector<AddressPtr> &inputs,
                                       const std::vector<AddressPtr> &workspace, const std::vector<AddressPtr> &outputs,
                                       void *stream) const {
  MS_EXCEPTION_IF_NULL(kernel);
  MS_EXCEPTION_IF_NULL(stream);
  auto kernel_mod = AnfAlgo::GetKernelMod(kernel);
  MS_EXCEPTION_IF_NULL(kernel_mod);
  return kernel_mod->Launch(inputs, workspace, outputs, stream);
}

void *GPUKernelExecutor::GetLaunchKernelStream(const CNodePtr &kernel) const {
  void *stream = nullptr;
  if (common::AnfAlgo::HasNodeAttr(kAttrStream, kernel)) {
    auto stream_id = common::AnfAlgo::GetNodeAttr<size_t>(kernel, kAttrStream);
    auto iter = res_manager_->stream_ids_.find(stream_id);
    if (iter == res_manager_->stream_ids_.end()) {
      MS_LOG(EXCEPTION) << "Can not find stream for stream id: " << stream_id;
    }
    stream = iter->second;
  } else {
    stream = res_manager_->streams_.front();
  }

  MS_EXCEPTION_IF_NULL(stream);
  return stream;
}

bool GPUDeviceResManager::SyncStream(size_t stream_id) const {
  void *stream = nullptr;
  auto iter = stream_ids_.find(stream_id);
  if (iter != stream_ids_.end()) {
    stream = iter->second;
  } else {
    if (stream_id >= streams_.size()) {
      MS_LOG(EXCEPTION) << "The stream_id: " << stream_id << " is greater than stream array size: " << streams_.size();
    }
    stream = streams_[stream_id];
  }

  MS_EXCEPTION_IF_NULL(stream);
  bool result = GPUDeviceManager::GetInstance().SyncStream(stream);
#ifdef ENABLE_DUMP_IR
  if (!result) {
    mindspore::RDR::TriggerAll();
  }
  // clear RDR gpu memory info
  mindspore::RDR::ClearMemAddressInfo();
#endif
  return result;
}

bool GPUDeviceResManager::CreateStream(void **stream) const {
  MS_EXCEPTION_IF_NULL(stream);
  if (!CudaDriver::CreateStream(stream)) {
    MS_LOG(ERROR) << "Failed to create CUDA stream.";
    return false;
  }
  return true;
}

bool GPUDeviceResManager::DestroyStream(void *stream) const {
  MS_EXCEPTION_IF_NULL(stream);
  if (!CudaDriver::DestroyStream(stream)) {
    MS_LOG(ERROR) << "Failed to destroy CUDA stream.";
    return false;
  }
  return true;
}

uint32_t GPUKernelExecutor::GetRankID() const {
  bool collective_inited = CollectiveInitializer::instance().collective_inited();
  uint32_t rank_id = 0;
  if (collective_inited) {
    if (!CommManager::GetInstance().GetRankID(kNcclWorldGroup, &rank_id)) {
      MS_LOG(EXCEPTION) << "Failed to get rank id.";
    }
  }
  return rank_id;
}

std::shared_ptr<Bucket> GPUKernelExecutor::CreateBucket(uint32_t bucket_id, uint32_t bucket_size) const {
  MS_EXCEPTION_IF_NULL(res_manager_);
  auto device_context = res_manager_->device_context_;
  MS_EXCEPTION_IF_NULL(device_context);
  auto bucket = std::make_shared<GPUBucket>(bucket_id, bucket_size, device_context->device_context_key().device_id_);
  MS_EXCEPTION_IF_NULL(bucket);
  // One computation stream, one communication stream.
  const size_t min_num_of_stream = 2;
  if (min_num_of_stream > res_manager_->streams_.size()) {
    MS_LOG(EXCEPTION) << "The total stream num: " << res_manager_->streams_.size()
                      << " is less than: " << min_num_of_stream;
  }

  bucket->Init({res_manager_->streams_[0]}, {res_manager_->streams_[1]});
  return bucket;
}

bool GPUDeviceResManager::LoadCollectiveCommLib() {
#ifdef ENABLE_MPI
  std::string nvidia_comm_lib_name = "libnvidia_collective.so";
  auto loader = std::make_shared<CollectiveCommLibLoader>(nvidia_comm_lib_name);
  MS_EXCEPTION_IF_NULL(loader);
  if (!loader->Initialize()) {
    MS_LOG(EXCEPTION) << "Loading NCCL collective library failed.";
    return false;
  }
  void *collective_comm_lib_handle = loader->collective_comm_lib_ptr();
  MS_EXCEPTION_IF_NULL(collective_comm_lib_handle);

  auto instance_func = DlsymFuncObj(communication_lib_instance, collective_comm_lib_handle);
  collective_comm_lib_ = instance_func();
  MS_EXCEPTION_IF_NULL(collective_comm_lib_);
  return true;
#else
  return false;
#endif
}

bool GPUDeviceResManager::BindDeviceToCurrentThread() const {
  if (cur_thread_device_inited) {
    return true;
  }

  if (!CudaDriver::SetDevice(UintToInt(device_context_->device_context_key().device_id_))) {
    MS_LOG(ERROR) << "Failed to set device id: " << device_context_->device_context_key().device_id_;
    return false;
  }

  cur_thread_device_inited = true;
  return true;
}

MS_REGISTER_DEVICE(kGPUDevice, GPUDeviceContext);
}  // namespace gpu
}  // namespace device
}  // namespace mindspore
