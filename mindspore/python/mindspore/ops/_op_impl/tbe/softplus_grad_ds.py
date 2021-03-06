# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""SoftplusGrad op"""
from mindspore.ops.op_info_register import op_info_register, TBERegOp, DataType

softplus_grad_ds_op_info = TBERegOp("SoftplusGrad") \
    .fusion_type("OPAQUE") \
    .async_flag(False) \
    .binfile_name("softplus_grad.so") \
    .compute_cost(10) \
    .kernel_name("softplus_grad") \
    .partial_flag(True) \
    .op_pattern("broadcast") \
    .dynamic_shape(True) \
    .input(0, "gradients", False, "required", "all") \
    .input(1, "features", False, "required", "all") \
    .output(0, "backprops", False, "required", "all") \
    .dtype_format(DataType.F16_None, DataType.F16_None, DataType.F16_None) \
    .dtype_format(DataType.F32_None, DataType.F32_None, DataType.F32_None) \
    .get_op_info()

@op_info_register(softplus_grad_ds_op_info)
def _softplus_grad_ds_tbe():
    """SoftplusGrad TBE register"""
    return
