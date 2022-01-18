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

#ifndef MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_CPU_EIGEN_MATRIX_BAND_PART_H
#define MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_CPU_EIGEN_MATRIX_BAND_PART_H
#include <vector>
#include <complex>
#include "backend/kernel_compiler/cpu/cpu_kernel.h"
#include "backend/kernel_compiler/cpu/cpu_kernel_factory.h"

namespace mindspore {
namespace kernel {
template <typename T>
class MatrixBandPartCPUKernel : public CPUKernel {
 public:
  MatrixBandPartCPUKernel() = default;
  ~MatrixBandPartCPUKernel() override = default;
  void InitKernel(const CNodePtr &kernel_node) override;
  bool Launch(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &workspace,
              const std::vector<AddressPtr> &outputs) override;

 private:
  std::vector<size_t> shapes_{};
  size_t dim_size_{1};
  size_t matrix_size_{0};
  size_t out_range_size_{1};
  size_t m_{1};
  size_t n_{1};
  TypeId dtype_{kNumberTypeFloat32};
};

MS_REG_CPU_KERNEL_T(MatrixBandPart,
                    KernelAttr()
                      .AddInputAttr(kNumberTypeInt32)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddOutputAttr(kNumberTypeInt32),
                    MatrixBandPartCPUKernel, int32_t);

MS_REG_CPU_KERNEL_T(MatrixBandPart,
                    KernelAttr()
                      .AddInputAttr(kNumberTypeInt64)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddOutputAttr(kNumberTypeInt64),
                    MatrixBandPartCPUKernel, int64_t);

MS_REG_CPU_KERNEL_T(MatrixBandPart,
                    KernelAttr()
                      .AddInputAttr(kNumberTypeFloat32)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddOutputAttr(kNumberTypeFloat32),
                    MatrixBandPartCPUKernel, float);

MS_REG_CPU_KERNEL_T(MatrixBandPart,
                    KernelAttr()
                      .AddInputAttr(kNumberTypeFloat64)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddInputAttr(kNumberTypeInt64)
                      .AddOutputAttr(kNumberTypeFloat64),
                    MatrixBandPartCPUKernel, double);
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_CPU_EIGEN_MATRIX_BAND_PART_H
