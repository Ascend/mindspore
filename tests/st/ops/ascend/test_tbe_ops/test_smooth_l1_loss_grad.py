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

import numpy as np
import pytest

import mindspore.context as context
import mindspore.nn as nn
from mindspore import Tensor
from mindspore.ops.composite import GradOperation

context.set_context(mode=context.GRAPH_MODE, device_target="Ascend")


class Grad(nn.Cell):
    def __init__(self, network):
        super(Grad, self).__init__()
        self.grad = GradOperation(get_all=True, sens_param=True)
        self.network = network

    def construct(self, x1, x2, sens):
        gout = self.grad(self.network)(x1, x2, sens)
        return gout


def smoothl1loss_grad(beta):
    np.random.seed(42)
    prediction = np.random.randn(20).astype(np.float32)
    target = np.random.randn(20).astype(np.float32)
    sens = np.random.randn(20).astype(np.float32)

    net = nn.SmoothL1Loss(beta)
    grad = Grad(net)
    return grad(Tensor(prediction), Tensor(target), Tensor(sens))


@pytest.mark.level0
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
def test_smoothl1loss_grad_no_reduce():
    """
    Feature: SmoothL1LossGrad cpu kernel.
    Description: test the rightness of SmoothL1LossGrad cpu kernel.
    Expectation: the output is same as expect.
    """

    epsilon = 1e-6

    beta = 1.0
    dx = smoothl1loss_grad(beta)
    dx1_expect = np.array([-0.71552587, 0.01499678, -0.06709455, -0.30110368, -0.45868093,
                           0.24838912, -0.46063876, 0.41411355, 0.04507046, -1.4708229,
                           0.04481723, 0.38508227, -0.17292616, -0.52333146, -1.0309995,
                           0.61330026, 0.83921754, -0.3092124, 0.1391843, -0.9755451], dtype=np.float32)

    dx2_expect = -dx1_expect

    diff1 = np.absolute(dx[0].asnumpy() - dx1_expect)
    diff2 = np.absolute(dx[1].asnumpy() - dx2_expect)
    assert(diff1 < epsilon).all()
    assert(diff2 < epsilon).all()

    beta = 1 / 9
    dx = smoothl1loss_grad(beta)
    dx1_expect = np.array([-0.73846656, 0.13497104, -0.11564828, -0.30110368, -1.478522,
                           0.7198442, -0.46063876, 1.0571222, 0.3436183, -1.7630402,
                           0.32408398, 0.38508227, -0.676922, -0.6116763, -1.0309995,
                           0.93128014, 0.83921754, -0.3092124, 0.33126342, -0.9755451], dtype=np.float32)

    dx2_expect = -dx1_expect

    diff1 = np.absolute(dx[0].asnumpy() - np.array(dx1_expect))
    diff2 = np.absolute(dx[1].asnumpy() - np.array(dx2_expect))
    assert(diff1 < epsilon).all()
    assert(diff2 < epsilon).all()


def smoothl1loss_grad_2(beta, reduction):
    prediction = np.array([1, 2, 3, 4, 5, 6], dtype=np.float32)
    target = np.array([100, 2, 7, 32, 34, 1], dtype=np.float32)

    net = nn.SmoothL1Loss(beta, reduction)
    grad = Grad(net)
    return grad(Tensor(prediction), Tensor(target), 9.)


@pytest.mark.level0
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
@pytest.mark.parametrize("reduction", ['mean', 'sum'])
def test_smoothl1loss_grad_sum(reduction):
    """
    Feature: SmoothL1LossGrad cpu kernel, reduction = sum.
    Description: test the rightness of SmoothL1LossGrad cpu kernel.
    Expectation: the output is same as expect.
    """

    beta = 1.0
    dx = smoothl1loss_grad_2(beta, reduction)

    sum_dx1_expect = np.array([-9, 0, -9, -9, -9, 9], dtype=np.float32)
    sum_dx2_expect = -sum_dx1_expect

    mean_dx1_expect = np.array(
        [-1.5, 0, -1.5, -1.5, -1.5, 1.5], dtype=np.float32)
    mean_dx2_expect = -mean_dx1_expect

    print("dx[0].asnumpy()", dx[0].asnumpy())
    print("dx[1].asnumpy()", dx[1].asnumpy())

    if reduction == 'sum':
        np.testing.assert_array_almost_equal(dx[0].asnumpy(), sum_dx1_expect)
        np.testing.assert_array_almost_equal(dx[1].asnumpy(), sum_dx2_expect)
    if reduction == 'mean':
        np.testing.assert_array_almost_equal(dx[0].asnumpy(), mean_dx1_expect)
        np.testing.assert_array_almost_equal(dx[1].asnumpy(), mean_dx2_expect)
