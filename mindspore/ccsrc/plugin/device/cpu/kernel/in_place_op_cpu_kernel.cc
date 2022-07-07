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

#include "plugin/device/cpu/kernel/in_place_op_cpu_kernel.h"
#include <map>
#include <memory>
#include <string>
#include <algorithm>
#include <unordered_map>
#include "mindspore/core/ops/inplace_add.h"
#include "mindspore/core/ops/inplace_sub.h"
#include "mindspore/core/ops/inplace_update.h"

namespace mindspore {
namespace kernel {
namespace {
struct Add {
  template <typename T>
  inline T operator()(const T &lhs, const T &rhs) const {
    return lhs + rhs;
  }
};
struct Sub {
  template <typename T>
  inline T operator()(const T &lhs, const T &rhs) const {
    return lhs - rhs;
  }
};

struct Update {
  template <typename T>
  inline T operator()(const T &lhs, const T &rhs) const {
    return rhs;
  }
};
template <typename Op>
struct NoCheck {
  template <typename T>
  static inline void compute(T *x, const size_t x_idx, const T *v, const size_t v_idx) {
    x[x_idx] = Op()(x[x_idx], v[v_idx]);
  }
};
template <typename Op>
struct Atomic {
  template <typename T>
  static inline void compute(T *x, const size_t x_idx, const T *v, const size_t v_idx) {
    auto &atomic_ = reinterpret_cast<std::atomic<T> *>(x)[x_idx];
    T expect = atomic_.load();
    T result = T(0);
    do {
      result = Op()(expect, v[v_idx]);
    } while (!atomic_.compare_exchange_weak(expect, result));
  }
};
template <typename T>
class InplaceOpCpuTypeFunc : public CpuKernelFunc {
 public:
  InplaceOpCpuTypeFunc() = default;
  ~InplaceOpCpuTypeFunc() override = default;
  void InitFunc(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
                const std::vector<KernelTensorPtr> &) override {
    MS_EXCEPTION_IF_NULL(base_operator);
    kernel_name_ = base_operator->GetPrim()->name();
    if (kernel_name_ == ops::kNameInplaceAdd) {
      auto kernel_ptr = std::make_shared<ops::InplaceAdd>(base_operator->GetPrim());
      indices_ = kernel_ptr->get_indices();
    } else if (kernel_name_ == ops::kNameInplaceSub) {
      auto kernel_ptr = std::make_shared<ops::InplaceSub>(base_operator->GetPrim());
      indices_ = kernel_ptr->get_indices();
    } else if (kernel_name_ == ops::kNameInplaceUpdate) {
      auto kernel_ptr = std::make_shared<ops::InplaceUpdate>(base_operator->GetPrim());
      indices_ = kernel_ptr->get_indices();
    } else {
      MS_LOG(EXCEPTION) << "InplaceOp cpu does not support " << kernel_name_;
    }

    static std::unordered_map<std::string, TypeComputeFunc> inplaceOpFuncMap = {
      {prim::kPrimInplaceAdd->name(), &InplaceOpCpuTypeFunc<T>::InplaceOp<NoCheck<Add>>},
      {prim::kPrimInplaceSub->name(), &InplaceOpCpuTypeFunc<T>::InplaceOp<NoCheck<Sub>>},
      {prim::kPrimInplaceUpdate->name(), &InplaceOpCpuTypeFunc<T>::InplaceOp<NoCheck<Update>>},
    };
    static std::unordered_map<std::string, TypeComputeFunc> inplaceOpAtomicFuncMap = {
      {prim::kPrimInplaceAdd->name(), &InplaceOpCpuTypeFunc<T>::InplaceOp<Atomic<Add>>},
      {prim::kPrimInplaceSub->name(), &InplaceOpCpuTypeFunc<T>::InplaceOp<Atomic<Sub>>},
    };
    if (inplaceOpFuncMap.find(kernel_name_) == inplaceOpFuncMap.end()) {
      MS_LOG(EXCEPTION) << "For 'InplaceOp', only supports operators in " << Unorderedmap2Str(inplaceOpFuncMap)
                        << ", but got " << kernel_name_ << ".";
    }

    // Check if indices is unique
    // InplaceUpdate does not suits atomic operations.
    // If the order needs to be kept, implement a serial version of InplaceOp.
    std::unordered_set<int64_t> indices_set(indices_.begin(), indices_.end());
    if (kernel_name_ != prim::kPrimInplaceUpdate->name() && (indices_set.size() != indices_.size())) {
      if (inplaceOpFuncMap.find(kernel_name_) == inplaceOpFuncMap.end()) {
        MS_LOG(EXCEPTION) << "For 'InplaceOp', atomic operations only support operators in "
                          << Unorderedmap2Str(inplaceOpFuncMap) << ", but got " << kernel_name_ << ".";
      }
      compute_func_ = inplaceOpAtomicFuncMap.at(kernel_name_);
    } else {
      compute_func_ = inplaceOpFuncMap.at(kernel_name_);
    }
  }

