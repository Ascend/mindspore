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
#include "plugin/device/cpu/kernel/complex_abs_cpu_kernel.h"
#include <complex>
#include "plugin/device/cpu/hal/device/cpu_device_address.h"

namespace {
const size_t kOutputsNum = 1;
const size_t kInputsNum = 1;

#define ComplexAbs_COMPUTE_CASE(IN_DTYPE, IN_TYPE, OUT_DTYPE) \
  case (IN_DTYPE): {                                          \
    ret = LaunchKernel<IN_TYPE, OUT_DTYPE>(inputs, outputs);  \
    break;                                                    \
  }
}  // namespace

namespace mindspore {
namespace kernel {
void ComplexAbsCpuKernelMod::InitKernel(const CNodePtr &kernel_node) {
  MS_EXCEPTION_IF_NULL(kernel_node);
  kernel_name_ = common::AnfAlgo::GetCNodeName(kernel_node);
  input_dtype_ = AnfAlgo::GetInputDeviceDataType(kernel_node, 0);
}

bool ComplexAbsCpuKernelMod::Launch(const std::vector<kernel::AddressPtr> &inputs,
                                    const std::vector<kernel::AddressPtr> &,
                                    const std::vector<kernel::AddressPtr> &outputs) {
  CHECK_KERNEL_INPUTS_NUM(inputs.size(), kInputsNum, kernel_name_);
  CHECK_KERNEL_OUTPUTS_NUM(outputs.size(), kOutputsNum, kernel_name_);
  bool ret = true;
  switch (input_dtype_) {
    ComplexAbs_COMPUTE_CASE(kNumberTypeComplex64, std::complex<float>, float)
      ComplexAbs_COMPUTE_CASE(kNumberTypeComplex128, std::complex<double>, double) default : ret = false;
    MS_EXCEPTION(TypeError) << "For ComplexAbs: unsupported input data type: " << TypeIdToString(input_dtype_) << " .";
  }
  return ret;
}

template <typename T, typename T2>
bool ComplexAbsCpuKernelMod::LaunchKernel(const std::vector<kernel::AddressPtr> &inputs,
                                          const std::vector<kernel::AddressPtr> &outputs) {
  auto input_addr = reinterpret_cast<T *>(inputs[0]->addr);
  auto output_addr = reinterpret_cast<T2 *>(outputs[0]->addr);
  size_t output_size = outputs[0]->size / sizeof(T2);
  auto task = [output_addr, input_addr](size_t start, size_t end) {
    for (size_t i = start; i < end; ++i) {
      T2 a = input_addr[i].real();
      T2 b = input_addr[i].imag();
      output_addr[i] = sqrt(b * b + a * a);
    }
  };
  ParallelLaunchAutoSearch(task, output_size, this, &parallel_search_info_);
  return true;
}

std::vector<KernelAttr> ComplexAbsCpuKernelMod::GetOpSupport() {
  static std::vector<KernelAttr> support_list = {
    KernelAttr().AddInputAttr(kNumberTypeComplex64).AddOutputAttr(kNumberTypeFloat32),
    KernelAttr().AddInputAttr(kNumberTypeComplex128).AddOutputAttr(kNumberTypeFloat64)};

  return support_list;
}

MS_KERNEL_FACTORY_REG(NativeCpuKernelMod, ComplexAbs, ComplexAbsCpuKernelMod);
}  // namespace kernel
}  // namespace mindspore
