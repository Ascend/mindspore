import pytest
import numpy as np
import mindspore.context as context
import mindspore.nn as nn
from mindspore import Tensor, COOTensor
from mindspore.ops import functional as F
import mindspore.common.dtype as mstype


class SparseConcatNet(nn.Cell):
    def construct(self, input_list, concat_dim, num):
        sp_input = []
        for i in range(0, num):
            sp_input.append(COOTensor(input_list[i*3], input_list[i*3+1], input_list[i*3+2]))
        return F.sparse_concat(sp_input, concat_dim)


def judge_result_correct(result, expect):
    indices_result = result.indices.asnumpy()
    assert indices_result.dtype == expect[0].asnumpy().dtype
    assert indices_result.shape == expect[0].asnumpy().shape
    assert np.allclose(indices_result, expect[0].asnumpy())
    values_result = result.values.asnumpy()
    assert values_result.dtype == expect[1].asnumpy().dtype
    assert values_result.shape == expect[1].asnumpy().shape
    assert np.allclose(values_result, expect[1].asnumpy())
    assert np.allclose(result.shape, expect[2])


def sparse_concat_int(i_type, v_type):
    indices0 = Tensor([[0, 1], [1, 2]], dtype=i_type)
    values0 = Tensor([1, 2], dtype=v_type)
    shape0 = (3, 4)
    input0 = COOTensor(indices0, values0, shape0)
    indices1 = Tensor([[0, 0], [1, 1]], dtype=i_type)
    values1 = Tensor([3, 4], dtype=v_type)
    shape1 = (3, 4)
    input1 = COOTensor(indices1, values1, shape1)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices0, values0, shape0, indices1, values1, shape1), concat_dim, 2)
    expect_forward_output_indices = Tensor([[0, 1], [0, 4], [1, 2], [1, 5]], dtype=i_type)
    expect_forward_output_values = Tensor([1, 3, 2, 4], dtype=v_type)
    expect_forward_output_shape = (3, 8)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)
    #single op run
    forward_output = F.sparse_concat((input0, input1), concat_dim)
    judge_result_correct(forward_output, expect_forward_output)


    indices0 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values0 = Tensor([1, 2], dtype=v_type)
    shape0 = (3, 4)
    indices1 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values1 = Tensor([3, 4], dtype=v_type)
    shape1 = (3, 4)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices0, values0, shape0, indices1, values1, shape1), concat_dim, 2)
    expect_forward_output_indices = Tensor([[0, 1], [0, 2], [0, 5], [0, 6]], dtype=i_type)
    expect_forward_output_values = Tensor([1, 2, 3, 4], dtype=v_type)
    expect_forward_output_shape = (3, 8)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)


    indices0 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values0 = Tensor([1, 2], dtype=v_type)
    shape0 = (3, 4)
    indices1 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values1 = Tensor([3, 4], dtype=v_type)
    shape1 = (3, 4)
    indices2 = Tensor([[1, 1], [1, 2], [1, 3]], dtype=i_type)
    values2 = Tensor([5, 6, 7], dtype=v_type)
    shape2 = (3, 4)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices0, values0, shape0, \
                                 indices1, values1, shape1, indices2, values2, shape2), concat_dim, 3)
    expect_forward_output_indices = Tensor([[0, 1], [0, 2], [0, 5], [0, 6], [1, 9], [1, 10], [1, 11]], dtype=i_type)
    expect_forward_output_values = Tensor([1, 2, 3, 4, 5, 6, 7], dtype=v_type)
    expect_forward_output_shape = (3, 12)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)


    indices0 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values0 = Tensor([1, 2], dtype=v_type)
    shape0 = (3, 4)
    indices1 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values1 = Tensor([3, 4], dtype=v_type)
    shape1 = (3, 4)
    indices2 = Tensor([[1, 1], [1, 2], [1, 3]], dtype=i_type)
    values2 = Tensor([5, 6, 7], dtype=v_type)
    shape2 = (3, 4)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices2, values2, shape2, \
                                 indices1, values1, shape1, indices0, values0, shape0), concat_dim, 3)
    expect_forward_output_indices = Tensor([[0, 5], [0, 6], [0, 9], [0, 10], [1, 1], [1, 2], [1, 3]], dtype=i_type)
    expect_forward_output_values = Tensor([3, 4, 1, 2, 5, 6, 7], dtype=v_type)
    expect_forward_output_shape = (3, 12)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)


