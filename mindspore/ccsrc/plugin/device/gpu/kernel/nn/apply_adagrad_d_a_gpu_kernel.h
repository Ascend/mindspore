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

#ifndef MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_NN_APPLY_ADAGRAD_AD_KERNEL_H_
#define MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_NN_APPLY_ADAGRAD_AD_KERNEL_H_
#include <vector>
#include <map>
#include <utility>

#include "mindspore/core/ops/apply_adagrad_d_a.h"
#include "plugin/device/gpu/kernel/gpu_kernel.h"
#include "plugin/factory/ms_factory.h"

namespace mindspore {
namespace kernel {
class ApplyAdagradDAGpuKernelMod : public NativeGpuKernelMod {
 public:
  ApplyAdagradDAGpuKernelMod() {}
  ~ApplyAdagradDAGpuKernelMod() override = default;

  bool Launch(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &workspace,
              const std::vector<AddressPtr> &outputs, void *stream_ptr) override;

  bool Init(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
            const std::vector<KernelTensorPtr> &outputs) override;
  int Resize(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
             const std::vector<KernelTensorPtr> &outputs,
             const std::map<uint32_t, tensor::TensorPtr> &others = std::map<uint32_t, tensor::TensorPtr>()) override;

 protected:
  std::vector<KernelAttr> GetOpSupport() override;

 private:
  void CheckParam(const std::vector<KernelTensorPtr> &inputs, const std::vector<KernelTensorPtr> &outputs) const;
  void CheckShape(const std::vector<KernelTensorPtr> &inputs, const std::vector<KernelTensorPtr> &outputs) const;
  void CheckDType(const std::vector<KernelTensorPtr> &inputs, const std::vector<KernelTensorPtr> &outputs) const;
  template <typename T, typename T1, typename T2, typename T3, typename T4>
  bool LaunchKernel(const std::vector<kernel::AddressPtr> &inputs, const std::vector<kernel::AddressPtr> &outputs);
  using ApplyAdagradDAFunc = std::function<bool(ApplyAdagradDAGpuKernelMod *, const std::vector<kernel::AddressPtr> &,
                                                const std::vector<kernel::AddressPtr> &)>;
  static std::vector<std::pair<KernelAttr, ApplyAdagradDAFunc>> func_list_;
  ApplyAdagradDAFunc kernel_func_;

  void *stream_ptr_{nullptr};
  size_t unit_size_{0};
  bool is_null_input_{false};
  size_t input_elements_{0};
  size_t batch_rank_;
  size_t batch_size_;
};
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_NN_APPLY_ADAGRAD_AD_KERNEL_H_
