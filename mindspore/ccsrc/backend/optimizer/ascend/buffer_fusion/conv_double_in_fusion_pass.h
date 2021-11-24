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
#ifndef MINDSPORE_CCSRC_BACKEND_OPTIMIZER_ASCEND_BUFFER_FUSION_PASS_CONV_DOUBLE_IN_FUSION_PASS_H_
#define MINDSPORE_CCSRC_BACKEND_OPTIMIZER_ASCEND_BUFFER_FUSION_PASS_CONV_DOUBLE_IN_FUSION_PASS_H_

#include <vector>

#include "utils/hash_set.h"
#include "backend/optimizer/ascend/buffer_fusion/fusion_base_pass.h"
#include "ir/anf.h"
#include "backend/optimizer/common/pass.h"
#include "backend/optimizer/common/fusion_id_allocator.h"
#include "runtime/device/kernel_info.h"
#include "backend/kernel_compiler/kernel.h"
#include "backend/session/kernel_graph.h"

namespace mindspore {
namespace opt {
using FusedNodeRecord = std::vector<mindspore::HashSet<AnfNodePtr>>;

class ConvDoubleInFusionPass : public FusionBasePass {
 public:
  explicit ConvDoubleInFusionPass(FusionIdAllocatorPtr idAllocator)
      : FusionBasePass("ConvDoubleInFusionPass", idAllocator) {}
  ~ConvDoubleInFusionPass() override = default;
  void MatchSingleFusionPattern(const session::KernelGraph &kernel_graph, FusedNodeRecord *candidate_fusion) override;

 private:
  void MatchConvDoubleInEltwise(const CNodePtr &cnode, const session::KernelGraph &kernel_graph,
                                FusedNodeRecord *candidate_fusion);
};
}  // namespace opt
}  // namespace mindspore
#endif  // MINDSPORE_CCSRC_BACKEND_OPTIMIZER_ASCEND_BUFFER_FUSION_PASS_CONV_DOUBLE_IN_FUSION_PASS_H_
