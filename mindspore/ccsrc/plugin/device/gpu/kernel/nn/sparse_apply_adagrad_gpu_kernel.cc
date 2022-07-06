/**
 * Copyright 2020-2022 Huawei Technologies Co., Ltd
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

#include "mindspore/core/ops/sparse_apply_adagrad.h"
#include "plugin/device/gpu/kernel/nn/sparse_apply_adagrad_gpu_kernel.h"

namespace mindspore {
namespace kernel {
namespace {
constexpr size_t kSparseApplyAdagradInputsNum = 4;
constexpr size_t kVarIndex = 0;
constexpr size_t kAccIndex = 1;
constexpr size_t kGradIndex = 2;
constexpr size_t kIndicesIndex = 3;
}  // namespace

bool SparseApplyAdagradGpuKernelMod::Init(const BaseOperatorPtr &base_operator,
                                          const std::vector<KernelTensorPtr> &inputs,
                                          const std::vector<KernelTensorPtr> &outputs) {
  MS_EXCEPTION_IF_NULL(base_operator);
  kernel_name_ = base_operator->name();
  if (kernel_name_ != prim::kPrimSparseApplyAdagrad->name()) {
    MS_LOG(ERROR) << "For 'SparseApplyAdagrad', the kernel name must be 'SparseApplyAdagrad', but got " << kernel_name_;
    return false;
  }

  auto kernel_ptr = std::dynamic_pointer_cast<ops::SparseApplyAdagrad>(base_operator);
  MS_EXCEPTION_IF_NULL(kernel_ptr);
  if (!kernel_ptr) {
    MS_LOG(ERROR) << "SparseApplyAdagrad ops failed!";
    return false;
  }
  lr_ = kernel_ptr->get_lr();
  update_slots_ = kernel_ptr->get_update_slots();

  auto kernel_attr = GetKernelAttrFromTensors(inputs, outputs);
  auto [is_match, index] = MatchKernelAttr(kernel_attr, GetOpSupport());
  if (!is_match) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', it does not support this kernel data type: " << kernel_attr;
    return false;
  }
  kernel_func_ = func_list_[index].second;
  unit_size_ = abstract::TypeIdSize(kernel_attr.GetInputAttr(kIndex0).first);
  if (inputs.empty() || outputs.empty()) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "' got empty inputs or outputs, which is invalid.";
    return false;
  }
  return true;
}

int SparseApplyAdagradGpuKernelMod::Resize(const BaseOperatorPtr &base_operator,
                                           const std::vector<KernelTensorPtr> &inputs,
                                           const std::vector<KernelTensorPtr> &outputs,
                                           const std::map<uint32_t, tensor::TensorPtr> &) {
  int ret = KernelMod::Resize(base_operator, inputs, outputs);
  if (ret != 0) {
    return ret;
  }

  if (input_size_list_.size() != kSparseApplyAdagradInputsNum) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "' input size must be equal 4 but got " << input_size_list_.size();
    return KRET_RESIZE_FAILED;
  }
  std::vector<int64_t> var_shape = inputs[kVarIndex]->GetShapeVector();
  std::vector<int64_t> accum_shape = inputs[kAccIndex]->GetShapeVector();
  std::vector<int64_t> grad_shape = inputs[kGradIndex]->GetShapeVector();
  std::vector<int64_t> indices_shape = inputs[kIndicesIndex]->GetShapeVector();
  if (var_shape.empty()) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the dimension of 'var' must be at least 1-D, but got scalar or None.";
    return KRET_RESIZE_FAILED;
  }
  if (!IsSameShape(var_shape, accum_shape)) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the shape of 'accum' must be the same as the shape of 'var', "
                     "but got the shape of 'accum': "
                  << Vector2Str(accum_shape) << " and the shape of 'var': " << Vector2Str(var_shape);
    return KRET_RESIZE_FAILED;
  }
  if (!IsSameShape(var_shape, grad_shape)) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the shape of 'grad' must be the same as the shape of 'var', "
                     "but got the shape of 'grad': "
                  << Vector2Str(grad_shape) << " and the shape of 'var': " << Vector2Str(var_shape);
    return KRET_RESIZE_FAILED;
  }
  if (!IsSameShape(grad_shape, indices_shape)) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the shape of 'indices' must be the same as the shape of 'grad', "
                     "but got the shape of 'indices': "
                  << Vector2Str(indices_shape) << " and the shape of 'grad': " << Vector2Str(grad_shape);
    return KRET_RESIZE_FAILED;
  }

  input_elements_ = input_size_list_[0] / unit_size_;
  return ret;
}

template <typename T, typename S>
bool SparseApplyAdagradGpuKernelMod::LaunchKernel(const std::vector<AddressPtr> &inputs,
                                                  const std::vector<AddressPtr> &workspace,
                                                  const std::vector<AddressPtr> &outputs) {
  auto var = reinterpret_cast<T *>(inputs[kVarIndex]->addr);
  auto accum = reinterpret_cast<T *>(inputs[kAccIndex]->addr);
  auto grad = reinterpret_cast<T *>(inputs[kGradIndex]->addr);
  auto indices = reinterpret_cast<S *>(inputs[kIndicesIndex]->addr);
  auto var_out = reinterpret_cast<T *>(outputs[kVarIndex]->addr);
  auto accum_out = reinterpret_cast<T *>(outputs[kAccIndex]->addr);

  CalSparseApplyAdagrad(input_elements_, sizeof(S) / sizeof(int), lr_, update_slots_, grad, indices, var, accum,
                        var_out, accum_out, reinterpret_cast<cudaStream_t>(cuda_stream_));

  return true;
}

std::vector<std::pair<KernelAttr, SparseApplyAdagradGpuKernelMod::SparseApplyAdagradFunc>>
  SparseApplyAdagradGpuKernelMod::func_list_ = {{KernelAttr()
                                                   .AddInputAttr(kNumberTypeFloat32)
                                                   .AddInputAttr(kNumberTypeFloat32)
                                                   .AddInputAttr(kNumberTypeFloat32)
                                                   .AddInputAttr(kNumberTypeInt32)
                                                   .AddOutputAttr(kNumberTypeFloat32)
                                                   .AddOutputAttr(kNumberTypeFloat32)
                                                   .AddOutInRef(0, 0)
                                                   .AddOutInRef(1, 1),
                                                 &SparseApplyAdagradGpuKernelMod::LaunchKernel<float, int>},
                                                {KernelAttr()
                                                   .AddInputAttr(kNumberTypeFloat16)
                                                   .AddInputAttr(kNumberTypeFloat16)
                                                   .AddInputAttr(kNumberTypeFloat16)
                                                   .AddInputAttr(kNumberTypeInt32)
                                                   .AddOutputAttr(kNumberTypeFloat16)
                                                   .AddOutputAttr(kNumberTypeFloat16)
                                                   .AddOutInRef(0, 0)
                                                   .AddOutInRef(1, 1),
                                                 &SparseApplyAdagradGpuKernelMod::LaunchKernel<half, int>}};

std::vector<KernelAttr> SparseApplyAdagradGpuKernelMod::GetOpSupport() {
  std::vector<KernelAttr> support_list;
  (void)std::transform(func_list_.begin(), func_list_.end(), std::back_inserter(support_list),
                       [](const std::pair<KernelAttr, SparseApplyAdagradFunc> &pair) { return pair.first; });
  return support_list;
}

MS_KERNEL_FACTORY_REG(NativeGpuKernelMod, SparseApplyAdagrad, SparseApplyAdagradGpuKernelMod);
}  // namespace kernel
}  // namespace mindspore
