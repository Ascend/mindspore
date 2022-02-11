# Copyright 2022 Huawei Technologies Co., Ltd
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

"""EnvironSet op"""
from mindspore.ops.op_info_register import op_info_register, AiCPURegOp, DataType

environ_set_op_info = AiCPURegOp("EnvironSet") \
    .fusion_type("OPAQUE") \
    .attr("value_type", "int") \
    .input(0, "env", "required") \
    .input(1, "key", "required") \
    .input(2, "value", "required") \
    .output(0, "env", "required") \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.I64_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.I32_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.I16_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.U32_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.U8_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.U64_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.F16_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.F32_Default, DataType.I64_Default) \
    .dtype_format(DataType.I64_Default, DataType.I64_Default, DataType.BOOL_Default, DataType.I64_Default) \
    .get_op_info()

@op_info_register(environ_set_op_info)
def _environ_set_aicpu():
    """EnvironSet AiCPU register"""
    return