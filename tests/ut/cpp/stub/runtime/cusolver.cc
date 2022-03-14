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
#ifndef TESTS_UT_STUB_RUNTIME_INCLUDE_CUSOLVER_H_
#define TESTS_UT_STUB_RUNTIME_INCLUDE_CUSOLVER_H_

#include <cstddef>

extern "C" {
typedef enum { CUSOLVER_STATUS_SUCCESS = 0 } cusolverStatus_t;

struct cusolverDnHandle_t {};
struct cudaStream_t {};

cusolverStatus_t cusolverDnCreate(cusolverDnHandle_t *handle) { return CUSOLVER_STATUS_SUCCESS; }
cusolverStatus_t cusolverDnDestroy(cusolverDnHandle_t handle) { return CUSOLVER_STATUS_SUCCESS; }
cusolverStatus_t cusolverDnSetStream(cusolverDnHandle_t handle, cudaStream_t streamId) {
  return CUSOLVER_STATUS_SUCCESS;
}
}
#endif  // TESTS_UT_STUB_RUNTIME_INCLUDE_CUSOLVER_H_
