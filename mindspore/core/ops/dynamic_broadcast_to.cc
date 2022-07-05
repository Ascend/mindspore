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

#include "ops/dynamic_broadcast_to.h"

#include <set>
#include "utils/check_convert_utils.h"
#include "ops/op_utils.h"

namespace mindspore {
namespace ops {
namespace {
inline void CheckShapeValid(const ShapeVector &x_shape, const ShapeVector &output_shape) {
  auto outer_dim_offset = output_shape.size() - x_shape.size();
  for (size_t i = 0; i < x_shape.size(); ++i) {
    if (output_shape[i + outer_dim_offset] == -1 || x_shape[i] == -1) {
      continue;
    }
    if (output_shape[i + outer_dim_offset] != x_shape[i] && x_shape[i] != 1) {
      MS_EXCEPTION(ValueError) << "Not support shapes for broadcast, x_shape: " << x_shape
                               << ", target shape: " << output_shape;
    }
  }
}
abstract::ShapePtr DynamicBroadcastToInferShape(const PrimitivePtr &primitive,
                                                const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  auto prim_name = primitive->name();
  CheckAndConvertUtils::CheckInteger("input numbers", SizeToLong(input_args.size()), kEqual, 2, prim_name);
  auto x_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[0]->BuildShape())[kShape];
  auto input_y = input_args[1];
  MS_EXCEPTION_IF_NULL(input_y);
  abstract::ShapePtr y_shape;
  auto y_value = input_y->BuildValue();
  MS_EXCEPTION_IF_NULL(y_value);
  if (input_y->isa<abstract::AbstractTensor>()) {
    if (y_value->isa<tensor::Tensor>()) {
      auto shape_value = CheckAndConvertUtils::CheckTensorIntValue("shape", y_value, prim_name);
      return std::make_shared<abstract::Shape>(shape_value);
    }
    y_shape = CheckAndConvertUtils::GetTensorInputShape(prim_name, input_args, 1);
    auto shape_value = y_shape->shape();
    if (shape_value.size() != 1) {
      MS_EXCEPTION(TypeError) << "For '" << prim_name << "', the shape size must be 1, but got: " << shape_value.size()
                              << ".";
    }
    std::vector<int64_t> output_shape;
    std::vector<int64_t> max_shape;
    std::vector<int64_t> min_shape;

    if (y_shape->IsDynamic()) {
      output_shape.push_back(-2);
    } else {
      auto out_dims = LongToSize(y_shape->shape()[0]);
      auto min_value = input_y->cast<abstract::AbstractTensorPtr>()->get_min_value();
      auto max_value = input_y->cast<abstract::AbstractTensorPtr>()->get_max_value();
      min_shape = min_value ? GetValue<std::vector<int64_t>>(min_value) : ShapeVector();
      max_shape = max_value ? GetValue<std::vector<int64_t>>(max_value) : ShapeVector();
      if (min_shape.empty() || max_shape.empty()) {
        for (size_t i = 0; i < out_dims; i++) {
          output_shape.push_back(-1);
        }
      } else {
        if (min_shape.size() != out_dims || max_shape.size() != out_dims) {
          MS_EXCEPTION(ValueError)
            << "For 'BroadcastTo', inputs['shape'] min or max must have the same size as output's"
               ". But got min shape size: "
            << min_shape.size() << ", max shape size: " << max_shape.size() << ", output size: " << out_dims << ".";
        }
        for (size_t i = 0; i < out_dims; i++) {
          auto value = min_shape[i] == max_shape[i] ? max_shape[i] : -1;
          output_shape.push_back(value);
        }
      }

      CheckAndConvertUtils::Check("x shape", SizeToLong(x_shape.size()), kLessEqual, SizeToLong(output_shape.size()),
                                  prim_name);
      CheckShapeValid(x_shape, output_shape);
    }
    return std::make_shared<abstract::Shape>(output_shape, min_shape, max_shape);
  } else if (input_y->isa<abstract::AbstractTuple>()) {
    auto out_shape = GetValue<std::vector<int64_t>>(y_value);
    return std::make_shared<abstract::Shape>(out_shape);
  }
  MS_EXCEPTION(TypeError) << "For 'BroadcastTo', input args must be tensor or tuple.";
}

TypePtr DynamicBroadcastToInferType(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  for (const auto &item : input_args) {
    MS_EXCEPTION_IF_NULL(item);
  }
  auto x_dtype = input_args[0]->BuildType()->cast<TensorTypePtr>();
  std::set<TypePtr> template_types = {kTensorType};
  CheckAndConvertUtils::CheckSubClass("x_dtype", x_dtype, template_types, prim->name());
  return x_dtype->element();
}
}  // namespace

MIND_API_OPERATOR_IMPL(DynamicBroadcastTo, BaseOperator);
AbstractBasePtr DynamicBroadcastToInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                        const std::vector<AbstractBasePtr> &input_args) {
  return abstract::MakeAbstract(DynamicBroadcastToInferShape(primitive, input_args),
                                DynamicBroadcastToInferType(primitive, input_args));
}
REGISTER_PRIMITIVE_EVAL_IMPL(DynamicBroadcastTo, prim::kPrimDynamicBroadcastTo, DynamicBroadcastToInfer, nullptr, true);
}  // namespace ops
}  // namespace mindspore
