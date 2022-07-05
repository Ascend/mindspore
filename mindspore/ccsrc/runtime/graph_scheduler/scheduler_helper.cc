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

#include "runtime/graph_scheduler/scheduler_helper.h"
#include "runtime/graph_scheduler/actor/actor_dump.h"
#include "backend/common/session/anf_runtime_algorithm.h"
#include "include/common/utils/anfalgo.h"
#include "utils/anf_utils.h"
#include "utils/log_adapter.h"
#include "include/common/utils/convert_utils.h"

namespace mindspore {
namespace runtime {
size_t SchedulerHelper::fusion_actor_index_ = 0;

std::vector<AbstractActorPtr> SchedulerHelper::CollectActors(const ActorSet *actor_set) {
  MS_EXCEPTION_IF_NULL(actor_set);
  std::vector<AbstractActorPtr> actors;

  if (actor_set->data_prepare_actor_ != nullptr) {
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(actor_set->data_prepare_actor_));
  }
  for (auto &data_source_actor : actor_set->data_source_actors_) {
    MS_EXCEPTION_IF_NULL(data_source_actor);
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(data_source_actor));
  }
  for (auto &custom_actor : actor_set->custom_actors_) {
    MS_EXCEPTION_IF_NULL(custom_actor);
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(custom_actor));
  }
  for (auto &kernel_actor : actor_set->kernel_actors_) {
    MS_EXCEPTION_IF_NULL(kernel_actor);
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(kernel_actor));
  }
  for (auto &super_kernel_actor : actor_set->super_kernel_actors_) {
    MS_EXCEPTION_IF_NULL(super_kernel_actor);
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(super_kernel_actor));
  }
  for (auto &copy_actor : actor_set->copy_actors_) {
    MS_EXCEPTION_IF_NULL(copy_actor);
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(copy_actor));
  }
  for (auto &fusion_actor : actor_set->fusion_actors_) {
    MS_EXCEPTION_IF_NULL(fusion_actor);
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(fusion_actor));
  }
  if (actor_set->loop_count_actor_ != nullptr) {
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(actor_set->loop_count_actor_));
  }
  if (actor_set->output_actor_ != nullptr) {
    (void)actors.emplace_back(static_cast<AbstractActorPtr>(actor_set->output_actor_));
  }
  if (actor_set->control_actors_ != nullptr) {
    const auto &control_actor_set = actor_set->control_actors_;
    for (auto &switch_actor : control_actor_set->switch_actors_) {
      MS_EXCEPTION_IF_NULL(switch_actor);
      (void)actors.emplace_back(static_cast<AbstractActorPtr>(switch_actor));
    }
    for (auto &gather_actor : control_actor_set->gather_actors_) {
      MS_EXCEPTION_IF_NULL(gather_actor);
      (void)actors.emplace_back(static_cast<AbstractActorPtr>(gather_actor));
    }
    for (auto &entrance_actor : control_actor_set->entrance_actors_) {
      MS_EXCEPTION_IF_NULL(entrance_actor);
      (void)actors.emplace_back(static_cast<AbstractActorPtr>(entrance_actor));
    }
    for (auto &exit_actor : control_actor_set->exit_actors_) {
      MS_EXCEPTION_IF_NULL(exit_actor);
      (void)actors.emplace_back(static_cast<AbstractActorPtr>(exit_actor));
    }
    for (auto &stack_actor : control_actor_set->stack_actors_) {
      MS_EXCEPTION_IF_NULL(stack_actor);
      (void)actors.emplace_back(static_cast<AbstractActorPtr>(stack_actor));
    }
  }

  return actors;
}

void SchedulerHelper::AddDeviceTensorStore(const AnfNode *anf_node, const DeviceTensorPtr &device_tensor) {
  MS_EXCEPTION_IF_NULL(anf_node);
  MS_EXCEPTION_IF_NULL(device_tensor);
  MS_LOG(DEBUG) << "Add device tensor store:" << device_tensor << " for node:" << anf_node->DebugString();
  DeviceTensorStore::GetInstance().Insert(const_cast<AnfNode *>(anf_node), device_tensor);
  UpdateRefCount(device_tensor.get(), true);
}

