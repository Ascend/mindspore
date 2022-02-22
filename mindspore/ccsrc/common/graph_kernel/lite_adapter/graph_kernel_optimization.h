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
#ifndef MINDSPORE_CCSRC_BACKEND_OPTIMIZER_GRAPH_KERNEL_LITE_ADAPTER_GRAPH_KERNEL_OPTIMIZATION_H_
#define MINDSPORE_CCSRC_BACKEND_OPTIMIZER_GRAPH_KERNEL_LITE_ADAPTER_GRAPH_KERNEL_OPTIMIZATION_H_

#include "ir/anf.h"
#include "ir/func_graph.h"
#include "backend/common/optimizer/optimizer.h"
#include "backend/common/optimizer/pass_manager.h"

namespace mindspore::graphkernel {
using opt::PassManagerPtr;
class GraphKernelOptimizer {
 public:
  void Run(const FuncGraphPtr &kernel_graph);

 private:
  // before graph_kernel
  PassManagerPtr PreProcess() const;
  // Cluster kernels
  PassManagerPtr Cluster() const;
  // Split kernels
  PassManagerPtr Split() const;
};

void GraphKernelOptimize(const FuncGraphPtr &kernel_graph);
}  // namespace mindspore::graphkernel
#endif  // MINDSPORE_CCSRC_BACKEND_OPTIMIZER_GRAPH_KERNEL_LITE_ADAPTER_GRAPH_KERNEL_OPTIMIZATION_H_