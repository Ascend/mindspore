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

#include "backend/kernel_compiler/cpu/matrix_diag_part_cpu_kernel.h"
#include <algorithm>
#include <string>

namespace mindspore {
namespace kernel {
template <typename T>
void MatrixDiagPartCpuKernelMod<T>::InitKernel(const CNodePtr &kernel_node) {
  shapes_ = AnfAlgo::GetPrevNodeOutputInferShape(kernel_node, 0);
  out_shapes_ = shapes_;
  dim_size_ = shapes_.size();
  if (shapes_.size() < kDim2) {
    MS_LOG(EXCEPTION) << "Wrong array shape, A should be a matrix max than 2.";
  }
  m_ = shapes_[dim_size_ - kDim2];
  n_ = shapes_[dim_size_ - kDim1];
  for (size_t i = 0; i < shapes_.size() - kDim2; i++) {
    out_range_size_ *= shapes_[i];
  }
  // Invalid alignment will throw an exception.
  auto alignment = AnfAlgo::GetNodeAttr<std::string>(kernel_node, ALIGNMENT);
  alignment_ = GetAlignments(alignment);
  node_wpt_ = kernel_node;
}

template <typename T>
bool MatrixDiagPartCpuKernelMod<T>::Launch(const std::vector<AddressPtr> &inputs,
                                           const std::vector<AddressPtr> &workspace,
                                           const std::vector<AddressPtr> &outputs) {
  T *in_value = reinterpret_cast<T *>(inputs[0]->addr);
  // K is 2 elements vector, k[0] is lower part, k[0]<0, k[1] is upper part,
  int64_t *k_range = reinterpret_cast<int64_t *>(inputs[1]->addr);
  T *padding_value = reinterpret_cast<T *>(inputs[2]->addr);
  T *out_value = reinterpret_cast<T *>(outputs[0]->addr);
  int64_t l = k_range[0];
  int64_t u = k_range[1];
  // New diagonal matrix m*n matrix, m dimension ;
  if (l > u) {
    MS_LOG(EXCEPTION) << "The k[1] must not less than k[0].";
  }
  u = std::min(u, n_ - 1);
  l = std::max(-(m_ - 1), l);
  int64_t num_diags = u - l + 1;
  // New diagonal matrix m * n matrix, n dimension
  int64_t max_diag_len =
    std::min(m_ + std::min(u, static_cast<int64_t>(0)), n_ + std::min(-l, static_cast<int64_t>(0)));
  MS_LOG(DEBUG) << "Num_diags:" << num_diags << ",max_diag_len:" << max_diag_len;
  int64_t dest_inner_matrix_size = num_diags * max_diag_len;
  out_shapes_ = shapes_;
  // Set dynamic shape and dtype
  if (!node_wpt_.expired()) {
    auto node_ = node_wpt_.lock();
    out_shapes_[shapes_.size() - kDim1] = max_diag_len;
    // If the out shape m' * n', the m' dimension is 1, then remove this dimension
    out_shapes_[shapes_.size() - kDim2] = num_diags;
    if (num_diags == 1) {
      out_shapes_.erase(out_shapes_.begin() + shapes_.size() - kDim2);
    }
    auto dtype = AnfAlgo::GetOutputDeviceDataType(node_, 0);
    AnfAlgo::SetOutputInferTypeAndShape({dtype}, {out_shapes_}, node_.get());
  }
  for (int64_t i = 0; i < out_range_size_; i++) {
    // The j_index means current dest row index
    for (int64_t j = u; j >= l; j--) {
      int64_t current_diag_len = j >= 0 ? std::min(n_ - j, m_) : std::min(m_ + j, n_);
      int64_t current_pad_len = max_diag_len - current_diag_len;
      // Pad left by default
      bool pad_left = (alignment_.first == MatrixDiag::Alignment::RIGHT && j > 0) ||
                      (alignment_.second == MatrixDiag::Alignment::RIGHT && j < 0);
      // Set none-padding values, l means current diag col index
      for (int64_t k = 0; k < max_diag_len; k++) {
        // Source pos, k offset, only effective when pad left
        int64_t k_offset = (pad_left && k >= current_pad_len) ? k - current_pad_len : k;
        // Calculate source offset row/col offset
        size_t row_index = j >= 0 ? j + k_offset : k_offset;
        size_t col_index = j >= 0 ? k_offset : k_offset - j;
        size_t source_offset = i * m_ * n_ + col_index * n_ + row_index;
        // If current pos need pad, then the value is pad value
        bool current_pad_flag = (pad_left && k < current_pad_len) || (!pad_left && k >= current_diag_len);
        T current_pad_value = current_pad_flag ? *padding_value : *(in_value + source_offset);
        int64_t j_index = u - j;
        size_t dest_offset = dest_inner_matrix_size * i + j_index * max_diag_len + k;
        MS_LOG(DEBUG) << "the diag j:" << j << ",k:" << k << ",k_offset:" << k_offset << ",row:" << row_index
                      << ",col:" << col_index << ",j_index:" << j_index << ",current_pad_value:" << current_pad_value;
        *(out_value + dest_offset) = current_pad_value;
      }
    }
  }
  return true;
}
}  // namespace kernel
}  // namespace mindspore