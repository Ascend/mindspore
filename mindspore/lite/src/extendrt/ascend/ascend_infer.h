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
#ifndef MINDSPORE_LITE_SRC_EXTENDRT_ASCEND_INFER_EXECUTOR_H_
#define MINDSPORE_LITE_SRC_EXTENDRT_ASCEND_INFER_EXECUTOR_H_
#include <functional>
#include <map>
#include <string>
#include <vector>
#include <memory>
#include <utility>
#include "include/api/status.h"
#include "include/api/graph.h"
#include "extendrt/graph_executor.h"
#include "runtime/context.h"

namespace mindspore {
class AscendInferExecutor : public GraphExecutor {
 public:
  AscendInferExecutor();
  ~AscendInferExecutor() override;

  Status Execute(const ExecutePlan &plan, const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs) override;

 protected:
  bool CheckDeviceSupport(mindspore::DeviceType device_type) override;
  Status Load(uint32_t device_id);
  Status InitEnv();
  Status FinalizeEnv();
  Status CheckModelInputs(const std::vector<tensor::TensorPtr> &inputs) const;

 private:
  uint32_t graph_id_;
  std::string device_type_;
  uint32_t device_id_;
  rtContext_t context_;
  std::vector<tensor::TensorPtr> inputs_info_;
  std::vector<tensor::TensorPtr> outputs_info_;
  std::vector<tensor::TensorPtr> last_inputs_;
  std::vector<tensor::TensorPtr> last_outputs_;
  std::vector<std::string> input_names_;
  std::vector<std::string> output_names_;
  bool load_flag_;

  std::shared_ptr<MsEnvGuard> env_guard_;
};

class AscendInferSession::MsEnvGuard {
 public:
  explicit MsEnvGuard(uint32_t device_id);
  ~MsEnvGuard();
  Status GetErrno() const { return errno_; }
  static std::shared_ptr<MsEnvGuard> GetEnv(uint32_t device_id);

 private:
  static std::map<uint32_t, std::weak_ptr<MsEnvGuard>> global_ms_env_;
  static std::mutex global_ms_env_mutex_;

  Status errno_;
  uint32_t device_id_;
};

class PythonEnvGuard {
 public:
  PythonEnvGuard();
  ~PythonEnvGuard();

 private:
  bool PythonIsInited() const;
  void InitPython() const;
  void FinalizePython() const;
  bool origin_init_status_;
};
}  // namespace mindspore
#endif  // MINDSPORE_LITE_SRC_EXTENDRT_CXX_API_GRAPH_ASCEND_ASCEND_GRAPH_IMPL_H_
