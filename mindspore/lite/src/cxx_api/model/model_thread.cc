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
#ifdef USING_SERVING
#include "src/cxx_api/model/model_thread.h"
#include "src/common/log.h"
#include "src/common/utils.h"
namespace mindspore {
Status ModelThread::Init(const std::string &model_path, const std::shared_ptr<Context> &model_context,
                         const Key &dec_key, const std::string &dec_mode) {
  model_ = std::make_shared<Model>();
  mindspore::ModelType model_type = kMindIR;
  auto status = model_->Build(model_path, model_type, model_context, dec_key, dec_mode);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "model build failed in ModelPool Init";
    return status;
  }
  return kSuccess;
}

Status ModelThread::ModelRun(const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs,
                             const MSKernelCallBack &before, const MSKernelCallBack &after) {
  auto status = model_->Predict(inputs, outputs, before, after);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "model predict failed.";
    return status;
  }
  return kSuccess;
}

std::pair<std::vector<std::vector<int64_t>>, bool> ModelThread::GetModelResize(
  const std::vector<MSTensor> &model_inputs, const std::vector<MSTensor> &inputs) {
  std::unique_lock<std::mutex> model_lock(mtx_model_);
  std::vector<std::vector<int64_t>> dims;
  bool need_resize = false;
  for (size_t i = 0; i < model_inputs.size(); i++) {
    for (size_t j = 0; j < model_inputs[i].Shape().size(); j++) {
      if (model_inputs[i].Shape()[j] != inputs[i].Shape()[j]) {
        need_resize = true;
      }
    }
    dims.push_back(inputs[i].Shape());
  }
  return std::make_pair(dims, need_resize);
}

Status ModelThread::Predict(const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs,
                            const MSKernelCallBack &before, const MSKernelCallBack &after) {
  // model
  auto model_input = model_->GetInputs();
  if (model_input.size() != inputs.size()) {
    MS_LOG(ERROR) << "model input size is: " << model_input.size() << ", but get input size is: " << inputs.size();
    return kLiteError;
  }
  auto resize_pair = GetModelResize(model_input, inputs);
  if (resize_pair.second) {
    auto dims = resize_pair.first;
    auto status = model_->Resize(model_->GetInputs(), dims);
    if (status != kSuccess) {
      MS_LOG(ERROR) << "model pool resize failed.";
      return kLiteError;
    }
  }

  auto status = ModelRun(inputs, outputs, before, after);
  if (status != kSuccess) {
    MS_LOG(ERROR) << "model predict failed in ModelPool.";
    return status;
  }
  return kSuccess;
}
}  // namespace mindspore
#endif