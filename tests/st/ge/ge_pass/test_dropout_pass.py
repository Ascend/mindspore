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
""" test ge frontend pass `DropoutForGE` `DropoutGradForGE` """
import os
import pytest


@pytest.mark.level1
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
def test_ge_dropout_pass():
    """
    Description: run dropout and dropoutgrad in ge backend
    Expectation: success
    """
    sh_path = os.path.split(os.path.realpath(__file__))[0]
    ret = os.system(f"sh {sh_path}/run_ge_dropout_pass.sh")
    os.system(f"grep -E 'ERROR|error' {sh_path}/ge_dropout_pass/log.log -C 3")
    assert ret == 0
