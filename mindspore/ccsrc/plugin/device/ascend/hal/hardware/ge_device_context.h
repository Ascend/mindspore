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
#ifndef MINDSPORE_CCSRC_RUNTIME_HARDWARE_ASCEND_GE_DEVICE_CONTEXT_H_
#define MINDSPORE_CCSRC_RUNTIME_HARDWARE_ASCEND_GE_DEVICE_CONTEXT_H_

#include <vector>
#include <memory>
#include <string>
#include <map>
#include "runtime/hardware/device_context.h"
#include "runtime/device/memory_manager.h"
#include "utils/ms_context.h"

namespace mindspore {
namespace device {
namespace ascend {
class GeDeviceResManager : public DeviceResManager {
 public:
  GeDeviceResManager() : mem_manager_(nullptr) {}
  ~GeDeviceResManager() override = default;

  void Initialize() override;

  void Destroy() override;

  std::vector<void *> AllocateContinuousMemory(const std::vector<size_t> &size_list) const override;

  DeviceAddressPtr CreateDeviceAddress(void *const device_ptr, size_t device_size, const string &format, TypeId type_id,
                                       const ShapeVector &shape = ShapeVector()) const override;

 protected:
  // Relevant function to allocate and free device memory of raw ptr.
  void *AllocateMemory(size_t size) const override;
  void FreeMemory(void *ptr) const override;

 private:
  std::shared_ptr<MemoryManager> mem_manager_;
};

class GeGraphExecutor : public GraphExecutor {
 public:
  ~GeGraphExecutor() override = default;
  bool CompileGraph(const FuncGraphPtr &graph, const std::map<string, string> &compile_options) override;
  bool RunGraph(const FuncGraphPtr &graph, const std::vector<tensor::Tensor> &inputs,
                std::vector<tensor::Tensor> *outputs, const std::map<string, string> &compile_options) override;

 private:
  void AllocInputHostMemory(const KernelGraphPtr &kernel_graph) const;
  void AllocOutputHostMemory(const KernelGraphPtr &kernel_graph) const;
};

class GeDeviceContext : public DeviceInterface<GeGraphExecutor, GeDeviceResManager> {
 public:
  explicit GeDeviceContext(const DeviceContextKey &device_context_key)
      : DeviceInterface(device_context_key), initialized_(false) {}
  ~GeDeviceContext() override = default;

  void Initialize() override;

  void Destroy() override;

  bool PartitionGraph(const FuncGraphPtr &func_graph) const override;
  RunMode GetRunMode(const FuncGraphPtr &func_graph) const override;

 private:
  DISABLE_COPY_AND_ASSIGN(GeDeviceContext);

  bool InitGe(const std::shared_ptr<MsContext> &inst_context);
  bool FinalizeGe(const std::shared_ptr<MsContext> &inst_context);
  void GetGeOptions(const std::shared_ptr<MsContext> &inst_context, std::map<std::string, std::string> *ge_options);
  void SetHcclOptions(const std::shared_ptr<MsContext> &inst_context, std::map<std::string, std::string> *ge_options);
  void SetDisableReuseMemoryFlag(std::map<std::string, std::string> *ge_options);

  bool initialized_;
};
}  // namespace ascend
}  // namespace device
}  // namespace mindspore

#endif  // MINDSPORE_CCSRC_RUNTIME_HARDWARE_ASCEND_GE_DEVICE_CONTEXT_H_
