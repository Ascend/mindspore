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

#include <cuda_runtime.h>
#include <numeric>
#include <memory>
#include <vector>
#include <functional>
#include <unordered_map>
#include "src/extendrt/delegate/tensorrt/tensorrt_utils.h"
#include "NvInferRuntimeCommon.h"
#include "src/extendrt/delegate/tensorrt/op/cumsum_tensorrt.h"
#include "cumsum_impl.cuh"

namespace mindspore::lite {
int CumsumTensorRT::IsSupport(const schema::Primitive *primitive, const std::vector<mindspore::MSTensor> &in_tensors,
                              const std::vector<mindspore::MSTensor> &out_tensors) {
  if (in_tensors.size() != 2) {
    MS_LOG(ERROR) << "Unsupported input tensor size, size is " << in_tensors.size();
    return RET_ERROR;
  }

  if (out_tensors.size() < 1) {
    MS_LOG(ERROR) << "Unsupported output tensor size, size is " << out_tensors.size();
    return RET_ERROR;
  }
  return RET_OK;
}

int CumsumTensorRT::AddInnerOp(TensorRTContext *ctx) {
  ITensorHelper input;
  int ret = PreprocessInputs2SameDim(ctx, tensorrt_in_tensors_[0], &input);
  if (ret != RET_OK || input.trt_tensor_ == nullptr) {
    MS_LOG(ERROR) << "PreprocessInputs2SameDim input tensor failed for " << op_name_;
    return ret;
  }
  int axis = static_cast<const int *>(in_tensors_[1].Data().get())[0];
  bool exclusive = op_primitive_->value_as_CumSum()->exclusive();
  bool reverse = op_primitive_->value_as_CumSum()->reverse();
  auto plugin = std::make_shared<CumsumPlugin>(input.trt_tensor_->getName(), axis, exclusive, reverse, device_id_);
  nvinfer1::ITensor *inputTensors[] = {input.trt_tensor_};
  nvinfer1::IPluginV2Layer *cumsum_opt_layer = ctx->network()->addPluginV2(inputTensors, 1, *plugin);
  if (cumsum_opt_layer == nullptr) {
    MS_LOG(ERROR) << "add cumsum op failed for TensorRT.";
    return RET_ERROR;
  }
  cumsum_opt_layer->setName(op_name_.c_str());
  nvinfer1::ITensor *out_tensor = cumsum_opt_layer->getOutput(0);
  out_tensor->setName((op_name_ + "_output").c_str());
  this->AddInnerOutTensors(
    ITensorHelper{out_tensor, tensorrt_in_tensors_[0].format_, tensorrt_in_tensors_[0].same_format_});
  this->layer_ = cumsum_opt_layer;
  return RET_OK;
}

REGISTER_TENSORRT_PLUGIN(CumsumPluginCreater);
template class TensorRTPluginCreater<CumsumPlugin>;
template <class T>
nvinfer1::PluginFieldCollection TensorRTPluginCreater<T>::field_collection_{};
template <class T>
std::vector<nvinfer1::PluginField> TensorRTPluginCreater<T>::fields_;

int CumsumPlugin::enqueue(const nvinfer1::PluginTensorDesc *inputDesc, const nvinfer1::PluginTensorDesc *outputDesc,
                          const void *const *inputs, void *const *outputs, void *workspace,
                          cudaStream_t stream) noexcept {
  return RunCudaCumsum(inputDesc, inputs, outputs, stream);
}

int CumsumPlugin::RunCudaCumsum(const nvinfer1::PluginTensorDesc *inputDesc, const void *const *inputs,
                                void *const *outputs, cudaStream_t stream) {
  auto &dims = inputDesc[0].dims;
  size_t out_dim = 1;
  for (int i = 0; i < axis_; ++i) {
    out_dim *= dims.d[i];
  }
  size_t in_dim = 1;
  for (int i = axis_ + 1; i < dims.nbDims; ++i) {
    in_dim *= dims.d[i];
  }
  size_t axis_dim = dims.d[axis_];
  size_t stride = axis_dim * in_dim;
  size_t stride2 = in_dim;
  CumSum<int32_t>(static_cast<const int32_t *>(inputs[0]), static_cast<int32_t *>(outputs[0]), nullptr, out_dim,
                  axis_dim, in_dim, stride, stride2, exclusive_, reverse_, device_id_, stream);
  return RET_OK;
}

nvinfer1::IPluginV2DynamicExt *CumsumPlugin::clone() const noexcept {
  auto *plugin = new (std::nothrow) CumsumPlugin(*this);
  if (plugin == nullptr) {
    MS_LOG(ERROR) << "new plugin failed!";
    return nullptr;
  }
  plugin->setPluginNamespace(name_space_.c_str());
  return plugin;
}

size_t CumsumPlugin::getSerializationSize() const noexcept { return sizeof(int) + 2 * sizeof(bool); }

void CumsumPlugin::serialize(void *buffer) const noexcept {
  SerializeValue(&buffer, &axis_, sizeof(int));
  SerializeValue(&buffer, &exclusive_, sizeof(bool));
  SerializeValue(&buffer, &reverse_, sizeof(bool));
}
REGISTER_TENSORRT_CREATOR(schema::PrimitiveType_CumSum, CumsumTensorRT)
}  // namespace mindspore::lite
