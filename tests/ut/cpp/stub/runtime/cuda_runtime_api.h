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
#ifndef TESTS_UT_STUB_RUNTIME_INCLUDE_CUDA_RUNTIME_API_H_
#define TESTS_UT_STUB_RUNTIME_INCLUDE_CUDA_RUNTIME_API_H_

#include <cstddef>

extern "C" {
typedef enum { cudaSuccess = 0, cudaErrorNotReady = 1 } cudaError_t;

inline const unsigned int cudaEventDefault = 0;

enum cudaMemcpyKind {
  cudaMemcpyHostToHost = 0,
  cudaMemcpyHostToDevice = 1,
  cudaMemcpyDeviceToHost = 2,
  cudaMemcpyDeviceToDevice = 3
};

struct CUstream_st {
  int arch;
};

struct CUevent_st {};
typedef struct CUevent_st *cudaEvent_t;

typedef struct CUStream_st *cudaStream_t;

struct cudaDeviceProp {};

cudaError_t cudaMalloc(void **devPtr, size_t size);
cudaError_t cudaHostAlloc(void **pHost, size_t size, unsigned int flags);
cudaError_t cudaFree(void *devPtr);
cudaError_t cudaFreeHost(void *devPtr);
cudaError_t cudaMemcpy(void *dst, const void *src, size_t count, enum cudaMemcpyKind kind);
cudaError_t cudaMemcpyAsync(void *dst, const void *src, size_t count, cudaMemcpyKind kind, cudaStream_t stream = 0);
cudaError_t cudaMemsetAsync(void *devPtr, int value, size_t count, cudaStream_t stream = 0);
cudaError_t cudaMemGetInfo(size_t *free, size_t *total);
cudaError_t cudaStreamCreate(cudaStream_t *pStream);
cudaError_t cudaStreamCreateWithFlags(cudaStream_t *pStream, unsigned int flags);
cudaError_t cudaStreamDestroy(cudaStream_t stream);
cudaError_t cudaStreamSynchronize(cudaStream_t stream);
cudaError_t cudaStreamWaitEvent(cudaStream_t stream, cudaEvent_t event, unsigned int flags = 0);
cudaError_t cudaGetDeviceCount(int *count);
cudaError_t cudaGetDeviceProperties(cudaDeviceProp *prop, int device);
cudaError_t cudaSetDevice(int device);
const char *cudaGetErrorString(cudaError_t error);
cudaError_t cudaEventCreate(cudaEvent_t *event);
cudaError_t cudaEventDestroy(cudaEvent_t event);
cudaError_t cudaEventQuery(cudaEvent_t event);
cudaError_t cudaEventElapsedTime(float *ms, cudaEvent_t start, cudaEvent_t end);
cudaError_t cudaEventCreateWithFlags(cudaEvent_t *event, unsigned int flags);
cudaError_t cudaEventRecord(cudaEvent_t event, cudaStream_t stream = 0);
cudaError_t cudaEventRecordWithFlags(cudaEvent_t event, cudaStream_t stream = 0, unsigned int flags = 0);
cudaError_t cudaEventSynchronize(cudaEvent_t event);
}
#endif  // TESTS_UT_STUB_RUNTIME_INCLUDE_CUDA_RUNTIME_API_H_