  int Resize(
    const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
    const std::vector<KernelTensorPtr> &outputs,
    const std::map<uint32_t, tensor::TensorPtr> &inputsOnHost = std::map<uint32_t, tensor::TensorPtr>()) override {
    auto v_shape = inputs.at(1)->GetShapeVector();

    // x_shape_.size() == v_shape.size() is checked at front end
    // x_shape_[1:] == v_shape[1:] is checked at front end
    band_size_ = std::accumulate(v_shape.begin() + 1, v_shape.end(), int64_t(1), std::multiplies{});

    // indices_.size() == v_shape[0] is checked at front end
    v_size_ = band_size_ * v_shape[0];

    return KRET_OK;
  }

  template <typename Op>
  void InplaceOp(T *x, const T *v) {
    const int64_t band_size = band_size_;
    const int64_t *indices = indices_.data();
    auto task = [band_size, indices, x, v](size_t start, size_t end) {
      while (start < end) {
        const int64_t v_row = SizeToLong(start) / band_size;
        const int64_t x_row = indices[v_row];

        size_t offset = SizeToLong(start) % band_size;
        size_t up_bound = (LongToSize((v_row + 1) * band_size) > end) ? end % band_size : band_size;

        size_t x_offset = x_row * band_size;
        size_t v_offset = v_row * band_size;
        for (size_t j = offset; j < up_bound; ++j) {
          Op::compute(x, x_offset + j, v, v_offset + j);
        }
        start = v_row * band_size + up_bound;
      }
    };
    ParallelLaunchAutoSearch(task, v_size_, this, &parallel_search_info_);
  }

  bool RunFunc(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &,
               const std::vector<AddressPtr> &outputs) override {
    auto *x = reinterpret_cast<T *>(inputs[0]->addr);
    const auto *v = reinterpret_cast<T *>(inputs[1]->addr);
    auto *output = reinterpret_cast<T *>(outputs[0]->addr);
    if (memcpy_s(output, outputs[0]->size, x, inputs[0]->size) != EOK) {
      MS_LOG(ERROR) << "Function memcpy_s failed in 'InplaceOp'.";
      return false;
    }
    compute_func_(this, output, v);
    return true;
  }

 private:
  std::string kernel_name_;
  int64_t band_size_{1};
  int64_t v_size_{1};
  std::vector<int64_t> indices_;

