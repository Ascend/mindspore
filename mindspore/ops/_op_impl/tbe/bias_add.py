# Copyright 2020 Huawei Technologies Co., Ltd
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

"""BiasAdd op"""
from mindspore.ops.op_info_register import op_info_register, TBERegOp, DataType

bias_add_grad_op_info = TBERegOp("BiasAdd") \
    .fusion_type("COMMREDUCE") \
    .async_flag(False) \
    .binfile_name("bias_add.so") \
    .compute_cost(10) \
    .kernel_name("bias_add") \
    .partial_flag(True) \
    .attr("data_format", "required", "str", "all") \
    .input(0, "x", False, "required", "all") \
    .input(1, "bias", False, "required", "all") \
    .output(0, "y", False, "required", "all") \
    .op_pattern("dynamicFormat") \
    .dtype_format(DataType.I32_Default, DataType.I32_Default, DataType.I32_Default) \
    .dtype_format(DataType.F16_Default, DataType.F16_Default, DataType.F16_Default) \
    .dtype_format(DataType.F32_Default, DataType.F32_Default, DataType.F32_Default) \
    .get_op_info()


@op_info_register(bias_add_grad_op_info)
def _bias_add_tbe():
    """BiasAdd TBE register"""
    return
