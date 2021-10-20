/**
 * Copyright 2020-2021 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_CORE_OPS_CONV2D_BACKPROP_INPUT_FUSION_H_
#define MINDSPORE_CORE_OPS_CONV2D_BACKPROP_INPUT_FUSION_H_
#include <vector>
#include "ops/grad/conv2d_backprop_input.h"
#include "ops/op_utils.h"
#include "utils/check_convert_utils.h"

namespace mindspore {
namespace ops {
constexpr auto kNameConv2DBackpropInputFusion = "Conv2DBackpropInputFusion";
/// \brief Conv2DBackpropInputFusion defined Conv2DBackpropInput operator prototype of lite.
class MS_CORE_API Conv2DBackpropInputFusion : public Conv2DBackpropInput {
 public:
  /// \brief Constructor.
  Conv2DBackpropInputFusion() : Conv2DBackpropInput(kNameConv2DBackpropInputFusion) {}

  /// \brief Destructor.
  ~Conv2DBackpropInputFusion() = default;

  MS_DECLARE_PARENT(Conv2DBackpropInputFusion, Conv2DBackpropInput);

  /// \brief Method to init the op's attributes.
  ///
  /// \param[in] in_channel Define the number of input channel.
  /// \param[in] out_channel Define the number of output channel.
  /// \param[in] kernel_size Define the size of the filter kernel.
  /// \param[in] mode Define the category of conv, which is useless on lite.
  /// \param[in] pad_mode Define the padding method.
  /// \param[in] pad Define the concrete padding value on H and W dimension, which is replaced with pad_list.
  /// \param[in] stride Define the moving size of the filter kernel.
  /// \param[in] dilation Define the coefficient of expansion of the filter kernel, which is useful for dilated
  ///            convolution.
  /// \param[in] group Define the number of group.
  /// \param[in] format Define the format of input tensor.
  /// \param[in] pad_list Define the concrete padding value on H and W dimension.
  /// \param[in] activation_type Define the activation type.
  void Init(int64_t in_channel, int64_t out_channel, const std::vector<int64_t> &kernel_size, int64_t mode = 1,
            const PadMode &pad_mode = VALID, const std::vector<int64_t> &pad = {0, 0, 0, 0},
            const std::vector<int64_t> &stride = {1, 1, 1, 1}, const std::vector<int64_t> &dilation = {1, 1, 1, 1},
            int64_t group = 1, const Format &format = NCHW, const std::vector<int64_t> &pad_list = {0, 0, 0, 0},
            const ActivationType &activation_type = NO_ACTIVATION);

  /// \brief Method to set in_channel attribute.
  ///
  /// \param[in] in_channel Define the number of input channel.
  void set_in_channel(int64_t in_channel);

  /// \brief Method to set activation type.
  ///
  /// \param[in] activation_type Define the activation type.
  void set_activation_type(const ActivationType &activation_type);

  /// \brief Method to get in_channel attribute.
  ///
  /// \return the number of input channel.
  int64_t get_in_channel() const;

  /// \brief Method to get activation type.
  ///
  /// \return activation type.
  ActivationType get_activation_type() const;
};
}  // namespace ops
}  // namespace mindspore

#endif  // MINDSPORE_CORE_OPS_CONV2D_BACKPROP_INPUT_FUSION_H_
