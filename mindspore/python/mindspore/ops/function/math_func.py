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

"""Defines math operators with functional form."""

import math
from itertools import zip_longest
from collections import deque
import numpy as np
import mindspore.ops as ops
from mindspore.common import dtype as mstype
from mindspore.ops.primitive import constexpr
from mindspore.ops import operations as P
from mindspore.ops import composite as C
from mindspore.ops.operations._inner_ops import Cummin
from mindspore.ops.operations.math_ops import STFT
from mindspore.ops.operations.math_ops import ReduceStd
from mindspore.nn import layer
from mindspore._checkparam import check_is_number
from ..operations.math_ops import (
    Bernoulli,
    BesselJ0,
    BesselJ1,
    BesselK0,
    BesselK0e,
    BesselY0,
    BesselY1,
    BesselK1,
    BesselK1e,
    MatrixSolve,
    Renorm,
    Hypot,
    Lcm,
    Gcd,
    SparseSegmentMean,
    InplaceUpdateV2,
)
from ...common import dtype as mstype
from ...common.tensor import Tensor
from ..._c_expression import Tensor as Tensor_
from ..._checkparam import Validator as validator
from .._primitive_cache import _get_cache_prim


@constexpr
def _make_tensor(val, dtype):
    """Returns the tensor with value `val` and dtype `dtype`."""
    return Tensor(val, dtype)


@constexpr
def get_x_shape(x_shape):
    s = 1
    for i in x_shape:
        s = s * i
    return (s,)


#####################################
# Public Operation Functions.
#####################################
absolute = P.Abs()
tensor_ceil = P.Ceil()
tensor_add = P.Add()
neg_tensor = P.Neg()
tensor_sub = P.Sub()
tensor_mul = P.Mul()
tensor_div = P.RealDiv()
tensor_floordiv = P.FloorDiv()
floordiv = tensor_floordiv
tensor_xdivy = P.Xdivy()
tensor_pow = P.Pow()
pows = tensor_pow
tensor_mod = P.FloorMod()
floormod = tensor_mod
tensor_exp = P.Exp()
tensor_expm1 = P.Expm1()
tensor_lt = P.Less()
tensor_le = P.LessEqual()
tensor_gt = P.Greater()
tensor_ge = P.GreaterEqual()
not_equal = P.NotEqual()

#####################################
# Private Operation Functions.
#####################################
addn_ = P.AddN()
log_ = P.Log()
floor_ = P.Floor()
logical_not_ = P.LogicalNot()
logical_or_ = P.LogicalOr()
logical_and_ = P.LogicalAnd()
sin_ = P.Sin()
cos_ = P.Cos()
tan_ = P.Tan()
asin_ = P.Asin()
acos_ = P.ACos()
atan_ = P.Atan()
sinh_ = P.Sinh()
cosh_ = P.Cosh()
tanh_ = P.Tanh()
asinh_ = P.Asinh()
acosh_ = P.Acosh()
atanh_ = P.Atanh()
atan2_ = P.Atan2()
bitwise_and_ = P.BitwiseAnd()
bitwise_or_ = P.BitwiseOr()
bitwise_xor_ = P.BitwiseXor()
inv_ = P.math_ops.Inv()
invert_ = P.Invert()
erf_ = P.Erf()
erfc_ = P.Erfc()
bessel_j1_ = BesselJ1()
bessel_j0_ = BesselJ0()
bessel_i0_ = P.BesselI0()
bessel_i0e_ = P.BesselI0e()
bessel_k0_ = BesselK0()
bessel_k0e_ = BesselK0e()
bessel_y0_ = BesselY0()
bessel_y1_ = BesselY1()
bessel_i1_ = P.BesselI1()
bessel_i1e_ = P.BesselI1e()
bessel_k1_ = BesselK1()
bessel_k1e_ = BesselK1e()
equal_ = P.Equal()
isfinite_ = P.IsFinite()
isnan_ = P.IsNan()
same_type_shape_ = P.SameTypeShape()
maximum_ = P.Maximum()
minimum_ = P.Minimum()
lerp_ = P.Lerp()
tensor_round_ = P.Round()
linspace_ = P.LinSpace()
matrix_determinant_ = P.MatrixDeterminant()
log_matrix_determinant_ = P.LogMatrixDeterminant()
exp2_ = P.Pow()
truncate_div_ = P.TruncateDiv()
truncate_mod_ = P.TruncateMod()
sparse_segment_mean_ = SparseSegmentMean()
xlogy_ = P.Xlogy()


#####################################
# Element-wise Operation Functions.
#####################################

def addn(x):
    """
    Computes addition of all input tensors element-wise.

    All input tensors must have the same shape.

    Args:
        x (Union(tuple[Tensor], list[Tensor])): A tuple or list composed of Tensor, the data type is
            `bool_ <https://www.mindspore.cn/docs/api/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `number <https://www.mindspore.cn/docs/api/en/master/api_python/mindspore.html#mindspore.dtype>`_ .

    Returns:
        Tensor, has the same shape and dtype as each Tensor of `x`.

    Raises:
        TypeError: If `x` is neither tuple nor list.
        ValueError: If there are Tensors with different shapes in `x`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.float32)
        >>> y = Tensor(np.array([4, 5, 6]), mindspore.float32)
        >>> output = ops.addn([x, y, x, y])
        >>> print(output)
        [10. 14. 18.]
    """
    return addn_(x)


def abs(x):
    r"""
    Returns absolute value of a tensor element-wise.

    .. math::

        out_i = |x_i|

    Args:
        x (Tensor): The input tensor. The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1.0, 1.0, 0.0]), mindspore.float32)
        >>> output = ops.abs(x)
        >>> print(output)
        [1. 1. 0.]
    """
    return absolute(x)


def add(x, y):
    r"""
    Adds two input tensors element-wise.

    .. math::

        out_{i} = x_{i} + y_{i}

    .. note::
        - Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        - The inputs must be two tensors or one tensor and one scalar.
        - When the inputs are two tensors,
          dtypes of them cannot be bool at the same time, and the shapes of them can be broadcast.
        - When the inputs are one tensor and one scalar, the scalar could only be a constant.

    Args:
        x (Union[Tensor, number.Number, bool]): The first input is a number.Number or
            a bool or a tensor whose data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        y (Union[Tensor, number.Number, bool]): The second input, when the first input is a Tensor,
            the second input should be a number.Number or bool value, or a Tensor whose data type is number or bool\_.
            When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one of the input `x` , `y` after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, number.Number, bool.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> # case 1: x and y are both Tensor.
        >>> x = Tensor(np.array([1, 2, 3]).astype(np.float32))
        >>> y = Tensor(np.array([4, 5, 6]).astype(np.float32))
        >>> output = ops.add(x, y)
        >>> print(output)
        [5. 7. 9.]
        >>> # case 2: x is a scalar and y is a Tensor
        >>> x = Tensor(1, mindspore.int32)
        >>> y = Tensor(np.array([4, 5, 6]).astype(np.float32))
        >>> output = ops.add(x, y)
        >>> print(output)
        [5. 6. 7.]
        >>> # the data type of x is int32, the data type of y is float32,
        >>> # and the output is the data format of higher precision float32.
        >>> print(output.dtype)
        Float32
    """
    return tensor_add(x, y)


def exp2(x):
    """
    Computes the base two exponential function of input.

    Calculates ``2^x``.

    Args:
        x (Tensor): Input tensor.

    Returns:
        Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

     Examples:
        >>> x = Tensor(np.array([2, 3, 4]), mindspore.float32)
        >>> output = ops.exp2(x)
        >>> print(output)
        [ 4.  8. 16.]
    """

    tensor_2 = Tensor(np.array(2.0).astype(np.float32))
    if x.dtype == mstype.float16:
        tensor_2 = Tensor(np.array(2.0).astype(np.float16))
    return exp2_(tensor_2, x)


def argmin(x, axis=-1):
    """
    Returns the indices of the minimum value of a tensor across the axis.

    If the shape of input tensor is :math:`(x_1, ..., x_N)`, the shape of the output tensor is
    :math:`(x_1, ..., x_{axis-1}, x_{axis+1}, ..., x_N)`.

    Args:
        x (Tensor): Input tensor. The shape is :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
        axis (int): Axis where the Argmin operation applies to. Default: -1.

    Returns:
        Tensor, indices of the min value of input tensor across the axis.

    Raises:
        TypeError: If `axis` is not an int.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([2.0, 3.1, 1.2]), mindspore.float32)
        >>> index = ops.argmin(input_x)
        >>> print(index)
        2
    """
    _argmin = _get_cache_prim(P.Argmin)(axis)
    return _argmin(x)


neg_tensor = P.Neg()


def neg(x):
    """
    Returns a tensor with negative values of the input tensor element-wise.

    .. math::

        out_{i} = - x_{i}

    Args:
        x (Tensor): The input tensor whose dtype is number.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape and dtype as input.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, -1, 2, 0, -3.5]), mindspore.float32)
        >>> output = ops.neg(x)
        >>> print(output)
        [-1.  -2.   1.  -2.   0.   3.5]
    """
    return neg_tensor(x)


def ceil(x):
    r"""
    Rounds a tensor up to the closest integer element-wise.

    .. math::

        out_i = \lceil x_i \rceil = \lfloor x_i \rfloor + 1

    Args:
        x (Tensor): The input tensor. It's element data type must be float16 or float32.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16 or float32.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> x = Tensor(np.array([1.1, 2.5, -1.5]), mindspore.float32)
        >>> output = F.ceil(x)
        >>> print(output)
        [ 2.  3. -1.]
    """
    return tensor_ceil(x)


def round(x):
    r"""
    Returns half to even of a tensor element-wise.

    .. math::

        out_i \approx x_i

    Args:
        x (Tensor): The input tensor.

    Returns:
        Tensor, has the same shape and type as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
         >>> x = Tensor(np.array([0.8, 1.5, 2.3, 2.5, -4.5]), mindspore.float32)
         >>> output = ops.round(x)
         >>> print(output)
         [ 1.  2.  2.  2. -4.]
    """
    return tensor_round_(x)


def sub(x, y):
    r"""
    Subtracts the second input tensor from the first input tensor element-wise.

    .. math::

        out_{i} = x_{i} - y_{i}

    .. note::
        - Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        - The inputs must be two tensors or one tensor and one scalar.
        - When the inputs are two tensors,
          dtypes of them cannot be bool at the same time, and the shapes of them can be broadcast.
        - When the inputs are one tensor and one scalar, the scalar could only be a constant.

    Args:
        x (Union[Tensor, number.Number, bool]): The first input is a number.Number or
            a bool or a tensor whose data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        y (Union[Tensor, number.Number, bool]): The second input, when the first input is a Tensor,
            the second input should be a number.Number or bool value, or a Tensor whose data type is number or bool\_.
            When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not a number.Number or a bool or a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([4, 5, 6]), mindspore.int32)
        >>> output = ops.sub(x, y)
        >>> print(output)
        [-3 -3 -3]
    """
    return tensor_sub(x, y)


def mul(x, y):
    r"""
    Multiplies two tensors element-wise.

    .. math::

        out_{i} = x_{i} * y_{i}
    .. note::
        - Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        - The inputs must be two tensors or one tensor and one scalar.
        - When the inputs are two tensors,
          dtypes of them cannot be bool at the same time, and the shapes of them can be broadcast.
        - When the inputs are one tensor and one scalar, the scalar could only be a constant.

    Args:
        x (Union[Tensor, number.Number, bool]): The first input is a number.Number or
            a bool or a tensor whose data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        y (Union[Tensor, number.Number, bool]): The second input, when the first input is a Tensor,
            the second input should be a number.Number or bool value, or a Tensor whose data type is number or bool\_.
            When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, number.Number, bool.
        ValueError: If `x` and `y` are not the same shape.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 2.0, 3.0]), mindspore.float32)
        >>> y = Tensor(np.array([4.0, 5.0, 6.0]), mindspore.float32)
        >>> output = ops.mul(x, y)
        >>> print(output)
        [ 4. 10. 18.]
    """
    return tensor_mul(x, y)


def div(x, y):
    """
    Divides the first input tensor by the second input tensor in floating-point type element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    .. math::

        out_{i} = x_{i} / y_{i}

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 2.0, 3.0]), mindspore.float32)
        >>> y = Tensor(np.array([4.0, 5.0, 6.0]), mindspore.float32)
        >>> output = ops.div(x, y)
        >>> print(output)
        [0.25 0.4  0.5 ]
    """
    return tensor_div(x, y)


def floor_div(x, y):
    """
    Divides the first input tensor by the second input tensor element-wise and round down to the closest integer.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    .. math::

        out_{i} = \\text{floor}( \\frac{x_i}{y_i})

    where the :math:`floor` indicates the Floor operator, for more details, please refer to the Floor operator.

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, -1]), mindspore.int32)
        >>> y = Tensor(np.array([3, 3, 3]), mindspore.int32)
        >>> output = ops.floor_div(x, y)
        >>> print(output)
        [ 0  1 -1]
    """
    return tensor_floordiv(x, y)


def pow(x, y):
    r"""
    Calculates the `y` power of each element in `x`.

    .. math::

        out_{i} = x_{i} ^{ y_{i}}

    .. note::
        - Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        - The inputs must be two tensors or one tensor and one scalar.
        - When the inputs are two tensors,
          dtypes of them cannot be bool at the same time, and the shapes of them can be broadcast.

    Args:
        x (Union[Tensor, number.Number, bool]): The first input is a number.Number or
            a bool or a tensor whose data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        y (Union[Tensor, number.Number, bool]): The second input, when the first input is a Tensor,
            the second input should be a number.Number or bool value, or a Tensor whose data type is number or bool\_.
            When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, number.Number or bool.
        ValueError: If the shape of `x` and `y` are different.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 2.0, 4.0]), mindspore.float32)
        >>> y = 3.0
        >>> output = ops.pow(x, y)
        >>> print(output)
        [ 1.  8. 64.]
        >>>
        >>> x = Tensor(np.array([1.0, 2.0, 4.0]), mindspore.float32)
        >>> y = Tensor(np.array([2.0, 4.0, 3.0]), mindspore.float32)
        >>> output = ops.pow(x, y)
        >>> print(output)
        [ 1. 16. 64.]
    """
    return tensor_pow(x, y)


def floor_mod(x, y):
    r"""
    Computes the remainder of division element-wise. It's a flooring divide.
    E.g. :math:`floor(x / y) * y + mod(x, y) = x`.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be both bool, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    .. math::

        out_{i} =\text{floor}(x_{i} // y_{i})

    where the :math:`floor` indicates the Floor operator, for more details, please refer to the Floor operator.

    .. warning::
        - The input data does not support 0.
        - When the elements of input exceeds 2048 , the accuracy of operator cannot guarantee the requirement of
          double thousandths in the mini form.
        - Due to different architectures, the calculation results of this operator on NPU and CPU may be inconsistent.
        - If shape is expressed as (D1,D2... ,Dn), then D1\*D2... \*DN<=1000000,n<=8.

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision of the two inputs.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, -1]), mindspore.int32)
        >>> y = Tensor(np.array([3, 3, 3]), mindspore.int32)
        >>> output = ops.floor_mod(x, y)
        >>> print(output)
        [2 1 2]
    """
    return tensor_mod(x, y)


def exp(x):
    r"""
    Returns exponential of a tensor element-wise.

    .. math::

        out_i = e^{x_i}

    Args:
        x (Tensor): The input tensor.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 2.0, 4.0]), mindspore.float32)
        >>> output = ops.exp(x)
        >>> print(output)
        [ 2.718282  7.389056 54.598152]
    """
    return tensor_exp(x)


