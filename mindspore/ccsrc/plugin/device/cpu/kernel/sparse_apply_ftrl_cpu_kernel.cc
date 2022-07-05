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

#include "plugin/device/cpu/kernel/sparse_apply_ftrl_cpu_kernel.h"
#include <memory>
#include <map>
#include <utility>
#include "kernel/common_utils.h"
#include "plugin/device/cpu/hal/device/cpu_device_address.h"
#include "ops/fused_sparse_ftrl.h"

namespace mindspore {
namespace kernel {
namespace {
// "var","accum","linear","grad","indices"
constexpr size_t kVarIndex = 0;
constexpr size_t kAccumIndex = 1;
constexpr size_t kLinearIndex = 2;
constexpr size_t kGradIndex = 3;
constexpr size_t kIndicesIndex = 4;
constexpr size_t kSparseApplyFtrlInputsNum = 5;
constexpr size_t kSparseApplyFtrlWorkspaceSize = 4;
constexpr char kKernelName[] = "SparseApplyFtrl";

using KernelRunFunc = SparseApplyFtrlCpuKernelMod::KernelRunFunc;

template <typename T>
void ComputeFtrl(MultiThreadComputeParams<T> *input_params, size_t start, size_t end) {
  MS_EXCEPTION_IF_NULL(input_params);
  auto var = input_params->var_;
  auto accum = input_params->accum_;
  auto linear = input_params->linear_;
  const auto lr = input_params->lr_;
  const auto l1 = input_params->l1_;
  const auto l2_plus = 2 * input_params->l2_;
  const auto lr_power = input_params->lr_power_;
  const auto unique_sparse_grad = input_params->sparse_grad_;
  const auto var_first_dim_size = input_params->var_first_dim_size_;
  const auto var_outer_dim_size = input_params->var_outer_dim_size_;
  for (size_t i = start; i < end; ++i) {
    T index = unique_sparse_grad.indices_[i];
    if (index < 0 || LongToSize(index) >= var_first_dim_size) {
      MS_LOG(EXCEPTION) << "For '" << kKernelName << "', each element in 'indices' must be in range [0, "
                        << SizeToLong(var_first_dim_size) << "), but got " << index;
    }
    size_t start_index = var_outer_dim_size * static_cast<size_t>(index);
    size_t end_index = start_index + var_outer_dim_size;
    for (size_t j = start_index, k = var_outer_dim_size * i; j < end_index; ++j, ++k) {
      auto summed_grad = unique_sparse_grad.value_[k];
      auto accum_new = accum[j] + summed_grad * summed_grad;
      float y;
      linear[j] += summed_grad;
      if (lr_power == -0.5) {
        y = std::sqrt(accum_new);
        linear[j] -= ((y - std::sqrt(accum[j])) / lr) * var[j];
      } else {
        y = std::pow(accum_new, -lr_power);
        linear[j] -= ((y - std::pow(accum[j], -lr_power)) / lr) * var[j];
      }
      accum[j] = accum_new;
      auto x = Sign(linear[j]) * l1 - linear[j];
      y = y / lr + l2_plus;
      var[j] = std::fabs(linear[j]) > l1 ? x / y : 0;
    }
  }
}
}  // namespace

template <typename T>
void SparseApplyFtrlCpuKernelMod::InitWorkspaceSize() {
  (void)workspace_size_list_.emplace_back(indices_size_ * var_outer_dim_size_ * sizeof(float));
  (void)workspace_size_list_.emplace_back(indices_size_ * sizeof(T));
  (void)workspace_size_list_.emplace_back(indices_size_ * var_outer_dim_size_ * sizeof(float));
  (void)workspace_size_list_.emplace_back(indices_size_ * sizeof(T));
}

bool SparseApplyFtrlCpuKernelMod::Init(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
                                       const std::vector<KernelTensorPtr> &outputs) {
  kernel_name_ = base_operator->name();
  if (inputs.empty() || outputs.empty()) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', it got empty inputs or outputs, which is invalid.";
    return false;
  }
  if (inputs.size() != kSparseApplyFtrlInputsNum) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', input size must be " << kSparseApplyFtrlInputsNum << ", but got "
                  << inputs.size();
    return false;
  }
  auto kernel_ptr = std::make_shared<ops::FusedSparseFtrl>(base_operator->GetPrim());
  lr_ = kernel_ptr->get_lr();
  if (lr_ <= 0) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', 'lr' must be a positive scalar, but got " << lr_;
    return false;
  }
  l1_ = kernel_ptr->get_l1();
  if (l1_ < 0) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', 'l1' must be a non-negative scalar, but got " << l1_;
    return false;
  }
  l2_ = kernel_ptr->get_l2();
  if (l2_ < 0) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', 'l2' must be a non-negative scalar, but got " << l2_;
    return false;
  }
  lr_power_ = kernel_ptr->get_lr_power();
  if (lr_power_ > 0) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', 'lr_power' must be a non-negative scalar, but got " << lr_power_;
    return false;
  }
  if (!MatchKernelFunc(base_operator, inputs, outputs)) {
    return false;
  }
  return true;
}