void SchedulerHelper::AddDataArrow(AbstractActor *const from_actor, AbstractActor *const to_actor,
                                   size_t from_output_index, size_t to_input_index, const AnfNodePtr &from_kernel) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);

  if (IsControlFlowActor(to_actor->type()) && (from_actor->type() == KernelTransformType::kKernelActor) &&
      (to_actor->type() != KernelTransformType::kExitActor)) {
    MS_LOG(WARNING) << "Kernel actor:" << from_actor->GetAID() << " link data arrow to actor:" << to_actor->GetAID()
                    << " is not an exit actor.";
  }

  auto data_arrow = std::make_shared<DataArrow>(from_output_index, to_actor->GetAID(), to_input_index);
  (void)from_actor->output_data_arrows_.emplace_back(data_arrow);
  (void)from_actor->output_data_nodes_.emplace_back(from_kernel);
  to_actor->input_datas_num_++;
  (void)to_actor->input_data_arrow_aids_.emplace_back(std::make_pair(from_actor->GetAID(), data_arrow.get()));

  if (from_kernel == nullptr) {
    return;
  }
  // Update the reference count of from_kernel.
  auto device_tensor = AnfAlgo::GetMutableOutputAddr(from_kernel, from_output_index, false);
  // The device address of super kernel actor can't be changed, so set the max reference count.
  if (IsControlFlowActor(to_actor->type()) || (from_actor->type_ == KernelTransformType::kSuperKernelActor) ||
      (to_actor->type_ == KernelTransformType::kSuperKernelActor)) {
    UpdateRefCount(device_tensor.get(), true);
  } else {
    UpdateRefCount(device_tensor.get(), false);
  }

  if (IsControlFlowActor(to_actor->type())) {
    device_tensor->SetNodeIndex(from_kernel, from_output_index);
  }
}

void SchedulerHelper::AddResultArrow(AbstractActor *const from_actor, OutputActor *const to_actor,
                                     const AnfNodePtr &from_kernel, size_t from_output_index, size_t output_position) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);
  MS_EXCEPTION_IF_NULL(from_kernel);

  auto result_arrow = std::make_shared<DataArrow>(from_output_index, to_actor->GetAID(), output_position);
  (void)from_actor->output_data_arrows_.insert(from_actor->output_data_arrows_.begin(), result_arrow);
  (void)from_actor->output_data_nodes_.insert(from_actor->output_data_nodes_.begin(), from_kernel);
  to_actor->input_datas_num_++;
  (void)to_actor->input_data_arrow_aids_.emplace_back(std::make_pair(from_actor->GetAID(), result_arrow.get()));

  auto device_tensor = AnfAlgo::GetMutableOutputAddr(from_kernel, from_output_index, false);
  MS_EXCEPTION_IF_NULL(device_tensor);
  // The output actor need use the relevant information of node to create output tensor.
  device_tensor->SetNodeIndex(from_kernel, from_output_index);

  // The device tensor of graph out need be taken over by host tensor, so set the max reference count.
  UpdateRefCount(device_tensor.get(), true);
}

void SchedulerHelper::AddControlArrow(AbstractActor *const from_actor, AbstractActor *const to_actor) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);

  // Check the control arrow whether exists.
  auto iter = std::find_if(from_actor->output_control_arrows_.begin(), from_actor->output_control_arrows_.end(),
                           [&to_actor](const auto &output_control_arrow) {
                             return output_control_arrow->to_op_id_.Name() == to_actor->GetAID().Name();
                           });
  if (iter != from_actor->output_control_arrows_.end()) {
    // The stack actor can only link the single control arrow.
    if (to_actor->type_ == KernelTransformType::kStackActor) {
      MS_LOG(EXCEPTION) << "The control arrow between " << from_actor->GetAID().Name() << " and "
                        << to_actor->GetAID().Name() << " is repeat.";
    }
    return;
  }

  auto control_arrow = std::make_shared<ControlArrow>(to_actor->GetAID());
  (void)from_actor->output_control_arrows_.emplace_back(control_arrow);
  to_actor->input_controls_num_++;
  (void)to_actor->input_control_arrow_aids_.emplace_back(std::make_pair(from_actor->GetAID(), control_arrow.get()));
}

void SchedulerHelper::AddPartialArrow(ControlActor *const from_actor, ControlActor *const to_actor, size_t from_index,
                                      size_t to_index) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);
  auto op_arrow = std::make_shared<DataArrow>(from_index, to_actor->GetAID(), to_index);
  (void)from_actor->output_partial_arrows_.emplace_back(op_arrow);
  to_actor->input_partials_num_++;
  (void)to_actor->input_partial_arrow_aids_.emplace_back(from_actor->GetAID());
}