def expm1(x):
    r"""
    Returns exponential then minus 1 of a tensor element-wise.

    .. math::

        out_i = e^{x_i} - 1

    Args:
        x (Tensor): The input tensor. With float16 or float32 data type.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is neither float16 nor float32.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.0, 1.0, 2.0, 4.0]), mindspore.float32)
        >>> output = ops.expm1(x)
        >>> print(output)
        [ 0.        1.718282  6.389056 53.598152]
    """
    return tensor_expm1(x)


def log(x):
    """
    Returns the natural logarithm of a tensor element-wise.

    .. math::
        y_i = log_e(x_i)

    .. note::
        The dimension of the input Tensor on Ascend should be less than or equal to 8, and the dimension of the
        input Tensor on the CPU should be less than 8.

    .. warning::
        If the input value of operator Log is within the range (0, 0.01] or [0.95, 1.05], the output accuracy may
        be affacted.

    Args:
        x (Tensor): Input Tensor of any dimension. The value must be greater than 0.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64 on GPU and CPU.
        TypeError: If dtype of `x` is not float16 or float32 on Ascend.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 2.0, 4.0]), mindspore.float32)
        >>> output = ops.log(x)
        >>> print(output)
        [0.        0.6931472 1.3862944]
    """
    return log_(x)


def floor(x):
    r"""
    Rounds a tensor down to the closest integer element-wise.

    .. math::

        out_i = \lfloor x_i \rfloor

    Args:
        x (Tensor): The input tensor. Its element data type must be float16 or float32.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not in [float16, float32, float64].

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.1, 2.5, -1.5]), mindspore.float32)
        >>> output = ops.floor(x)
        >>> print(output)
        [ 1.  2. -2.]
    """
    return floor_(x)


def inplace_update(x, v, indices):
    """
    Updates specified rows with values in `v`.

    Args:
        indices (Union[int, tuple], Tensor): Indices into the left-most dimension of `x`, and determines which rows of x
            to update with v. It is an int or tuple, whose value is in [0, the first dimension size of x). If the type
            is Tensor, it supports dynamic shape. Otherwise, it only supports static shape.
        x (Tensor) - A tensor which to be inplace updated. It can be one of the following data types:
            float32, float16 and int32.
        v (Tensor) - A tensor with the same type as `x` and the same dimension size as `x` except
            the first dimension, which must be the same as the size of `indices`.

    Returns:
        Tensor, with the same type and shape as the input `x`.

    Raises:
        TypeError: If `indices` is neither int nor tuple.
        TypeError: If `indices` is a tuple and its element is not an int.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> indices = (0, 1)
        >>> x = Tensor(np.array([[1, 2], [3, 4], [5, 6]]), mindspore.float32)
        >>> v = Tensor(np.array([[0.5, 1.0], [1.0, 1.5]]), mindspore.float32)
        >>> inplace_update = ops.InplaceUpdate(indices)
        >>> output = inplace_update(x, v)
        >>> print(output)
        [[0.5 1. ]
         [1.  1.5]
         [5.  6. ]]
    """
    if not isinstance(indices, (Tensor, Tensor_)):
        inplace_update_inner = _get_cache_prim(P.InplaceUpdate)(indices)
        output = inplace_update_inner(x, v)
    else:
        inplace_update_inner = InplaceUpdateV2()
        output = inplace_update_inner(x, indices, v)
    return output


def inplace_add(x, v, indices):
    """
    Adds `v` into specified rows of `x`. Computes `y` = `x`; y[i,] += `v`.

    Args:
        indices (Union[int, tuple]): Indices into the left-most dimension of `x`, and determines which rows of `x`
            to add with `v`. It is an integer or a tuple, whose value is in [0, the first dimension size of `x`).
        x (Tensor) - The first input is a tensor whose data type is float16, float32 or int32.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        v (Tensor) - The second input is a tensor that has the same dimension sizes as `x` except
            the first dimension, which must be the same as indices' size. It has the same data type with `x`.

    Returns:
        Tensor, has the same shape and dtype as `x`.

    Raises:
        TypeError: If `indices` is neither int nor tuple.
        TypeError: If `indices` is a tuple whose elements are not all int.
        ValueError: If the rank of `x` is not equal to the rank of `v`.
        ValueError: If the length of `indices` is not equal to `v.shape[0]`.
        ValueError: If the values of `indices` are not in range of `[0, x.shape[0])`.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore
        >>> from mindspore import Tensor, ops
        >>> indices = (0, 1)
        >>> x = Tensor(np.array([[1, 2], [3, 4], [5, 6]]), mindspore.float32)
        >>> input_v = Tensor(np.array([[0.5, 1.0], [1.0, 1.5]]), mindspore.float32)
        >>> output = ops.inplace_add(x, input_v, indices)
        >>> print(output)
        [[1.5 3. ]
         [4.  5.5]
         [5.  6. ]]
    """
    inplace_add_inner = _get_cache_prim(P.InplaceAdd)(indices)
    return inplace_add_inner(x, v)


def inplace_sub(x, v, indices):
    """
    Subtracts `v` into specified rows of `x`. Computes `y` = `x`; y[i,] -= `v`.

    Args:
        indices (Union[int, tuple]): Indices into the left-most dimension of `x`, and determines which rows of `x`
            to subtract with `v`. It is an int or tuple, whose value is in [0, the first dimension size of `x`).
        x (Tensor) - The first input is a tensor whose data type is float16, float32 or int32.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        v (Tensor) - The second input is a tensor who has the same dimension sizes as `x` except
            the first dimension, which must be the same as indices' size. It has the same data type with `x`.

    Returns:
        Tensor, has the same shape and dtype as `x`.

    Raises:
        TypeError: If `indices` is neither int nor tuple.
        TypeError: If `indices` is a tuple whose elements are not all int.
        ValueError: If the rank of `x` is not equal to the rank of `v`.
        ValueError: If the length of `indices` is not equal to `v.shape[0]`.
        ValueError: If the values of `indices` are not in range of `[0, x.shape[0])`.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore
        >>> from mindspore import Tensor, ops
        >>> indices = (0, 1)
        >>> x = Tensor(np.array([[1, 2], [3, 4], [5, 6]]), mindspore.float32)
        >>> input_v = Tensor(np.array([[0.5, 1.0], [1.0, 1.5]]), mindspore.float32)
        >>> output = ops.inplace_sub(x, input_v, indices)
        >>> print(output)
        [[0.5 1. ]
         [2.  2.5]
         [5.  6. ]]
    """
    inplace_sub_inner = _get_cache_prim(P.InplaceSub)(indices)
    return inplace_sub_inner(x, v)


def logical_not(x):
    """
    Computes the "logical NOT" of a tensor element-wise.

    .. math::

        out_{i} = \\neg x_{i}

    Args:
        x (Tensor): The input tensor whose dtype is bool.
            :math:`(N,*)` where :math:`*` means,any number of additional dimensions.

    Returns:
        Tensor, the shape is the same as the `x`, and the dtype is bool.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not a bool.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([True, False, True]), mindspore.bool_)
        >>> output = ops.logical_not(x)
        >>> print(output)
        [False  True False]
    """
    return logical_not_(x)


def logical_or(x):
    """
    Computes the "logical OR" of two tensors element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one bool.
    When the inputs are two tensors, the shapes of them could be broadcast,
    and the data types of them must be bool.
    When the inputs are one tensor and one bool, the bool object could only be a constant,
    and the data type of the tensor must be bool.

    .. math::

        out_{i} = x_{i} \\vee y_{i}

    Note:
        LogicalOr supports broadcasting.

    Args:
        x (Union[Tensor, bool]): The first input is a bool or a tensor whose data type is bool.
        y (Union[Tensor, bool]): The second input is a bool when the first input is a tensor or
            a tensor whose data type is bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting, and the data type is bool.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([True, False, True]), mindspore.bool_)
        >>> y = Tensor(np.array([True, True, False]), mindspore.bool_)
        >>> output = ops.logical_or(x, y)
        >>> print(output)
        [ True  True  True]
    """
    return logical_or_(x)


def logical_and(x):
    r"""
    Computes the "logical AND" of two tensors element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one bool.
    When the inputs are two tensors, the shapes of them could be broadcast,
    and the data types of them must be bool.
    When the inputs are one tensor and one bool, the bool object could only be a constant,
    and the data type of the tensor must be bool.

    .. math::

        out_{i} = x_{i} \wedge y_{i}

    Note:
        LogicalAnd supports broadcasting.

    Args:
        x (Union[Tensor, bool]): The first input is a bool or a tensor whose data type is bool.
        y (Union[Tensor, bool]): The second input is a bool when the first input is a tensor or
            a tensor whose data type is bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting, and the data type is bool.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([True, False, True]), mindspore.bool_)
        >>> y = Tensor(np.array([True, True, False]), mindspore.bool_)
        >>> output = ops.logical_and(x, y)
        >>> print(output)
        [ True False False]
    """
    return logical_and_(x)


def sin(x):
    r"""
    Computes sine of the input element-wise.

    .. math::

        out_i = sin(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.62, 0.28, 0.43, 0.62]), mindspore.float32)
        >>> output = ops.sin(x)
        >>> print(output)
        [0.5810352 0.27635565 0.41687083 0.5810352]
    """
    return sin_(x)


def cos(x):
    r"""
    Computes cosine of input element-wise.

    .. math::
        out_i = cos(x_i)

    .. warning::
        Currently support Float16, Float32 data type. If use Float64, there may
        be a problem of missing precision.

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.24, 0.83, 0.31, 0.09]), mindspore.float32)
        >>> output = ops.cos(x)
        >>> print(output)
        [0.971338 0.6748758 0.95233357 0.9959527]
    """
    return cos_(x)


def tan(x):
    r"""
    Computes tangent of `x` element-wise.

    .. math::

        out_i = tan(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> x = Tensor(np.array([-1.0, 0.0, 1.0]), mindspore.float32)
        >>> output = ops.tan(x)
        >>> print(output)
        [-1.5574081 0. 1.5574081]
    """
    return tan_(x)


def xlogy(x, y):
    r"""
    Computes the first input tensor multiplied by the logarithm of second input tensor element-wise.
    Returns zero when `x` is zero.

    .. math::

        out_i = x_{i}\ln{y_{i}}

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    Args:
        - **x** (Union[Tensor, number.Number, bool]) - The first input is a number.Number or
          a bool or a tensor whose data type is
          `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
          `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        - **y** (Union[Tensor, number.Number, bool]) - The second input is a number.Number or
          a bool when the first input is a tensor or a tensor whose data type is number or bool\_.
          When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not a number.Number or a bool or a Tensor.
        TypeError: If dtype of `x` and 'y' is not in [float16, float32, float64].
        ValueError: If `x` could not be broadcast to a tensor with shape of `y`.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([-5, 0, 4]), mindspore.float32)
        >>> y = Tensor(np.array([2, 2, 2]), mindspore.float32)
        >>> xlogy = ops.Xlogy()
        >>> output = xlogy(x, y)
        >>> print(output)
        [-3.465736   0.        2.7725887]
    """
    return xlogy_(x, y)


def asin(x):
    r"""
    Computes arcsine of input tensors element-wise.

    .. math::

        out_i = sin^{-1}(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
            The data type should be one of the following types: float16, float32, float64.

    Returns:
        Tensor, has the same shape and dtype as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32, float64.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.74, 0.04, 0.30, 0.56]), mindspore.float32)
        >>> output = ops.asin(x)
        >>> print(output)
        [0.8330704  0.04001067 0.30469266 0.5943858 ]
    """
    return asin_(x)


def acos(x):
    r"""
    Computes arccosine of input tensors element-wise.

    .. math::

        out_i = cos^{-1}(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
            The data type should be one of the following types: float16, float32, float64.

    Returns:
        Tensor, has the same shape and dtype as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.74, 0.04, 0.30, 0.56]), mindspore.float32)
        >>> output = ops.acos(x)
        >>> print(output)
        [0.737726  1.5307857 1.2661036 0.9764105]
    """
    return acos_(x)


def atan(x):
    r"""
    Computes the trigonometric inverse tangent of the input element-wise.

    .. math::

        out_i = tan^{-1}(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
            The data type should be one of the following types: float16, float32.

    Returns:
        A Tensor, has the same type as the input.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16 or float32.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 0.0]), mindspore.float32)
        >>> output = ops.atan(x)
        >>> print(output)
        [0.7853982 0.       ]
    """
    return atan_(x)


def sinh(x):
    r"""
    Computes hyperbolic sine of the input element-wise.

    .. math::

        out_i = \sinh(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.62, 0.28, 0.43, 0.62]), mindspore.float32)
        >>> output = ops.sinh(x)
        >>> print(output)
        [0.6604918  0.28367308 0.44337422 0.6604918 ]
    """
    return sinh_(x)


def cosh(x):
    r"""
    Computes hyperbolic cosine of input element-wise.

    .. math::

        out_i = \cosh(x_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If the dtype of `x` is not one of the following types:
                   float16, float32, float64, complex64, complex128.
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.24, 0.83, 0.31, 0.09]), mindspore.float32)
        >>> output = ops.cosh(x)
        >>> print(output)
        [1.0289385 1.364684 1.048436 1.0040528]
    """
    return cosh_(x)


def tanh(input_x):
    r"""
    Tanh activation function.

    Computes hyperbolic tangent of input element-wise. The Tanh function is defined as:

    .. math::

        tanh(x_i) = \frac{\exp(x_i) - \exp(-x_i)}{\exp(x_i) + \exp(-x_i)} = \frac{\exp(2x_i) - 1}{\exp(2x_i) + 1},

    where :math:`x_i` is an element of the input Tensor.

    Args:
        input_x (Tensor): Tensor of shape :math:`(N, *)`, where :math:`*` means, any number of
            additional dimensions, with float16 or float32 data type.

    Returns:
        Tensor, with the same type and shape as the `input_x`.

    Raises:
        TypeError: If dtype of `input_x` is neither float16 nor float32.
        TypeError: If `input_x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU``  ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([1, 2, 3, 4, 5]), mindspore.float32)
        >>> output = ops.tanh(input_x)
        >>> print(output)
        [0.7615941 0.9640276 0.9950547 0.9993293 0.9999092]
    """
    return tanh_(input_x)


def asinh(x):
    r"""
    Computes inverse hyperbolic sine of the input element-wise.

    .. math::

        out_i = \sinh^{-1}(input_i)

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape and type as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([-5.0, 1.5, 3.0, 100.0]), mindspore.float32)
        >>> output = ops.asinh(x)
        >>> print(output)
        [-2.3124382  1.1947632  1.8184465  5.298342 ]
    """
    return asinh_(x)


def acosh(x):
    r"""
    Computes inverse hyperbolic cosine of the inputs element-wise.

    .. math::

        out_i = \cosh^{-1}(input_i)

    .. warning::
        Given an input tensor x, the function computes inverse hyperbolic cosine of every element.
        Input range is [1, inf].

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shape and type as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1.0, 1.5, 3.0, 100.0]), mindspore.float32)
        >>> output = ops.acosh(x)
        >>> print(output)
        [0.        0.9624237 1.7627472 5.298292 ]
    """
    return acosh_(x)


def atanh(x):
    r"""
    Computes inverse hyperbolic tangent of the input element-wise.

    .. math::

        out_i = \tanh^{-1}(x_{i})

    .. warning::
        This is an experimental prototype that is subject to change and/or deletion.

    Args:
        x (Tensor): The shape of tensor is
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
            The data type should be one of the following types: float16, float32.

    Returns:
        A Tensor, has the same type as the input.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16 or float32.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0, -0.5]), mindspore.float32)
        >>> output = ops.atanh(x)
        >>> print(output)
        [ 0.         -0.54930615]
    """
    return atanh_(x)