void SparseApplyFtrlCpuKernelMod::ResetResource() noexcept {
  input_size_list_.clear();
  output_size_list_.clear();
  workspace_size_list_.clear();
  indices_data_type_ = kNumberTypeInt32;
  indices_size_ = 0;
  var_first_dim_size_ = 0;
  var_outer_dim_size_ = 1;
}

int SparseApplyFtrlCpuKernelMod::Resize(const BaseOperatorPtr &base_operator,
                                        const std::vector<KernelTensorPtr> &inputs,
                                        const std::vector<KernelTensorPtr> &outputs,
                                        const std::map<uint32_t, tensor::TensorPtr> &) {
  ResetResource();
  int ret = KernelMod::Resize(base_operator, inputs, outputs);
  if (ret != KRET_OK) {
    return ret;
  }
  ShapeVector var_shape = inputs[kVarIndex]->GetShapeVector();
  ShapeVector accum_shape = inputs[kAccumIndex]->GetShapeVector();
  ShapeVector linear_shape = inputs[kLinearIndex]->GetShapeVector();
  ShapeVector grad_shape = inputs[kGradIndex]->GetShapeVector();
  ShapeVector indices_shape = inputs[kIndicesIndex]->GetShapeVector();
  if (var_shape.empty()) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', the 'var' must be at least 1-D, but got scalar or None.";
    return KRET_RESIZE_FAILED;
  }
  if (!IsSameShape(var_shape, accum_shape)) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the shape of 'accum' must be the same as the shape of 'var', "
                     "but got the shape of 'accum': "
                  << Vector2Str(accum_shape) << " and the shape of 'var': " << Vector2Str(var_shape);
    return KRET_RESIZE_FAILED;
  }
  if (!IsSameShape(var_shape, linear_shape)) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the shape of 'linear' must be the same as the shape of 'var', "
                     "but got the shape of 'linear': "
                  << Vector2Str(linear_shape) << " and the shape of 'var': " << Vector2Str(var_shape);
    return KRET_RESIZE_FAILED;
  }
  if (var_shape.size() != grad_shape.size()) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the dimension of 'grad' must be the same as the dimension of "
                     "'var', but got the dimension of 'grad': "
                  << grad_shape.size() << " and the dimension of 'var': " << var_shape.size() << ".";
    return KRET_RESIZE_FAILED;
  }
  var_first_dim_size_ = var_shape[0];
  for (size_t i = 1; i < var_shape.size(); ++i) {
    if (var_shape[i] != grad_shape[i]) {
      MS_LOG(ERROR) << "For '" << kernel_name_ << "', the shape of 'var' and 'grad' must be equal in dimension i=" << i
                    << ", but got 'var_shape[i]': " << var_shape[i] << " and 'grad_shape[i]': " << grad_shape[i];
      return KRET_RESIZE_FAILED;
    }
    var_outer_dim_size_ *= var_shape[i];
  }
  if (indices_shape.size() != 1) {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', the 'indices' must be a 1-D vector, but got "
                  << indices_shape.size() << "-D.";
    return KRET_RESIZE_FAILED;
  }
  indices_size_ = indices_shape[0];
  if (grad_shape[0] != SizeToLong(indices_size_)) {
    MS_LOG(ERROR) << "For '" << kernel_name_
                  << "', the first dimension value of 'grad' must be equal to "
                     "the first dimension value of 'indices', but got the first dimension value of 'grad': "
                  << grad_shape[0] << ", and the first dimension value of 'indices': " << indices_size_;
    return KRET_RESIZE_FAILED;
  }
  indices_data_type_ = inputs[kIndicesIndex]->GetDtype();
  if (indices_data_type_ == kNumberTypeInt32) {
    InitWorkspaceSize<int>();
  } else if (indices_data_type_ == kNumberTypeInt64) {
    InitWorkspaceSize<int64_t>();
  } else {
    MS_LOG(ERROR) << "For '" << kernel_name_ << "', the dtype of 'indices' must be int32 or int64, but got "
                  << TypeIdToType(indices_data_type_)->ToString();

    return KRET_RESIZE_FAILED;
  }
  return KRET_OK;
}