void SchedulerHelper::AddBranchIDArrow(ControlActor *const from_actor, ControlActor *const to_actor) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);
  (void)from_actor->output_branch_id_arrows_.emplace_back(to_actor->GetAID());
  (void)to_actor->input_branch_id_arrow_aids_.emplace_back(from_actor->GetAID());
  to_actor->input_branch_ids_num_++;
}

void SchedulerHelper::AddLoopBodyControlArrow(AbstractActor *from_actor, EntranceActor *to_actor) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);
  MS_LOG(DEBUG) << "Link loop body control arrow from:" << from_actor->GetAID() << " to actor:" << to_actor->GetAID();
  auto control_arrow = std::make_shared<ControlArrow>(to_actor->GetAID());
  (void)from_actor->output_control_arrows_.emplace_back(control_arrow);
  to_actor->loop_body_input_controls_nums_++;
  (void)to_actor->loop_body_input_control_arrow_aids_.emplace_back(from_actor->GetAID());
}

void SchedulerHelper::AddDataWithBranchIDArrow(GatherActor *const gather_actor, EntranceActor *const entrance_actor,
                                               const FuncGraphPtr &func_graph) {
  MS_EXCEPTION_IF_NULL(gather_actor);
  MS_EXCEPTION_IF_NULL(entrance_actor);
  (void)gather_actor->output_data_with_branch_id_arrows_[func_graph.get()].emplace_back(entrance_actor->GetAID());
}

void SchedulerHelper::AddDataArrowForExitActor(ExitActor *const exit_actor, AbstractActor *const to_actor,
                                               size_t from_index, size_t to_index, int branch_id) {
  MS_EXCEPTION_IF_NULL(exit_actor);
  MS_EXCEPTION_IF_NULL(to_actor);

  MS_LOG(DEBUG) << "Link data arrow from actor:" << exit_actor->GetAID() << " from index:" << from_index
                << " to actor:" << to_actor->GetAID() << " to index:" << to_index;
  auto data_arrow = std::make_shared<DataArrow>(from_index, to_actor->GetAID(), to_index);
  (void)exit_actor->output_branch_data_arrows_[branch_id].emplace_back(data_arrow);
  (void)to_actor->input_data_arrow_aids_.emplace_back(std::make_pair(exit_actor->GetAID(), data_arrow.get()));
}

void SchedulerHelper::AddPartialArrowForExitActor(ExitActor *const exit_actor, ControlActor *const to_actor,
                                                  size_t from_index, size_t to_index, int branch_id) {
  MS_EXCEPTION_IF_NULL(exit_actor);
  MS_EXCEPTION_IF_NULL(to_actor);
  MS_LOG(DEBUG) << "Link partial arrow from actor:" << exit_actor->GetAID() << " from index:" << from_index
                << " to actor:" << to_actor->GetAID() << " to index:" << to_index;
  auto partial_arrow = std::make_shared<DataArrow>(from_index, to_actor->GetAID(), to_index);
  (void)exit_actor->output_branch_partial_arrows_[branch_id].emplace_back(partial_arrow);
  (void)to_actor->input_partial_arrow_aids_.emplace_back(exit_actor->GetAID());
}

void SchedulerHelper::AddControlArrowForExitActor(ExitActor *from_actor, AbstractActor *to_actor, int branch_id) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);

  MS_LOG(DEBUG) << "Link control arrow from:" << from_actor->GetAID() << " to:" << to_actor->GetAID();
  (void)from_actor->output_branch_control_arrows_[branch_id].emplace_back(to_actor->GetAID());
  to_actor->input_controls_num_++;
  (void)to_actor->input_control_arrow_aids_.emplace_back(std::make_pair(from_actor->GetAID(), nullptr));
}

