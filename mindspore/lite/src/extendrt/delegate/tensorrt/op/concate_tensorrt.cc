/**
 * Copyright 2021 Huawei Technologies Co., Ltd
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

#include "src/extendrt/delegate/tensorrt/op/concate_tensorrt.h"
#include <experimental/optional>
#include <algorithm>

namespace mindspore::lite {
int ConcateTensorRT::IsSupport(const schema::Primitive *primitive, const std::vector<mindspore::MSTensor> &in_tensors,
                               const std::vector<mindspore::MSTensor> &out_tensors) {
  if (!IsShapeKnown()) {
    MS_LOG(ERROR) << "Unsupported input tensor unknown shape: " << op_name_;
    return RET_ERROR;
  }
  if (type_ != schema::PrimitiveType_Stack && type_ != schema::PrimitiveType_Concat) {
    MS_LOG(ERROR) << "Unsupported op :" << op_name_ << " , type: " << type_;
    return RET_ERROR;
  }
  if (in_tensors.size() == 0 || in_tensors.size() < INPUT_SIZE2 && type_ != schema::PrimitiveType_Stack) {
    MS_LOG(ERROR) << "Unsupported input tensor size, size is " << in_tensors.size();
    return RET_ERROR;
  }
  if (out_tensors.size() != 1) {
    MS_LOG(ERROR) << "Unsupported output tensor size, size is " << out_tensors.size();
    return RET_ERROR;
  }

  int input_nbDims = in_tensors_[0].Shape().size();
  if (axis_ == -1) {
    axis_ = input_nbDims - 1;
  }
  if (axis_ < 0 || axis_ > input_nbDims || axis_ == input_nbDims && type_ != schema::PrimitiveType_Stack) {
    MS_LOG(ERROR) << "concate_op valid axis : " << axis_ << " , input dims : " << input_nbDims;
    return RET_ERROR;
  }
  return RET_OK;
}
int ConcateTensorRT::AddInnerOp(TensorRTContext *ctx) {
  if (ctx == nullptr || ctx->network() == nullptr) {
    MS_LOG(ERROR) << "context or network is invalid";
    return RET_ERROR;
  }

  if (in_tensors_.size() != in_tensors_.size()) {
    MS_LOG(ERROR) << "concate_op in tensor is invalid, trt tensor has " << in_tensors_.size()
                  << ", but origin ms tensor has " << in_tensors_.size();
    return RET_ERROR;
  }

  nvinfer1::ITensor *trt_input_tensors[in_tensors_.size()];
  int ret = PreProcessInputs(ctx, trt_input_tensors);
  if (ret != RET_OK) {
    MS_LOG(ERROR) << "PreProcessInputs failed for " << op_name_;
    return ret;
  }

  if (!same_format_) {
    if (trt_input_tensors[0]->getDimensions().nbDims == DIMENSION_4D && out_format_ == Format::NCHW) {
      // when inputs all NCHW, change axis
      axis_ = ConvertAxisFromNHWC2NCHW(axis_);
      MS_LOG(DEBUG) << "concate axis change to " << axis_ << " when using NCHW format.";
    } else {
      MS_LOG(WARNING) << "input tensor format needs check, convert concat axis failed for " << op_name_;
    }
  }

  if (type_ == schema::PrimitiveType_Stack) {
    for (size_t i = 0; i != in_tensors_.size(); ++i) {
      auto shuffle_layer = ctx->network()->addShuffle(*trt_input_tensors[i]);
      if (shuffle_layer == nullptr) {
        MS_LOG(ERROR) << "addShuffle failed for TensorRT.";
        return RET_ERROR;
      }
      auto shuffer_dims_opt = UnsqueezeDims(trt_input_tensors[i]->getDimensions(), axis_, 1);
      if (!shuffer_dims_opt) {
        MS_LOG(ERROR) << "UnsqueezeDims failed.";
        return RET_ERROR;
      }
      shuffle_layer->setReshapeDimensions(shuffer_dims_opt.value());
      trt_input_tensors[i] = shuffle_layer->getOutput(0);
    }
  }
  nvinfer1::IConcatenationLayer *concate_layer =
    ctx->network()->addConcatenation(trt_input_tensors, static_cast<int>(in_tensors_.size()));
  if (concate_layer == nullptr) {
    MS_LOG(ERROR) << "addConcatenation failed for TensorRT.";
    return RET_ERROR;
  }

  if (axis_ != RET_INVALID_OP_ATTR) {
    concate_layer->setAxis(axis_);
  }
  concate_layer->setName(op_name_.c_str());
  auto concat_output = concate_layer->getOutput(0);
  ctx->RegisterTensor(ITensorHelper{concat_output, out_format_, same_format_}, out_tensors_[0].Name());
  this->layer_ = concate_layer;
  return RET_OK;
}

int ConcateTensorRT::PreProcessInputs(TensorRTContext *ctx, nvinfer1::ITensor *trt_input_tensors[]) {
  int input_nbDims = input(ctx, 0).trt_tensor_->getDimensions().nbDims;
  out_format_ = input(ctx, 0).format_;
  same_format_ = input(ctx, 0).same_format_;

  for (size_t i = 0; i < in_tensors_.size(); i++) {
    if (input(ctx, i).trt_tensor_->getDimensions().nbDims != input_nbDims) {
      MS_LOG(ERROR) << "dims of inputs is invalid for " << op_name_;
      return RET_ERROR;
    }
    // keep origin format if all input format are the same
    if (input_nbDims == DIMENSION_4D && input(ctx, i).format_ != out_format_) {
      out_format_ = Format::NHWC;
    }
  }

  // make sure all inputs are same format
  if (input_nbDims == DIMENSION_4D) {
    for (size_t i = 0; i < in_tensors_.size(); i++) {
      if (input(ctx, i).format_ == out_format_) {
        trt_input_tensors[i] = input(ctx, i).trt_tensor_;
        MS_LOG(DEBUG) << "concate input " << GetTensorFormat(input(ctx, i));
      } else {
        nvinfer1::IShuffleLayer *transpose_layer = NCHW2NHWC(ctx, *input(ctx, i).trt_tensor_);
        if (transpose_layer == nullptr) {
          MS_LOG(ERROR) << "op action convert failed";
          return RET_ERROR;
        }
        trt_input_tensors[i] = transpose_layer->getOutput(0);
        this->transpose_layer_ = transpose_layer;
        same_format_ = true;
        MS_LOG(DEBUG) << "concate input " << GetTensorFormat(trt_input_tensors[i], Format::NHWC, true);
      }
    }
  } else {
    for (size_t i = 0; i < in_tensors_.size(); i++) {
      trt_input_tensors[i] = input(ctx, i).trt_tensor_;
      MS_LOG(DEBUG) << "concate input " << GetTensorFormat(input(ctx, i));
    }
  }
  return RET_OK;
}
REGISTER_TENSORRT_CREATOR(schema::PrimitiveType_Concat, ConcateTensorRT)
REGISTER_TENSORRT_CREATOR(schema::PrimitiveType_Stack, ConcateTensorRT)
}  // namespace mindspore::lite
