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
#include "ops/ps_roi_pooling.h"
#include <set>

#include "ops/op_utils.h"
#include "utils/check_convert_utils.h"
#include "utils/tensor_construct_utils.h"
#include "abstract/ops/primitive_infer_map.h"
#include "mindapi/src/helper.h"

namespace mindspore {
namespace ops {
namespace {
abstract::ShapePtr PSROIPoolingInferShape(const PrimitivePtr &primitive,
                                          const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);

  auto prim_name = primitive->name();
  (void)CheckAndConvertUtils::CheckInteger("input numbers", int64_t(input_args.size()), kGreaterEqual, 2, prim_name);
  for (const auto &item : input_args) {
    MS_EXCEPTION_IF_NULL(item);
  }

  auto x_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[0]->BuildShape())[kShape];
  if (x_shape.size() != 4) {
    MS_LOG(EXCEPTION) << "For '" << primitive->name()
                      << "', input x shape must be 4d(NCHW), but got: " << x_shape.size();
  }

  auto group_size_ptr = primitive->GetAttr("group_size");
  MS_EXCEPTION_IF_NULL(group_size_ptr);
  auto group_size = GetValue<int64_t>(group_size_ptr);

  // The value of group_size must be less than 128
  if (group_size <= 0 || group_size >= 128) {
    MS_LOG(EXCEPTION) << "For '" << primitive->name()
                      << "', 'group_size' should be in the range (0, 128), but got: " << group_size;
  }

  auto output_dim_ptr = primitive->GetAttr("output_dim");
  MS_EXCEPTION_IF_NULL(output_dim_ptr);
  auto output_dim = GetValue<int64_t>(output_dim_ptr);

  // the first dimension of the input data should be equal group_size * group_size * output_dim
  if (x_shape[1] / (group_size * group_size) != output_dim) {
    MS_LOG(EXCEPTION) << "For '" << primitive->name() << "', the second dimension(" << x_shape[1]
                      << ") of the input x is illegal, it is not equal to group_size(" << group_size
                      << ") * group_size(" << group_size << ") * output_dim(" << output_dim << ").";
  }

  auto rois_shape = CheckAndConvertUtils::ConvertShapePtrToShapeMap(input_args[1]->BuildShape())[kShape];
  if (rois_shape.size() < 3) {
    MS_LOG(EXCEPTION) << "For '" << primitive->name()
                      << "', the dimension of 'rois' should be equal 3, but got: " << rois_shape.size();
  }

  std::vector<int64_t> ret_shape({rois_shape[0] * rois_shape[2], output_dim, group_size, group_size});

  return std::make_shared<abstract::Shape>(ret_shape);
}

TypePtr PSROIPoolingInferType(const PrimitivePtr &prim, const std::vector<AbstractBasePtr> &input_args) {
  for (const auto &item : input_args) {
    MS_EXCEPTION_IF_NULL(item);
  }
  return input_args[0]->BuildType();
}
}  // namespace

MIND_API_OPERATOR_IMPL(PSROIPooling, BaseOperator);
AbstractBasePtr PSROIPoolingInfer(const abstract::AnalysisEnginePtr &, const PrimitivePtr &primitive,
                                  const std::vector<AbstractBasePtr> &input_args) {
  MS_EXCEPTION_IF_NULL(primitive);
  auto infertype = PSROIPoolingInferType(primitive, input_args);
  auto infershape = PSROIPoolingInferShape(primitive, input_args);
  return abstract::MakeAbstract(infershape, infertype);
}
REGISTER_PRIMITIVE_EVAL_IMPL(PSROIPooling, prim::kPrimPSROIPooling, PSROIPoolingInfer, nullptr, true);
}  // namespace ops
}  // namespace mindspore