void SchedulerHelper::AddFormalParameterDeviceTensor(ControlActor *const from_actor, size_t from_index,
                                                     const AnfNodePtr &input_node, const KernelGraphPtr &graph) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(input_node);
  MS_EXCEPTION_IF_NULL(graph);

  // Collect backend parameters with dynamic shapes.
  auto base_shape = input_node->Shape();
  if (input_node->isa<Parameter>() && base_shape != nullptr && base_shape->isa<abstract::Shape>()) {
    if (AnfUtils::IsShapeDynamic(base_shape->cast<abstract::ShapePtr>())) {
      if (from_index >= from_actor->backend_parameters_.size()) {
        MS_LOG(EXCEPTION) << "Invalid from index:" << from_index << " for actor:" << from_actor->GetAID()
                          << " vector size:" << from_actor->backend_parameters_.size();
      }
      MS_LOG(INFO) << "Add dynamic shape backend parameter:" << input_node->DebugString() << " index:" << from_index
                   << " for actor:" << from_actor->GetAID();
      from_actor->backend_parameters_[from_index].emplace_back(input_node);
    }
  }

  if (!common::AnfAlgo::HasAbstractRef(input_node)) {
    return;
  }

  auto device_tensor = AnfAlgo::GetMutableOutputAddr(input_node, 0, false);
  MS_EXCEPTION_IF_NULL(device_tensor);
  (void)from_actor->ref_formal_parameter_device_tensors_[from_index].insert(device_tensor);
  if (graph->IsRefOutputMapValue({input_node, 0})) {
    (void)from_actor->ref_node_formal_parameter_device_tensors_[from_index].insert(device_tensor);
  }

  UpdateRefCount(device_tensor.get(), true);
  device_tensor->SetNodeIndex(input_node, 0);
}

void SchedulerHelper::ConvertDataArrowToControlArrow(AbstractActor *const from_actor, AbstractActor *const to_actor,
                                                     const DataArrowPtr &data_arrow, size_t data_arrow_index) {
  MS_EXCEPTION_IF_NULL(from_actor);
  MS_EXCEPTION_IF_NULL(to_actor);
  MS_EXCEPTION_IF_NULL(data_arrow);
  MS_EXCEPTION_IF_CHECK_FAIL((data_arrow_index < from_actor->output_data_nodes_.size()), "Index out of range.");
  auto &need_converted_node = from_actor->output_data_nodes_[data_arrow_index];
  MS_EXCEPTION_IF_NULL(need_converted_node);

  // Erase the output data arrow in from actor.
  (void)from_actor->output_data_arrows_.erase(from_actor->output_data_arrows_.begin() + data_arrow_index);
  (void)from_actor->output_data_nodes_.erase(from_actor->output_data_nodes_.begin() + data_arrow_index);

  // Erase the input data arrow aid in to actor.
  bool to_actor_erase = false;
  for (auto iter = to_actor->input_data_arrow_aids_.begin(); iter != to_actor->input_data_arrow_aids_.end(); ++iter) {
    if ((*iter).first == from_actor->GetAID()) {
      (void)to_actor->input_data_arrow_aids_.erase(iter);
      to_actor_erase = true;
      to_actor->input_datas_num_--;
      break;
    }
  }
  if (to_actor_erase == false) {
    MS_LOG(EXCEPTION) << "Erase no input data arrow, from actor:" << from_actor->GetAID().Name()
                      << ", to actor:" << to_actor->GetAID().Name() << ", data arrow index:" << data_arrow_index;
  }

  // Recalculate the ref count of converted node.
  auto device_tensor = AnfAlgo::GetMutableOutputAddr(need_converted_node, data_arrow->from_output_index_, false);
  MS_EXCEPTION_IF_NULL(device_tensor);
  size_t old_ref_count = device_tensor->ref_count();
  // Ref count Initial value is 1.
  size_t new_ref_count = 1;
  for (auto &output_data_arrow : from_actor->output_data_arrows_) {
    MS_EXCEPTION_IF_NULL(output_data_arrow);
    if (output_data_arrow->from_output_index_ != data_arrow->from_output_index_) {
      continue;
    }
    if ((output_data_arrow->to_op_id_.Name().find(kExitActorNameSuffix) != std::string::npos) ||
        (output_data_arrow->to_op_id_.Name().find(kOutputActorNameSuffix) != std::string::npos)) {
      new_ref_count = SIZE_MAX;
      break;
    }
    ++new_ref_count;
  }
  device_tensor->set_original_ref_count(new_ref_count);
  device_tensor->ResetRefCount();
  MS_LOG(INFO) << "Erase the invalid data arrow, from actor:" << from_actor->GetAID().Name()
               << ", from index:" << data_arrow->from_output_index_ << ", to actor:" << to_actor->GetAID().Name()
               << ", to index:" << data_arrow->to_input_index_ << ", old ref count:" << old_ref_count
               << ", new ref count:" << new_ref_count;

  // Add the control arrow.
  SchedulerHelper::AddControlArrow(from_actor, to_actor);
}