def atan2(x, y):
    r"""
    Returns arctangent of x/y element-wise.

    It returns :math:`\theta\ \in\ [-\pi, \pi]`
    such that :math:`x = r*\sin(\theta), y = r*\cos(\theta)`, where :math:`r = \sqrt{x^2 + y^2}`.

    Args of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower precision data type will be converted to
    the relatively highest precision data type.

    Args:
        x (Tensor): The input tensor.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
        y (Tensor): The input tensor. It has the same shape with `x`.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,and the data type is same as `x`.

    Raises:
        TypeError: If `x` or `y` is not a Tensor.
        RuntimeError: If the data type of `x` and `y` conversion of Parameter is required
                      when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> x = Tensor(np.array([0, 1]), mindspore.float32)
        >>> y = Tensor(np.array([1, 1]), mindspore.float32)
        >>> output = ops.atan2(x, y)
        >>> print(output)
        [0.        0.7853982]
    """
    return atan2_(x, y)


def bitwise_and(x, y):
    r"""
    Returns bitwise `and` of two tensors element-wise.

    .. math::

        out_i = x_{i} \wedge y_{i}

    Args of `x` and `y` comply with the implicit type conversion rules to
    make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        x (Tensor): The input tensor with int16, int32 or uint16 data type.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
        y (Tensor): The input tensor with same type as the `x`.

    Returns:
        Tensor, has the same type as the `x`.

    Raises:
        TypeError: If `x` or `y` is not a Tensor.
        RuntimeError: If the data type of `x` and `y` conversion of Parameter is required
                      when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0, 0, 1, -1, 1, 1, 1]), mindspore.int16)
        >>> y = Tensor(np.array([0, 1, 1, -1, -1, 2, 3]), mindspore.int16)
        >>> output = ops.bitwise_and(x, y)
        >>> print(output)
        [ 0  0  1 -1  1  0  1]
    """
    return bitwise_and_(x, y)


def bitwise_or(x, y):
    r"""
    Returns bitwise `or` of two tensors element-wise.

    .. math::

        out_i = x_{i} \mid y_{i}

    Args of `x` and `y` comply with the implicit type conversion rules to
    make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        x (Tensor): The input tensor with int16, int32 or uint16 data type.
        y (Tensor): The input tensor with same type as the `x`.

    Returns:
        Tensor, has the same type as the `x`.

    Raises:
        TypeError: If `x` or `y` is not a Tensor.
        RuntimeError: If the data type of `x`, `y` conversion of Parameter is required
                      when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0, 0, 1, -1, 1, 1, 1]), mindspore.int16)
        >>> y = Tensor(np.array([0, 1, 1, -1, -1, 2, 3]), mindspore.int16)
        >>> output = ops.bitwise_or(x, y)
        >>> print(output)
        [ 0  1  1 -1 -1  3  3]
    """
    return bitwise_or_(x, y)


def bitwise_xor(x, y):
    r"""
    Returns bitwise `xor` of two tensors element-wise.

    .. math::

        out_i = x_{i} \oplus y_{i}

    Args of `x` and `y` comply with the implicit type conversion rules to
    make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        x (Tensor): The input tensor with int16, int32 or uint16 data type.
        y (Tensor): The input tensor with same type as the `x`.

    Returns:
        Tensor, has the same type as the `x`.

    Raises:
        TypeError: If `x` or `y` is not a Tensor.
        RuntimeError: If the data type of `x`, `y` conversion of Parameter is required
                      when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([0, 0, 1, -1, 1, 1, 1]), mindspore.int16)
        >>> y = Tensor(np.array([0, 1, 1, -1, -1, 2, 3]), mindspore.int16)
        >>> output = ops.bitwise_xor(x, y)
        >>> print(output)
        [ 0  1  0  0 -2  3  2]
    """
    return bitwise_xor_(x, y)


def inv(x):
    r"""
    Computes Reciprocal of input tensor element-wise.

    .. math::
        out_i = \frac{1}{x_{i} }

    Args:
        x (Tensor): Tensor of any dimension. Must be one of the following types: float16, float32 or int32.

    Returns:
        Tensor, has the same type and shape as input shape value.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not one of float16, float32, int32.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> x = Tensor(np.array([0.25, 0.4, 0.31, 0.52]), mindspore.float32)
        >>> output = F.inv(x)
        >>> print(output)
        [4.        2.5       3.2258065 1.923077 ]
    """
    return inv_(x)


def invert(x):
    r"""
    Flips all bits of input tensor element-wise.

    .. math::
        out_i = ~x_{i}

    Args:
        x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
            The data type should be one of the following types: int16, uint16.

    Returns:
        Tensor, has the same shape as `x`.

    Raises:
        TypeError: If dtype of `x` is neither int16 nor uint16.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> x = Tensor(np.array([25, 4, 13, 9]), mindspore.int16)
        >>> output = F.invert(x)
        >>> print(output)
        [-26 -5 -14 -10]
    """
    return invert_(x)


def erf(x):
    r"""
    Computes the Gauss error function of `x` element-wise.

    .. math::

        erf(x)=\frac{2} {\sqrt{\pi}} \int\limits_0^{x} e^{-t^{2}} dt

    Args:
        x (Tensor): Input Tensor of Gaussian error function. Its dimension must be less than 8 and
            data type must be float16 or float32.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is neither float16 nor float32.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1, 0, 1, 2, 3]), mindspore.float32)
        >>> output = ops.erf(x)
        >>> print(output)
        [-0.8427168   0.          0.8427168   0.99530876  0.99997765]
    """
    return erf_(x)


def erfc(x):
    r"""
    Computes the complementary error function of `x` element-wise.

    .. math::

        erfc(x) = 1 - \frac{2} {\sqrt{\pi}} \int\limits_0^{x} e^{-t^{2}} dt

    Args:
        x (Tensor): The input tensor. The data type must be float16 or float32.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.

    Returns:
        Tensor, has the same shap dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16 or float32.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1, 0, 1, 2, 3]), mindspore.float32)
        >>> output = ops.erfc(x)
        >>> print(output)
        [1.8427168e+00 1.0000000e+00 1.5728319e-01 4.6912432e-03 2.2351742e-05]
    """
    return erfc_(x)


def bessel_j0(x):
    r"""
    Computes the Bessel j0 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_j0(x)
        >>> print(output)
        [1.8427168e+00 1.0000000e+00 1.5728319e-01 4.6912432e-03 2.2351742e-05]
    """
    return bessel_j0_(x)


def bessel_j1(x):
    r"""
    Computes the Bessel j1 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_j1(x)
        >>> print(output)
        [0.24226846,  0.44005059,  0.57672481, -0.06604333]
    """
    return bessel_j1_(x)


def bessel_i0(x):
    r"""
    Computes the Bessel i0 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1, -0.5, 0.5, 1]), mindspore.float32)
        >>> output = ops.bessel_i0(x)
        >>> print(output)
        [1.26606588, 1.06348337, 1.06348337, 1.26606588]
    """
    return bessel_i0_(x)


def bessel_i0e(x):
    r"""
    Computes the Bessel i0e function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1, -0.5, 0.5, 1]), mindspore.float32)
        >>> output = ops.bessel_i0e(x)
        >>> print(output)
        [0.46575961, 0.64503527, 0.64503527, 0.46575961]
    """
    return bessel_i0e_(x)


def bessel_k0(x):
    r"""
    Computes the Bessel k0 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_k0(x)
        >>> print(output)
        [0.92441907, 0.42102444, 0.11389387, 0.01115968]
    """
    return bessel_k0_(x)


def bessel_k0e(x):
    r"""
    Computes the Bessel k0e function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_k0e(x)
        >>> print(output)
        [1.52410939, 1.14446308, 0.84156822, 0.60929767]
    """
    return bessel_k0e_(x)


def bessel_y0(x):
    r"""
    Computes the Bessel y0 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_y0(x)
        >>> print(output)
        [-0.44451874  0.08825696  0.51037567  -0.01694074]
    """
    return bessel_y0_(x)


def bessel_y1(x):
    r"""
    Computes the Bessel y1 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_y1(x)
        >>> print(output)
        [-1.47147239  -0.78121282  -0.10703243  0.39792571]
    """
    return bessel_y1_(x)


def linspace(start, stop, num):
    r"""
    Returns a Tensor whose value is `num` evenly spaced in the interval `start` and `stop` (including `start` and
    `stop`), and the length of the output Tensor is `num`.

    .. math::
        \begin{aligned}
        &step = (stop - start)/(num - 1)\\
        &output = [start, start+step, start+2*step, ... , stop]
        \end{aligned}

    Args:
        start (Tensor): Start value of interval. The tensor data type must be float32 and with shape of 0-D.
        stop (Tensor): Last value of interval. The tensor data type must be float32 and with shape of 0-D.
        num (int): Number of ticks in the interval, inclusive of start and stop.
            Must be positive int number.

    Outputs:
        Tensor, has the same dtype as `start`, and the shape of :math:`(num)`

    Raises:
        TypeError: If `start` or `stop` is not a Tensor.
        TypeError: If dtype of `start` or dtype of `stop` is not float32.
        ValueError: If shape of `start` or shape of `stop` is not 0-D.
        TypeError: If `num` is not int.
        ValueError: If `num` is not positive int number.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> start = Tensor(1, mindspore.float32)
        >>> stop = Tensor(10, mindspore.float32)
        >>> num = 5
        >>> output = ops.linspace(start, stop, num)
        >>> print(output)
        [ 1.    3.25  5.5   7.75 10.  ]
    """
    return linspace_(start, stop, num)


def matrix_determinant(x):
    """
    Computes the determinant of one or more square matrices.

    Args:
        x (Tensor): A matrix to be calculated. The matrix must be at least two dimensions, and the last two
          dimensions must be the same size. Data type must be float32, float64, complex64 or complex128.

    Returns:
        Tensor, The shape is `x_shape[:-2]`, the dtype is same as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` not float32, float64, complex64 or complex128.
        ValueError: If the last two dimensions of `x` is not same size.
        ValueError: If the dimension of `x` is less than 2.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[[-4.5, -1.5], [7.0, 6.0]], [[2.5, 0.5], [3.0, 9.0]]]), mindspore.float32)
        >>> output = ops.matrix_determinant(input_x)
        >>> print(output)
        [-16.5 21. ]
    """
    return matrix_determinant_(x)


def log_matrix_determinant(x):
    """
    Computes the sign and the log of the absolute value of the determinant of one or more square matrices.

    Args:
        x (Tensor): A matrix to be calculated. The matrix must be at least two dimensions, and the last two
          dimensions must be the same size. Data type must be float32, float64, complex64 or complex128.

    Returns:
        Tensor, The signs of the log determinants. The shape is `x_shape[:-2]`, the dtype is same as `x`.
        Tensor, The absolute values of the log determinants. The shape is `x_shape[:-2]`, the dtype is same as `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` not float32, float64, complex64 or complex128.
        ValueError: If the last two dimensions of `x` is not same size.
        ValueError: If the dimension of `x` is less than 2.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[[-4.5, -1.5], [7.0, 6.0]], [[2.5, 0.5], [3.0, 9.0]]]), mindspore.float32)
        >>> output = ops.log_matrix_determinant(input_x)
        >>> print(output)
        (Tensor(shape=[2], dtype=Float32, value= [-1.00000000e+00,  1.00000000e+00]), Tensor(shape=[2], dtype=Float32,
        value= [ 2.80336046e+00,  3.04452229e+00]))
    """
    return log_matrix_determinant_(x)


def matrix_solve(matrix, rhs, adjoint=False):
    r"""
    Solves systems of linear equations.

    .. math::
        \begin{aligned}
        &matrix[..., M, M] * x[..., M, K] = rhs[..., M, K] \\
        &adjoint(matrix[..., M, M]) * x[..., M, K] = rhs[..., M, K]
        \end{aligned}


    Args:
        matrix (Tensor): The shape of tensor is :math:`[..., M, M]`.
        rhs (Tensor): The shape of tensor is :math:`[..., M, K]`. `rhs` must have the same dtype as `matrix`.
        adjoint(bool): Indicating whether to solve with matrix or its (block-wise) adjoint. Default: False.

    Returns:
        x (Tensor): The dtype and shape is the same as 'rhs'.

    Raises:
        TypeError: If adjoint is not the type of bool.
        TypeError: If the type of matrix is not one of the following dtype:
                   mstype.float16, mstype.float32, mstype.float64, mstype.complex64, mstype.complex128.
        TypeError: If the type of `matrix` is not the same as that of `rhs`.
        ValueError: If the rank of `matrix` less than 2.
        ValueError: If the dimension of `matrix` is not the same as `rhs`.
        ValueError: If the inner-most 2 dimension of `matrix` is not the same.
        ValueError: If the inner-most 2 dimension of `rhs` does not match `matrix`.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> matrix = Tensor([[5, 4], [3, 1]], mindspore.float32)
        >>> rhs = Tensor([[7], [2]], mindspore.float32)
        >>> result = ops.matrix_solve(matrix, rhs)
        >>> print(result)
        [[0.14285707]
         [1.5714287 ]]
    """
    matrix_solve_ = _get_cache_prim(MatrixSolve)(adjoint=adjoint)
    return matrix_solve_(matrix, rhs)


def truncate_div(x, y):
    """
    Divides the first input tensor by the second input tensor element-wise for integer types, negative numbers will
    round fractional quantities towards zero.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    Note:
        Broadcasting is supported.

    Args:
        - x(Union[Tensor, Number, bool]) - The first input is a number, or a bool,
          or a tensor whose data type is number or bool.
        - y(Union[Tensor, Number, bool]) - The second input is a number, or a bool when the first input
          is a tensor, or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, -1]), mindspore.int32)
        >>> y = Tensor(np.array([3, 3, 3]), mindspore.int32)
        >>> truncate_div = ops.truncate_div()
        >>> output = truncate_div(x, y)
        >>> print(output)
        [0 1 0]
    """
    return truncate_div_(x, y)


def truncate_mod(x, y):
    r"""
    Returns the remainder of division element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    Args:
        - **x** (Union[Tensor, numbers.Number, bool]) - The first input is a number, or a bool,
          or a tensor whose data type is number or bool.
        - **y** (Union[Tensor, numbers.Number, bool]) - The second input is a number, or a bool when the first input
          is a tensor, or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision among the two inputs.

    Raises:
        TypeError: If neither `x` nor `y` is one of the following: Tensor, number, bool.
        TypeError: If neither `x` nor `y` is a Tensor.
        ValueError: If the shape `x` and `y` cannot be broadcasted to each other.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, -1]), mindspore.int32)
        >>> y = Tensor(np.array([3, 3, 3]), mindspore.int32)
        >>> truncate_mod = ops.truncate_mod()
        >>> output = truncate_mod(x, y)
        >>> print(output)
        [ 2  1 -1]
    """
    return truncate_mod_(x, y)


def ldexp(x, other):
    """
    Multiplies input by 2**:attr:other.

    .. math::

        out_{i} = input_{i} * ( 2_{i} ^{ other} )

    Note:
        Typically this function can create floating point numbers
        by multiplying mantissas in input with powers of intger 2
        from the exponents in :attr:’other’.

    Args:
        x (Tensor): The input tensor.
        other (Tensor): A tensor of exponents, typically integers.

    Outputs:
        out (Tensor, optional) : the output tensor.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If `other` is not a Tensor.
        ValueError: If the size of tensor `x` and `other` are different at non-singleton dimension, and not equal to 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> x = Tensor(np.array([1.]), mindspore.float32)
        >>> other = Tensor(np.array([1, 2, 3, 4]), mindspore.int32)
        >>> out = ops.ldexp(x, other)
        >>> print(out)
        [ 2.  4.  8. 16.]
    """

    pow_ops = _get_cache_prim(P.Pow)()
    mul_ops = _get_cache_prim(P.Mul)()

    out = mul_ops(x, pow_ops(2.0, other))
    return out


