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
#ifndef MINDSPORE_LITE_SRC_RUNTIME_CXX_API_MODEL_POOL_MODEL_POOL_H_
#define MINDSPORE_LITE_SRC_RUNTIME_CXX_API_MODEL_POOL_MODEL_POOL_H_
#include <vector>
#include <unordered_map>
#include <memory>
#include <utility>
#include <string>
#include <queue>
#include <map>
#include <set>
#include "src/runtime/dynamic_mem_allocator.h"
#include "include/api/status.h"
#include "include/api/context.h"
#include "include/api/model_parallel_runner.h"
#include "src/runtime/cxx_api/model_pool/model_worker.h"
#include "src/runtime/cxx_api/model_pool/predict_task_queue.h"
namespace mindspore {
using ModelPoolConfig = std::vector<std::shared_ptr<WorkerConfig>>;

class ModelPool {
 public:
  ModelPool() = default;

  ~ModelPool();

  Status Init(const std::string &model_path, const std::shared_ptr<RunnerConfig> &runner_config = nullptr);

  Status UpdateConfig(const std::string &section, const std::pair<std::string, std::string> &config);

  std::vector<MSTensor> GetInputs();

  std::vector<MSTensor> GetOutputs();

  Status Predict(const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs,
                 const MSKernelCallBack &before = nullptr, const MSKernelCallBack &after = nullptr);

 private:
  ModelPoolConfig CreateModelPoolConfig(const std::shared_ptr<RunnerConfig> &runner_config);
  std::shared_ptr<Context> GetInitContext(const std::shared_ptr<RunnerConfig> &runner_config);

  Status SetWorkersNum(const std::shared_ptr<RunnerConfig> &runner_config, const std::shared_ptr<Context> &context);

  std::shared_ptr<mindspore::Context> GetDefaultContext();
  std::shared_ptr<Context> GetUserDefineContext(const std::shared_ptr<RunnerConfig> &runner_config);
  Status SetDefaultOptimalModelNum(int thread_num);

  Status SetModelBindMode(std::vector<std::vector<int>> *all_worker_bind_list, std::vector<int> *numa_node_id,
                          std::shared_ptr<Context> model_context);
  Status SetNumaBindStrategy(std::vector<std::vector<int>> *all_worker_bind_list, std::vector<int> *numa_node_id,
                             int thread_num);
  Status SetBindStrategy(std::vector<std::vector<int>> *all_model_bind_list, std::vector<int> *numa_node_id,
                         int thread_num);

  std::shared_ptr<ModelWorker> GetMaxWaitWorkerNum(int *max_wait_worker_node_id, int *max_wait_worker_num);

  PredictTask *CreatePredictTask(const std::vector<MSTensor> &inputs, std::vector<MSTensor> *outputs,
                                 const MSKernelCallBack &before, const MSKernelCallBack &after, size_t *task_id);

  void UpdateFreeTaskId(size_t id);

  Status DistinguishPhysicalAndLogicalByNuma(const std::vector<int> &physical_core_list,
                                             const std::vector<int> &logical_core_list);

  Status InitNumaParameter(const std::shared_ptr<RunnerConfig> &runner_config);

  Status InitModelPoolBindList(const std::shared_ptr<Context> &init_context,
                               std::vector<std::vector<int>> *bind_core_list, std::vector<int> *bind_numa_list);

  Status SetWorkersNumaId(std::vector<int> *numa_node_id);

  ModelPoolConfig CreateGpuModelPoolConfig(const std::shared_ptr<RunnerConfig> &runner_config,
                                           const std::shared_ptr<Context> &init_context);

  ModelPoolConfig CreateCpuModelPoolConfig(const std::shared_ptr<RunnerConfig> &runner_config,
                                           const std::shared_ptr<Context> &init_context,
                                           const std::vector<std::vector<int>> &all_worker_bind_list,
                                           const std::vector<int> &numa_node_id);

  Status CreateWorkers(char *graph_buf, size_t size, const ModelPoolConfig &model_pool_config);

  Status CheckAffinityCoreList(const std::shared_ptr<RunnerConfig> &runner_config);

 private:
  // different workers get tasks from different task queues.
  // currently task queues are distinguished according to different numa node numbers.
  // if you do not distinguish between numa nodes, the default task queue number is 0.
  // task queue id <=> worker : sort workers by performance.
  std::unordered_map<int, std::vector<std::shared_ptr<ModelWorker>>> all_model_workers_;

  // save all worker thread
  std::vector<std::thread> worker_thread_vec_;
  std::mutex predict_task_mutex_;
  std::vector<MSTensor> model_pool_inputs_;
  std::vector<MSTensor> model_pool_outputs_;
  size_t workers_num_ = 1;

  // create predict task
  std::shared_ptr<PredictTaskQueue> predict_task_queue_ = nullptr;
  PredictTask *tasks_ = nullptr;
  std::mutex task_id_mutex_;
  std::queue<size_t> free_tasks_id_;

  // bind core
  bool is_user_core_list_ = false;

  // use numa
  bool numa_available_ = false;
  size_t numa_node_num_ = 1;
  std::vector<std::vector<int>> numa_physical_cores_;
  std::vector<std::vector<int>> numa_logical_cores_;
  bool use_numa_bind_mode_ = false;
  size_t used_numa_node_num_ = 0;  // Initialize in SetNumaBindStrategy
  std::unordered_map<int, std::shared_ptr<Allocator>> numa_allocator_;
};
}  // namespace mindspore
#endif  // MINDSPORE_LITE_SRC_RUNTIME_CXX_API_MODEL_POOL_MODEL_POOL_H_
