/**
 * Copyright 2020 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_CORE_C_OPS_UNSORTED_SEGMENT_SUM_H_
#define MINDSPORE_CORE_C_OPS_UNSORTED_SEGMENT_SUM_H_

#include <map>
#include <vector>
#include <string>
#include <memory>
#include "ops/primitive_c.h"
#include "abstract/abstract_value.h"
#include "utils/check_convert_utils.h"

namespace mindspore {
namespace ops {
constexpr auto kNameUnsortedSegmentSum = "UnsortedSegmentSum";
class UnsortedSegmentSum : public PrimitiveC {
 public:
  UnsortedSegmentSum() : PrimitiveC(kNameUnsortedSegmentSum) {
    InitIOName({"x", "segment_ids", "num_segments"}, {"y"});
  }
  ~UnsortedSegmentSum() = default;
  MS_DECLARE_PARENT(UnsortedSegmentSum, PrimitiveC);
  void Init() {}
};

AbstractBasePtr UnsortedSegmentSumInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                        const std::vector<AbstractBasePtr> &input_args);
using PrimUnsortedSegmentSumPtr = std::shared_ptr<UnsortedSegmentSum>;
}  // namespace ops
}  // namespace mindspore

#endif  // MINDSPORE_CORE_C_OPS_UNSORTED_SEGMENT_SUM_H_
