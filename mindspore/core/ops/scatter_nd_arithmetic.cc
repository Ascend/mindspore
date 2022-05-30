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

#include "ops/scatter_nd_update.h"
#include "ops/scatter_nd_add.h"
#include "ops/scatter_nd_sub.h"
#include "ops/scatter_nd_mul.h"
#include "ops/scatter_nd_div.h"
#include "ops/scatter_nd_max.h"
#include "ops/scatter_nd_min.h"
#include <map>
#include <string>
#include <sstream>
#include "abstract/ops/primitive_infer_map.h"
#include "ops/op_utils.h"
#include "utils/check_convert_utils.h"
#include "mindapi/src/helper.h"

namespace mindspore {
namespace ops {
namespace {
abstract::ShapePtr ScatterNdArithmeticInferShape(const PrimitivePtr &primitive,
                                                 const std::vector<AbstractBasePtr> &input_args) {
  auto prim_name = primitive->name();
  auto input_x_shape_ptr = input_args[kInputIndex0]->BuildShape();
  MS_EXCEPTION_IF_NULL(input_x_shape_ptr);
  auto indices_shape_ptr = input_args[kInputIndex1]->BuildShape();
  MS_EXCEPTION_IF_NULL(indices_shape_ptr);
  auto updates_shape_ptr = input_args[kInputIndex2]->BuildShape();
  MS_EXCEPTION_IF_NULL(updates_shape_ptr);
  if (input_x_shape_ptr->IsDynamic() || indices_shape_ptr->IsDynamic() || updates_shape_ptr->IsDynamic()) {
    return input_args[kInputIndex0]->BuildShape()->cast<abstract::ShapePtr>();
  }

  auto input_x_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_x_shape_ptr)[kShape];
  auto indices_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(indices_shape_ptr)[kShape];
  auto updates_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(updates_shape_ptr)[kShape];

  const int64_t input_x_size = SizeToLong(input_x_shape.size());
  const int64_t indices_size = SizeToLong(indices_shape.size());
  const int64_t updates_size = SizeToLong(updates_shape.size());
  const int64_t last_dim = indices_shape.back();

  CheckAndConvertUtils::CheckValue("the value of last dimension of 'indices'", last_dim, kLessEqual,
                                   "the dimension of 'input_x'", input_x_size, prim_name);

  CheckAndConvertUtils::CheckValue<int64_t>("dimension of 'indices'", indices_size, kGreaterEqual, 1, prim_name);
  CheckAndConvertUtils::CheckValue<int64_t>("dimension of 'updates'", updates_size, kGreaterEqual, 1, prim_name);

  CheckAndConvertUtils::CheckValue("len(updates.shape)'", updates_size, kEqual,
                                   "len(indices.shape) - 1 + len(input_x.shape) - indices.shape[-1]",
                                   indices_size - 1 + input_x_size - last_dim, prim_name);

  std::stringstream value_ss, match_value_ss;
  for (int i = 0; i < indices_size - 1; ++i) {
    value_ss.clear();
    match_value_ss.clear();
    value_ss << i << "th dimension of indices";
    match_value_ss << i << "th dimension of updates";
    CheckAndConvertUtils::CheckValue<int64_t>(value_ss.str(), indices_shape[i], kEqual, match_value_ss.str(),
                                              updates_shape[i], prim_name);
  }
  for (int64_t i = indices_size - 1; i < updates_size; ++i) {
    value_ss.clear();
    match_value_ss.clear();
    value_ss << i << "th dimension of updates";
    match_value_ss << (i - (indices_size - 1) + last_dim) << "th dimension of input_x.shape[indices.shape[-1]:]";
    CheckAndConvertUtils::CheckValue<int64_t>(value_ss.str(), updates_shape[i], kEqual, match_value_ss.str(),
                                              input_x_shape[i - (indices_size - 1) + last_dim], prim_name);
  }
  auto output_shape = input_x_shape_ptr->cast<abstract::ShapePtr>();
  return output_shape;
}

TypePtr ScatterNdArithmeticInferType(const PrimitivePtr &primitive, const std::vector<AbstractBasePtr> &input_args) {
  auto prim_name = primitive->name();
  auto input_x_dtype = input_args[kInputIndex0]->BuildType();
  auto indices_dtype = input_args[kInputIndex1]->BuildType();
  auto updates_dtype = input_args[kInputIndex2]->BuildType();
  (void)CheckAndConvertUtils::CheckTensorTypeValid("indices type", indices_dtype, {kInt32, kInt64}, prim_name);
  std::map<std::string, TypePtr> type_dict = {{"input_x type", input_x_dtype}, {"updates type", updates_dtype}};
  // Only ScatterNdUpdate supports boolean type
  if (prim_name == prim::kPrimScatterNdUpdate->name()) {
    return CheckAndConvertUtils::CheckTensorTypeSame(type_dict, common_valid_types_with_bool, prim_name);
  }
  return CheckAndConvertUtils::CheckTensorTypeSame(type_dict, common_valid_types, prim_name);
}
}  // namespace

void ScatterNdUpdate::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdUpdate::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdUpdate::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void ScatterNdAdd::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdAdd::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdAdd::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void ScatterNdSub::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdSub::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdSub::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void ScatterNdMul::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdMul::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdMul::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void ScatterNdDiv::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdDiv::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdDiv::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void ScatterNdMax::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdMax::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdMax::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void ScatterNdMin::Init(const bool use_locking) { this->set_use_locking(use_locking); }

void ScatterNdMin::set_use_locking(const bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool ScatterNdMin::get_use_locking() const {
  auto value_ptr = this->GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

MIND_API_OPERATOR_IMPL(ScatterNdUpdate, BaseOperator);
MIND_API_OPERATOR_IMPL(ScatterNdAdd, BaseOperator);
MIND_API_OPERATOR_IMPL(ScatterNdSub, BaseOperator);
MIND_API_OPERATOR_IMPL(ScatterNdMul, BaseOperator);
MIND_API_OPERATOR_IMPL(ScatterNdDiv, BaseOperator);
MIND_API_OPERATOR_IMPL(ScatterNdMax, BaseOperator);
MIND_API_OPERATOR_IMPL(ScatterNdMin, BaseOperator);
AbstractBasePtr ScatterNdArithmeticInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                         const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  const int64_t kInputNum = 3;
  (void)CheckAndConvertUtils::CheckInputArgs(input_args, kGreaterEqual, kInputNum, primitive->name());
  auto infer_type = ScatterNdArithmeticInferType(primitive, input_args);
  auto infer_shape = ScatterNdArithmeticInferShape(primitive, input_args);
  return abstract::MakeAbstract(infer_shape, infer_type);
}
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdUpdate, prim::kPrimScatterNdUpdate, ScatterNdArithmeticInfer, nullptr, true);
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdAdd, prim::kPrimScatterNdAdd, ScatterNdArithmeticInfer, nullptr, true);
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdSub, prim::kPrimScatterNdSub, ScatterNdArithmeticInfer, nullptr, true);
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdMul, prim::kPrimScatterNdMul, ScatterNdArithmeticInfer, nullptr, true);
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdDiv, prim::kPrimScatterNdDiv, ScatterNdArithmeticInfer, nullptr, true);
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdMax, prim::kPrimScatterNdMax, ScatterNdArithmeticInfer, nullptr, true);
REGISTER_PRIMITIVE_EVAL_IMPL(ScatterNdMin, prim::kPrimScatterNdMin, ScatterNdArithmeticInfer, nullptr, true);
}  // namespace ops
}  // namespace mindspore