#####################################
# Comparison Operation Functions.
#####################################


def less(x, y):
    r"""
    Computes the boolean value of :math:`x < y` element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    .. math::

        out_{i} =\begin{cases}
            & \text{True,    if } x_{i}<y_{i} \\
            & \text{False,   if } x_{i}>=y_{i}
            \end{cases}

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,and the data type is bool.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([1, 1, 4]), mindspore.int32)
        >>> output = ops.less(x, y)
        >>> print(output)
        [False False True]
    """
    return tensor_lt(x, y)


def le(x, y):
    r"""
    Computes the boolean value of :math:`x <= y` element-wise.

    .. math::

        out_{i} =\begin{cases}
            & \text{True,    if } x_{i}<=y_{i} \\
            & \text{False,   if } x_{i}>y_{i}
            \end{cases}

    .. note::
        - Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        - The inputs must be two tensors or one tensor and one scalar.
        - When the inputs are two tensors,
          dtypes of them cannot be both bool , and the shapes of them can be broadcast.
        - When the inputs are one tensor and one scalar, the scalar could only be a constant.

    Args:
        x (Union[Tensor, number.Number, bool]): The first input is a number.Number or
            a bool or a tensor whose data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        y (Union[Tensor, number.Number, bool]): The second input, when the first input is a Tensor,
            the second input should be a number.Number or bool value, or a Tensor whose data type is number or bool\_.
            When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one after broadcasting, and the data type is bool.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([1, 1, 4]), mindspore.int32)
        >>> output = ops.le(x, y)
        >>> print(output)
        [ True False  True]
    """
    return tensor_le(x, y)


def gt(x, y):
    r"""
    Compare the value of the input parameters :math:`x,y` element-wise, and the output result is a bool value.

    .. math::

        out_{i} =\begin{cases}
            & \text{True,    if } x_{i}>y_{i} \\
            & \text{False,   if } x_{i}<=y_{i}
            \end{cases}

    Note:
        - Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        - The inputs must be two tensors or one tensor and one scalar.
        - When the inputs are two tensors, dtypes of them cannot be bool at the same time,
          and the shapes of them can be broadcast.
        - When the inputs are one tensor and one scalar, the scalar could only be a constant.
        - Broadcasting is supported.
        - If the input Tensor can be broadcast, the low dimension will be extended to the corresponding high dimension
          in another input by copying the value of the dimension.

    Args:
        x (Union[Tensor, number.Number, bool]): The first input is a number.Number or
            a bool or a tensor whose data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ .
        y (Union[Tensor, number.Number, bool]): The second input, when the first input is a Tensor,
            the second input should be a number.Number or bool value, or a Tensor whose data type is number or bool\_.
            When the first input is Scalar, the second input must be a Tensor whose data type is number or bool\_.

    Returns:
        Tensor, the shape is the same as the one after broadcasting, and the data type is bool.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([1, 1, 4]), mindspore.int32)
        >>> output = ops.gt(x, y)
        >>> print(output)
        [False  True False]
    """
    return tensor_gt(x, y)


def ge(x, y):
    r"""
    Computes the boolean value of :math:`x >= y` element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    .. math::

        out_{i} =\begin{cases}
            & \text{True,    if } x_{i}>=y_{i} \\
            & \text{False,   if } x_{i}<y_{i}
            \end{cases}

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting, and the data type is bool.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([1, 1, 4]), mindspore.int32)
        >>> output = ops.ge(x, y)
        >>> print(output)
        [True True False]
    """
    return tensor_ge(x, y)


def equal(x, y):
    r"""
    Computes the equivalence between two tensors element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors, the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar, the scalar could only be a constant.

    .. math::

        out_{i} =\begin{cases}
            & \text{True,    if } x_{i} = y_{i} \\
            & \text{False,   if } x_{i} \ne y_{i}
            \end{cases}

    Args:
        x (Union[Tensor, Number]): The first input is a number or
            a tensor whose data type is number.
        y (Union[Tensor, Number]): The second input is a number
            when the first input is a tensor or a tensor whose data type is number.
            The data type is the same as the first input.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,and the data type is bool.

    Raises:
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> # case 1: The shape of two inputs are different
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.float32)
        >>> output = ops.equal(x, 2.0)
        >>> print(output)
        [False True False]
        >>> # case 2: The shape of two inputs are the same
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([1, 2, 4]), mindspore.int32)
        >>> output = ops.equal(x, y)
        >>> print(output)
        [ True  True False]
    """
    return equal_(x, y)


def ne(x, y):
    r"""
    Computes the non-equivalence of two tensors element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors, the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar, the scalar could only be a constant.

    .. math::

        out_{i} =\begin{cases}
            & \text{True,    if } x_{i} \ne y_{i} \\
            & \text{False,   if } x_{i} = y_{i}
            \end{cases}

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,and the data type is bool.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.
        TypeError: If neither `x` nor `y` is a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.float32)
        >>> output = ops.ne(x, 2.0)
        >>> print(output)
        [ True False  True]
        >>>
        >>> x = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> y = Tensor(np.array([1, 2, 4]), mindspore.int32)
        >>> output = ops.ne(x, y)
        >>> print(output)
        [False False  True]
    """
    return not_equal(x, y)


def approximate_equal(x, y, tolerance=1e-5):
    r"""
    Returns True if abs(x-y) is smaller than tolerance element-wise, otherwise False.

    .. math::

        out_i = \begin{cases}
        & \text{ if } \left | x_{i} - y_{i} \right | < \text{tolerance},\ \ True  \\
        & \text{ if } \left | x_{i} - y_{i} \right | \ge \text{tolerance},\ \  False
        \end{cases}

    where `tolerance` indicates Acceptable maximum tolerance.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower precision data type will be converted to
    the relatively highest precision data type.

    Args:
        x (Tensor): A tensor. Must be one of the following types: float32, float16.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        y (Tensor): A tensor of the same type and shape as `x`.
        tolerance (float): The maximum deviation that two elements can be considered equal. Default: 1e-05.

    Outputs:
        Tensor, the shape is the same as the shape of `x`, and the data type is bool.

    Raises:
        TypeError: If `tolerance` is not a float.
        RuntimeError: If the data type of `x`, `y` conversion of Parameter is given
                      but data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> from mindspore.ops.function.math_func import approximate_equal
        >>> ...
        >>> tol = 2.
        >>> x = Tensor(np.array([1, 2, 3]), mstype.float32)
        >>> y = Tensor(np.array([2, 4, 6]), mstype.float32)
        >>> output = approximate_equal(Tensor(x), Tensor(y), tol)
        >>> print(output)
        [ True  False  False]
    """
    return P.ApproximateEqual(tolerance)(x, y)


def isfinite(x):
    r"""
    Determines which elements are finite for each position.

    .. math::

        out_i = \begin{cases}
          & \text{ if } x_{i} = \text{Finite},\ \ True\  \\
          & \text{ if } x_{i} \ne \text{Finite},\ \ False
        \end{cases}

    Args:
        x (Tensor): The input tensor.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape of input, and the dtype is bool.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([np.log(-1), 1, np.log(0)]), mindspore.float32)
        >>> output = ops.isfinite(x)
        >>> print(output)
        [False  True False]
    """
    return isfinite_(x)


def isnan(x):
    r"""
    Determines which elements are NaN for each position.

    .. math::

        out_i = \begin{cases}
          & \ True,\ \text{ if } x_{i} = \text{Nan} \\
          & \ False,\ \text{ if } x_{i} \ne  \text{Nan}
        \end{cases}

    where :math:`Nan` means not a number.

    Args:
        x (Tensor): The input tensor.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape of input, and the dtype is bool.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([np.log(-1), 1, np.log(0)]), mindspore.float32)
        >>> output = ops.isnan(x)
        >>> print(output)
        [ True False False]
    """
    return isnan_(x)


def isclose(x1, x2, rtol=1e-05, atol=1e-08, equal_nan=False):
    """
    Returns a new Tensor with boolean elements representing if each element of `x1`
    is “close” to the corresponding element of `x2`. Closeness is defined as:

    .. math::

            ∣x1−x2∣  ≤  atol + rtol × ∣x2∣

    Note:
        On Ascend, input arrays containing inf or NaN are not supported. Therefore, when the input is NaN or inf,
        the result is uncertain. And `equal_nan` must be True on Ascend.

    Args:
        x1 (Tensor): First Tensor to compare, with data type belongs to float32, float16, int32.
        x2 (Tensor): Second Tensor to compare, with data type belongs to float32, float16, int32.
        rtol (float, optional): Relative tolerance. Default: 1e-05.
        atol (float, optional): Absolute tolerance. Default: 1e-08.
        equal_nan (bool, optional): If True, then two NaNs will be considered equal. Default: False.

    Returns:
        A bool Tensor, with the shape as broadcasted result of the input `x1` and `x2`.

    Raises:
        TypeError: If either of `x1` and `x2` is not Tensor.
        TypeError: If either of `x1` and `x2` is not float16, float32 or int32.
        TypeError: If either of `atol` and `rtol` is not float.
        TypeError: If `equal_nan` is not bool.
        TypeError: If the dtype of `x1` is not same as the `x2`.
        ValueError: If `x1` and `x2` can not be broadcast.
        ValueError: If either of `atol` and `rtol` is less than zero.
        ValueError: If `equal_nan` is False on Ascend platform.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> input = Tensor(np.array([1.3, 2.1, 3.2, 4.1, 5.1]), mindspore.float16)
        >>> other = Tensor(np.array([1.3, 3.3, 2.3, 3.1, 5.1]), mindspore.float16)
        >>> output = ops.isclose(input, other)
        >>> print(output)
            [true false false false true]
    """
    is_close = _get_cache_prim(P.IsClose)(rtol=rtol, atol=atol, equal_nan=equal_nan)
    return is_close(x1, x2)


def isreal(x):
    """
    Returns a new tensor with boolean elements representing whether each element of `x` is real-valued.
    All real value types are considered real numbers.
    A complex value is considered real when its imaginary part is 0.

    Inputs:
        - **x** (Tensor) - The input tensor.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Outputs:
        Tensor, has the same shape of input, and the dtype is bool.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> from mindspore import ops
        >>> x = Tensor([1, 1+1j, 2+0j], mstype.complex64)
        >>> output = ops.isreal(x)
        >>> print(output)
        [ True False  True]
    """

    if not isinstance(x, (Tensor, Tensor_)):
        raise TypeError("the input x must be Tensor!")

    # Note: Integral and Floating tensor values are always real
    ones_op = _get_cache_prim(P.Ones)()
    real_dtype = mstype.int_type + mstype.uint_type + mstype.float_type + (mstype.bool_,)
    if x.dtype in real_dtype:
        return ones_op(x.shape, mstype.bool_)

    imag_op = _get_cache_prim(P.Imag)()
    return imag_op(x) == 0


def same_type_shape(input_x, input_y):
    """
    Checks whether the data type and shape of two tensors are the same.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        input_y (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_S)`.

    Returns:
        Tensor, the shape of tensor is :math:`(x_1, x_2, ..., x_R)`,
        if data type and shape of `input_x` and `input_y` are the same.

    Raises:
        TypeError: If the data types of `input_x` and `input_y` are not the same.
        ValueError: If the shapes of `input_x` and `input_y` are not the same.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[2, 2], [2, 2]]), mindspore.float32)
        >>> input_y = Tensor(np.array([[2, 2], [2, 2]]), mindspore.float32)
        >>> output = ops.same_type_shape(input_x, input_y)
        >>> print(output)
        [[2. 2.]
         [2. 2.]]
    """
    return same_type_shape_(input_x, input_y)


def maximum(x, y):
    """
    Computes the maximum of input tensors element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.
    If one of the elements being compared is a NaN, then that element is returned.

    .. math::
        output_i = max(x_i, y_i)

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.
        ValueError: If `x` and `y` are not the same shape.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> # case 1 : same data type
        >>> x = Tensor(np.array([1.0, 5.0, 3.0]), mindspore.float32)
        >>> y = Tensor(np.array([4.0, 2.0, 6.0]), mindspore.float32)
        >>> output = ops.maximum(x, y)
        >>> print(output)
        [4. 5. 6.]
        >>> # case 2 : different data type
        >>> x = Tensor(np.array([1.0, 5.0, 3.0]), mindspore.int32)
        >>> y = Tensor(np.array([4.0, 2.0, 6.0]), mindspore.float32)
        >>> output = ops.maximum(x, y)
        >>> print(output.dtype)
        Float32
    """
    return maximum_(x, y)


def minimum(x, y):
    r"""
    Computes the minimum of input tensors element-wise.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.
    If one of the elements being compared is a NaN, then that element is returned.

    .. math::
        output_i = min(x_i, y_i)

    Args:
        x (Union[Tensor, Number, bool]): The first input is a number or
            a bool or a tensor whose data type is number or bool.
        y (Union[Tensor, Number, bool]): The second input is a number or
            a bool when the first input is a tensor or a tensor whose data type is number or bool.

    Returns:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.
        ValueError: If `x` and `y` are not the same shape.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> # case 1 : same data type
        >>> x = Tensor(np.array([1.0, 5.0, 3.0]), mindspore.float32)
        >>> y = Tensor(np.array([4.0, 2.0, 6.0]), mindspore.float32)
        >>> output = ops.minimum(x, y)
        >>> print(output)
        [1. 2. 3.]
        >>> # case 2 : different data type
        >>> x = Tensor(np.array([1.0, 5.0, 3.0]), mindspore.int32)
        >>> y = Tensor(np.array([4.0, 2.0, 6.0]), mindspore.float32)
        >>> output = ops.minimum(x, y)
        >>> print(output.dtype)
        Float32
    """
    return minimum_(x, y)


def hypot(x1, x2):
    """
    Computes hypotenuse of input tensors element-wise as legs of a right triangle.
    The shape of two inputs should be broadcastable, and data type of them should be
    one of: float32, float64

    Args:
        - **x1** (Tensor) - The first input tensor.
        - **x2** (Tensor) - The second input tensor.

    Returns:
        Tensor, the shape is the same as the one after broadcasting, and the data type is one
        with higher precision in the two inputs.

    Raises:
        TypeError: If data type `x1` or `x2` is not float32 or float64.
        ValueError: If shape of two inputs are not broadcastable.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x1 = Tensor(np.array([3., 5., 7.]))
        >>> x2 = Tensor(np.array([4., 12., 24.]))
        >>> y = ops.hypot(x1, x2)
        >>> print(y)
        [ 5. 13. 25.]
    """

    hypot_ = Hypot()
    return hypot_(x1, x2)


def logaddexp(x1, x2):
    """
    Computes the logarithm of the sum of exponentiations of the inputs.

    Calculates ``log(exp(x1) + exp(x2))``. This function is useful in statistics, where the
    computed probability of an event may be so small that it exceeds the range of a normal
    floating point number. In this case, the logarithm of the calculated probability is stored.
    This function allows to add probabilities stored in this way.

    Args:
        x1 (Tensor): Input Tensor.
        x2 (Tensor): Input Tensor. If ``x1.shape != x2.shape``, they must be broadcastable to
            a common shape (which becomes the shape of the output).

    Returns:
        Tensor or scalar. This is a scalar if both `x1` and `x2` are scalars.

    Raises:
        TypeError: If `x1`, `x2` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x1 = Tensor(np.array([1, 2, 3]).astype(np.float16))
        >>> x2 = Tensor(np.array(2).astype(np.float16))
        >>> output = ops.logaddexp(x1, x2)
        >>> print(output)
        [2.312 2.693 3.312]
    """

    log_op = _get_cache_prim(P.Log)()
    exp_op = _get_cache_prim(P.Exp)()

    y = log_op(exp_op(x1) + exp_op(x2))
    return y


