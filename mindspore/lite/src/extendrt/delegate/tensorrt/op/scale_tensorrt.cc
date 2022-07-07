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

#include <numeric>
#include <functional>
#include "src/extendrt/delegate/tensorrt/op/scale_tensorrt.h"
#include "src/extendrt/delegate/tensorrt/op/activation_tensorrt.h"
#include "src/extendrt/delegate/tensorrt/tensorrt_utils.h"

namespace mindspore::lite {
constexpr int SCALE_INDEX = 1;
constexpr int SHIFT_INDEX = 2;
constexpr int POWER_INDEX = 3;

int ScaleTensorRT::IsSupport(const schema::Primitive *primitive, const std::vector<mindspore::MSTensor> &in_tensors,
                             const std::vector<mindspore::MSTensor> &out_tensors) {
  if (!IsShapeKnown()) {
    MS_LOG(ERROR) << "Unsupported input tensor unknown shape: " << op_name_;
    return RET_ERROR;
  }
  if (in_tensors.size() != INPUT_SIZE2 && in_tensors.size() != INPUT_SIZE3 && in_tensors.size() != INPUT_SIZE4) {
    MS_LOG(ERROR) << "Unsupported input tensor size, size is: " << in_tensors.size();
    return RET_ERROR;
  }
  if (out_tensors.size() != 1) {
    MS_LOG(ERROR) << "Unsupported output tensor size, size is: " << out_tensors.size();
    return RET_ERROR;
  }
  return RET_OK;
}

int ScaleTensorRT::AddInnerOp(TensorRTContext *ctx) {
  CHECK_NULL_RETURN(ctx);
  auto scale_op = op_primitive_->value_as_ScaleFusion();
  CHECK_NULL_RETURN(scale_op);

  schema::ActivationType activation_type = scale_op->activation_type();
  // mode of scale
  axis_ = scale_op->axis();
  axis_ = axis_ < 0 ? static_cast<int64_t>(in_tensors_[0].Shape().size() + axis_) : axis_;
  out_format_ = input(ctx, 0).format_;
  out_same_format_ = input(ctx, 0).same_format_;
  mode_ = GetScaleMode(axis_);
  MS_LOG(DEBUG) << "before transpose " << GetTensorFormat(input(ctx, 0));

  nvinfer1::ITensor *scale_in_tensor = PreProcessInputTensor(ctx);
  if (scale_in_tensor == nullptr) {
    MS_LOG(ERROR) << "PreProcessInputTensor failed: " << op_name_;
    return RET_ERROR;
  }

  MS_LOG(DEBUG) << "after transpose " << GetTensorFormat(scale_in_tensor, out_format_, out_same_format_);

  nvinfer1::ITensor *op_out_tensor{nullptr};
  if (scale_in_tensor->getDimensions().nbDims == DIMENSION_4D) {
    op_out_tensor = RunAs4DimsScale(ctx, scale_in_tensor);
  } else {
    op_out_tensor = RunAsMutiDimsScale(ctx, scale_in_tensor);
  }
  CHECK_NULL_RETURN(op_out_tensor);

  // add activation
  if (activation_type != schema::ActivationType::ActivationType_NO_ACTIVATION) {
    auto activation_layer = ActivationTensorRT::AddActivation(ctx, activation_type, 0, 0, 0, op_out_tensor, device_id_);
    CHECK_NULL_RETURN(activation_layer);
    activation_layer->setName((op_name_ + "_activation").c_str());
    op_out_tensor = activation_layer->getOutput(0);
  }

  auto output_helper = ITensorHelper{op_out_tensor, out_format_, out_same_format_};
  ctx->RegisterTensor(output_helper, out_tensors_[0].Name());
  MS_LOG(DEBUG) << "output " << GetTensorFormat(output_helper);
  return RET_OK;
}

nvinfer1::ITensor *ScaleTensorRT::PreProcessInputTensor(TensorRTContext *ctx) {
  nvinfer1::ITensor *scale_in_tensor = input(ctx, 0).trt_tensor_;
  if (input(ctx, 0).trt_tensor_->getDimensions().nbDims == DIMENSION_4D && mode_ == nvinfer1::ScaleMode::kCHANNEL) {
    // per channel input format should be nchw, otherwise should be same with scale nhwc
    // transpose: NHWC->NCHW
    if ((input(ctx, 0).format_ == Format::NHWC && axis_ == kNHWC_C) ||
        (input(ctx, 0).same_format_ == true && axis_ == kNHWC_C)) {
      nvinfer1::IShuffleLayer *transpose_layer_in = NHWC2NCHW(ctx, *input(ctx, 0).trt_tensor_);
      if (transpose_layer_in == nullptr) {
        MS_LOG(ERROR) << "op action convert failed";
        return nullptr;
      }
      transpose_layer_in->setName((op_name_ + "_transpose2NCHW").c_str());
      scale_in_tensor = transpose_layer_in->getOutput(0);
      out_format_ = Format::NCHW;
      out_same_format_ = !out_same_format_;
    } else if (out_format_ != Format::NCHW && axis_ != kNCHW_C) {
      MS_LOG(WARNING) << op_name_ << " out format (NHWC:1, NCHW:0) infer as " << out_format_ << ", and axis is "
                      << axis_;
    }
  } else if (input(ctx, 0).trt_tensor_->getDimensions().nbDims == DIMENSION_4D &&
             input(ctx, 0).format_ == Format::NCHW && mode_ == nvinfer1::ScaleMode::kELEMENTWISE) {
    // transpose: NCHW->NHWC
    nvinfer1::IShuffleLayer *transpose_layer_in = NCHW2NHWC(ctx, *input(ctx, 0).trt_tensor_);
    if (transpose_layer_in == nullptr) {
      MS_LOG(ERROR) << "op action convert failed";
      return nullptr;
    }
    transpose_layer_in->setName((op_name_ + "_transpose2NHWC").c_str());
    scale_in_tensor = transpose_layer_in->getOutput(0);
    out_format_ = Format::NHWC;
    out_same_format_ = true;
  }
  return scale_in_tensor;
}

nvinfer1::ScaleMode ScaleTensorRT::GetScaleMode(int64_t axis) {
  nvinfer1::ScaleMode mode = nvinfer1::ScaleMode::kUNIFORM;
  auto input_data_shape = in_tensors_[0].Shape();
  auto input_weight_shape = in_tensors_[1].Shape();
  int total = std::accumulate(input_data_shape.begin(), input_data_shape.end(), 1, std::multiplies<int>());
  if (input_weight_shape.size() == 0 || (input_weight_shape.size() == 1 && input_weight_shape[0] == 1)) {
    mode = nvinfer1::ScaleMode::kUNIFORM;
  } else if ((axis < static_cast<int64_t>(input_data_shape.size()) && input_weight_shape.size() == 1 &&
              input_data_shape[axis] == input_weight_shape[0]) ||
             (input_data_shape.size() == DIMENSION_4D && axis == DIMENSION_3D)) {
    mode = nvinfer1::ScaleMode::kCHANNEL;
  } else if (input_weight_shape.size() == 1 && input_weight_shape[0] == total) {
    mode = nvinfer1::ScaleMode::kELEMENTWISE;
  } else {
    MS_LOG(ERROR) << "ScaleMode create failed: " << op_name_;
    return mode;
  }
  MS_LOG(DEBUG) << op_name_ << " ScaleMode(UNIFORM 0, CHANNEL 1, ELEMENTWISE 2): " << static_cast<int>(mode);
  return mode;
}

nvinfer1::ITensor *ScaleTensorRT::RunAs4DimsScale(TensorRTContext *ctx, nvinfer1::ITensor *scale_in_tensor) {
  bool nd = false;
  // (input * scale + shift) ^ power
  nvinfer1::Weights power{nvinfer1::DataType::kFLOAT, nullptr, 0};
  nvinfer1::Weights shift{nvinfer1::DataType::kFLOAT, nullptr, 0};
  nvinfer1::Weights scale{nvinfer1::DataType::kFLOAT, nullptr, 0};
  if (in_tensors_.size() > SCALE_INDEX) {
    scale.values = in_tensors_[SCALE_INDEX].MutableData();
    MS_ASSERT(scale.values);
    scale.count = in_tensors_[SCALE_INDEX].ElementNum();
    scale.type = ConvertDataType(in_tensors_[SCALE_INDEX].DataType());
    shift.type = scale.type;
    power.type = scale.type;
    nd = in_tensors_[1].Shape().size() == 1 ? false : true;
  }
  if (in_tensors_.size() > SHIFT_INDEX) {
    shift.values = in_tensors_[SHIFT_INDEX].MutableData();
    MS_ASSERT(shift.values);
    shift.count = in_tensors_[SHIFT_INDEX].ElementNum();
  }
  if (in_tensors_.size() > POWER_INDEX) {
    power.values = in_tensors_[POWER_INDEX].MutableData();
    MS_ASSERT(power.values);
    power.count = in_tensors_[POWER_INDEX].ElementNum();
  }
  nvinfer1::IScaleLayer *cal_layer = nullptr;

  if (nd) {
    MS_LOG(WARNING) << "multi dims ScaleMode enter";
    cal_layer = ctx->network()->addScaleNd(*scale_in_tensor, mode_, shift, scale, power, axis_);
  } else {
    cal_layer = ctx->network()->addScale(*scale_in_tensor, mode_, shift, scale, power);
  }

  if (cal_layer == nullptr) {
    MS_LOG(ERROR) << "addScaleNd failed for: " << op_name_;
    return nullptr;
  }
  cal_layer->setName(op_name_.c_str());
  this->layer_ = cal_layer;
  return cal_layer->getOutput(0);
}

nvinfer1::ITensor *ScaleTensorRT::RunAsMutiDimsScale(TensorRTContext *ctx, nvinfer1::ITensor *scale_in_tensor) {
  auto scale_tensor = ConvertConstantTensorWithDims(ctx, in_tensors_[1], in_tensors_[0].Shape(), op_name_);
  if (scale_tensor == nullptr) {
    MS_LOG(ERROR) << "ConvertConstantTensorWithDims failed for " << op_name_;
    return nullptr;
  }
  auto mul_layer =
    ctx->network()->addElementWise(*scale_in_tensor, *scale_tensor, nvinfer1::ElementWiseOperation::kPROD);
  if (mul_layer == nullptr) {
    MS_LOG(ERROR) << "add mul failed for " << op_name_;
    return nullptr;
  }
  mul_layer->setName((op_name_ + "_scale").c_str());
  layer_ = mul_layer;
  nvinfer1::ITensor *out_tensor = mul_layer->getOutput(0);
  // add shift
  if (in_tensors_.size() >= INPUT_SIZE3) {
    auto shift_tensor = ConvertConstantTensorWithDims(ctx, in_tensors_[SHIFT_INDEX], in_tensors_[0].Shape(), op_name_);
    if (shift_tensor == nullptr) {
      MS_LOG(ERROR) << "ConvertConstantTensorWithDims failed for " << op_name_;
      return nullptr;
    }
    auto shift_layer = ctx->network()->addElementWise(*out_tensor, *shift_tensor, nvinfer1::ElementWiseOperation::kSUM);
    if (shift_layer == nullptr) {
      MS_LOG(ERROR) << "add bias failed for " << op_name_;
      return nullptr;
    }
    shift_layer->setName((op_name_ + "_shift").c_str());
    out_tensor = shift_layer->getOutput(0);
  }
  if (in_tensors_.size() == INPUT_SIZE4) {
    MS_LOG(WARNING) << op_name_ << " has power";
    return nullptr;
  }
  return out_tensor;
}
REGISTER_TENSORRT_CREATOR(schema::PrimitiveType_ScaleFusion, ScaleTensorRT)
}  // namespace mindspore::lite