void SchedulerHelper::FuseDataArrowsToBatchDataArrow(AbstractActor *const actor) {
  MS_EXCEPTION_IF_NULL(actor);
  // Count the number of the same destination actor.
  mindspore::HashMap<std::string, size_t> to_actor_count;
  for (const auto &data_arrow : actor->output_data_arrows()) {
    MS_EXCEPTION_IF_NULL(data_arrow);
    ++(to_actor_count[data_arrow->to_op_id_.Name()]);
  }

  // Sign and add the batch data arrow.
  for (auto &data_arrow : actor->output_data_arrows()) {
    MS_EXCEPTION_IF_NULL(data_arrow);
    auto &to_op_name = data_arrow->to_op_id_.Name();
    // The output data cannot be reused whose destination is stack actor, and cannot to be fused.
    if ((to_actor_count[to_op_name] > 1) && (to_op_name.find(kStackActorNameSuffix) == std::string::npos)) {
      SET_FLAG(data_arrow->flag_, kOutputDataFlagBatch);
      (void)actor->batch_output_data_arrows_[to_op_name].emplace_back(data_arrow);
    }
  }
}

void SchedulerHelper::AddDependency(AbstractActor *const actor, const AbstractActor *dependent_actor) {
  MS_EXCEPTION_IF_NULL(actor);
  MS_EXCEPTION_IF_NULL(dependent_actor);
  // For example, ActorA->dependent_actor->actor, the expanded dependent actors of actor are dependent_actor and ActorA.
  (void)actor->dependent_actors_.insert(dependent_actor->GetAID().Name());
  (void)actor->dependent_actors_.insert(dependent_actor->dependent_actors_.begin(),
                                        dependent_actor->dependent_actors_.end());
}

bool SchedulerHelper::CheckDependency(const std::vector<AbstractActorPtr> &output_actors) {
  if (output_actors.size() <= 1) {
    return true;
  }

  for (size_t i = 1; i < output_actors.size(); ++i) {
    auto &pre_actor = output_actors[i - 1];
    auto &actor = output_actors[i];
    MS_EXCEPTION_IF_NULL(pre_actor);
    MS_EXCEPTION_IF_NULL(actor);
    // The outputs have no dependencies.
    if ((actor->dependent_actors_.count(pre_actor->GetAID().Name()) == 0) &&
        (pre_actor->dependent_actors_.count(actor->GetAID().Name()) == 0)) {
      return false;
    }
  }

  return true;
}

FusionActorPtr SchedulerHelper::BuildFusionActor(const std::vector<AbstractActorPtr> &actors) {
  if (actors.size() <= 1) {
    MS_LOG(EXCEPTION) << "The fusion actor size must be greater than 1.";
  }

  std::string fusion_actor_name = std::to_string(++fusion_actor_index_) + kFusionActorNameSuffix;
  auto fusion_actor = std::make_shared<FusionActor>(fusion_actor_name);
  for (auto &actor : actors) {
    MS_EXCEPTION_IF_NULL(actor);
    actor->parent_fusion_actor_ = fusion_actor.get();
    fusion_actor->sub_actors_[actor->GetAID().Name()] = actor;
  }
  return fusion_actor;
}

