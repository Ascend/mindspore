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

#ifndef MINDSPORE_CORE_OPS_UNIQUE_CONSECUTIVE_H_
#define MINDSPORE_CORE_OPS_UNIQUE_CONSECUTIVE_H_
#include <memory>
#include <vector>

#include "abstract/abstract_value.h"
#include "mindapi/base/types.h"
#include "ops/base_operator.h"
#include "ops/primitive_c.h"

namespace mindspore {
namespace ops {
constexpr auto kNameUniqueConsecutive = "UniqueConsecutive";
/// \brief Returns the elements that are unique in each consecutive group of equivalent elements in the input tensor.
/// Refer to Python API @ref mindspore.ops.UniqueConsecutive for more details.
class MIND_API UniqueConsecutive : public BaseOperator {
 public:
  MIND_API_BASE_MEMBER(UniqueConsecutive);
  /// \brief Constructor.
  UniqueConsecutive() : BaseOperator(kNameUniqueConsecutive) {
    InitIOName({"input", "return_idx", "return_counts", "axis"}, {"output", "idx", "counts"});
  }
  /// \brief Init.
  void Init() const {}
};
AbstractBasePtr UniqueConsecutiveInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                       const std::vector<AbstractBasePtr> &input_args);
using PrimUniqueConsecutivePtr = std::shared_ptr<UniqueConsecutive>;
}  // namespace ops
}  // namespace mindspore

#endif  // MINDSPORE_CORE_OPS_UNIQUE_CONSECUTIVE_H_