def logaddexp2(x1, x2):
    """
    Computes the logarithm of the sum of exponentiations in base of 2 of the inputs.

    Calculates ``log2(2**x1 + 2**x2)``. This function is useful in machine learning when the computed
    probability of an event may be small beyond the range of normal floating point numbers.
    In this case, the base-2 logarithm of the calculated probability can be used instead.
    This function allows to add probabilities stored in this way.

    Args:
        x1 (Tensor): Input tensor.
        x2 (Tensor): Input tensor. If ``x1.shape != x2.shape``, they must be broadcastable to
            a common shape (which becomes the shape of the output).

    Returns:
        Tensor or scalar. This is a scalar if both `x1` and `x2` are scalars.

    Raises:
        TypeError: If `x1`, `x2` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x1 = Tensor(np.array([2, 4, 8]).astype(np.float16))
        >>> x2 = Tensor(np.array([2]).astype(np.float16))
        >>> output = ops.logaddexp2(x1, x2)
        >>> print(output)
        [3. 4.32 8.02]
    """

    log_op = _get_cache_prim(P.Log)()
    pow_op = _get_cache_prim(P.Pow)()
    add_op = _get_cache_prim(P.Add)()

    if not isinstance(x1, (Tensor, Tensor_)):
        raise TypeError("The input x1 must be Tensor.")
    if not isinstance(x2, (Tensor, Tensor_)):
        raise TypeError("The input x2 must be Tensor.")

    add_exp = add_op(pow_op(2, x1), pow_op(2, x2))
    tensor_2 = _make_tensor(2, add_exp.dtype)

    return log_op(add_exp) / log_op(tensor_2)


def std(input_x, axis=(), unbiased=True, keep_dims=False):
    """
    Returns the standard-deviation and mean of each row of the input tensor in the dimension `axis`.
    If `axis` is a list of dimensions, reduce over all of them.

    Args:
        input_x (Tensor): Input tensor.
        axis (Union[int, tuple(int), list(int)]): The dimensions to reduce. Default: (), reduce all dimensions.
                                                  Only constant value is allowed.
                                                  Must be in the range [-rank(`input_x`), rank(`input_x`)).
        unbiased (bool):  Whether to use Bessel’s correction.
                          If true, will use the Bessel correction unbiased estimation.
                          If false, will through the biased estimation to calculate the standard deviation.
        keep_dims (bool): Whether the output tensor has dim retained or not.
                          If true, keep these reduced dimensions and the length is 1.
                          If false, don't keep these dimensions.

    Returns:
        A tuple (output_std, output_mean) containing the standard deviation and mean.

    Raises:
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `input_x` is not a Tensor.
        ValueError: If `axis` is not one of the following: int, tuple or list.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> input_x = Tensor(np.array([[1, 2, 3], [-1, 1, 4]]).astype(np.float32))
        >>> output = F.std(input_x, 1, True, False)
        >>> output_std, output_mean = output[0], output[1]
        >>> print(output_std)
        [1.        2.5166116]
        >>> print(output_mean)
        [2.        1.3333334]
    """
    reduce_std_op = ReduceStd(axis=axis, unbiased=unbiased, keep_dims=keep_dims)
    output = reduce_std_op(input_x)
    return output


def outer(x1, x2):
    """
    Return outer product of `x1` and `x2`. If `x1` is a vector of size n and `x2` is a vector of size m,
    then output must be a matrix of size n x m.

    Note:
        This function does not broadcast.

    Args:
        x1 (Tensor): 1-D input vector.
        x2 (Tensor): 1-D input vector.

    Outputs:
        out (Tensor, optional) : optional output matrix.

    Raises:
        TypeError: If `x1` is not a Tensor.
        TypeError: If `x2` is not a Tensor.
        ValueError: Expected 1-D input `x1`, but got n-D.
        ValueError: Expected 1-D input `x2`, but got n-D.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> x1 = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> x2 = Tensor(np.array([1, 2, 3]), mindspore.int32)
        >>> out = ops.outer(x1, x2)
        >>> print(out)
        [[1 2 3]
         [2 4 6]
         [3 6 9]]
    """

    if not isinstance(x1, (Tensor, Tensor_)):
        raise TypeError("the input x1 must be Tensor!")
    if not isinstance(x2, (Tensor, Tensor_)):
        raise TypeError("the input x2 must be Tensor!")
    if len(x1.shape) != 1:
        raise ValueError("the input x1 must be a 1-D vector!")
    if len(x2.shape) != 1:
        raise ValueError("the input x2 must be a 1-D vector!")
    x1 = x1.reshape(-1, 1)
    mul_ops = _get_cache_prim(P.Mul)()
    y = mul_ops(x1, x2)
    return y


def mv(mat, vec):
    """
    Multiplies matrix `mat` and vector `vec`.

    If mat is a :math:`(N, M)` tensor, vec is a 1-D tensor of size :math:`M`, out will be 1-D of size :math:`N`.

    Args:
        mat (Tensor): Input matrix of the tensor. The shape of the tensor is :math:`(N, M)`.
        vec (Tensor): Input vector of the tensor. The shape of the tensor is :math:`(M,)`.

    Outputs:
        Tensor, the shape of the output tensor is :math:`(N,)`.

    Raises:
        TypeError: If `mat`, `vec` is not a Tensor.
        ValueError: If `mat` is not a 2-D Tensor.
            If `vec` is not a 1-D Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> mat = Tensor(np.array([[3., 4.], [1., 6.], [1., 3.]]).astype(np.float32))
        >>> vec = Tensor(np.array([1., 2.]).astype(np.float32))
        >>> output = mv(mat, vec)
        >>> print(output)
        [11. 13. 7.]
    """

    matmul_op = _get_cache_prim(P.MatMul)()
    reshape_op = _get_cache_prim(P.Reshape)()

    if not isinstance(mat, (Tensor, Tensor_)):
        raise TypeError("The input mat must be Tensor.")
    if not isinstance(vec, (Tensor, Tensor_)):
        raise TypeError("The input vec must be Tensor.")
    if len(mat.shape) != 2:
        raise ValueError("The input mat must be 2-D Tensor.")
    if len(vec.shape) != 1:
        raise ValueError("The input vec must be 1-D Tensor.")

    length_vec = get_x_shape(vec.shape)
    vec = reshape_op(vec, (length_vec[0], 1))

    out = matmul_op(mat, vec)
    out = out.T
    out = out[0]
    return out


def lcm(x1, x2):
    """
    Computes least common multiplier of input tensors element-wise.
    The shape of two inputs should be broadcastable, and data type of them should be
    one of: int32, int64

    Inputs:
        - **x1** (Tensor) - The first input tensor.
        - **x2** (Tensor) - The second input tensor.

    Outputs:
        Tensor, the shape is the same as the one after broadcasting, and the data type is one
        with higher digits in the two inputs.

    Raises:
        TypeError: If data type `x1` or `x2` is not int32 or int64.
        ValueError: If shape of two inputs are not broadcastable.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x1 = Tensor(np.array([7, 8, 9]))
        >>> x2 = Tensor(np.array([14, 6, 12]))
        >>> y = ops.lcm(x1, x2)
        >>> print(y)
        [14 24 36]
    """

    lcm_ = _get_cache_prim(Lcm)()
    return lcm_(x1, x2)


def cdist(x, y, p=2.0):
    """
    Computes batched the p-norm distance between each pair of the two collections of row vectors.

    Args:
        x (Tensor): Input tensor of shape :math:`(B, P, M)`.
          Letter :math:`B` represents 0 or positive int number.
          When :math:`B` is equal to 0, it means this dimension can be ignored,
          i.e. shape of the tensor is :math:`(P, M)`.
        y (Tensor): Input tensor of shape :math:`(B, R, M)`.
        p (float): P value for the p-norm distance to calculate between each vector pair, P ∈ [0,∞]. Default: 2.0.

    Returns:
        Tensor, has the same dtype as `x`, which shape is :math:`(B, P, R)`.

    Raises:
        TypeError: If `x` or `y` is not a Tensor.
        TypeError: If dtype of `x` or `y` is neither float16 nor float32.
        TypeError: If `p` is not a float.
        ValueError: If `p` is a negative float.
        ValueError: If dimension of `x` is not the same as `y`.
        ValueError: If dimension of `x` or `y` is neither 2 nor 3.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> x = Tensor(np.array([[[1.0, 1.0], [2.0, 2.0]]]).astype(np.float32))
        >>> y = Tensor(np.array([[[3.0, 3.0], [3.0, 3.0]]]).astype(np.float32))
        >>> output = F.cdist(x, y, 2.0)
        >>> print(output)
        [[[2.8284273 2.8284273]
          [1.4142137 1.4142137]]]
    """
    cdist_ = _get_cache_prim(P.Cdist)(p)
    return cdist_(x, y)


def gcd(x1, x2):
    """
    Computes greatest common divisor of input tensors element-wise.
    The shape of two inputs should be broadcastable, and data type of them should be
    one of: int32, int64

    Inputs:
        - **x1** (Tensor) - The first input tensor.
        - **x2** (Tensor) - The second input tensor.

    Outputs:
        Tensor, the shape is the same as the one after broadcasting, and the data type is one
        with higher digits in the two inputs.

    Raises:
        TypeError: If data type `x1` or `x2` is not int32 or int64.
        ValueError: If shape of two inputs are not broadcastable.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> x1 = Tensor(np.array([7, 8, 9]))
        >>> x2 = Tensor(np.array([14, 6, 12]))
        >>> y = ops.gcd(x1, x2)
        >>> print(y)
        [7 2 3]
    """

    gcd_ = _get_cache_prim(Gcd)()
    return gcd_(x1, x2)


def lerp(start, end, weight):
    """
    Does a linear interpolation of two tensors start and end based on a float or tensor weight.

    If `weight` is a tensor, the shapes of three inputs need to be broadcast;
    If `weight` is a float, the shapes of `start` and `end` need to be broadcast.

    .. math::

        output_{i} = start_{i} + weight_{i} * (end_{i} - start_{i})

    Args:
        start (Tensor): The tensor with the starting points. Data type must be float16 or float32.
        end (Tensor): The tensor with the ending points. Data type must be float16 or float32.
        weight (Union[float, Tensor]): The weight for the interpolation formula. Must be a float
            or a scalar tensor with float16 or float32 data type.

    Returns:
        Tensor, has the same type and shape as input `start`.

    Raises:
        TypeError: If `start` or `end` is not a tensor.
        TypeError: If `weight` is neither scalar(float) nor tensor.
        TypeError: If dtype of `start` or `end` is neither float16 nor float32.
        TypeError: If dtype of `weight` is neither float16 nor float32 when it is a tensor.
        TypeError: If `start` and `end` have different data types.
        TypeError: If `start`, `end` and `weight` have different data types when `weight` is a tensor.
        ValueError: If `end` could not be broadcast to a tensor with shape of `start`.
        ValueError: If `weight` could not be broadcast to tensors with shapes of `start` and `end` when it is a tensor.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> start = Tensor(np.array([1., 2., 3., 4.]), mindspore.float32)
        >>> end = Tensor(np.array([10., 10., 10., 10.]), mindspore.float32)
        >>> output = ops.lerp(start, end, 0.5)
        >>> print(output)
        [5.5 6. 6.5 7. ]
    """
    return lerp_(start, end, weight)


def bernoulli(x, p=0.5, seed=-1):
    """
    Randomly set the elements of output to 0 or 1 with the probability of P which follows the Bernoulli distribution.

    .. math::

        out_{i} ~ Bernoulli(p_{i})

    Args:
        x (Tensor): Tensor of shape :math:`(N,*)` where :math:`*` means, any number of additional dimensions. Data
                    type must be int8, uint8, int16, int32，int64，bool, float32 or float64。
        p (Union[Tensor, float], optional): The shape of p need to be broadcast. The elements of p represent the
                                            probability of setting 1 for the corresponding broadcast position of
                                            the current Tensor. Default: 0.5.
        seed (int, optional): The seed value for random generating. Default: -1.

    Returns:
        Tensor, with the same shape and type as x.

    Raises:
        TypeError: If `seed` is not an int.
        TypeError: If dtype of `input` is not one of: int8, uint8, int16, int32，int64，bool, float32, float64.
        TypeError: If dtype of `input` is not one of: float32, float64.
        ValueError: If `p` is not in range [0, 1].
        ValueError: If `seed` is less than 0.

    Supported Platforms:
        ``GPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> import mindspore.ops as ops
        >>> input_x = Tensor(np.array([1, 2, 3]), mindspore.int8)
        >>> output = ops.bernoulli(input_x, p=1.0)
        >>> print(output)
        [1 1 1]
        >>> input_p = Tensor(np.array([0.0, 1.0, 1.0]), mindspore.float32)
        >>> output = ops.bernoulli(input_x, input_p)
        >>> print(output)
        [0 1 1]
    """
    bernoulli_ = _get_cache_prim(Bernoulli)(seed)
    return bernoulli_(x, p)


def bessel_i1(x):
    r"""
    Computes the Bessel i1 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1, -0.5, 0.5, 1]), mindspore.float32)
        >>> output = ops.bessel_i1(x)
        >>> print(output)
        [-0.5651591, -0.25789431, 0.25789431, 0.5651591]
    """
    return bessel_i1_(x)


def bessel_i1e(x):
    r"""
    Computes the Bessel i1e function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([-1, -0.5, 0.5, 1]), mindspore.float32)
        >>> output = ops.bessel_i1e(x)
        >>> print(output)
        [-0.20791042, -0.15642083, 0.15642083, 0.20791042]
    """
    return bessel_i1e_(x)


def bessel_k1(x):
    r"""
    Computes the Bessel k1 function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_k1(x)
        >>> print(output)
        [1.65644112, 0.60190723, 0.13986588, 0.0124835]
    """
    return bessel_k1_(x)


def bessel_k1e(x):
    r"""
    Computes the Bessel k1e function of x element-wise.

    Args:
        x (Tensor): The input tensor. The data type must be float16, float32 or float64.
            :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    Returns:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16, float32 or float64.

    Supported Platforms:
        ``CPU``

    Examples:
        >>> x = Tensor(np.array([0.5, 1., 2., 4.]), mindspore.float32)
        >>> output = ops.bessel_k1e(x)
        >>> print(output)
        [2.73100971, 1.63615349, 1.03347685, 0.68157595]
    """
    return bessel_k1e_(x)


@constexpr
def _check_input_dtype(param_name, input_dtype, allow_dtypes, cls_name):
    validator.check_type_name(param_name, input_dtype, allow_dtypes, cls_name)


def deg2rad(x):
    """
    Calculates a new tensor with each of the elements of `x` converted from angles in degrees to radians.

    Args:
        - **x** (Tensor[Number]) - The input tensor. It must be a positive-definite matrix.
          With float16, float32 or float64 data type.

    Outputs:
        Tensor, has the same dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` isn't float16, float32 or float64.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([[90.0, -90.0], [180.0, -180.0], [270.0, -270.0]]).astype(np.float32))
        >>> op = nn.Deg2Rad()
        >>> output = op(x)
        >>> print(output)
        [[ 1.5707964 -1.5707964]
         [ 3.1415927 -3.1415927]
         [ 4.712389  -4.712389 ]]
    """
    if not isinstance(x, (Tensor, Tensor_)):
        raise TypeError("The input x must be tensor")
    dtype_op = _get_cache_prim(P.DType)()
    x_dtype = dtype_op(x)
    _check_input_dtype("x", x_dtype, [mstype.float16, mstype.float32, mstype.float64], "")
    if x_dtype == mstype.float16:
        out = x * (Tensor(math.pi / 180.0).astype(mstype.float16))
    else:
        out = x * math.pi / 180.0
    return out


