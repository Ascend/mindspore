/**
 * Copyright 2019-2022 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_CPU_ARGMAX_CPU_KERNEL_H_
#define MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_CPU_ARGMAX_CPU_KERNEL_H_

#include <vector>
#include <memory>

#include "plugin/device/cpu/kernel/cpu_kernel.h"
#include "plugin/device/cpu/kernel/cpu_kernel_factory.h"

namespace mindspore {
namespace kernel {
template <typename T>
class ArgmaxCpuKernelMod : public NativeCpuKernelMod {
 public:
  ArgmaxCpuKernelMod() = default;
  ~ArgmaxCpuKernelMod() override = default;

  void InitKernel(const CNodePtr &kernel_node) override;

  bool Launch(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &workspace,
              const std::vector<AddressPtr> &outputs) override;

 private:
  std::vector<size_t> shape_;
  size_t num_before_axis_{0};
  size_t num_after_axis_{0};
  size_t dim_axis_{0};
};

MS_REG_CPU_KERNEL_T(Argmax, KernelAttr(), ArgmaxCpuKernelMod, float);
MS_REG_CPU_KERNEL_T(Argmax, KernelAttr(), ArgmaxCpuKernelMod, float16);
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_CPU_ARGMAX_CPU_KERNEL_H_