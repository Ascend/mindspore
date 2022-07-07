/**
 * Copyright 2020-2022 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_LITE_SRC_RUNTIME_DELEGATE_COREML_PASS_COREML_TRANS_EXTEND_PASS_H_
#define MINDSPORE_LITE_SRC_RUNTIME_DELEGATE_COREML_PASS_COREML_TRANS_EXTEND_PASS_H_
#include <vector>
#include "src/runtime/delegate/coreml/op/coreml_op.h"
#include "src/runtime/delegate/coreml/pass/coreml_base_pass.h"
namespace mindspore::lite {
enum class InsertState { InsertNone, PreInsert, PostInsert, BothInsert };
class CoreMLTransExtendPass : public CoreMLBasePass {
 public:
  CoreMLTransExtendPass() { name_ = "CoreMLTransExtendPass"; }

  int Run(CoreMLGraph *subgraph) override;

 private:
  InsertState GetInsertState(CoreMLOp *op);
  bool IsNeedInsert(size_t transpose_tensor_num, size_t graph_input_num, size_t graph_output_num,
                    size_t in_out_tensor_num, bool need_pre_insert, bool need_post_insert);
  int InsertPreNodes(CoreMLOp *op, std::vector<CoreMLOp *> *trans_ops);
  int InsertPostNodes(CoreMLOp *op, std::vector<CoreMLOp *> *trans_ops);
  int InsertTransNode(CoreMLOp *op, CoreMLOp *post_op, const mindspore::MSTensor &trans_in_tensor,
                      std::vector<CoreMLOp *> *trans_ops);

 private:
  int total = 0;
  std::vector<CoreMLOp *> *all_ops_ = nullptr;
  std::vector<mindspore::MSTensor *> *all_tensors_ = nullptr;
};
}  // namespace mindspore::lite
#endif  // MINDSPORE_LITE_SRC_RUNTIME_DELEGATE_COREML_PASS_COREML_TRANS_EXTEND_PASS_H_
