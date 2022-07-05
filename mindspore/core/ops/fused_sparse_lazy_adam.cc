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

#include "ops/fused_sparse_lazy_adam.h"
#include <string>
#include <memory>
#include <vector>
#include <algorithm>
#include "ops/op_utils.h"
#include "utils/check_convert_utils.h"
#include "abstract/ops/primitive_infer_map.h"
#include "mindapi/src/helper.h"

namespace mindspore {
namespace ops {
namespace fused_sparse_lazy_adam {
// "var","m","v","beta1_power","beta2_power","lr","beta1","beta2","epsilon","grad","indices"
constexpr size_t kVarIndex = 0;
constexpr size_t kMIndex = 1;
constexpr size_t kVIndex = 2;
constexpr size_t kBeta1PowerIndex = 3;
constexpr size_t kBeta2Powerndex = 4;
constexpr size_t kLrIndex = 5;
constexpr size_t kBeta1Index = 6;
constexpr size_t kBeta2Index = 7;
constexpr size_t kEpsilonIndex = 8;
constexpr size_t kGradIndex = 9;
constexpr size_t kIndicesIndex = 10;
constexpr size_t kFusedSparseLazyAdamInputNum = 11;

abstract::TupleShapePtr FusedSparseLazyAdamInferShape(const PrimitivePtr &primitive,
                                                      const std::vector<AbstractBasePtr> &input_args) {
  // "var","m","v","beta1_power","beta2_power","lr","beta1","beta2","epsilon","grad","indices"
  auto prim_name = primitive->name();
  // the output is useless, so we don't have to focus on the output shape, cannot return 1
  auto var_shape_r = input_args[kVarIndex]->Broaden()->BuildShape();
  auto m_shape_r = input_args[kMIndex]->Broaden()->BuildShape();
  auto v_shape_r = input_args[kVIndex]->Broaden()->BuildShape();
  auto outputs =
    std::make_shared<abstract::TupleShape>(std::vector<abstract::BaseShapePtr>({var_shape_r, m_shape_r, v_shape_r}));
  for (auto &input : input_args) {
    if (input->BuildShape()->IsDynamic()) {
      return outputs;
    }
  }
  auto var_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[kVarIndex]->BuildShape())[kShape];
  auto m_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[kMIndex]->BuildShape())[kShape];
  auto v_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[kVIndex]->BuildShape())[kShape];
  auto indices_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[kIndicesIndex]->BuildShape())[kShape];
  auto grad_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[kGradIndex]->BuildShape())[kShape];

  (void)CheckAndConvertUtils::CheckValue("var_shape", var_shape, kEqual, "m_shape", m_shape, prim_name);
  (void)CheckAndConvertUtils::CheckValue("var_shape", var_shape, kEqual, "v_shape", v_shape, prim_name);
  (void)CheckAndConvertUtils::CheckInteger("indices rank", indices_shape.size(), kEqual, 1, prim_name);
  (void)CheckAndConvertUtils::CheckInteger("grad rank", grad_shape.size(), kGreaterEqual, 1, prim_name);
  (void)CheckAndConvertUtils::CheckValue("grad_shape[0]", grad_shape[0], kEqual, "indices_shape[0]", indices_shape[0],
                                         prim_name);
  if (var_shape.size() > 1) {
    auto expect_shape = indices_shape;
    std::copy(var_shape.begin() + 1, var_shape.end(), std::back_inserter(expect_shape));
    if (grad_shape != expect_shape) {
      MS_EXCEPTION(ValueError) << "For '" << prim_name << "', the shape of updates must be [] or "
                               << "grad_shape = indices_shape + var_shape[1:], but got var_shape: " << var_shape
                               << ", indices_shape: " << indices_shape << ", grad_shape: " << grad_shape << ".";
    }
  }
  return outputs;
}

TypePtr FusedSparseLazyAdamInferType(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  // "var","m","v","beta1_power","beta2_power","lr","beta1","beta2","epsilon","grad","indices"
  auto prim_name = prim->name();
  std::map<std::string, TypePtr> types = {{"var", input_args[kVarIndex]->BuildType()},
                                          {"m", input_args[kMIndex]->BuildType()},
                                          {"v", input_args[kVIndex]->BuildType()},
                                          {"grad", input_args[kGradIndex]->BuildType()}};
  (void)CheckAndConvertUtils::CheckTensorTypeSame(types, common_valid_types_with_complex, prim_name);

  types = {
    {"beta1_power", input_args[kBeta1PowerIndex]->BuildType()},
    {"beta2_power", input_args[kBeta2Powerndex]->BuildType()},
    {"lr", input_args[kLrIndex]->BuildType()},
    {"beta1", input_args[kBeta1Index]->BuildType()},
    {"beta2", input_args[kBeta2Index]->BuildType()},
    {"epsilon", input_args[kEpsilonIndex]->BuildType()},
  };
  (void)CheckAndConvertUtils::CheckScalarOrTensorTypesSame(types, {kFloat16, kFloat32}, prim_name);

  auto indices_dtype = input_args[kIndicesIndex]->BuildType();
  (void)CheckAndConvertUtils::CheckTensorTypeValid("indices", indices_dtype, {kInt32}, prim_name);

  auto type = input_args[kVarIndex]->BuildType();
  return std::make_shared<Tuple>(std::vector<TypePtr>{type, type, type});
}
}  // namespace fused_sparse_lazy_adam
void FusedSparseLazyAdam::set_use_locking(bool use_locking) {
  (void)this->AddAttr(kUseLocking, api::MakeValue(use_locking));
}

bool FusedSparseLazyAdam::get_use_locking() const {
  auto value_ptr = GetAttr(kUseLocking);
  return GetValue<bool>(value_ptr);
}

void FusedSparseLazyAdam::set_use_nesterov(bool use_nesterov) {
  (void)this->AddAttr(kUseNesterov, api::MakeValue(use_nesterov));
}

bool FusedSparseLazyAdam::get_use_nesterov() const {
  auto value_ptr = GetAttr(kUseNesterov);
  return GetValue<bool>(value_ptr);
}

void FusedSparseLazyAdam::Init(bool use_locking, bool use_nesterov) {
  this->set_use_locking(use_locking);
  this->set_use_nesterov(use_nesterov);
}

MIND_API_OPERATOR_IMPL(FusedSparseLazyAdam, BaseOperator);
AbstractBasePtr FusedSparseLazyAdamInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                         const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  for (auto &item : input_args) {
    MS_EXCEPTION_IF_NULL(item);
  }
  auto op_name = primitive->name();
  (void)CheckAndConvertUtils::CheckInteger("input numbers", SizeToLong(input_args.size()), kGreaterEqual,
                                           fused_sparse_lazy_adam::kFusedSparseLazyAdamInputNum, op_name);
  auto types = fused_sparse_lazy_adam::FusedSparseLazyAdamInferType(primitive, input_args);
  auto shapes = fused_sparse_lazy_adam::FusedSparseLazyAdamInferShape(primitive, input_args);
  return abstract::MakeAbstract(shapes, types);
}

REGISTER_PRIMITIVE_EVAL_IMPL(FusedSparseLazyAdam, prim::kPrimFusedSparseLazyAdam, FusedSparseLazyAdamInfer, nullptr,
                             true)
}  // namespace ops
}  // namespace mindspore