  using TypeComputeFunc = std::function<void(InplaceOpCpuTypeFunc *, T *x, const T *v)>;
  TypeComputeFunc compute_func_{nullptr};
};

template <typename T>
std::shared_ptr<CpuKernelFunc> InplaceOpCpuFunc() {
  return std::make_shared<InplaceOpCpuTypeFunc<T>>();
}
using InplaceOpCpuFuncCreator = std::function<std::shared_ptr<CpuKernelFunc>()>;
using OpFuncList = std::vector<std::pair<KernelAttr, InplaceOpCpuFuncCreator>>;
static const mindspore::HashMap<std::string, OpFuncList> kernel_attr_list = {
  {ops::kNameInplaceAdd,
   {
     {KernelAttr().AddInputAttr(kNumberTypeInt32).AddInputAttr(kNumberTypeInt32).AddOutputAttr(kNumberTypeInt32),
      InplaceOpCpuFunc<int32_t>},
     {KernelAttr().AddInputAttr(kNumberTypeFloat32).AddInputAttr(kNumberTypeFloat32).AddOutputAttr(kNumberTypeFloat32),
      InplaceOpCpuFunc<float>},
     {KernelAttr().AddInputAttr(kNumberTypeFloat16).AddInputAttr(kNumberTypeFloat16).AddOutputAttr(kNumberTypeFloat16),
      InplaceOpCpuFunc<float16>},
   }},
  {ops::kNameInplaceSub,
   {
     {KernelAttr().AddInputAttr(kNumberTypeInt32).AddInputAttr(kNumberTypeInt32).AddOutputAttr(kNumberTypeInt32),
      InplaceOpCpuFunc<int32_t>},
     {KernelAttr().AddInputAttr(kNumberTypeFloat32).AddInputAttr(kNumberTypeFloat32).AddOutputAttr(kNumberTypeFloat32),
      InplaceOpCpuFunc<float>},
     {KernelAttr().AddInputAttr(kNumberTypeFloat16).AddInputAttr(kNumberTypeFloat16).AddOutputAttr(kNumberTypeFloat16),
      InplaceOpCpuFunc<float16>},
   }},
  {ops::kNameInplaceUpdate,
   {
     {KernelAttr().AddInputAttr(kNumberTypeInt32).AddInputAttr(kNumberTypeInt32).AddOutputAttr(kNumberTypeInt32),
      InplaceOpCpuFunc<int32_t>},
     {KernelAttr().AddInputAttr(kNumberTypeFloat32).AddInputAttr(kNumberTypeFloat32).AddOutputAttr(kNumberTypeFloat32),
      InplaceOpCpuFunc<float>},
     {KernelAttr().AddInputAttr(kNumberTypeFloat16).AddInputAttr(kNumberTypeFloat16).AddOutputAttr(kNumberTypeFloat16),
      InplaceOpCpuFunc<float16>},
   }},
};
}  // namespace

bool InPlaceOpCpuKernelMod::Init(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
                                 const std::vector<KernelTensorPtr> &outputs) {
  kernel_name_ = base_operator->GetPrim()->name();
  if (kernel_name_ != kernel_type_) {
    MS_LOG(EXCEPTION) << "Need to be " << kernel_type_ << " but got kernel name as " << kernel_name_;
  }

  auto kernel_attr = GetKernelAttrFromTensors(inputs, outputs);
  auto [is_match, index] = MatchKernelAttr(kernel_attr, GetOpSupport());
  if (!is_match) {
    MS_LOG(EXCEPTION) << "InplaceOp does not support this kernel data type: " << kernel_attr;
  }

  func_obj_ = kernel_attr_list.at(kernel_name_)[index].second();

  func_obj_->InitFunc(base_operator, inputs, outputs);

  return true;
}

int InPlaceOpCpuKernelMod::Resize(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
                                  const std::vector<KernelTensorPtr> &outputs,
                                  const std::map<uint32_t, tensor::TensorPtr> &) {
  if (auto ret = KernelMod::Resize(base_operator, inputs, outputs); ret != KRET_OK) {
    return ret;
  }
  return func_obj_->Resize(base_operator, inputs, outputs);
}

std::vector<KernelAttr> InPlaceOpCpuKernelMod::GetOpSupport() {
  auto iter = kernel_attr_list.find(kernel_type_);
  if (iter == kernel_attr_list.end()) {
    MS_LOG(EXCEPTION) << "InplaceOp cpu does not support " << kernel_type_;
  }

  std::vector<KernelAttr> support_list;
  (void)std::transform(iter->second.begin(), iter->second.end(), std::back_inserter(support_list),
                       [](const std::pair<KernelAttr, InplaceOpCpuFuncCreator> &pair) { return pair.first; });

  return support_list;
}

MS_KERNEL_FACTORY_REG_WITH_NAME_PARAM(NativeCpuKernelMod, InplaceAdd, InPlaceOpCpuKernelMod);
MS_KERNEL_FACTORY_REG_WITH_NAME_PARAM(NativeCpuKernelMod, InplaceSub, InPlaceOpCpuKernelMod);
MS_KERNEL_FACTORY_REG_WITH_NAME_PARAM(NativeCpuKernelMod, InplaceUpdate, InPlaceOpCpuKernelMod);
}  // namespace kernel
}  // namespace mindspore
