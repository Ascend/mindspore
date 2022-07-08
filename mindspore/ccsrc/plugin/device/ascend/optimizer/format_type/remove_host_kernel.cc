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

#include "plugin/device/ascend/optimizer/format_type/remove_host_kernel.h"
#include <memory>
#include "backend/common/session/anf_runtime_algorithm.h"
#include "include/common/utils/anfalgo.h"
#include "include/common/utils/utils.h"
#include "mindspore/core/ops/core_ops.h"
#include "runtime/device/kernel_info.h"
#include "backend/common/optimizer/helper.h"

namespace mindspore {
namespace opt {
const BaseRef RemoveHostKernel::DefinePattern() const {
  VarPtr X = std::make_shared<Var>();
  return VectorRef({prim::kPrimTensorShape, X});
}

/**
 * host node need remove if it is not dynamic shape
 * */
const AnfNodePtr RemoveHostKernel::Process(const FuncGraphPtr &graph, const AnfNodePtr &node, const EquivPtr &) const {
  MS_EXCEPTION_IF_NULL(graph);
  if (node == nullptr || !node->isa<CNode>()) {
    return nullptr;
  }
  if (!common::AnfAlgo::IsDynamicShape(node)) {
    auto cnode = node->cast<CNodePtr>();
    auto output_shape = common::AnfAlgo::GetPrevNodeOutputInferShape(cnode, 0);
    auto output_type = TypeId::kNumberTypeInt64;
    auto tensor = std::make_shared<tensor::Tensor>(output_type, output_shape);
    MS_EXCEPTION_IF_NULL(tensor);
    auto data = static_cast<int64_t *>(tensor->data_c());
    MS_EXCEPTION_IF_NULL(data);
    for (size_t i = 0; i < output_shape.size(); i++) {
      *(data + i) = output_shape[i];
    }
    auto abs = std::make_shared<abstract::AbstractTensor>(kInt64, output_shape);
    auto kernel_graph = graph->cast<KernelGraphPtr>();
    MS_EXCEPTION_IF_NULL(kernel_graph);
    auto new_value_node = kernel_graph->NewValueNode(abs, tensor);
    kernel_graph->AddValueNodeToGraph(new_value_node);
    common::AnfAlgo::SetOutputInferTypeAndShape({output_type}, {output_shape}, new_value_node.get());
    return new_value_node;
  }
  return nullptr;
}
}  // namespace opt
}  // namespace mindspore