def rad2deg(x):
    """
    Returns a new tensor with each of the elements of `x` converted from angles in radians to degrees.

    Args:
        x (Tensor): The input tensor.

    Outputs:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` isn't float16, float32 or float64.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> from mindspore import Tensor
        >>> import mindspore.ops as ops
        >>> x = Tensor([[6.283, -3.142],[1.570, -6.283],[3.142, -1.570]], mindspore.float32)
        >>> output = rad2deg(x)
        >>> print(output)
        [[ 359.98935 -180.02333]
         [  89.95438 -359.98935]
         [ 180.02333  -89.95438]]

    """
    if not isinstance(x, (Tensor, Tensor_)):
        raise TypeError("The input x must be tensor")
    dtype_op = _get_cache_prim(P.DType)()
    x_dtype = dtype_op(x)
    _check_input_dtype("x", x_dtype, [mstype.float16, mstype.float32, mstype.float64], "")
    if x_dtype == mstype.float16:
        out = x * (Tensor(180.0 / math.pi).astype(mstype.float16))
    else:
        out = x * 180.0 / math.pi
    return out


def frac(x):
    """
    Calculates the fractional part of each element in the input

    Inputs:
        - x (Tensor) - x is a tensor.

    Outputs:
        Tensor, has the same shape and type as input.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> from mindspore.common import dtype as mstype
        >>> import mindspore.ops as ops
        >>> x = Tensor([2, 4.2, -2.5], mstype.float16)
        >>> output = frac(x)
        >>> print(output)
        [ 0.      0.1992 -0.5   ]
    """
    frac_op = P.Mod()
    return frac_op(x, 1)


#####################################
# Reduction Operation Functions.
#####################################


@constexpr
def _create_cummin_perm(axis, x_shape):
    """Insure axis is in [-len(x_shape),len(s_shape)-1]"""
    len_axis = len(x_shape)
    if not isinstance(axis, int):
        raise TypeError(f"The date type of 'axis' must be Int, but got {axis}.")
    if axis < -len_axis or axis > len_axis:
        raise ValueError(f"The value of axis must be in [{-len_axis}, {len_axis}], but got {axis}.")
    prem = [i for i in range(len_axis)]
    if axis < 0:
        axis = axis + len_axis
    prem[0], prem[axis] = axis, 0
    prem = tuple(prem)
    return prem


def cummin(x, axis):
    r"""
    Returns a tuple (values,indices) where 'values' is the cumulative minimum value of input Tensor `x`
    along the dimension `axis`, and `indices` is the index location of each minimum value.

    .. math::
        \begin{array}{ll} \\
            y{i} = min(x{1}, x{2}, ... , x{i})
        \end{array}

    Args:
        x (Tensor): The input Tensor, rank of `x` > 0.
        axis (int): The dimension to do the operation over. The value of `axis` must be in the range
            `[-x.ndim, x.ndim - 1]`.

    Returns:
        tuple [Tensor], tuple of 2 Tensors, containing the cumulative minimum of elements and the index,
        The shape of each output tensor is the same as input `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If `axis` is not an int.
        ValueError: If `axis` is out the range of `[-x.ndim, x.ndim - 1]`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore import Tensor, ops
        >>> import mindspore
        >>> a = Tensor([-0.2284, -0.6628,  0.0975,  0.2680, -1.3298, -0.4220], mindspore.float32)
        >>> output = ops.cummin(a, axis=0)
        >>> print(output[0])
        [-0.2284 -0.6628 -0.6628 -0.6628 -1.3298 -1.3298]
        >>> print(output[1])
        [0 1 1 1 4 4]
    """
    cummin_op = _get_cache_prim(Cummin)(axis=0)
    if axis == 0:
        out1, out2 = cummin_op(x)
    else:
        transpose = _get_cache_prim(P.Transpose)()
        _shape_op = _get_cache_prim(P.Shape)()
        x_shape = _shape_op(x)
        prem = _create_cummin_perm(axis, x_shape)
        x = transpose(x, prem)
        out1, out2 = cummin_op(x)
        out1 = transpose(out1, prem)
        out2 = transpose(out2, prem)
    return [out1, out2]


def cummax(x, axis):
    r"""
    Returns a tuple (values,indices) where 'values' is the cumulative maximum value of input Tensor `x`
    along the dimension `axis`, and `indices` is the index location of each maximum value.

    .. math::
        \begin{array}{ll} \\
            y{i} = max(x{1}, x{2}, ... , x{i})
        \end{array}

    Args:
        x (Tensor): The input Tensor, rank of `x` > 0.
        axis (int): The dimension to do the operation over. The value of `axis` must be in the range
            `[-x.ndim, x.ndim - 1]`.

    Returns:
        tuple [Tensor], tuple of 2 Tensors, containing the cumulative maximum of elements and the index,
        The shape of each output tensor is the same as input `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If `axis` is not an int.
        ValueError: If `axis` is out the range of `[-x.ndim, x.ndim - 1]`.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> import mindspore.ops as ops
        >>> x = Tensor(np.array([[3, 4, 6, 10], [1, 6, 7, 9], [4, 3, 8, 7], [1, 3, 7, 9]]).astype(np.float32))
        >>> output = ops.cummax(x, axis=0)
        >>> print(output[0])
        [[ 3.  4.  6. 10.]
         [ 3.  6.  7. 10.]
         [ 4.  6.  8. 10.]
         [ 4.  6.  8. 10.]]
        >>> print(output[1])
        [[0 0 0 0]
         [0 1 1 0]
         [2 1 2 0]
         [2 1 2 0]]
    """
    _cummax = _get_cache_prim(ops.Cummax)(axis=axis)
    return _cummax(x)


def sparse_segment_mean(x, indices, segment_ids):
    """
    Computes the mean along sparse segments of a tensor.
    """
    return sparse_segment_mean_(x, indices, segment_ids)


def logsumexp(x, axis, keep_dims=False):
    r"""
    Reduces a dimension of a tensor by calculating exponential for all elements in the dimension,
    then calculate logarithm of the sum.

    .. math::

        logsumexp(x) = \log(\sum(e^(x-x_{max}))) + x_{max}

    Args:
        x (Tensor): The input tensor. With float16 or float32 data type.
        axis (Union[int, tuple(int), list(int)]): The dimensions to reduce. Default: (), reduce all dimensions.
            Only constant value is allowed.
        keep_dims (bool): If True, keep these reduced dimensions and the length is 1.
            If False, don't keep these dimensions.
            Default : False.

    Outputs:
        Tensor, has the same dtype as the `x`.

        - If axis is (), and keep_dims is False,
          the output is a 0-D tensor representing the sum of all elements in the input tensor.
        - If axis is int, set as 2, and keep_dims is False,
          the shape of output is :math:`(x_1, x_3, ..., x_R)`.
        - If axis is tuple(int), set as (2, 3), and keep_dims is False,
          the shape of output is :math:`(x_1, x_4, ..., x_R)`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.random.randn(3, 4, 5, 6).astype(np.float32))
        >>> op = ops.logsumexp(x, 1, keep_dims=True)
        >>> output = op(x)
        >>> print(output.shape)
        (3, 1, 5, 6)
    """
    _exp = _get_cache_prim(P.Exp)()
    _reduce_sum = _get_cache_prim(P.ReduceSum)(keep_dims)
    _log = _get_cache_prim(P.Log)()

    x_max = x.max()
    x_exp = _exp(x - x_max)
    x_sumexp = _reduce_sum(x_exp, axis)
    x_logsumexp = _log(x_sumexp)
    return x_logsumexp + x_max


def reduce_min(x, axis, keep_dims=False):
    r"""
    Reduces a dimension of a tensor by the minimum value in the dimension, by default. And also can
    reduce a dimension of `x` along the axis. Determine whether the dimensions of the output and input are the same by
    controlling `keep_dims`.

    Args:
        keep_dims (bool): If true, keep these reduced dimensions and the length is 1.
                          If false, don't keep these dimensions. Default: False.
        x (Tensor[Number]): The input tensor. The dtype of the tensor to be reduced is number.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        axis (Union[int, tuple(int), list(int)]): The dimensions to reduce. Default: (), reduce all dimensions.
          Only constant value is allowed. Must be in the range [-rank(`x`), rank(`x`)).

    Raises:
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `x` is not a Tensor.
        TypeError: If `axis` is not one of the following: int, tuple or list.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.random.randn(3, 4, 5, 6).astype(np.float32))
        >>> output = ops.reduce_min(x, 1, keep_dims=True)
        >>> result = output.shape
        >>> print(result)
        (3, 1, 5, 6)
        >>> # case 1: Reduces a dimension by the minimum value of all elements in the dimension.
        >>> x = Tensor(np.array([[[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3]],
        ...                      [[4, 4, 4, 4, 4, 4], [5, 5, 5, 5, 5, 5], [6, 6, 6, 6, 6, 6]],
        ...                      [[7, 7, 7, 7, 7, 7], [8, 8, 8, 8, 8, 8], [9, 9, 9, 9, 9, 9]]]), mindspore.float32)
        >>> output = ops.reduce_min(x)
        >>> print(output)
        [[[1.]]]
        >>> print(output.shape)
        (1, 1, 1)
        >>> # case 2: Reduces a dimension along axis 0.
        >>> output = opops.reduce_min(x, 0)
        >>> print(output)
        [[[1. 1. 1. 1. 1. 1.]
          [2. 2. 2. 2. 2. 2.]
          [3. 3. 3. 3. 3. 3.]]]
        >>> # case 3: Reduces a dimension along axis 1.
        >>> output = ops.reduce_min(x, 1)
        >>> print(output)
        [[[1. 1. 1. 1. 1. 1.]]
         [[4. 4. 4. 4. 4. 4.]]
         [[7. 7. 7. 7. 7. 7.]]]
        >>> # case 4: Reduces a dimension along axis 2.
        >>> output = ops.reduce_min(x, 2)
        >>> print(output)
        [[[1.]
          [2.]
          [3.]]
         [[4.]
          [5.]
          [6.]]
         [[7.]
          [8.]
          [9.]]]
    """
    return P.ReduceMin(keep_dims)(x, axis)


def reduce_max(x, axis, keep_dims=False):
    r"""
    Reduces a dimension of a tensor by the maximum value in this dimension, by default. And also can
    reduce a dimension of `x` along the axis. Determine whether the dimensions of the output and input are the same by
    controlling `keep_dims`.

    Args:
        keep_dims (bool): If true, keep these reduced dimensions and the length is 1.
                          If false, don't keep these dimensions. Default: False.
        x (Tensor[Number]): The input tensor. The dtype of the tensor to be reduced is number.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        axis (Union[int, tuple(int), list(int)]): The dimensions to reduce. Default: (), reduce all dimensions.
          Only constant value is allowed. Must be in the range [-rank(`x`), rank(`x`)).

    Raises:
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `x` is not a Tensor.
        TypeError: If `axis` is not one of the following: int, tuple or list.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.random.randn(3, 4, 5, 6).astype(np.float32))
        >>> output = ops.reduce_max(x, 1, keep_dims=True)
        >>> result = output.shape
        >>> print(result)
        (3, 1, 5, 6)
        >>> # case 1: Reduces a dimension by the maximum value of all elements in the dimension.
        >>> x = Tensor(np.array([[[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3]],
        ...                      [[4, 4, 4, 4, 4, 4], [5, 5, 5, 5, 5, 5], [6, 6, 6, 6, 6, 6]],
        ...                      [[7, 7, 7, 7, 7, 7], [8, 8, 8, 8, 8, 8], [9, 9, 9, 9, 9, 9]]]), mindspore.float32)
        >>> output = ops.reduce_max(x)
        >>> print(output)
        [[[9.]]]
        >>> print(output.shape)
        (1, 1, 1)
        >>> # case 2: Reduces a dimension along axis 0.
        >>> output = ops.reduce_max(x, 0)
        >>> print(output)
        [[[7. 7. 7. 7. 7. 7.]
          [8. 8. 8. 8. 8. 8.]
          [9. 9. 9. 9. 9. 9.]]]
        >>> # case 3: Reduces a dimension along axis 1.
        >>> output = ops.reduce_max(x, 1)
        >>> print(output)
        [[[3. 3. 3. 3. 3. 3.]]
         [[6. 6. 6. 6. 6. 6.]]
         [[9. 9. 9. 9. 9. 9.]]]
        >>> # case 4: Reduces a dimension along axis 2.
        >>> output = ops.reduce_max(x, 2)
        >>> print(output)
        [[[1.]
          [2.]
          [3.]]
         [[4.]
          [5.]
          [6.]]
         [[7.]
          [8.]
          [9.]]]
    """
    return P.ReduceMax(keep_dims)(x, axis)


def reduce_mean(x, axis, keep_dims=False):
    r"""
    Reduces a dimension of a tensor by averaging all elements in the dimension, by default. And also can reduce
    a dimension of `x` along the axis. Determine whether the dimensions of the output and input are the same by
    controlling `keep_dims`.

    Args:
        keep_dims (bool): If true, keep these reduced dimensions and the length is 1.
                          If false, don't keep these dimensions. Default: False.
        x (Tensor[Number]): The input tensor. The dtype of the tensor to be reduced is number.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        axis (Union[int, tuple(int), list(int)]): The dimensions to reduce. Default: (), reduce all dimensions.
          Only constant value is allowed. Must be in the range [-rank(`x`), rank(`x`)).

    Raises:
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `x` is not a Tensor.
        TypeError: If `axis` is not one of the following: int, tuple or list.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.random.randn(3, 4, 5, 6).astype(np.float32))
        >>> output = ops.reduce_mean(x, 1, keep_dims=True)
        >>> result = output.shape
        >>> print(result)
        (3, 1, 5, 6)
        >>> # case 1: Reduces a dimension by averaging all elements in the dimension.
        >>> x = Tensor(np.array([[[2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2]],
        ... [[4, 4, 4, 4, 4, 4], [5, 5, 5, 5, 5, 5], [6, 6, 6, 6, 6, 6]],
        ... [[6, 6, 6, 6, 6, 6], [8, 8, 8, 8, 8, 8], [10, 10, 10, 10, 10, 10]]]),
        ... mindspore.float32)
        >>> output = ops.reduce_mean(x)
        >>> print(output)
        [[[5.]]]
        >>> print(output.shape)
        (1, 1, 1)
        >>> # case 2: Reduces a dimension along the axis 0
        >>> output = ops.reduce_mean(x, 0)
        >>> print(output)
        [[[4. 4. 4. 4. 4. 4.]
          [5. 5. 5. 5. 5. 5.]
          [6. 6. 6. 6. 6. 6.]]]
        >>> # case 3: Reduces a dimension along the axis 1
        >>> output = ops.reduce_mean(x, 1)
        >>> print(output)
        [[[2. 2. 2. 2. 2. 2.]]
         [[5. 5. 5. 5. 5. 5.]]
         [[8. 8. 8. 8. 8. 8.]]]
        >>> # case 4: Reduces a dimension along the axis 2
        >>> output = ops.reduce_mean(x, 2)
        >>> print(output)
        [[[ 2.]
          [ 2.]
          [ 2.]]
         [[ 4.]
          [ 5.]
          [ 6.]]
         [[ 6.]
          [ 8.]
          [10.]]]
    """

    return P.ReduceMean(keep_dims)(x, axis)