void SchedulerHelper::AddArrowForFusionActor(FusionActor *fusion_actor) {
  MS_EXCEPTION_IF_NULL(fusion_actor);
  for (auto &actor_iter : fusion_actor->sub_actors_) {
    auto &actor = actor_iter.second;
    MS_EXCEPTION_IF_NULL(actor);

    mindspore::HashMap<std::string, std::unordered_set<std::string>> modified_batch_data_infos;
    // Link data arrow of fusion actor by the input data arrow of real actor.
    for (auto &input_data_arrow_aid : actor->input_data_arrow_aids_) {
      auto input_data_arrow = input_data_arrow_aid.second;
      MS_EXCEPTION_IF_NULL(input_data_arrow);
      // Mark the kOutputDataFlagBetweenFusion flag when the input data arrow is the Internal actor in fusion actor.
      if (fusion_actor->sub_actors_.count(input_data_arrow_aid.first.Name()) > 0) {
        SET_FLAG(input_data_arrow->flag_, kOutputDataFlagBetweenFusion);
        continue;
      }

      SET_FLAG(input_data_arrow->flag_, kOutputDataFlagToFusion);
      // The ActorB is in fusion actor and the input ActorA is on the outside of fusion actor, then change
      // 'ActorA->ActorB' to 'ActorA->FusionActor'.
      auto from_actor = FetchActor(input_data_arrow_aid.first.Name());
      MS_EXCEPTION_IF_NULL(from_actor);
      // Record the input index of real actor and fusion actor.
      (void)fusion_actor->real_input_data_.emplace_back(std::make_pair(actor.get(), input_data_arrow->to_input_index_));
      from_actor->data_arrow_to_fusion_actor_indexs_[input_data_arrow] = fusion_actor->input_data_arrow_aids_.size();
      input_data_arrow->to_input_index_ = fusion_actor->input_data_arrow_aids_.size();

      input_data_arrow->to_op_id_ = fusion_actor->GetAID();
      ++fusion_actor->input_datas_num_;
      (void)fusion_actor->input_data_arrow_aids_.emplace_back(
        std::make_pair(input_data_arrow_aid.first, input_data_arrow));
    }

    // Link control arrow of fusion actor by the input control arrow of real actor.
    for (auto &input_control_arrow_aid : actor->input_control_arrow_aids_) {
      auto input_control_arrow = input_control_arrow_aid.second;
      MS_EXCEPTION_IF_NULL(input_control_arrow);
      // Mark the kOutputDataFlagBetweenFusion flag when the input control arrow is the Internal actor in fusion
      // actor.
      if (fusion_actor->sub_actors_.count(input_control_arrow_aid.first.Name()) > 0) {
        SET_FLAG(input_control_arrow->flag_, kOutputDataFlagBetweenFusion);
        continue;
      }

      SET_FLAG(input_control_arrow->flag_, kOutputDataFlagToFusion);
      // The ActorB is in fusion actor and the input ActorA is on the outside of fusion actor, then change
      // 'ActorA->ActorB' to 'ActorA->FusionActor'.
      (void)fusion_actor->real_input_controls_[input_control_arrow_aid.first.Name()].emplace_back(actor.get());
      input_control_arrow->to_op_id_ = fusion_actor->GetAID();
      ++fusion_actor->input_controls_num_;
      (void)fusion_actor->input_control_arrow_aids_.emplace_back(
        std::make_pair(input_control_arrow_aid.first, input_control_arrow));
    }
  }
}