def sparse_concat_float(i_type, v_type):
    indices0 = Tensor([[0, 1], [1, 2]], dtype=i_type)
    values0 = Tensor([1.0, 2.0], dtype=v_type)
    shape0 = (3, 4)
    input0 = COOTensor(indices0, values0, shape0)
    indices1 = Tensor([[0, 0], [1, 1]], dtype=i_type)
    values1 = Tensor([3.0, 4.0], dtype=v_type)
    shape1 = (3, 4)
    input1 = COOTensor(indices1, values1, shape1)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices0, values0, shape0, indices1, values1, shape1), concat_dim, 2)
    expect_forward_output_indices = Tensor([[0, 1], [0, 4], [1, 2], [1, 5]], dtype=i_type)
    expect_forward_output_values = Tensor([1.0, 3.0, 2.0, 4.0], dtype=v_type)
    expect_forward_output_shape = (3, 8)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)
    #single op run
    forward_output = F.sparse_concat((input0, input1), concat_dim)
    judge_result_correct(forward_output, expect_forward_output)


    indices0 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values0 = Tensor([1.0, 2.0], dtype=v_type)
    shape0 = (3, 4)
    indices1 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values1 = Tensor([3.0, 4.0], dtype=v_type)
    shape1 = (3, 4)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices0, values0, shape0, indices1, values1, shape1), concat_dim, 2)
    expect_forward_output_indices = Tensor([[0, 1], [0, 2], [0, 5], [0, 6]], dtype=i_type)
    expect_forward_output_values = Tensor([1.0, 2.0, 3.0, 4.0], dtype=v_type)
    expect_forward_output_shape = (3, 8)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)


    indices0 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values0 = Tensor([1.0, 2.0], dtype=v_type)
    shape0 = (3, 4)
    indices1 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values1 = Tensor([3.0, 4.0], dtype=v_type)
    shape1 = (3, 4)
    indices2 = Tensor([[1, 1], [1, 2], [1, 3]], dtype=i_type)
    values2 = Tensor([5.0, 6.0, 7.0], dtype=v_type)
    shape2 = (3, 4)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices0, values0, shape0, \
                                 indices1, values1, shape1, indices2, values2, shape2), concat_dim, 3)
    expect_forward_output_indices = Tensor([[0, 1], [0, 2], [0, 5], [0, 6], [1, 9], [1, 10], [1, 11]], dtype=i_type)
    expect_forward_output_values = Tensor([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=v_type)
    expect_forward_output_shape = (3, 12)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)


    indices0 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values0 = Tensor([1.0, 2.0], dtype=v_type)
    shape0 = (3, 4)
    indices1 = Tensor([[0, 1], [0, 2]], dtype=i_type)
    values1 = Tensor([3.0, 4.0], dtype=v_type)
    shape1 = (3, 5)
    indices2 = Tensor([[1, 1], [1, 2], [1, 3]], dtype=i_type)
    values2 = Tensor([5.0, 6.0, 7.0], dtype=v_type)
    shape2 = (3, 6)
    forward_net = SparseConcatNet()
    concat_dim = 1
    #net run
    forward_output = forward_net((indices2, values2, shape2, \
                                        indices1, values1, shape1, indices0, values0, shape0), concat_dim, 3)
    expect_forward_output_indices = Tensor([[0, 7], [0, 8], [0, 12], [0, 13], [1, 1], [1, 2], [1, 3]], dtype=i_type)
    expect_forward_output_values = Tensor([3.0, 4.0, 1.0, 2.0, 5.0, 6.0, 7.0], dtype=v_type)
    expect_forward_output_shape = (3, 15)
    expect_forward_output = (expect_forward_output_indices, expect_forward_output_values, expect_forward_output_shape)
    judge_result_correct(forward_output, expect_forward_output)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
def test_sparse_concat_int():
    """
    Feature: Test sparse_concat Ops. And the input COOTensor dtype is int
    Description: Test spare_concat, test different inputs.
    Expectation: Success.
    """
    context.set_context(mode=context.PYNATIVE_MODE, device_target="CPU")
    values_types = (mstype.int8, mstype.int16, mstype.int32, mstype.int64, \
                     mstype.uint8, mstype.uint16, mstype.uint32, mstype.uint64)
    indices_types = (mstype.int64, mstype.int16, mstype.int32)
    for v_type in values_types:
        for i_type in indices_types:
            sparse_concat_int(i_type, v_type)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
def test_sparse_concat_float():
    """
    Feature: Test sparse_concat Ops. And the input COOTensor dtype is float
    Description: Test spare_concat, test different inputs.
    Expectation: Success.
    """
    context.set_context(mode=context.PYNATIVE_MODE, device_target="CPU")
    sparse_concat_float(mstype.int32, mstype.float32)
    sparse_concat_float(mstype.int32, mstype.float16)