def reduce_prod(x, axis, keep_dims=False):
    r"""
    Reduces a dimension of a tensor by multiplying all elements in the dimension, by default. And also can
    reduce a dimension of `x` along the axis. Determine whether the dimensions of the output and input are the same by
    controlling `keep_dims`.

    Args:
        keep_dims (bool): If true, keep these reduced dimensions and the length is 1.
                          If false, don't keep these dimensions. Default: False.
        x (Tensor[Number]): The input tensor. The dtype of the tensor to be reduced is number.
          :math:`(N,*)` where :math:`*` means, any number of additional dimensions, its rank should be less than 8.
        axis (Union[int, tuple(int), list(int)]): The dimensions to reduce. Default: (), reduce all dimensions.
          Only constant value is allowed. Must be in the range [-rank(`x`), rank(`x`)).

    Raises:
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `x` is not a Tensor.
        TypeError: If `axis` is not one of the following: int, tuple or list.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.random.randn(3, 4, 5, 6).astype(np.float32))
        >>> output = ops.reduce_prod(x, 1, keep_dims=True)
        >>> result = output.shape
        >>> print(result)
        (3, 1, 5, 6)
        >>> # case 1: Reduces a dimension by multiplying all elements in the dimension.
        >>> x = Tensor(np.array([[[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3]],
        ...                      [[4, 4, 4, 4, 4, 4], [5, 5, 5, 5, 5, 5], [6, 6, 6, 6, 6, 6]],
        ...                      [[7, 7, 7, 7, 7, 7], [8, 8, 8, 8, 8, 8], [9, 9, 9, 9, 9, 9]]]), mindspore.float32)
        >>> output = ops.reduce_prod(x)
        >>> print(output)
        [[[2.2833798e+33]]]
        >>> print(output.shape)
        (1, 1, 1)
        >>> # case 2: Reduces a dimension along axis 0.
        >>> output = ops.reduce_prod(x, 0)
        >>> print(output)
        [[[ 28.  28.  28.  28.  28.  28.]
          [ 80.  80.  80.  80.  80.  80.]
          [162. 162. 162. 162. 162. 162.]]]
        >>> # case 3: Reduces a dimension along axis 1.
        >>> output = ops.reduce_prod(x, 1)
        >>> print(output)
        [[[  6.   6.   6.   6.   6.   6.]]
         [[120. 120. 120. 120. 120. 120.]]
         [[504. 504. 504. 504. 504. 504.]]]
        >>> # case 4: Reduces a dimension along axis 2.
        >>> output = ops.reduce_prod(x, 2)
        >>> print(output)
        [[[1.00000e+00]
          [6.40000e+01]
          [7.29000e+02]]
         [[4.09600e+03]
          [1.56250e+04]
          [4.66560e+04]]
         [[1.17649e+05]
          [2.62144e+05]
          [5.31441e+05]]]
    """
    return P.ReduceProd(keep_dims)(x, axis)


def norm(input_x, axis, p=2, keep_dims=False, epsilon=1e-12):
    r"""
    Returns the matrix norm or vector norm of a given tensor.

    .. math::
        output = sum(abs(input)**p)**(1/p)

    Args:
        input_x (Tensor): Input tensor. The dtype must be float32 or float16.
        axis (Union[int,list,tuple]): Specifies which dimension or dimensions of input to calculate the norm across.
        p (int): The order of norm. Default: 2. `p` is greater than or equal to 0.
        keep_dims (bool): Whether the output tensors have dim retained or not. Default: False.
        epsilon (float): A value added to the denominator for numerical stability. Default: 1e-12.

    Returns:
        Tensor, has the same dtype as `input`, which shape depends on the args axis. For example, if the size of input
        is (2, 3, 4), axis is [0, 1], Outputs' shape will be (4,).

    Raises:
        TypeError: If `input` is not a Tensor.
        TypeError: If dtype of `input` is not one of: float16, float32.
        TypeError: If `p` is not an int.
        TypeError: If `axis` is not an int, a tuple or a list.
        TypeError: If `axis` is a tuple or a list, but the element of `axis` is not an int.
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `epsilon` is not a float.
        ValueError: If the element of `axis` is out of the range [-len(input.shape), len(input.shape)).
        ValueError: If the length of shape of `axis` is bigger than the length of shape of `input`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]).astype(np.float32))
        >>> output = ops.norm(input_x, [0, 1], p=2)
        >>> print(output)
        [ 9.165152 10.954452]
    """
    lp_norm_inner = _get_cache_prim(P.LpNorm)(axis, p, keep_dims, epsilon)
    return lp_norm_inner(input_x)


def renorm(input_x, p, dim, maxnorm):
    """
    Renormalizes the sub-tensors along dimension `dim`, and each sub-tensor's p-norm should not exceed the
    'maxnorm'. The values of current sub-tensor don't need change if the p-norm of the sub-tensor is less than
    `maxnorm`. Otherwise the sub-tensor needs to be modified to the original value of the corresponding position
    divided by the p-norm of the substensor and then multiplied by `maxnorm`.

    Args:
        input_x: A Tensor, types: float32 or float16.
        p (int): P-norm.
        dim (int): The dimension that expected to get the slice-tensor.
        maxnorm (float): Max norm.

    Returns:
        Tensor, has the same dtype and shape as input_x.

    Raises:
        TypeError: If dtype of `p` is not int.
        TypeError: If dtype of `dim` is not int.
        TypeError: If dtype of `maxnorm` is not float32.
        ValueError: If the value of `p` less than 1.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Example:
        >>> x = Tensor(np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]]), mindspore.float32)
        >>> y = ops.renorm(x, p=1, dim=0, maxnorm=5.)
        >>> print(y)
        [[1.       1.        1.        1.       ]
        [1.6666666 1.6666666 1.6666666 1.6666666]
        [1.6666667 1.6666667 1.6666667 1.6666667]]
    """
    renorm_ = _get_cache_prim(Renorm)(p, dim, maxnorm)
    return renorm_(input_x)


@constexpr
def _check_attr_dtype(param_name, input_dtype, allow_dtypes, cls_name):
    validator.check_value_type(param_name, input_dtype, allow_dtypes, cls_name)


@constexpr
def _check_positive_float(arg_value, arg_name, cls_name):
    validator.check_positive_float(arg_value, arg_name, cls_name)


def gumbel_softmax(logits, tau=1, hard=False, dim=-1):
    r"""
    Returns the samples from the Gumbel-Softmax distribution and optionally discretizes. If `hard = True`, the returned
    samples will be one-hot, otherwise it will be probability distributions that sum to 1 across `dim`.

    Args:
        logits (Tensor): Unnormalized log probabilities. The data type must be float16 or float32.
        tau (float): The scalar temperature, which is a positive number. Default: 1.0.
        hard (bool): if `True`, the returned samples will be discretized as one-hot vectors, but will be differentiated
          as if it is the soft sample in autograd. Default: False.
        dim (int): Dim for softmax to compute. Default: -1.

    Returns:
        Tensor, has the same dtype and shape as `logits`.

    Raises:
        TypeError: If `logits` is not a Tensor.
        TypeError: If dtype of `logits` is not one of: float16, float32.
        TypeError: If `tau` is not an float.
        TypeError: If `hard` is not a bool.
        TypeError: If `dim` is not a int.
        ValueError: If If `tau` is not positive.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> output = ops.gumbel_softmax(input_x, 1.0, True, -1)
        >>> print(output.shape)
        (2, 3)
    """
    if not isinstance(logits, (Tensor, Tensor_)):
        raise TypeError("The input logits must be tensor")
    dtype_op = _get_cache_prim(P.DType)()
    logits_dtype = dtype_op(logits)
    _check_input_dtype("logits", logits_dtype, [mstype.float16, mstype.float32], "gumbel_softmax")
    _check_attr_dtype("tau", tau, [float], "gumbel_softmax")
    _check_attr_dtype("hard", hard, [bool], "gumbel_softmax")
    _check_attr_dtype("dim", dim, [int], "gumbel_softmax")
    _check_positive_float(tau, "tau", "gumbel_softmax")

    shape_op = _get_cache_prim(P.Shape)()
    cast_op = _get_cache_prim(P.Cast)()
    log_op = _get_cache_prim(P.Log)()
    const_op = _get_cache_prim(P.ScalarToArray)()
    softmax_op = _get_cache_prim(P.Softmax)(dim)
    onehot_op = _get_cache_prim(P.OneHot)(dim)

    sample_shape = shape_op(logits)
    uniform = C.uniform(sample_shape, const_op(0.0), const_op(1.0))
    uniform = cast_op(uniform, logits_dtype)
    gumbel = neg_tensor(log_op(neg_tensor(log_op(uniform))))
    gumbel = (logits + gumbel) / tau
    y_soft = softmax_op(gumbel)
    if hard:
        index = y_soft.argmax(axis=dim)
        y_hard = onehot_op(index, sample_shape[dim], Tensor(1, logits_dtype), Tensor(0, logits_dtype))
        ret = y_hard - ops.stop_gradient(y_soft) + y_soft
    else:
        ret = y_soft
    return ret


def stft(x, n_fft, hop_length=None, win_length=None, window=None, center=True,
         pad_mode="REFLECT", normalized=False, onesided=None, return_complex=None):
    r"""
    STFTs can be used as a way of quantifying the change
    of a nonstationary signal’s frequency and phase content over time.

    Args:
        x (Tensor): Time sequence of stft, must be either a 1-D time tensor or a 2-D tensor.
        n_fft (int): The size of Fourier transform.
        hop_length (int, optional): The distance between neighboring sliding window
            frames. Default: ``None`` (treated as equal to ``floor(n_fft / 4)``).
        win_length (int, optional): the size of window frame and STFT filter.
            Default: ``None``  (treated as equal to :attr:`n_fft`).
        window (Tensor, optional): the optional window function.
            Default: ``None`` (treated as window of all :math:`1` s).
        center (bool, optional): whether to pad :attr:`input` on both sides.
            Default: ``True``.
        pad_mode (string, optional): controls the padding method used when
            :attr:`center` is ``True``. Default: ``"REFLECT"``.
        normalized (bool, optional): controls whether to return the normalized STFT results
             Default: ``False``.
        onesided (bool, optional): controls whether to return half of results to
            avoid redundancy for real inputs.
            Default: ``True`` for real :attr:`input` and :attr:`window`, ``False`` otherwise.
        return_complex (bool, optional): whether to return a complex tensor, or
            a real tensor with an extra last dimension for the real and
            imaginary components.
            Default: ``True`` for complex :attr:`input` or :attr:`window`, ``False`` otherwise.

    Returns:
        Tensor.

        - **output** (Tensor) - A tensor containing the STFT result with shape described above.

    Raises:
        TypeError: If the x is not a tensor.
        ValueError: If x arguments have values not specified above.

    Examples:
        >>> x = Tensor(np.random.rand(2,7192), mindspore.float32)
        >>> output = ops.stft(n_fft=64, x=x)
        >>> print(output.shape)
        (2, 33, 450, 2)
    """
    if hop_length is None:
        hop_length = int(np.floor(n_fft / 4))
    if win_length is None:
        win_length = int(np.floor(n_fft))
    if window is None:
        window = P.Ones()((win_length,), mstype.float32)

    def _is_complex(x):
        dtype = P.DType()
        return dtype(x) in [mstype.complex64, mstype.complex128]

    if onesided is None:
        onesided = (not _is_complex(x)) and (not _is_complex(window))
    if return_complex is None:
        return_complex = _is_complex(x) or _is_complex(window)
    if center:
        signal_dim = len(x.shape)
        pad = n_fft // 2
        if signal_dim == 1:
            x = layer.Pad(((pad, pad)), pad_mode)(x)
        elif signal_dim == 2:
            x = layer.Pad(((0, 0), (pad, pad)), pad_mode)(x)
        else:
            raise ValueError(
                f"Expected a 1-D tensor or a 2-D tensor, but got {signal_dim}")
    stft_ = STFT(n_fft, hop_length, win_length,
                 normalized, onesided, return_complex)
    return stft_(x, window)


def _check_same_type(dtype1, dtype2):
    return dtype1 == dtype2


@constexpr
def _max(*args):
    """Returns the maximum value."""
    return max(*args)


@constexpr
def _min(*args):
    """Returns the minimum value."""
    return min(*args)


@constexpr
def _infer_shape_rem(shape1, shape2, ndim1, ndim2, transpose_b):
    """Infers the shape of the last two dimensions after performing matmul."""
    shape_rem = []
    if ndim1 >= 2:
        shape_rem.append(shape1[-2])
    if transpose_b:
        if ndim2 >= 2:
            shape_rem.append(shape2[-2])
    else:
        if ndim1 >= 1:
            shape_rem.append(shape2[-1])
    return tuple(shape_rem)


@constexpr
def _check_matmul_shapes(shape1, shape2, prim_name=None):
    """Checks shape1 and shape2 are valid to perform matmul, and returns output shape after broadcasting."""
    msg_prefix = f"For '{prim_name}', the" if prim_name else "The"
    ndim1, ndim2 = len(shape1), len(shape2)
    if ndim1 < 1 or ndim2 < 1:
        raise ValueError(f"{msg_prefix} dimension of input operands must be at least 1, but got "
                         f"the length of shape1: {ndim1}, the length of shape2: {ndim2}.")
    if ndim2 >= 2 and shape1[-1] != shape2[-2]:
        raise ValueError(f"{msg_prefix} shape1[-1] must be equal to shape2[-2] when the length of shape2 "
                         f"is greater than or equal to 2, but got shape1[-1]: {shape1[-1]}, "
                         f"shape2[-2]: {shape2[-2]}.")
    shape_out = deque()
    for items in zip_longest(reversed(shape1[:-2]), reversed(shape2[:-2]), fillvalue=1):
        max_size = max(items)
        if any(item not in (1, max_size) for item in items):
            raise ValueError(f"{msg_prefix} operands could not be broadcast together with shape1 {shape1} and "
                             f"shape2 {shape2}.")
        shape_out.appendleft(max_size)
    return tuple(shape_out)


@constexpr
def _tile_size(shape, out_shape, ndim):
    """Returns tile_size such that shape*tile_size = out_shape"""
    size = [1] * ndim
    for idx, (i, j) in enumerate(zip(shape, out_shape)):
        if i != j:
            size[idx] = j
    return tuple(size)


@constexpr
def _check_need_broadcast(shape1, shape2):
    """Returns True if broadcast is necessary for batchmatmul."""
    return shape1[:-2] != shape2[:-2]


def _expand(x, ndim):
    """Expand x to ndim from axis, which can be 0 or -1."""
    rank_op = _get_cache_prim(P.Rank)()
    expand_dims_op = _get_cache_prim(P.ExpandDims)()
    while rank_op(x) < ndim:
        x = expand_dims_op(x, 0)
    return x


def _broadcast_to(x, shape_cur, shape_to, ndim_to):
    """Broadcasts x from shape_cur to shape_to."""
    tile_op = _get_cache_prim(P.Tile)()
    size = _tile_size(shape_cur, shape_to, ndim_to)
    return tile_op(x, size)