const std::vector<std::pair<KernelAttr, KernelRunFunc>> &SparseApplyFtrlCpuKernelMod::GetFuncList() const {
  static const std::vector<std::pair<KernelAttr, KernelRunFunc>> func_list = {
    {KernelAttr()
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeInt32)
       .AddOutputAttr(kNumberTypeFloat32)
       .AddOutputAttr(kNumberTypeFloat32)
       .AddOutputAttr(kNumberTypeFloat32)
       .AddOutInRef(0, 0),
     &SparseApplyFtrlCpuKernelMod::LaunchKernel<int>},
    {KernelAttr()
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeFloat32)
       .AddInputAttr(kNumberTypeInt64)
       .AddOutputAttr(kNumberTypeFloat32)
       .AddOutputAttr(kNumberTypeFloat32)
       .AddOutputAttr(kNumberTypeFloat32)
       .AddOutInRef(0, 0),
     &SparseApplyFtrlCpuKernelMod::LaunchKernel<int64_t>}};
  return func_list;
}

template <typename T>
bool SparseApplyFtrlCpuKernelMod::LaunchKernel(const std::vector<kernel::AddressPtr> &inputs,
                                               const std::vector<kernel::AddressPtr> &workspace,
                                               const std::vector<kernel::AddressPtr> &) const {
  auto *var = reinterpret_cast<float *>(inputs[0]->addr);
  auto *accum = reinterpret_cast<float *>(inputs[1]->addr);
  auto *linear = reinterpret_cast<float *>(inputs[2]->addr);
  auto *grad = reinterpret_cast<float *>(inputs[3]->addr);
  auto *indices = reinterpret_cast<T *>(inputs[4]->addr);
  auto *new_grad = reinterpret_cast<float *>(workspace[0]->addr);
  auto *new_indices = reinterpret_cast<T *>(workspace[1]->addr);
  auto *workspace_grad = reinterpret_cast<float *>(workspace[2]->addr);
  auto *workspace_indices = reinterpret_cast<T *>(workspace[3]->addr);

  SparseGradient<T> unique_sparse_grad({new_grad, new_indices, indices_size_});
  SparseGradient<T> workspace_sparse_grad({workspace_grad, workspace_indices, indices_size_});
  SparseGradient<T> input_sparse_grad({grad, indices, indices_size_});
  ReduceSparseGradientParam<T> param;
  param.input_grad_ = &input_sparse_grad;
  param.workspace_grad_ = &workspace_sparse_grad;
  param.output_grad_ = &unique_sparse_grad;
  param.max_index_ = var_first_dim_size_;
  param.value_stride_ = var_outer_dim_size_;
  BucketReduceSparseGradient(param);

  MultiThreadComputeParams<T> input_params;
  input_params.var_ = var;
  input_params.accum_ = accum;
  input_params.linear_ = linear;
  input_params.lr_ = lr_;
  input_params.l1_ = l1_;
  input_params.l2_ = l2_;
  input_params.lr_power_ = lr_power_;
  input_params.sparse_grad_ = unique_sparse_grad;
  input_params.var_first_dim_size_ = var_first_dim_size_;
  input_params.var_outer_dim_size_ = var_outer_dim_size_;
  MultiThreadCompute<T>(ComputeFtrl<T>, &input_params, unique_sparse_grad.indices_size_);
  return true;
}

MS_KERNEL_FACTORY_REG(NativeCpuKernelMod, FusedSparseFtrl, SparseApplyFtrlCpuKernelMod);
}  // namespace kernel
}  // namespace mindspore