namespace {
bool CheckKernelActorValid(const std::vector<KernelActorPtr> &kernel_actors) {
  for (const auto &kernel_actor : kernel_actors) {
    MS_EXCEPTION_IF_NULL(kernel_actor);
    std::string exit_actor_name = "";

    for (const auto arrow : kernel_actor->output_data_arrows()) {
      MS_EXCEPTION_IF_NULL(arrow);
      if (arrow->to_op_id_.Name().find(kExitActorNameSuffix) == std::string::npos) {
        continue;
      }
      if (exit_actor_name == "") {
        exit_actor_name = arrow->to_op_id_.Name();
        continue;
      }
      if (exit_actor_name != arrow->to_op_id_.Name()) {
        MS_LOG(EXCEPTION) << "Kernel actor:" << kernel_actor->GetAID() << " link to two exit actor:" << exit_actor_name
                          << " and:" << arrow->to_op_id_.Name();
        return false;
      }
    }
  }
  return true;
}

bool CheckExitActorInvalid(const ExitActorPtr &exit_actor) {
  MS_EXCEPTION_IF_NULL(exit_actor);

  return exit_actor->output_data_arrows().empty() && exit_actor->output_partial_arrows().empty() &&
         exit_actor->output_control_arrows().empty() && exit_actor->output_branch_control_arrows().empty() &&
         exit_actor->output_branch_data_arrows().empty() && exit_actor->output_branch_partial_arrows().empty();
}

// Convert the control actors vector by the control actor set.
std::vector<ControlActorPtr> CollectControlActors(const ControlActorSetPtr &control_actor_set) {
  MS_EXCEPTION_IF_NULL(control_actor_set);
  std::vector<ControlActorPtr> actors;

  for (auto &switch_actor : control_actor_set->switch_actors_) {
    MS_EXCEPTION_IF_NULL(switch_actor);
    (void)actors.emplace_back(static_cast<ControlActorPtr>(switch_actor));
  }
  for (auto &gather_actor : control_actor_set->gather_actors_) {
    MS_EXCEPTION_IF_NULL(gather_actor);
    (void)actors.emplace_back(static_cast<ControlActorPtr>(gather_actor));
  }
  for (auto &entrance_actor : control_actor_set->entrance_actors_) {
    MS_EXCEPTION_IF_NULL(entrance_actor);
    (void)actors.emplace_back(static_cast<ControlActorPtr>(entrance_actor));
  }
  for (auto &exit_actor : control_actor_set->exit_actors_) {
    MS_EXCEPTION_IF_NULL(exit_actor);
    (void)actors.emplace_back(static_cast<ControlActorPtr>(exit_actor));
  }
  for (auto &stack_actor : control_actor_set->stack_actors_) {
    MS_EXCEPTION_IF_NULL(stack_actor);
    (void)actors.emplace_back(static_cast<ControlActorPtr>(stack_actor));
  }

  return actors;
}

bool CheckControlActorValid(const ActorSet *actor_set) {
  MS_EXCEPTION_IF_NULL(actor_set);
  if (actor_set->control_actors_ == nullptr) {
    return true;
  }

  if (!CheckKernelActorValid(actor_set->kernel_actors_)) {
    return false;
  }

  auto control_actors = CollectControlActors(actor_set->control_actors_);
  for (const auto &control_actor : control_actors) {
    MS_EXCEPTION_IF_NULL(control_actor);
    for (auto &ref_node_formal_parameter_device_tensor : control_actor->ref_node_formal_parameter_device_tensors()) {
      auto &device_tensors = ref_node_formal_parameter_device_tensor.second;
      for (auto iter = device_tensors.begin(); iter != device_tensors.end(); ++iter) {
        if (((*device_tensors.begin())->format() != (*iter)->format()) ||
            ((*device_tensors.begin())->GetDeviceType() != (*iter)->GetDeviceType()) ||
            ((*device_tensors.begin())->type_id() != (*iter)->type_id())) {
          MS_LOG(EXCEPTION) << control_actor->GetAID().Name()
                            << " does not support the ref node formal parameters that are different format.";
        }
      }
    }

    for (auto &ref_formal_parameter_device_tensor : control_actor->ref_formal_parameter_device_tensors()) {
      auto &device_tensors = ref_formal_parameter_device_tensor.second;
      for (auto iter = device_tensors.begin(); iter != device_tensors.end(); ++iter) {
        if ((*device_tensors.begin())->type_id() != (*iter)->type_id()) {
          MS_LOG(EXCEPTION) << control_actor->GetAID().Name()
                            << " does not support the ref formal parameters that are different type.";
        }
      }
    }
  }

  for (const auto &exit_actor : actor_set->control_actors_->exit_actors_) {
    MS_EXCEPTION_IF_NULL(exit_actor);
    if (CheckExitActorInvalid(exit_actor)) {
      MS_LOG(EXCEPTION) << "Invalid exit actor:" << exit_actor->GetAID();
    }
  }

  // Since some control arrows of stack actors need to be counted according to aid, the input control arrow cannot
  // be repeated, otherwise the count will be inaccurate. But there are exceptions, if the control arrow does not
  // need to be counted according to aid, it can be repeated.
  for (const auto &stack_actor : actor_set->control_actors_->stack_actors_) {
    MS_EXCEPTION_IF_NULL(stack_actor);
    const auto &input_control_aids = stack_actor->input_control_arrow_aids();
    std::set<AID> aid_set;
    (void)std::for_each(input_control_aids.begin(), input_control_aids.end(),
                        [&aid_set](const auto &input_control_aid) { (void)aid_set.emplace(input_control_aid.first); });
    if (aid_set.size() != input_control_aids.size()) {
      MS_LOG(WARNING) << "Stack actor:" << stack_actor->GetAID() << " has duplicate control arrows.";
    }
  }
  return true;
}
}  // namespace