def matmul(x1, x2):
    """
    Returns the matrix product of two tensors.

    Note:
        Numpy arguments `out`, `casting`, `order`, `subok`, `signature`, and `extobj` are
        not supported.
        On GPU, the supported dtypes are np.float16 and np.float32.
        On CPU, the supported dtypes are np.float16 and np.float32.

    Args:
        x1 (Tensor): Input tensor, scalar not allowed.
          The last dimension of `x1` must be the same size as the second last dimension of `x2`.
          And the shape of x1 and x2 could be broadcast.
        x2 (Tensor): Input tensor, scalar not allowed.
          The last dimension of `x1` must be the same size as the second last dimension of `x2`.
          And the shape of x1 and x2 could be broadcast.

    Returns:
        Tensor or scalar, the matrix product of the inputs. This is a scalar only
        when both `x1`, `x2` are 1-d vectors.

    Raises:
        ValueError: If the last dimension of `x1` is not the same size as the
            second-to-last dimension of `x2`, or if a scalar value is passed in.
        ValueError: If the shape of `x1` and `x2` could not broadcast together.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore import Tensor, ops
        >>> import mindspore
        >>> # case 1 : Reasonable application of broadcast mechanism
        >>> x1 = Tensor(np.arange(2*3*4).reshape(2, 3, 4), mindspore.float32)
        >>> x2 = Tensor(np.arange(4*5).reshape(4, 5), mindspore.float32)
        >>> output = ops.matmul(x1, x2)
        >>> print(output)
        [[[  70.   76.   82.   88.   94.]
        [ 190.  212.  234.  256.  278.]
        [ 310.  348.  386.  424.  462.]]
        [[ 430.  484.  538.  592.  646.]
        [ 550.  620.  690.  760.  830.]
        [ 670.  756.  842.  928. 1014.]]]
        >>> print(output.shape)
        (2, 3, 5)
        >>> # case 2 : the rank of `x1` is 1
        >>> x1 = Tensor(np.ones([1, 2]), mindspore.float32)
        >>> x2 = Tensor(np.ones([2,]), mindspore.float32)
        >>> output = ops.matmul(x1, x2)
        >>> print(output)
        [2.]
        >>> print(output.shape)
        (1,)
    """
    dtype_op = _get_cache_prim(P.DType)()
    rank_op = _get_cache_prim(P.Rank)()
    shape_op = _get_cache_prim(P.Shape)()
    reshape_op = _get_cache_prim(P.Reshape)()

    dtype1 = dtype_op(x1)
    dtype2 = dtype_op(x2)
    if not _check_same_type(dtype1, dtype2):
        x1 = x1.astype(mstype.float32)
        x2 = x2.astype(mstype.float32)

    ndim1_orig, ndim2_orig = rank_op(x1), rank_op(x2)
    shape1_orig, shape2_orig = shape_op(x1), shape_op(x2)
    transpose_b = ndim2_orig == 1
    shape_backbone = _check_matmul_shapes(shape1_orig, shape2_orig, 'matmul')
    # infers the shape of the output
    shape_out = shape_backbone + _infer_shape_rem(shape1_orig, shape2_orig,
                                                  ndim1_orig, ndim2_orig, transpose_b)

    _matmul = _get_cache_prim(P.MatMul)(False, transpose_b)
    _batch_matmul = _get_cache_prim(P.BatchMatMul)(False, transpose_b)

    x1 = _expand(x1, 2)
    x2 = _expand(x2, 2)
    if rank_op(x2) == 2:
        if rank_op(x1) > 2:
            x1 = reshape_op(x1, (-1, shape1_orig[-1]))
        res = _matmul(x1, x2)
    else:
        # broadcasts x1.shape[:-2] with x2.shape[:-2]
        ndim_aligned = _max(ndim1_orig, ndim2_orig)
        x1 = _expand(x1, ndim_aligned)
        x2 = _expand(x2, ndim_aligned)
        shape1_aligned, shape2_aligned = shape_op(x1), shape_op(x2)
        x1 = _broadcast_to(x1, shape1_aligned[:-2], shape_backbone, ndim_aligned)
        x2 = _broadcast_to(x2, shape2_aligned[:-2], shape_backbone, ndim_aligned)
        res = _batch_matmul(x1, x2)

    return reshape_op(res, shape_out)


def baddbmm(x, batch1, batch2, beta=1, alpha=1):
    r"""
    Performs a batch matrix-matrix product of matrices in batch1 and batch2. input is added to the final result.
    The formula is defined as follows:

    .. math::
        \text{out}_{i} = \beta \text{input}_{i} + \alpha (\text{batch1}_{i} \mathbin{@} \text{batch2}_{i})

    Args:
        x (Tensor): The tensor to be added.
        batch1 (Tensor): The first batch of matrices to be multiplied.
        batch2 (Tensor): The second batch of matrices to be multiplied.
        alpha: multiplier for `batch1 @ batch2`.
        beta: multiplier for input.

    Returns:
        Tensor, the output tensor.

    Raises:
        TypeError: For Baddbmm, inputs are not tensors.
        ValueError: If `batch1` and `batch2` are not 3-D tensors.
        TypeError: For inputs of type FloatTensor or DoubleTensor, \
                    arguments beta and alpha not be real numbers, otherwise not be integers.
        ValueError: For Baddbmm, attributes alpha and beta are not real numbers

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input = Tensor(np.ones([1, 3, 3]).astype(np.float32))
        >>> batch1 = Tensor(np.ones([1, 3, 4]).astype(np.float32))
        >>> batch2 = Tensor(np.ones([1, 4, 3]).astype(np.float32))
        >>> output = ops.baddbmm(input, batch1, batch2)
        >>> print(output)
        [[[5. 5. 5.]
          [5. 5. 5.]
          [5. 5. 5.]]]
    """
    dtypeop = _get_cache_prim(P.DType)()
    bmmop = _get_cache_prim(P.BatchMatMul)(False, False)
    if not (isinstance(x, Tensor) and isinstance(batch1, Tensor) and isinstance(batch2, Tensor)):
        raise TypeError("For Baddbmm, inputs must be all tensors.")
    if len(batch1.shape) != 3 or len(batch2.shape) != 3:
        raise ValueError("For batch1 and batch2 must be 3-D tensors each containing the same number of matrices, "
                         f"but got length of batch1:'{len(batch1.shape)}', length of batch2:'{len(batch2.shape)}'.")
    input_dtype = dtypeop(x)
    if not (input_dtype == dtypeop(batch1) and input_dtype == dtypeop(batch2)):
        raise TypeError("For Baddbmm, the inputs should be the same dtype.")
    if input_dtype in (mstype.float16, mstype.float32, mstype.float64):
        if not (isinstance(alpha, (int, float)) and isinstance(beta, (int, float))):
            raise TypeError("For attributes alpha and beta should be real numbers.")
        check_is_number(alpha, (int, float))
        check_is_number(beta, (int, float))
    else:
        if not (isinstance(alpha, int) and isinstance(beta, int)):
            raise TypeError("For inputs of type not FloatTensor or DoubleTensor, "
                            "arguments beta and alpha must be integers.")
    y = beta * x + alpha * (bmmop(batch1, batch2))
    return y


def log2(x):
    r"""
    Returns a new tensor with the logarithm to the base 2 of the elements of input.

    .. math::
        y_i = log_2(x_i)

    .. warning::
        If the input value of operator Log2 is within the range (0, 0.01] or [0.95, 1.05], the output accuracy may
        be affacted. If the input value of operator Log2 is less than or equal to 0, it will not raise Error.

    .. note::
        The dimension of the input Tensor on Ascend should be less than or equal to 8, and the dimension of the
        input Tensor on the CPU or GPU should be less than 8.

    Args:
        x (Tensor): Input Tensor of any dimension. The value must be greater than 0.

    Outputs:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16 or float32 or float64 on CPU and GPU, if dtype of `x` is not float16
        or float32 on Ascend.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, 8]).astype(np.float16))
        >>> output = ops.log2(x)
        >>> print(output)
        [1. 2. 3.]
    """

    dtype_op = _get_cache_prim(P.DType)()

    x_dtype = dtype_op(x)
    denominator = log_(_make_tensor(2, x_dtype))
    frac_log = log_(x)
    output = frac_log / denominator
    return output


def xdivy(x, y):
    """
    Divides the first input tensor by the second input tensor element-wise. Returns zero when `x` is zero.

    Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
    The inputs must be two tensors or one tensor and one scalar.
    When the inputs are two tensors,
    dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
    When the inputs are one tensor and one scalar,
    the scalar could only be a constant.

    Inputs:
        - **x** (Union[Tensor, Number, bool]) - The first input is a number, or a bool,
          or a tensor whose data type is float16, float32, float64, complex64, complex128 or bool.
        - **y** (Union[Tensor, Number, bool]) - The second input is a number,
          or a bool when the first input is a tensor, or a tensor whose data type is float16,
          float32, float64, complex64, complex128 or bool.

    Outputs:
        Tensor, the shape is the same as the one after broadcasting,
        and the data type is the one with higher precision or higher digits among the two inputs.

    Raises:
        TypeError: If `x` and `y` is not one of the following: Tensor, Number, bool.
        TypeError: If dtype of `x` and 'y' is not in [float16, float32, float64, complex64, complex128, bool].
        ValueError: If `x` could not be broadcast to a tensor with shape of `y`.
        RuntimeError: If the data type of `x`, `y` conversion of Parameter is given
                      but data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, -1]), mindspore.float32)
        >>> y = Tensor(np.array([2, 2, 2]), mindspore.float32)
        >>> output = ops.xdivy(x, y)
        >>> print(output)
        [ 1.   2.  -0.5]
    """
    return tensor_xdivy(x, y)


def log10(x):
    r"""
    Returns a new tensor with the logarithm to the base 10 of the elements of input.

    .. math::
        y_i = log_{10}(x_i)

    .. warning::
        If the input value of operator Log10 is within the range (0, 0.01] or [0.95, 1.05], the output accuracy may
        be affacted. If the input value of operator Log10 is less than or equal to 0, it will not raise Error.

    .. note::
        The dimension of the input Tensor on Ascend should be less than or equal to 8, and the dimension of the
        input Tensor on the CPU or GPU should be less than 8.

    Args:
        x (Tensor): Input Tensor of any dimension. The value must be greater than 0.

    Outputs:
        Tensor, has the same shape and dtype as the `x`.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If dtype of `x` is not float16 or float32 or float64 on CPU and GPU, if dtype of `x` is not float16
        or float32 on Ascend.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([2, 4, 10]).astype(np.float16))
        >>> output = ops.log10(x)
        >>> print(output)
        [0.301 0.602 1.   ]
    """

    dtype_op = P.DType()

    x_dtype = dtype_op(x)
    denominator = log_(_make_tensor(10, x_dtype))
    frac_log = log_(x)
    output = frac_log / denominator
    return output


def kron(x, y):
    """
    Computes the Kronecker product, denoted by ⊗, of `x` and `y`.

    If `x` is a :math:`(a_{0}` x :math:`a_{1}` x ... x :math:`a_{n})` tensor
    and `y` is a :math:`(b_{0}` x :math:`b_{1}` x ... x :math:`b_{n})` tensor,
    the result will be a :math:`(a_{0}*b_{0}` x :math:`a_{1}*b_{1}` x ... x :math:`a_{n}*b_{n})`
    tensor with the following entries:

    .. math::
            (x ⊗ y)_{k_{0},k_{1},...k_{n}} =
            x_{i_{0},i_{1},...i_{n}} * y_{j_{0},j_{1},...j_{n}},

    where :math:`k_{t} = i_{t} * b_{t} + j_{t}` for 0 ≤ `t` ≤ `n`. If one
    tensor has fewer dimensions than the other it is unsqueezed
    until it has the same number of dimensions.

    Note:
        Supports real-valued and complex-valued inputs.

    Args:
        x (Tensor): Input tensor.
        y (Tensor): Input tensor.

    Returns:
        Tensor.

    Raises:
        TypeError: If `x` is not a Tensor.
        TypeError: If `y` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor, nn
        >>> from mindspore import ops
        >>> x = Tensor(np.array([[0, 1, 2], [3, 4, 5]])).astype(np.float32)
        >>> y = Tensor(np.array([[-1, -2, -3], [-4, -6, -8]])).astype(np.float32)
        >>> output = ops.kron(x, y)
        >>> print(output)
        [[  0.   0.   0.  -1.  -2.  -3.  -2.  -4.  -6.]
         [  0.   0.   0.  -4.  -6.  -8.  -8. -12. -16.]
         [ -3.  -6.  -9.  -4.  -8. -12.  -5. -10. -15.]
         [-12. -18. -24. -16. -24. -32. -20. -30. -40.]]
    """

    if not isinstance(x, (Tensor, Tensor_)):
        raise TypeError("the input x must be Tensor!")
    if not isinstance(y, (Tensor, Tensor_)):
        raise TypeError("the input y must be Tensor!")
    if x is None or y is None:
        return None
    if x.ndim == 0 or y.ndim == 0:
        return x * y

    if x.ndim >= y.ndim:
        maxdim = x.ndim
    else:
        maxdim = y.ndim
    pad_x = maxdim - x.ndim
    pad_y = maxdim - y.ndim
    x_reshape = [0 for x in range(2 * maxdim)]
    y_reshape = [0 for x in range(2 * maxdim)]
    result_shape = [0 for x in range(maxdim)]

    for i in range(maxdim):
        if i >= pad_x:
            x_reshape[2 * i] = x.shape[i - pad_x]
        else:
            x_reshape[2 * i] = 1
        x_reshape[2 * i + 1] = 1
        y_reshape[2 * i] = 1
        if i >= pad_y:
            y_reshape[2 * i + 1] = y.shape[i - pad_y]
        else:
            y_reshape[2 * i + 1] = 1
        result_shape[i] = x_reshape[2 * i] * y_reshape[2 * i + 1]

    x = x.reshape(x_reshape)
    y = y.reshape(y_reshape)
    result = (x * y).reshape(result_shape)
    return result


__all__ = [
    'addn',
    'absolute',
    'abs',
    'tensor_add',
    'add',
    'argmin',
    'neg_tensor',
    'neg',
    'tensor_lt',
    'less',
    'logaddexp2',
    'tensor_le',
    'le',
    'lerp',
    'norm',
    'tensor_gt',
    'logaddexp',
    'mv',
    'outer',
    'gt',
    'tensor_ge',
    'ge',
    'tensor_sub',
    'sub',
    'tensor_mul',
    'mul',
    'tensor_div',
    'div',
    'tensor_floordiv',
    'floor_div',
    'floordiv',
    'tensor_xdivy',
    'xdivy',
    'tensor_pow',
    'pow',
    'pows',
    'renorm',
    'tensor_mod',
    'floor_mod',
    'floormod',
    'tensor_exp',
    'exp',
    'tensor_expm1',
    'expm1',
    'equal',
    'not_equal',
    'ne',
    'inplace_update',
    'inplace_add',
    'inplace_sub',
    'isfinite',
    'isnan',
    'isclose',
    'isreal',
    'log',
    'log_matrix_determinant',
    'matrix_determinant',
    'linspace',
    'matrix_solve',
    'std',
    'same_type_shape',
    'maximum',
    'minimum',
    'floor',
    'logical_not',
    'logical_or',
    'logical_and',
    'logsumexp',
    'ldexp',
    'sin',
    'cos',
    'tan',
    'asin',
    'acos',
    'atan',
    'sinh',
    'cosh',
    'tanh',
    'asinh',
    'acosh',
    'atanh',
    'atan2',
    'round',
    'bitwise_and',
    'bitwise_or',
    'bitwise_xor',
    'inv',
    'invert',
    'erf',
    'erfc',
    'cdist',
    'ceil',
    'bernoulli',
    'bessel_j0',
    'bessel_j1',
    'bessel_i0',
    'bessel_i0e',
    'bessel_k0',
    'bessel_k0e',
    'bessel_y0',
    'bessel_y1',
    'bessel_i1',
    'bessel_i1e',
    'bessel_k1',
    'bessel_k1e',
    'exp2',
    'deg2rad',
    'stft',
    'rad2deg',
    'truncate_div',
    'truncate_mod',
    'gumbel_softmax',
    'matmul',
    'baddbmm',
    'cummin',
    'cummax',
    'reduce_min',
    'reduce_max',
    'reduce_mean',
    'reduce_prod',
    'sparse_segment_mean',
    'log2',
    'xlogy',
    'log10',
    'approximate_equal',
    'frac',
    'kron'
]
__all__.sort()
