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

#ifndef MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_NN_KL_DIV_LOSS_GRAD_KERNEL_H
#define MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_NN_KL_DIV_LOSS_GRAD_KERNEL_H

#include <vector>
#include <string>
#include "plugin/device/gpu/kernel/gpu_kernel.h"
#include "plugin/device/gpu/kernel/gpu_kernel_factory.h"
#include "plugin/device/gpu/kernel/cuda_impl/cuda_ops/loss_with_reduction_impl.cuh"
#include "kernel/common_utils.h"

namespace mindspore {
namespace kernel {
template <typename T>
class KLDivLossGradGpuKernelMod : public DeprecatedNativeGpuKernelMod {
 public:
  KLDivLossGradGpuKernelMod() : input_size_(1), reduction_(ReductionMode::kMean), is_null_input_(false) {}
  ~KLDivLossGradGpuKernelMod() override = default;

  bool Launch(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &,
              const std::vector<AddressPtr> &outputs, void *stream_ptr) override {
    if (is_null_input_) {
      return true;
    }
    T *dloss = GetDeviceAddress<T>(inputs, kIndex0);
    T *input_x = GetDeviceAddress<T>(inputs, kIndex1);
    T *input_y = GetDeviceAddress<T>(inputs, kIndex2);
    T *dx = GetDeviceAddress<T>(outputs, kIndex0);
    KLDivLossGrad(input_size_, reduction_, input_x, input_y, dloss, dx, reinterpret_cast<cudaStream_t>(stream_ptr));
    return true;
  }

  bool Init(const CNodePtr &kernel_node) override {
    auto kernel_name = common::AnfAlgo::GetCNodeName(kernel_node);
    auto input_shape = common::AnfAlgo::GetPrevNodeOutputInferShape(kernel_node, kIndex1);
    kernel_node_ = kernel_node;
    is_null_input_ = CHECK_SHAPE_NULL(input_shape, kernel_name, "input");
    if (is_null_input_ || IsDynamic(input_shape)) {
      InitSizeLists();
      return true;
    }
    input_size_ *= SizeOf(input_shape);
    string reduction = GetAttr<string>(kernel_node, "reduction");
    reduction_ = kReductionModeMap[reduction];
    InitSizeLists();
    return true;
  }

 protected:
  void InitSizeLists() override {
    if (reduction_ == ReductionMode::kNone) {
      input_size_list_.push_back(input_size_ * sizeof(T));
    } else {
      input_size_list_.push_back(sizeof(T));
    }
    input_size_list_.push_back(input_size_ * sizeof(T));
    input_size_list_.push_back(input_size_ * sizeof(T));
    output_size_list_.push_back(input_size_ * sizeof(T));
  }

 private:
  size_t input_size_;
  ReductionMode reduction_;
  bool is_null_input_;
};
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_KL_DIV_LOSS_GRAD_KERNEL_H