void SchedulerHelper::CheckActorValid(const ActorSet *actor_set) {
  MS_EXCEPTION_IF_NULL(actor_set);
  auto actors = SchedulerHelper::CollectActors(actor_set);
  for (auto &actor : actors) {
    MS_EXCEPTION_IF_NULL(actor);
    if (actor->type_ >= KernelTransformType::kSwitchActor) {
      continue;
    }

    if ((actor->input_datas_num_ != actor->input_data_arrow_aids_.size()) ||
        (actor->input_controls_num_ != actor->input_control_arrow_aids_.size())) {
      MS_LOG(EXCEPTION) << "The input num of " << actor->GetAID().Name()
                        << " is wrong, expect data num: " << actor->input_datas_num_
                        << ", actual data num: " << actor->input_data_arrow_aids_.size()
                        << ", expect control num: " << actor->input_controls_num_
                        << ", actual control num: " << actor->input_control_arrow_aids_.size();
    }

    if ((actor->type_ != KernelTransformType::kOutputActor) && (actor->type_ != KernelTransformType::kCustomActor) &&
        (actor->output_data_arrows_.size() == 0) && (actor->output_control_arrows_.size() == 0)) {
      MS_LOG(EXCEPTION) << actor->GetAID().Name() << " has no user.";
    }
    if ((actor->type_ != KernelTransformType::kDataPrepareActor) &&
        (actor->type_ != KernelTransformType::kCustomActor) && (actor->input_datas_num_ == 0) &&
        (actor->input_controls_num_ == 0)) {
      MS_LOG(EXCEPTION) << actor->GetAID().Name() << " has no source.";
    }

    // Check the input of kernel actors and copy actors.
    if ((actor->type_ == KernelTransformType::kKernelActor) || (actor->type_ == KernelTransformType::kCopyActor)) {
      size_t expect_toal_input_num = 1;
      if (actor->type_ == KernelTransformType::kKernelActor) {
        auto kernel_actor = dynamic_cast<KernelActor *>(actor.get());
        MS_EXCEPTION_IF_NULL(kernel_actor);
        expect_toal_input_num = common::AnfAlgo::GetInputTensorNum(kernel_actor->kernel());
      }
      auto input_data_num = actor->input_datas_num_;
      auto device_tensor_store_num = actor->device_tensor_store_keys_.size();
      if (input_data_num + device_tensor_store_num != expect_toal_input_num) {
        MS_LOG(EXCEPTION) << "The input building of " << actor->GetAID().Name()
                          << " is wrong, input data num: " << input_data_num
                          << ", device tensor store num: " << device_tensor_store_num
                          << ", total input num: " << expect_toal_input_num;
      }
    }
  }

  // Check the output actor.
  auto output_actor = actor_set->output_actor_;
  MS_EXCEPTION_IF_NULL(output_actor);
  if (output_actor->input_datas_num_ + output_actor->device_tensor_store_keys_.size() != output_actor->outputs_num()) {
    MS_LOG(EXCEPTION) << "The outputs num of output actor is wrong, the total outputs num: "
                      << output_actor->outputs_num()
                      << ", the input data arrows num: " << output_actor->input_datas_num_
                      << ", the device tensor store num: " << output_actor->device_tensor_store_keys_.size();
  }

  CheckControlActorValid(actor_set);
}

void SchedulerHelper::DumpActorSet(const ActorSet *actor_set, std::ofstream &ofs) {
  MS_EXCEPTION_IF_NULL(actor_set);
  DumpDataPrepareActor(actor_set->data_prepare_actor_, ofs);
  DumpDSActors(actor_set->data_source_actors_, ofs);
  DumpKernelActors(actor_set->kernel_actors_, ofs);
  DumpSuperKernelActors(actor_set->super_kernel_actors_, ofs);
  // The on input kernel actors are taken over by control actor in the control flow scene.
  if (actor_set->control_actors_ == nullptr) {
    DumpNoInputKernelActors(actor_set->no_input_kernel_actors_, ofs);
  }
  DumpCopyActors(actor_set->copy_actors_, ofs);
  DumpLoopCountActor(actor_set->loop_count_actor_, ofs);
  DumpOutputActor(actor_set->output_actor_, ofs);
  DumpFusionActors(actor_set->fusion_actors_, ofs);
  DumpControlActors(actor_set->control_actors_, ofs);
  DumpCustomActors(actor_set->custom_actors_, ofs);
}
}  // namespace runtime
}  // namespace mindspore
