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

"""Defines parameter operators with functional form."""

from mindspore.ops.primitive import constexpr
from mindspore.ops import operations as P
from mindspore.ops import functional as F
from mindspore.ops.composite.multitype_ops import _constexpr_utils as const_utils
from ...common import dtype as mstype
from ...common.seed import _get_graph_seed
from .._primitive_cache import _get_cache_prim


@constexpr(reuse_result=False)
def _get_seed(op_seed, kernel_name):
    "Get the graph-level seed."
    return _get_graph_seed(op_seed, kernel_name)


def standard_laplace(shape, seed=0, seed2=0):
    r"""
    Generates random numbers according to the Laplace random number distribution (mean=0, lambda=1).
    It is defined as:

    .. math::
        \text{f}(x) = \frac{1}{2}\exp(-|x|),

    Args:
        shape (tuple): The shape of random tensor to be generated. Only constant value is allowed.
        seed (int): Random seed. Default: 0.
        seed2 (int): Random seed2. Default: 0.

    Returns:
        Tensor. The shape that the input 'shape' denotes. The dtype is float32.

    Raises:
        TypeError: If neither seed nor seed2 is an int.
        TypeError: If shape is not a tuple.
        ValueError: If shape is not a constant value.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> shape = (4, 4)
        >>> output = F.standard_laplace(shape)
        >>> result = output.shape
        >>> print(result)
        (4, 4)
    """
    standard_laplace_op = _get_cache_prim(P.StandardLaplace)(seed=seed, seed2=seed2)
    output = standard_laplace_op(shape)
    return output


def random_categorical(logits, num_sample, seed=0, dtype=mstype.int64):
    r"""
    Generates random samples from a given categorical distribution tensor.

    Args:
        logits (Tensor): The input tensor. 2-D Tensor with shape :math:`(batch_size, num_classes)`.
        num_sample (int):  Number of sample to be drawn. Only constant values is allowed.
        seed (int):  Random seed. Only constant values is allowed. Default: 0.
        dtype (mindspore.dtype): The type of output. Its value must be one of mindspore.int16,
            mindspore.int32 and mindspore.int64. Default: mindspore.int64.

    Returns:
        Tensor, The output Tensor with shape :math:`(batch_size, num_samples)`.

    Raises:
        TypeError: If `dtype` is not one of the following: mindspore.int16, mindspore.int32, mindspore.int64.
        TypeError: If `logits` is not a Tensor.
        TypeError: If neither `num_sample` nor `seed` is an int.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> import numpy as np
        >>> logits = np.random.random((10, 5)).astype(np.float32)
        >>> net = F.random_categorical(logits, 8)
        >>> output = net(Tensor(logits))
        >>> result = output.shape
        >>> print(result)F
        (10, 8)
    """
    random_categorical_ = P.RandomCategorical(dtype)
    return random_categorical_(logits, num_sample, seed)


def uniform(shape, minval, maxval, seed=None, dtype=mstype.float32):
    """
    Generates random numbers according to the Uniform random number distribution.

    Note:
        The number in tensor minval should be strictly less than maxval at any position after broadcasting.

    Args:
        shape (tuple): The shape of random tensor to be generated.
          The format is :math:`(N,*)` where :math:`*` means, any number of additional dimensions
          and the length of :math:`(N,*)` should be less than 8 in broadcast operation.
        minval (Tensor): The distribution parameter `a`.
          It defines the minimum possible generated value, with int32 or float32 data type.
          If dtype is int32, only one number is allowed.
        maxval (Tensor): The distribution parameter `b`.
          It defines the maximum possible generated value, with int32 or float32 data type.
          If dtype is int32, only one number is allowed.
        seed (int): Seed is used as entropy source for the random number engines to generate pseudo-random numbers,
          must be non-negative. Default: None, which will be treated as 0.
        dtype (mindspore.dtype): Type of the Uniform distribution. If it is int32, it generates numbers from discrete
          uniform distribution; if it is float32, it generates numbers from continuous uniform distribution. It only
          supports these two data types. Default: mindspore.float32.

    Returns:
        Tensor. The shape should be equal to the broadcasted shape between the input `shape` and shapes
        of `minval` and `maxval`.
        The dtype is designated as the input `dtype`.

    Raises:
        TypeError: If `shape` is not tuple.
        TypeError: If 'minval' or 'maxval' is neither int32 nor float32
            and dtype of 'minval' is not the same as 'maxval'.
        TypeError: If `seed` is not an int.
        TypeError: If 'dtype' is neither int32 nor float32.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
        >>> from mindspore import Tensor, ops
        >>> import mindspore
        >>> import numpy as np
        >>> # For discrete uniform distribution, only one number is allowed for both minval and maxval:
        >>> shape = (4, 2)
        >>> minval = Tensor(1, mindspore.int32)
        >>> maxval = Tensor(2, mindspore.int32)
        >>> output = F.uniform(shape, minval, maxval, seed=5, dtype=mindspore.int32)
        >>>
        >>> # For continuous uniform distribution, minval and maxval can be multi-dimentional:
        >>> shape = (3, 1, 2)
        >>> minval = Tensor(np.array([[3, 4], [5, 6]]), mindspore.float32)
        >>> maxval = Tensor([8.0, 10.0], mindspore.float32)
        >>> output = F.uniform(shape, minval, maxval, seed=5)
        >>> result = output.shape
        >>> print(result)
        (3, 2, 2)
    """
    minval_dtype = F.dtype(minval)
    maxval_dtype = F.dtype(maxval)
    const_utils.check_type_valid(dtype, [mstype.int32, mstype.float32], 'uniform')
    const_utils.check_tensors_dtype_same(minval_dtype, dtype, "uniform")
    const_utils.check_tensors_dtype_same(maxval_dtype, dtype, "uniform")
    seed1, seed2 = _get_seed(seed, "uniform")
    if const_utils.is_same_type(dtype, mstype.int32):
        random_uniform = P.UniformInt(seed1, seed2)
        value = random_uniform(shape, minval, maxval)
    else:
        uniform_real = P.UniformReal(seed1, seed2)
        random_uniform = uniform_real(shape)
        value = random_uniform * (maxval - minval) + minval
    return value


def standard_normal(shape, seed=0, seed2=0):
    r"""
    Generates random numbers according to the standard Normal (or Gaussian) random number distribution.

    Returns the tensor with the given shape, the random numbers in it drawn from normal distributions
    whose mean is 0 and standard deviation is 1.

    .. math::
        f(x)=\frac{1}{\sqrt{2 \pi}} e^{\left(-\frac{x^{2}}{2}\right)}

    Args:
        shape (tuple): The shape of random tensor to be generated. Only constant value is allowed.
        seed (int): Random seed, must be non-negative. Default: 0.
        seed2 (int): Random seed2, must be non-negative. A second seed to avoid seed collision. Default: 0.

    Returns:
        Tensor. The shape is the same as the input `shape`. The dtype is float32.

    Raises:
        TypeError: If neither `seed` nor `seed2` is an int.
        TypeError: If `shape` is not a tuple.
        ValueError: If `shape` is not a constant value.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> shape = (4, 4)
        >>> output = F.standard_normal(shape)
        >>> result = output.shape
        >>> print(result)
        (4, 4)
    """
    standard_normal_op = _get_cache_prim(P.StandardNormal)(seed=seed, seed2=seed2)
    return standard_normal_op(shape)


__all__ = [
    'standard_laplace',
    'random_categorical',
    'uniform',
    'standard_normal',
]
__all__.sort()
