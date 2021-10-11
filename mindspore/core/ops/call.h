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

#ifndef MINDSPORE_CORE_OPS_CALL_H_
#define MINDSPORE_CORE_OPS_CALL_H_
#include "ops/primitive_c.h"
#include "abstract/abstract_value.h"
#include "utils/check_convert_utils.h"

namespace mindspore {
namespace ops {
constexpr auto kNameCall = "call";
/// \brief Call op means function call in the MindIR. This operator is defined for serialization.
class MS_CORE_API Call : public PrimitiveC {
 public:
  /// \brief Constructor.
  Call() : PrimitiveC(kNameCall) {}
  /// \brief Destructor.
  ~Call() = default;
  MS_DECLARE_PARENT(Call, PrimitiveC);
};
}  // namespace ops
}  // namespace mindspore

#endif  // MINDSPORE_CORE_OPS_CALL_H_
