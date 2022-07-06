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
#include "ops/random_categorical.h"
#include <string>
#include <memory>
#include <set>
#include "ops/op_utils.h"
#include "utils/check_convert_utils.h"
#include "mindapi/src/helper.h"

namespace mindspore {
namespace ops {
namespace {
abstract::ShapePtr RandomCategoricalInferShape(const PrimitivePtr &primitive,
                                               const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  auto logits_shape_ptr = input_args[kInputIndex0]->BuildShape();
  auto logits_shape_map = CheckAndConvertUtils::ConvertShapePtrToShapeMap(logits_shape_ptr);
  auto logits_shape = logits_shape_map[kShape];
  if (logits_shape_ptr->IsDynamic()) {
    return logits_shape_ptr->cast<abstract::ShapePtr>();
  }
  if (logits_shape.size() != kDim2) {
    MS_EXCEPTION(TypeError) << "logits shape size only support 2D";
  }
  std::vector<int64_t> output_shape;
  for (size_t i = 0; i < logits_shape.size() - 1; ++i) {
    output_shape.push_back(logits_shape.at(i));
  }
  auto num_sample = primitive->GetAttr(kNumSample);
  if (num_sample == nullptr) {
    return logits_shape_ptr->cast<abstract::ShapePtr>();
  }
  output_shape.push_back(GetValue<int64_t>(num_sample));
  MS_LOG(INFO) << output_shape;
  return std::make_shared<abstract::Shape>(output_shape);
}

void AddNumSample(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  int64_t num_sample = -1;
  const auto &nun_sample_arg = input_args[kInputIndex1];
  if (nun_sample_arg->isa<abstract::AbstractScalar>()) {
    auto num_sample_input_type = nun_sample_arg->BuildType();
    if (num_sample_input_type->type_id() == kNumberTypeInt64) {
      auto num_sample_ptr = nun_sample_arg->cast<abstract::AbstractScalarPtr>();
      MS_EXCEPTION_IF_NULL(num_sample_ptr);
      num_sample = GetValue<int64_t>(num_sample_ptr->BuildValue());
    } else if (num_sample_input_type->type_id() == kNumberTypeInt32) {
      auto num_sample_ptr = nun_sample_arg->cast<abstract::AbstractScalarPtr>();
      MS_EXCEPTION_IF_NULL(num_sample_ptr);
      num_sample = GetValue<int32_t>(num_sample_ptr->BuildValue());
    } else {
      MS_EXCEPTION(TypeError) << "For '" << prim->name() << "' second input build type is invalid:"
                              << TypeIdToString(num_sample_input_type->type_id()) << ".";
    }
  } else if (nun_sample_arg->isa<abstract::AbstractTensor>()) {
    auto num_sample_ptr = nun_sample_arg->cast<abstract::AbstractTensorPtr>();
    MS_EXCEPTION_IF_NULL(num_sample_ptr);
    auto num_sample_value_ptr = num_sample_ptr->BuildValue();
    MS_EXCEPTION_IF_NULL(num_sample_value_ptr);
    auto num_sample_tensor = num_sample_value_ptr->cast<tensor::TensorPtr>();
    MS_EXCEPTION_IF_ZERO("num_sample_tensor->ElementsNum()", num_sample_tensor->ElementsNum());
    if (num_sample_tensor->data_type() == kNumberTypeInt64) {
      num_sample = static_cast<int64_t *>(num_sample_tensor->data_c())[0];
    } else if (num_sample_tensor->data_type() == kNumberTypeInt32) {
      num_sample = static_cast<int32_t *>(num_sample_tensor->data_c())[0];
    } else {
      MS_EXCEPTION(TypeError) << "For '" << prim->name() << "' second input build type is invalid:"
                              << TypeIdToString(num_sample_tensor->data_type()) << ".";
    }
  } else {
    MS_EXCEPTION(TypeError) << "For '" << prim->name()
                            << "', the second input type should be scalar or tensor, but got invalid abstract type:"
                            << nun_sample_arg->type_name() << ".";
  }
  prim->AddAttr(kNumSample, MakeValue(num_sample));
}

void AddSeed(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  int64_t seed = -1;
  const auto &seed_arg = input_args[kInputIndex2];
  if (seed_arg->isa<abstract::AbstractScalar>()) {
    auto seed_input_type = seed_arg->BuildType();
    if (seed_input_type->type_id() == kNumberTypeInt64) {
      auto seed_ptr = seed_arg->cast<abstract::AbstractScalarPtr>();
      MS_EXCEPTION_IF_NULL(seed_ptr);
      seed = GetValue<int64_t>(seed_ptr->BuildValue());
    } else if (seed_input_type->type_id() == kNumberTypeInt32) {
      auto seed_ptr = seed_arg->cast<abstract::AbstractScalarPtr>();
      MS_EXCEPTION_IF_NULL(seed_ptr);
      seed = GetValue<int32_t>(seed_ptr->BuildValue());
    } else {
      MS_EXCEPTION(TypeError) << "For '" << prim->name()
                              << "' third input build type is invalid:" << TypeIdToString(seed_input_type->type_id())
                              << ".";
    }
  } else if (seed_arg->isa<abstract::AbstractTensor>()) {
    auto seed_ptr = seed_arg->cast<abstract::AbstractTensorPtr>();
    MS_EXCEPTION_IF_NULL(seed_ptr);
    auto seed_value_ptr = seed_ptr->BuildValue();
    MS_EXCEPTION_IF_NULL(seed_value_ptr);
    auto seed_tensor = seed_value_ptr->cast<tensor::TensorPtr>();
    MS_EXCEPTION_IF_ZERO("seed_tensor->ElementsNum()", seed_tensor->ElementsNum());
    if (seed_tensor->data_type() == kNumberTypeInt64) {
      seed = static_cast<int64_t *>(seed_tensor->data_c())[0];
    } else if (seed_tensor->data_type() == kNumberTypeInt32) {
      seed = static_cast<int32_t *>(seed_tensor->data_c())[0];
    } else {
      MS_EXCEPTION(TypeError) << "For '" << prim->name()
                              << "' third input build type is invalid:" << TypeIdToString(seed_tensor->data_type())
                              << ".";
    }
  } else {
    MS_EXCEPTION(TypeError) << "For '" << prim->name()
                            << "', the third input type should be scalar, but got invalid abstract type:"
                            << seed_arg->type_name() << ".";
  }
  prim->AddAttr(kSeed, MakeValue(seed));
}

TypePtr RandomCategoricalInferType(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  auto prim_name = prim->name();
  const std::set<TypePtr> valid_logits_types = {kFloat16, kFloat32, kFloat64};
  (void)CheckAndConvertUtils::CheckTypeValid("logits", input_args[kInputIndex0]->BuildType(), valid_logits_types,
                                             prim_name);
  const std::set<TypePtr> valid_num_sample_types = {kInt32, kInt64};
  (void)CheckAndConvertUtils::CheckTypeValid("num_sample", input_args[kInputIndex1]->BuildType(),
                                             valid_num_sample_types, prim_name);
  const std::set<TypePtr> valid_seed_types = {kInt32, kInt64};
  (void)CheckAndConvertUtils::CheckTypeValid("seed", input_args[kInputIndex2]->BuildType(), valid_seed_types,
                                             prim_name);
  auto dtype_value = prim->GetAttr("dtype");
  if (!dtype_value->isa<Type>()) {
    MS_EXCEPTION(TypeError) << "For RandomPoisson, the dtype of " + prim_name + " is invalid!";
  }
  auto output_type = dtype_value->cast<TypePtr>();
  const std::set<TypePtr> valid_data_types = {kInt16, kInt32, kInt64};
  AddNumSample(prim, input_args);
  AddSeed(prim, input_args);
  return CheckAndConvertUtils::CheckSubClass("dtype", output_type, valid_data_types, prim_name);
}
}  // namespace

void RandomCategorical::Init(const int64_t num_sample, const int64_t seed) {
  this->set_num_sample(num_sample);
  this->set_seed(seed);
}

void RandomCategorical::set_num_sample(int64_t num_sample) {
  (void)this->AddAttr(kNumSample, api::MakeValue(num_sample));
}

int64_t RandomCategorical::get_num_sample() const {
  auto value_ptr = GetAttr(kNumSample);
  return GetValue<int64_t>(value_ptr);
}

void RandomCategorical::set_seed(int64_t seed) { (void)this->AddAttr(kSeed, api::MakeValue(seed)); }

int64_t RandomCategorical::get_seed() const {
  auto value_ptr = GetAttr(kSeed);
  return GetValue<int64_t>(value_ptr);
}

AbstractBasePtr RandomCategoricalInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                       const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  const int64_t kInputsNum = 3;
  CheckAndConvertUtils::CheckInputArgs(input_args, kEqual, kInputsNum, primitive->name());
  auto infertype = RandomCategoricalInferType(primitive, input_args);
  auto infershape = RandomCategoricalInferShape(primitive, input_args);
  return abstract::MakeAbstract(infershape, infertype);
}
MIND_API_OPERATOR_IMPL(RandomCategorical, BaseOperator);
REGISTER_PRIMITIVE_EVAL_IMPL(RandomCategorical, prim::kPrimRandomCategorical, RandomCategoricalInfer, nullptr, true);
}  // namespace ops
}  // namespace mindspore
