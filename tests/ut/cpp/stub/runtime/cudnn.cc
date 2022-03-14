/**
 * Copyright 2019 Huawei Technologies Co., Ltd
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
#ifndef TESTS_UT_STUB_RUNTIME_INCLUDE_CUDNN_H_
#define TESTS_UT_STUB_RUNTIME_INCLUDE_CUDNN_H_

#include <cstddef>

extern "C" {

typedef enum { CUDNN_STATUS_SUCCESS = 0 } cudnnStatus_t;

struct cudnnHandle_t {};
struct cudaStream_t {};

cudnnStatus_t cudnnCreate(cudnnHandle_t *handle) { return CUDNN_STATUS_SUCCESS; }
cudnnStatus_t cudnnDestroy(cudnnHandle_t handle) { return CUDNN_STATUS_SUCCESS; }
cudnnStatus_t cudnnSetStream(cudnnHandle_t handle, cudaStream_t streamId) { return CUDNN_STATUS_SUCCESS; }
const char *cudnnGetErrorString(cudnnStatus_t status) { return "CUDNN_STATUS_SUCCESS"; }
}
#endif  // TESTS_UT_STUB_RUNTIME_INCLUDE_CUDNN_H_
