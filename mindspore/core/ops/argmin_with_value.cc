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

#include "ops/argmin_with_value.h"
#include <set>
#include <string>

#include "ops/op_utils.h"
#include "utils/check_convert_utils.h"
#include "abstract/ops/primitive_infer_map.h"
#include "mindapi/src/helper.h"

namespace mindspore {
namespace ops {
int64_t ArgMinWithValue::axis() const {
  auto value_ptr = GetAttr("axis");
  MS_EXCEPTION_IF_NULL(value_ptr);
  return GetValue<int64_t>(value_ptr);
}

bool ArgMinWithValue::keep_dims() const {
  auto value_ptr = GetAttr("keep_dims");
  MS_EXCEPTION_IF_NULL(value_ptr);
  return GetValue<bool>(value_ptr);
}

namespace {
abstract::TupleShapePtr ArgMinWithValueInferShape(const PrimitivePtr &primitive,
                                                  const std::vector<AbstractBasePtr> &input_args) {
  auto prim_name = primitive->name();
  auto x_shape_ptr = input_args[0]->BuildShape();
  auto x_shape_map = CheckAndConvertUtils::ConvertShapePtrToShapeMap(x_shape_ptr);
  auto x_shape = x_shape_map[kShape];
  auto axis_value = primitive->GetAttr("axis");
  MS_EXCEPTION_IF_NULL(axis_value);
  auto axis = GetValue<int64_t>(axis_value);
  auto keep_dims_value = primitive->GetAttr("keep_dims");
  MS_EXCEPTION_IF_NULL(keep_dims_value);
  auto keep_dims = GetValue<bool>(keep_dims_value);
  auto x_rank = SizeToLong(x_shape.size());
  if (x_rank == 0) {
    if (axis != -1 && axis != 0) {
      MS_EXCEPTION(ValueError) << "For ArgMinWithValue with 0d input tensor, axis must be one of 0 or -1, but got"
                               << axis << ".";
    }
    return std::make_shared<abstract::TupleShape>(std::vector<abstract::BaseShapePtr>{x_shape_ptr, x_shape_ptr});
  }
  if (axis < 0) {
    axis += x_rank;
  }
  if (axis < 0 || axis >= x_rank) {
    MS_EXCEPTION(ValueError) << "For ArgMinWithValue, axis must be in range [-x_rank, x_rank), but got" << axis << ".";
  }
  (void)primitive->AddAttr("dimension", MakeValue(axis));
  // Calculate all the shapes.
  auto cal_shape = [axis, keep_dims](ShapeVector &shape, const ShapeVector &x_shape) -> void {
    (void)shape.insert(shape.end(), x_shape.begin(), x_shape.end());
    if (keep_dims) {
      shape[axis] = 1;
    } else {
      (void)shape.erase(shape.begin() + axis);
    }
  };
  ShapeVector output_shape;
  cal_shape(output_shape, x_shape);
  auto index_and_value_shape = std::make_shared<abstract::Shape>(output_shape);
  return std::make_shared<abstract::TupleShape>(
    std::vector<abstract::BaseShapePtr>{index_and_value_shape, index_and_value_shape});
}

TuplePtr ArgMinWithValueInferType(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  const std::set<TypePtr> valid_types = {kInt16, kInt32, kUInt16, kUInt32, kFloat16, kFloat32, kFloat64};
  TypePtr input_x_type = input_args[0]->BuildType();
  (void)CheckAndConvertUtils::CheckTensorTypeValid("input_x", input_x_type, valid_types, prim->name());
  auto index_type = std::make_shared<TensorType>(kInt32);
  return std::make_shared<Tuple>(std::vector<TypePtr>{index_type, input_x_type});
}
}  // namespace

AbstractBasePtr ArgMinWithValueInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                     const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  const int64_t input_num = 1;
  CheckAndConvertUtils::CheckInputArgs(input_args, kEqual, input_num, primitive->name());
  auto shapes = ArgMinWithValueInferShape(primitive, input_args);
  auto types = ArgMinWithValueInferType(primitive, input_args);
  return abstract::MakeAbstract(shapes, types);
}

MIND_API_OPERATOR_IMPL(ArgMinWithValue, BaseOperator);
REGISTER_PRIMITIVE_EVAL_IMPL(ArgMinWithValue, prim::kPrimArgMinWithValue, ArgMinWithValueInfer, nullptr, true);
}  // namespace ops
}  // namespace mindspore
