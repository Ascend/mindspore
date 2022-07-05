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

"""Operators for function."""

import mindspore.common.dtype as mstype
from mindspore.ops import operations as P
from mindspore.ops.primitive import constexpr

from ..operations.array_ops import (
    UniqueConsecutive,
    NonZero,
    MatrixDiagV3,
    MatrixDiagPartV3,
    Fills,
    Col2Im,
    ScatterNdMax,
    ScatterNdMul,
    IndexFill,
)
from ..operations.nn_ops import AdaptiveMaxPool2D
from ..operations.array_ops import TensorScatterElements
from ...common import Tensor
from .._primitive_cache import _get_cache_prim

eye_ = P.Eye()
fill_ = P.Fill()
fills_ = Fills()
ones_ = P.Ones()
ones_like_ = P.OnesLike()
tile_ = P.Tile()
unique_with_pad_ = P.UniqueWithPad()
size_ = P.Size()
shape_ = P.Shape()
rank_ = P.Rank()
tensor_shape_ = P.TensorShape()
reshape_ = P.Reshape()
flatten_ = P.Flatten()
tensor_slice = P.Slice()
expand_dims_ = P.ExpandDims()
transpose_ = P.Transpose()
scatter_add_ = P.ScatterAdd()
scatter_max_ = P.ScatterMax()
scatter_min_ = P.ScatterMin()
scatter_div_ = P.ScatterDiv()
scatter_nd_ = P.ScatterNd()
gather_ = P.Gather()
gather_d_ = P.GatherD()
gather_nd_ = P.GatherNd()
nonzero_ = NonZero()
scalar_cast_ = P.ScalarCast()
tensor_scatter_add_ = P.TensorScatterAdd()
tensor_scatter_sub_ = P.TensorScatterSub()
tensor_scatter_mul_ = P.TensorScatterMul()
tensor_scatter_div_ = P.TensorScatterDiv()
tensor_scatter_min_ = P.TensorScatterMin()
tensor_scatter_max_ = P.TensorScatterMax()
scalar_to_array_ = P.ScalarToArray()
scalar_to_tensor_ = P.ScalarToTensor()
tuple_to_array_ = P.TupleToArray()
masked_fill_ = P.MaskedFill()
masked_select_ = P.MaskedSelect()
matrix_band_part_ = P.array_ops.MatrixBandPart()
ger_ = P.Ger()
diag_ = P.Diag()
range_ = P.Range()
zeros_like_ = P.ZerosLike()
cast_ = P.Cast()
tensor_select_ = P.Select()
index_fill_ = IndexFill()


@constexpr
def get_x_shape(x_shape):
    s = 1
    for i in x_shape:
        s = s * i
    return (s,)


##############################
# Tensor Creation Functions.
##############################


def eye(n, m, t):
    """
    Creates a tensor with ones on the diagonal and zeros in the rest.

    Note:
        Combines ReverseV2 operator to get an anti-diagonal Tensor,
        but ReverseV2 only supports Ascend and GPU platforms currently.

    Args:
        n (int): The number of rows of returned tensor. Constant value only.
        m (int): The number of columns of returned tensor. Constant value only.
        t (mindspore.dtype): MindSpore's dtype, the data type of the returned tensor.
            The data type can be Number.

    Returns:
        Tensor, a tensor with ones on the diagonal and the rest of elements are zero. The shape of `output` depends on
        the user's Inputs `n` and `m`. And the data type depends on Inputs `t`.

    Raises:
        TypeError: If `m` or `n` is not an int.
        ValueError: If `m` or `n` is less than 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> output = ops.eye(2, 2, mindspore.int32)
        >>> print(output)
        [[1 0]
         [0 1]]
        >>> print(output.dtype)
        Int32
        >>> output = ops.eye(1, 2, mindspore.float64)
        >>> print(output)
        [[1. 0.]]
        >>> print(output.dtype)
        Float64
    """
    return eye_(n, m, t)


def matrix_band_part(x, lower, upper):
    r"""
    Copy a tensor setting everything outside a central band in each innermost matrix to zero.

    The shapes of `x`, `lower` and `upper` need to be the same or broadcast.

    Args:
        x (Tensor): Input tensor. :math:`(*, m, n)` where :math:`*` means, any number of additional dimensions.
            The data type must be float16, float32, float64, int32 or int64.
        lower (Union[int, Tensor]): Number of subdiagonals to keep. The data type must be int32 or int64.
            If negative, keep entire lower triangle.
        upper (Union[int, Tensor]): Number of superdiagonals to keep. The data type must be int32 or int64.
            If negative, keep entire upper triangle.

    Returns:
        Tensor, has the same type and shape as `x`.

    Raises:
        TypeError: If dtype of `x` is not one of float16, float32, float64, int32 or int64.
        TypeError: If `lower` is neither a number nor a Tensor.
        TypeError: If `upper` is neither a number nor a Tensor.
        TypeError: If dtype of `lower` is neither int32 nor a int64.
        TypeError: If dtype of `upper` is neither int32 nor a int64.
        ValueError: If the shape of `x` is not greater than or equal to 2D.
        ValueError: If the shapes of `x`, `lower` and `upper` could not be broadcast.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> x = Tensor(np.ones([2, 4, 4]).astype(np.float32))
        >>> output = F.matrix_band_part(x, 2, 1)
        >>> print(output)
        [[[1. 1. 0. 0.]
          [1. 1. 1. 0.]
          [1. 1. 1. 1.]
          [0. 1. 1. 1.]]
         [[1. 1. 0. 0.]
          [1. 1. 1. 0.]
          [1. 1. 1. 1.]
          [0. 1. 1. 1.]]]
    """
    return matrix_band_part_(x, lower, upper)


def padding(x, pad_dim_size=8):
    r"""
    Extends the last dimension of the input tensor from 1 to pad_dim_size, by filling with 0.

    Args:
        x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`. The rank of `x` must be at least 2.
            The last dimension of `x` must be 1. The data type is Number.
        pad_dim_size (int): The value of the last dimension of `x` to be extended, which must be positive. Default: 8.

    Returns:
        Tensor, has the same type and shape as input shape value.

    Raises:
        TypeError: If `pad_dim_size` is not an int.
        ValueError: If `pad_dim_size` is less than 1.
        ValueError: If last dim of `x` is not equal to 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops import functional as F
        >>> x = Tensor(np.array([[8], [10]]), mindspore.float32)
        >>> pad_dim_size = 4
        >>> output = F.padding(x, pad_dim_size)
        >>> print(output)
        [[ 8.  0.  0.  0.]
         [10.  0.  0.  0.]]
    """
    padding_ = _get_cache_prim(P.array_ops.Padding)(pad_dim_size)
    return padding_(x)


def one_hot(indices, depth, on_value, off_value, axis=-1):
    r"""
    Computes a one-hot tensor.

    The locations represented by indices in `indices` take value `on_value`, while all
    other locations take value `off_value`.

    Note:
        If the input indices is rank `N`, the output will have rank `N+1`. The new axis is created at dimension `axis`.

    Args:
        indices(Tensor): A tensor of indices. Tensor of shape :math:`(X_0, \ldots, X_n)`.
            Data type must be uint8, int32 or int64.
        depth(int): A scalar defining the depth of the one-hot dimension.
        on_value(Tensor): A value to fill in output when `indices[j] = i`.
            Support uint8, uint16, uint32, uint64, int8, int16, int32, int64, float16, float32, float64,
            bool, complex64, complex128.
        off_value(Tensor): A value to fill in output when `indices[j] != i`.
            Has the same data type as `on_value`.
        axis(int): Position to insert the value. e.g. If shape of `self` is :math:`(N, C)`, and `axis` is -1,
            the output shape will be :math:`(N, C, D)`, If `axis` is 0, the output shape will be :math:`(D, N, C)`.
            Default: -1.

    Returns:
        Tensor, one-hot tensor. Tensor of shape :math:`(X_0, \ldots, X_{axis}, \text{depth} ,X_{axis+1}, \ldots, X_n)`.

    Raises:
        TypeError: If `axis` or `depth` is not an int.
        TypeError: If dtype of `indices` is not uint8, int32 or int64.
        TypeError: If `indices`, `on_value` or `off_value` is not a Tensor.
        ValueError: If `axis` is not in range [-1, ndim].
        ValueError: If `depth` is less than 0.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> indices = Tensor(np.array([0, 1, 2]), mindspore.int32)
        >>> depth, on_value, off_value = 3, Tensor(1.0, mindspore.float32), Tensor(0.0, mindspore.float32)
        >>> output = ops.one_hot(indices, depth, on_value, off_value, axis=-1)
        >>> print(output)
        [[1. 0. 0.]
         [0. 1. 0.]
         [0. 0. 1.]]
    """
    onehot = _get_cache_prim(P.OneHot)(axis)
    return onehot(indices, depth, on_value, off_value)


def fill(type, shape, value):
    """
    Create a Tensor of the specified shape and fill it with the specified value.

    Args:
        type (mindspore.dtype): The specified type of output tensor. The data type only supports
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ and
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ .
        shape (tuple[int]): The specified shape of output tensor.
        value (Union(number.Number, bool)): Value to fill the returned tensor.

    Returns:
        Tensor.

    Raises:
        TypeError: If `shape` is not a tuple.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> output = ops.fill(mindspore.float32, (2, 2), 1)
        >>> print(output)
        [[1. 1.]
         [1. 1.]]
        >>> output = ops.fill(mindspore.float32, (3, 3), 0)
        >>> print(output)
        [[0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]]
    """
    return fill_(type, shape, value)


def fills(x, value):
    """
    Create a tensor of the same shape and type as the input tensor and fill it with specified value.

    Args:
        x (Tensor): Input tensor, used to specify the shape and type of the output tensor. The data type should be
            int8, int16, int32, float16 or float32.
        value (Union[int, float, Tensor]): All elements of the output tensor will be assigned this value. The
            type should be int, float or 0-dimensional tensor.

    Returns:
        Tensor, with the same shape and type as input tensor.

    Raises:
        TypeError: If `x` is not a tensor.
        TypeError: If `value` has types not specified above.
        RuntimeError: If `value` cannot be converted to the same type as `x`.
        ValueError: If `value` is a tensor and the length of dimension is not 0.

    Supported Platforms:
        ``GPU``

    Examples:
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> x = Tensor(np.arange(4).reshape((2, 2)).astype('float32'))
        >>> output = ops.fills(x, 1)
        >>> print(output)
        [[1. 1.]
         [1. 1.]]
    """
    if isinstance(value, float):
        value_ = value
    elif isinstance(value, int):
        value_ = float(value)
    elif isinstance(value, Tensor):
        if value.ndim != 0:
            raise ValueError("For 'ops.fills', if the argument 'value' is a tensor, the number of its dimension"
                             " should be 0, but got {}".format(value.ndim))
        value_ = value.astype(mstype.float32)
    else:
        raise TypeError("For 'ops.fills', the type of argument 'value' should be int, float or Tensor,"
                        " but got {}".format(type(value)))
    return fills_(x, value_)


def ones(shape, type):
    r"""
    Creates a tensor filled with value ones.

    Creates a tensor with shape described by the first argument and
    fills it with value ones in type of the second argument.

    Args:
        shape (Union[tuple[int], int]): The specified shape of output tensor. Only constant positive int is allowed.
        type (mindspore.dtype): The specified type of output tensor. Only constant value is allowed.

    Returns:
        Tensor, has the same type and shape as input shape value.

    Raises:
        TypeError: If `shape` is neither tuple nor int.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> output = ops.ones((2, 2), mindspore.float32)
        >>> print(output)
        [[1. 1.]
         [1. 1.]]
        >>> output = ops.ones((3, 3), mindspore.float32)
        >>> print(output)
        [[1. 1. 1.]
         [1. 1. 1.]
         [1. 1. 1.]]
    """
    return ones_(shape, type)


def ones_like(input_x):
    """
    Returns a Tensor with a value of 1 and its shape and data type is the same as the input.

    Args:
        input_x (Tensor): Tensor of any dimension.

    Returns:
        Tensor, has the same shape and type as `input_x` but filled with ones.

    Raises:
        TypeError: If `input_x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[0, 1], [2, 1]]).astype(np.int32))
        >>> output = ops.ones_like(input_x)
        >>> print(output)
        [[1 1]
         [1 1]]
    """
    return ones_like_(input_x)


def tile(input_x, multiples):
    r"""
    Replicates an input tensor with given multiples times.

    Creates a new tensor by replicating `input_x` `multiples` times. The i'th dimension of
    output tensor has `input_x.shape[i] * multiples[i]` elements, and the values of `input_x`
    are replicated `multiples[i]` times along the i'th dimension.

    Note:
        The length of `multiples` must be greater or equal to the length of dimension in `input_x`.

    Args:
        input_x (Tensor): 1-D or higher dimensional Tensor. Set the shape of input tensor as
            :math:`(x_1, x_2, ..., x_S)` .

        multiples (tuple[int]): The parameter that specifies the number of replications,
            the parameter type is tuple, and the data type is int, i.e., :math:`(y_1, y_2, ..., y_S)`.
            The length of `multiples` cannot be smaller than the length of the shape of `input_x`.
            Only constant value is allowed.

    Returns:
        Tensor, has the same data type as the `input_x`. Suppose the length of `multiples` is `d`,
        the dimension of `input_x` is `input_x.dim`, and the shape of `input_x` is :math:`(x_1, x_2, ..., x_S)`.

        - If `input_x.dim = d`, then the shape of their corresponding positions can be multiplied, and
          the shape of Outputs is :math:`(x_1*y_1, x_2*y_2, ..., x_S*y_R)`.
        - If `input_x.dim < d`, fill in multiple 1 in the length of the shape of `input_x` until their
          lengths are consistent. Such as set the shape of `input_x` as :math:`(1, ..., x_1, x_2, ..., x_S)`,
          then the shape of their corresponding positions can be multiplied, and the shape of Outputs is
          :math:`(1*y_1, ..., x_S*y_R)`.

    Raises:
        TypeError: If `multiples` is not a tuple or its elements are not all int.
        ValueError: If the elements of `multiples` are not all greater than 0.
        ValueError: If the length of `multiples` are smaller than the length of dimension in `input_x`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[1, 2], [3, 4]]), mindspore.float32)
        >>> multiples = (2, 3)
        >>> output = ops.tile(input_x, multiples)
        >>> print(output)
        [[1.  2.  1.  2.  1.  2.]
         [3.  4.  3.  4.  3.  4.]
         [1.  2.  1.  2.  1.  2.]
         [3.  4.  3.  4.  3.  4.]]
        >>> multiples = (2, 3, 2)
        >>> output = ops.tile(input_x, multiples)
        >>> print(output)
        [[[1. 2. 1. 2.]
          [3. 4. 3. 4.]
          [1. 2. 1. 2.]
          [3. 4. 3. 4.]
          [1. 2. 1. 2.]
          [3. 4. 3. 4.]]
         [[1. 2. 1. 2.]
          [3. 4. 3. 4.]
          [1. 2. 1. 2.]
          [3. 4. 3. 4.]
          [1. 2. 1. 2.]
          [3. 4. 3. 4.]]]
    """
    return tile_(input_x, multiples)


def range(start, limit, delta):
    r"""
    Creates a sequence of numbers that begins at `start` and extends by increments of
    `delta` up to but not including `limit`.

    The types of all 3 inputs must be the same. The type of the resulting tensor is
    the same as the type of the inputs.

    Args:
        start (Tensor): A scalar Tensor. The first number in the sequence. Must have
          type: int32 or float32.
        limit (Tensor): A scalar Tensor. Upper limit of the sequence, exclusive. Must
          have type: int32 or float32.
        delta (Tensor): A scalar Tensor. Number that increments `start`. Must have
          type: int32 or float32.

    Returns:
        A 1-D Tensor, with the same type as the inputs.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> start = Tensor(0, mstype.int32)
        >>> limit = Tensor(10, mstype.int32)
        >>> delta = Tensor(4, mstype.int32)
        >>> output = ops.range(start, limit, delta)
        >>> print(output)
        [0, 4, 8]
    """
    return range_(start, limit, delta)


##############################
# Tensor Operation Functions.
##############################


def unique(x):
    """
    Returns the unique elements of input tensor and also return a tensor containing the index of each value of input
    tensor corresponding to the output unique tensor.

    The output contains Tensor `y` and Tensor `idx`, the format is probably similar to (`y`, `idx`).
    The shape of Tensor `y` and Tensor `idx` is different in most cases, because Tensor `y` will be deduplicated,
    and the shape of Tensor `idx` is consistent with the input.

    To get the same shape between `idx` and `y`, please ref to :class:'mindspore.ops.UniqueWithPad' operator.

    Args:
        x (Tensor): The input tensor.
            The shape is :math:`(N,*)` where :math:`*` means, any number of additional dimensions.

    .. warning::
        This is an experimental prototype that is subject to change and/or deletion.

    Returns:
        Tuple, containing Tensor objects (`y`, `idx`), `y` is a tensor with the
        same type as `x`, and contains the unique elements in `x`.
        `idx` is a tensor containing indices of elements in
        the input corresponding to the output tensor, have the same shape with `x`.

    Raises:
        TypeError: If `x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor, nn
        >>> from mindspore import ops
        >>> x = Tensor(np.array([1, 2, 5, 2]), mindspore.int32)
        >>> output = ops.unique(x)
        >>> print(output)
        (Tensor(shape=[3], dtype=Int32, value= [1, 2, 5]), Tensor(shape=[4], dtype=Int32, value= [0, 1, 2, 1]))
        >>> y = output[0]
        >>> print(y)
        [1 2 5]
        >>> idx = output[1]
        >>> print(idx)
        [0 1 2 1]
    """

    unique_op = _get_cache_prim(P.Unique)()
    reshape_op = _get_cache_prim(P.Reshape)()

    shape_x = x.shape
    length_x = get_x_shape(shape_x)
    x = reshape_op(x, length_x)
    y, idx = unique_op(x)
    idx = reshape_op(idx, shape_x)
    return y, idx


def unique_with_pad(x, pad_num):
    """
    Returns unique elements and relative indexes in 1-D tensor, filled with padding num.

    The basic function is the same as the Unique operator, but the UniqueWithPad operator adds a Pad function.
    The returned tuple(`y`, `idx`) after the input Tensor `x` is processed by the unique operator,
    in which the shapes of `y` and `idx` are mostly not equal. Therefore, in order to solve the above situation,
    the UniqueWithPad operator will fill the `y` Tensor with the `pad_num` specified by the user
    to make it have the same shape as the Tensor `idx`.

    Args:
        x (Tensor): The tensor need to be unique. Must be 1-D vector with types: int32, int64.
        pad_num (int): Pad num. The data type is an int.

    Returns:
        tuple(Tensor), tuple of 2 tensors, `y` and `idx`.
        - y (Tensor) - The unique elements filled with pad_num, the shape and data type same as `x`.
        - idx (Tensor) - The index of each value of `x` in the unique output `y`, the shape and data type same as `x`.

    Raises:x
        TypeError: If dtype of `x` is neither int32 nor int64.
        ValueError: If length of shape of `x` is not equal to 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor, nn
        >>> from mindspore import ops
        >>> x = Tensor(np.array([1, 2, 5, 2, 3, 5]), mindspore.int32)
        >>> output = ops.unique_with_pad(x, 0)
        >>> print(output)
        (Tensor(shape=[6], dtype=Int32, value= [1, 2, 5, 3, 0, 0]),
         Tensor(shape=[6], dtype=Int32, value= [0, 1, 2, 1, 3, 2]))
        >>> y = output[0]
        >>> print(y)
        [1 2 5 3 0 0]
        >>> idx = output[1]
        >>> print(idx)
        [0 1 2 1 3 2]
    """
    return unique_with_pad_(x, pad_num)


def unique_consecutive(x, return_idx=False, return_counts=False, axis=None):
    """
    Returns the elements that are unique in each consecutive group of equivalent elements in the input tensor.

    Args:
        x (Tensor): The input tensor.
        return_idx (bool, optional): Whether to return the indices of the end position of each element in the
            original input list in the returned unique list. Default: False.
        return_counts (bool, optional): Whether to return the counts of each unique element. Default: False.
        axis (int, optional): The dimension to apply unique. If None, the unique of the flattened input is
            returned. If specified, it must be int32 or int64. Default: None.

    Returns:
        A tensor or a tuple of tensors containing tensor objects (`output`, `idx`, `counts`). `output` has the
        same type as `x` and is used to represent the output list of unique scalar elements. If `return_idx` is
        True, there will be an additional returned tensor, `idx`, which has the same shape as `x` and represents
        the index of where the element in the original input maps to the position in the output. If `return_counts`
        is True, there will be an additional returned tensor, `counts`, which represents the number of occurrences
        for each unique value or tensor.

    Raises:
        TypeError: If `x` is not a Tensor.
        RuntimeError: If `axis` is not in the range of :math:`[-ndim, ndim-1]`.

    Supported Platforms:
        ``GPU``

    Examples:
        >>> import numpy as np
        >>> from mindspore import ops
        >>> from mindspore import Tensor
        >>> from mindspore import dtype as mstype
        >>> x = Tensor(np.array([1, 1, 2, 2, 3, 1, 1, 2]), mstype.int32)
        >>> output, idx, counts = ops.unique_consecutive(x, True, True, None)
        >>> print(output)
        [1 2 3 1 2]
        >>> print(idx)
        [0 0 1 1 2 3 3 4]
        >>> print(counts)
        [2 2 1 2 1]
    """
    unique_consecutive_op = _get_cache_prim(UniqueConsecutive)(return_idx, return_counts, axis)
    output, idx, counts = unique_consecutive_op(x)
    if return_idx and return_counts:
        return output, idx, counts
    if return_idx:
        return output, idx
    if return_counts:
        return output, counts
    return output


def ger(x1, x2):
    r"""
    Ger product of `x1` and `x2`. Calculate the outer product of two arrays. If `x1` is a 1D Tensor of
    shape :math:`(m,)` and `x2` is a 1D Tensor of shape :math:`(n,)`, then `output` must be a 2D Tensor of shape
    :math:`(m, n)`.

    Note:
        Currently Ascend does not support float64 data input.

    Args:
        x1 (Tensor): input Tensor, with dtype of float16, float32 or float64.
        x2 (Tensor): input Tensor, with dtype of float16, float32 or float64, must have the same dtype as `x1`.

    Returns:
        Tensor, output matrix with the same dtype as inputs. With `x1` shape :math:`(m,)` and
        `x2` shape of :math:`(n,)`, the `output` has shape :math:`(m, n)`.

    Raises:
        TypeError: If `x1` or `x2` is not a 1-D Tensor.
        TypeError: If the dtype of `x1` and `x2` is not float16, float32 or float64.
        TypeError: If the dtype of `x1` and `x2` are not the same.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x1 = Tensor([1., 2., 3., 4.], mindspore.float32)
        >>> x2 = Tensor([1., 2., 3.], mindspore.float32)
        >>> output = ops.ger(x1, x2)
        >>> print(output)
        [[ 1.  2.  3.]
         [ 2.  4.  6.]
         [ 3.  6.  9.]
         [ 4.  8. 12.]]
    """
    return ger_(x1, x2)


def size(input_x):
    r"""
    Returns a Scalar of type int that represents the size of the input Tensor and the total number of elements in the
    Tensor.

    Args:
        input_x (Tensor): Input parameters, the shape of tensor is :math:`(x_1, x_2, ..., x_R)`. The data type is
            `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.

    Returns:
        int. A scalar representing the elements' size of `input_x`, tensor is the number of elements
        in a tensor, :math:`size=x_1*x_2*...x_R`. The data type is an int.

    Raises:
        TypeError: If `input_x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[2, 2], [2, 2]]), mindspore.float32)
        >>> output = ops.size(input_x)
        >>> print(output)
        4
    """
    return size_(input_x)


def shape(input_x):
    """
    Returns the shape of the input tensor. And it used to be static shape.

    static shape: A shape that can be obtained without running the graph. It is an inherent property of tensor and
    may be unknown. The static shape information can be completed by artificial setting.
    No matter what the input of the graph is, the static shape is not affected.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.

    Returns:
        tuple[int], the output tuple is constructed by multiple integers,
        :math:`(x_1, x_2, ..., x_R)`.

    Raises:
        TypeError: If `input_x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.ones(shape=[3, 2, 1]), mindspore.float32)
        >>> output = ops.shape(input_x)
        >>> print(output)
        (3, 2, 1)
    """
    return shape_(input_x)


def dyn_shape(input_x):
    """
    Returns the shape of the input tensor.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.

    Returns:
        Tensor[int], 1-dim Tensor of type int32

    Raises:
        TypeError: If `input_x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.ones(shape=[3, 2, 1]), mindspore.float32)
        >>> output = ops.dyn_shape(input_x)
        >>> print(output)
        [3 2 1]
    """
    return tensor_shape_(input_x)


def rank(input_x):
    """
    Returns the rank of a tensor.

    Returns a 0-D int32 Tensor representing the rank of input; the rank of a tensor
    is the number of indices required to uniquely select each element of the tensor.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`. The data type is Number.

    Returns:
        Tensor. 0-D int32 Tensor representing the rank of input, i.e., :math:`R`. The data type is an int.

    Raises:
        TypeError: If `input_x` is not a Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_tensor = Tensor(np.array([[2, 2], [2, 2]]), mindspore.float32)
        >>> output = ops.rank(input_tensor)
        >>> print(output)
        2
        >>> print(type(output))
        <class 'int'>
    """
    return rank_(input_x)


def reshape(input_x, input_shape):
    """
    Rearranges the input Tensor based on the given shape.

    The 'input_shape' can only have one -1 at most, in which case it’s inferred from the remaining dimensions and
    the number of elements in the input.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        input_shape (tuple[int]): The input tuple is constructed by multiple
            integers, i.e., :math:`(y_1, y_2, ..., y_S)`. Only constant value is allowed.

    Returns:
        Tensor, the shape of tensor is :math:`(y_1, y_2, ..., y_S)`.

    Raises:
        ValueError: Given a shape tuple, if it has several -1; or if the product
            of its elements is less than or equal to 0 or cannot be divided by the product
            of the input tensor shape; or if it does not match the input's array size.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> output = ops.reshape(input_x, (3, 2))
        >>> print(output)
        [[-0.1  0.3]
         [ 3.6  0.4]
         [ 0.5 -3.2]]
    """
    return reshape_(input_x, input_shape)


def flatten(input_x):
    r"""
    Flattens a tensor without changing its batch size on the 0-th axis.

    Args:
        input_x (Tensor): Tensor of shape :math:`(N, \ldots)` to be flattened, where :math:`N` is batch size.

    Returns:
        Tensor, the shape of the output tensor is :math:`(N, X)`, where :math:`X` is
        the product of the remaining dimension.

    Raises:
        TypeError: If `input_x` is not a Tensor.
        ValueError: If length of shape of `input_x` is less than 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.ones(shape=[1, 2, 3, 4]), mindspore.float32)
        >>> output = ops.flatten(input_x)
        >>> print(output.shape)
        (1, 24)
    """
    return flatten_(input_x)


@constexpr
def _check_select_type_match(scalar, tensor_type, scalar_name, tensor_name):
    if isinstance(scalar, int) and tensor_type != mstype.int32:
        raise TypeError(f"For functional operator[select], the input[{scalar_name}] is int, "
                        f"then the input[{tensor_name}] must be a Tensor of int32.")
    if isinstance(scalar, float) and tensor_type != mstype.float32:
        raise TypeError(f"For functional operator[select], the input[{scalar_name}] is float, "
                        f"then the input[{tensor_name}] must be a Tensor of float32.")


@constexpr
def _check_select_shape_match(input_shape, cond_shape, tensor_name):
    if input_shape != cond_shape:
        raise ValueError(f"For functional operator[select], the cond shape must be same as {tensor_name} shape.")


@constexpr
def _check_select_type(is_cond_tensor, is_x_scalar, is_y_scalar, is_x_tensor, is_y_tensor):
    if not is_cond_tensor:
        raise TypeError(f"For functional operator[select], the input[cond] must be a Tensor.")
    if is_x_scalar and not is_y_tensor:
        raise TypeError(f"For functional operator[select], the input[x] is int or float, "
                        f"then the input[y] must be a Tensor.")
    if is_y_scalar and not is_x_tensor:
        raise TypeError(f"For functional operator[select], the input[y] is int or float, "
                        f"then the input[x] must be a Tensor.")


def select(cond, x, y):
    r"""
    The conditional tensor determines whether the corresponding element in the output must be
    selected from :math:`x` (if true) or :math:`y` (if false) based on the value of each element.

    It can be defined as:

    .. math::
        out_i = \begin{cases}
        x_i, & \text{if } cond_i \\
        y_i, & \text{otherwise}
        \end{cases}

    Args:
        cond (Tensor[bool]): The condition tensor, decides which element is chosen.
          The shape is :math:`(x_1, x_2, ..., x_N, ..., x_R)`.
        x (Union[Tensor, int, float]): The first Tensor or number to be selected.
          If x is a Tensor, the shape is :math:`(x_1, x_2, ..., x_N, ..., x_R)`. If x is an int or a float,
          it will be cast to the type of int32 or float32, and broadcast to the same shape as y.
          One of x and y must be a Tensor.
        y (Union[Tensor, int, float]): The second Tensor or number to be selected.
          If y is a Tensor, The shape is :math:`(x_1, x_2, ..., x_N, ..., x_R)`. If y is an int or a float,
          it will be cast to the type of int32 or float32, and broadcast to the same shape as x.
          One of x and y must be a Tensor.

    Returns:
        Tensor, has the same shape as `cond`.

    Raises:
        TypeError: If `x` or `y` is not a Tensor, int or float.
        ValueError: The shapes of inputs are different.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> # 1) Both inputs are Tensor
        >>>
        >>> cond = Tensor([True, False])
        >>> x = Tensor([2,3], mindspore.float32)
        >>> y = Tensor([1,2], mindspore.float32)
        >>> output = ops.select(cond, x, y)
        >>> print(output)
        [2. 2.]
        >>> # 2) y is a float
        >>> cond = Tensor([True, False])
        >>> x = Tensor([2,3], mindspore.float32)
        >>> y = 2.0
        >>> output = ops.select(cond, x, y)
        >>> print(output)
        [2. 2.]
    """
    is_x_scalar = isinstance(x, (int, float))
    is_y_scalar = isinstance(y, (int, float))
    is_x_tensor = isinstance(x, Tensor)
    is_y_tensor = isinstance(y, Tensor)
    is_cond_tensor = isinstance(cond, Tensor)
    _check_select_type(is_cond_tensor, is_x_scalar, is_y_scalar, is_x_tensor, is_y_tensor)
    input_x = x
    input_y = y
    if is_x_scalar:
        _check_select_shape_match(y.shape, cond.shape, "y")
        _check_select_type_match(x, y.dtype, "x", "y")
        input_x = zeros_like_(y) + x
        if isinstance(x, int):
            input_x = cast_(input_x, mstype.int32)
        else:
            input_x = cast_(input_x, mstype.float32)

    if is_y_scalar:
        _check_select_shape_match(x.shape, cond.shape, "x")
        _check_select_type_match(y, x.dtype, "y", "x")
        input_y = zeros_like_(x) + y
        if isinstance(y, int):
            input_y = cast_(input_y, mstype.int32)
        else:
            input_y = cast_(input_y, mstype.float32)
    return tensor_select_(cond, input_x, input_y)


def slice(input_x, begin, size):
    """
    Slices a tensor in the specified shape.

    Slice the tensor `input_x` in shape of `size` and starting at the location specified by `begin`,
    The slice `begin` represents the offset in each dimension of `input_x`,
    The slice `size` represents the size of the output tensor.

    Note that `begin` is zero-based and `size` is one-based.

    If `size[i]` is -1, all remaining elements in dimension i are included in the slice.
    This is equivalent to setting :math:`size[i] = input_x.shape(i) - begin[i]`.

    Args:
        input_x (Tensor): The target tensor.
            The shape is :math:`(N,*)` where :math:`*` means, any number of additional dimensions.
        begin (Union[tuple, list]): The beginning of the slice. Only constant value(>=0) is allowed.
        size (Union[tuple, list]): The size of the slice. Only constant value is allowed.

    Returns:
        Tensor, the shape is : input `size`, the data type is the same as `input_x`.

    Raises:
        TypeError: If `begin` or `size` is neither tuple nor list.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> data = Tensor(np.array([[[1, 1, 1], [2, 2, 2]],
        ...                         [[3, 3, 3], [4, 4, 4]],
        ...                         [[5, 5, 5], [6, 6, 6]]]).astype(np.int32))
        >>> output = ops.slice(data, (1, 0, 0), (1, 1, 3))
        >>> print(output)
        [[[3 3 3]]]
        >>> output = ops.slice(data, (1, 0, 0), (1, 1, 2))
        >>> print(output)
        [[[3 3]]]
        >>> output = ops.slice(data, (1, 0, 0), (1, 1, 1))
        >>> print(output)
        [[[3]]]
        >>> output = ops.slice(data, (1, 1, 0), (1, 1, 3))
        >>> print(output)
        [[[4 4 4]]]
        >>> output = ops.slice(data, (1, 0, 1), (1, 1, 2))
        >>> print(output)
        [[[3 3]]]
    """
    return tensor_slice(input_x, begin, size)


def concat(input_x, axis=0):
    r"""
    Connect tensor in the specified axis.

    Connect input tensors along with the given axis.

    The input data is a tuple of tensors. These tensors have the same rank :math:`R`. Set the given axis as :math:`m`,
    and :math:`0 \le m < R`. Set the number of input tensors as :math:`N`. For the :math:`i`-th tensor :math:`t_i`,
    it has the shape of :math:`(x_1, x_2, ..., x_{mi}, ..., x_R)`. :math:`x_{mi}` is the :math:`m`-th dimension of the
    :math:`t_i`. Then, the shape of the output tensor is

    .. math::

        (x_1, x_2, ..., \sum_{i=1}^Nx_{mi}, ..., x_R)

    .. warning::
        The value range of "axis" is [-dims, dims - 1]. "dims" is the dimension length of "input_x".

    Args:
        input_x (tuple, list): A tuple or a list of input tensors.
            Suppose there are two tensors in this tuple or list, namely t1 and t2.
            To perform `concat` in the axis 0 direction, except for the :math:`0`-th axis,
            all other dimensions should be equal, that is,
            :math:`t1.shape[1] = t2.shape[1], t1.shape[2] = t2.shape[2], ..., t1.shape[R-1] = t2.shape[R-1]`,
        axis (int): The specified axis. Default: 0.

    Returns:
        Tensor, the shape is :math:`(x_1, x_2, ..., \sum_{i=1}^Nx_{mi}, ..., x_R)`.
            The data type is the same with `input_x`.

    Raises:
        TypeError: If `axis` is not an int.
        ValueError: If `input_x` have different dimension of tensor.
        ValueError: If `axis` not in [-dims, dims - 1].
        RuntimeError: If tensor's shape in `input_x` except for `axis` are different.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x1 = Tensor(np.array([[0, 1], [2, 1]]).astype(np.float32))
        >>> input_x2 = Tensor(np.array([[0, 1], [2, 1]]).astype(np.float32))
        >>> output = ops.concat((input_x1, input_x2))
        >>> print(output)
        [[0. 1.]
         [2. 1.]
         [0. 1.]
         [2. 1.]]
        >>> output = ops.concat((input_x1, input_x2), 1)
        >>> print(output)
        [[0. 1. 0. 1.]
         [2. 1. 2. 1.]]
    """
    _concat = _get_cache_prim(P.Concat)(axis)
    return _concat(input_x)


def expand_dims(input_x, axis):
    """
    Adds an additional dimension to `input_x` at the given axis.

    Note:
        If the specified axis is a negative number, the index is counted
        backward from the end and starts at 1.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        axis (int): Specifies the dimension index at which to expand
            the shape of `input_x`. The value of axis must be in the range
            `[-input_x.ndim-1, input_x.ndim]`. Only constant value is allowed.

    Returns:
        Tensor, the shape of tensor is :math:`(1, x_1, x_2, ..., x_R)` if the
        value of `axis` is 0. It has the same data type as `input_x`.

    Raises:
        ValueError: If `axis` is not an int or not in the valid range.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_tensor = Tensor(np.array([[2, 2], [2, 2]]), mindspore.float32)
        >>> output = ops.expand_dims(input_tensor, 0)
        >>> print(output)
        [[[2. 2.]
          [2. 2.]]]
    """
    return expand_dims_(input_x, axis)


def transpose(input_x, input_perm):
    """
    Permutes the dimensions of the input tensor according to input permutation.

    For a 1-D array this has no effect, as a transposed vector is simply the same vector.
    To convert a 1-D array into a 2D column vector please refer the class: mindspore.ops.ExpandDims.
    For a 2-D array, this is a standard matrix transpose. For an n-D array, if axes are given,
    their order indicates how the axes are permuted (see Examples).
    If axes are not provided and a.shape = (i[0], i[1], ... i[n-2], i[n-1]),
    then a.transpose().shape = (i[n-1], i[n-2], ... i[1], i[0]).

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        input_perm (tuple[int]): The permutation to be converted. The elements in `input_perm` are composed of
            the indexes of each dimension of `input_x`. The length of `input_perm` and the shape of `input_x` must be
            the same. Only constant value is allowed. Must be in the range [0, rank(input_x)).

    Returns:
        Tensor, the type of output tensor is the same as `input_x` and the shape of output tensor is decided by the
        shape of `input_x` and the value of `input_perm`.

    Raises:
        TypeError: If `input_perm` is not a tuple.
        ValueError: If length of shape of `input_x` is not equal to length of shape of `input_perm`.
        ValueError: If the same element exists in `input_perm`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]]), mindspore.float32)
        >>> input_perm = (0, 2, 1)
        >>> output = ops.transpose(input_x, input_perm)
        >>> print(output)
        [[[ 1.  4.]
          [ 2.  5.]
          [ 3.  6.]]
         [[ 7. 10.]
          [ 8. 11.]
          [ 9. 12.]]]
    """
    return transpose_(input_x, input_perm)


def scatter_max(input_x, indices, updates):
    r"""
    Using given values to update tensor value through the max operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    Args:
        input_x (Parameter) - The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor) - The index to do max operation whose data type must be mindspore.int32.
        updates (Tensor) - The tensor doing the max operation with `input_x`,
            the data type is same as `input_x`, the shape is `indices.shape + x.shape[1:]`.

    Outputs:
        Tensor, the updated `input_x`, the type and shape same as `input_x`.

    Raises:
        TypeError: If `indices` is not an int32 or int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape + input_x.shape[1:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.
        RuntimeError: On the Ascend platform, the input data dimension of `input_x` , `indices`
                      and `updates` is greater than 8 dimensions.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]), mindspore.float32), name="input_x")
        >>> indices = Tensor(np.array([[0, 0], [1, 1]]), mindspore.int32)
        >>> updates = Tensor(np.ones([2, 2, 3]) * 88, mindspore.float32)
        >>> scatter_max = ops.ScatterMax()
        >>> output = scatter_max(input_x, indices, updates)
        >>> print(output)
        [[88. 88. 88.]
         [88. 88. 88.]]
    """
    return scatter_max_(input_x, indices, updates)


def scatter_add(input_x, indices, updates):
    r"""
    Using given values to update tensor value through the add operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index to do add operation whose data type must be mindspore.int32.
        updates (Tensor): The tensor doing the add operation with `input_x`,
            the data type is same as `input_x`, the shape is `indices.shape + x.shape[1:]`.

    Returns:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `indices` is not an int32 or int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape + input_x.shape[1:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
            is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]), mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[0, 1], [1, 1]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1.0, 1.0, 1.0], [3.0, 3.0, 3.0]],
        ...                            [[7.0, 7.0, 7.0], [9.0, 9.0, 9.0]]]), mindspore.float32)
        >>> scatter_add = ops.scatter_add()
        >>> output = scatter_add(input_x, indices, updates)
        >>> print(output)
        [[ 1.  1.  1.]
         [19. 19. 19.]]
    """
    return scatter_add_(input_x, indices, updates)


def scatter_min(input_x, indices, updates):
    r"""
    Updates the value of the input tensor through the minimum operation.

    Using given values to update tensor value through the min operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    for each :math:`i, ..., j` in `indices.shape`:

    .. math::

        \text{input_x}[\text{indices}[i, ..., j], :]
        = min(\text{input_x}[\text{indices}[i, ..., j], :], \text{updates}[i, ..., j, :])

    Inputs of `input_x` and `updates` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index to do min operation whose data type must be mindspore.int32 or mindspore.int64.
        updates (Tensor): The tensor doing the min operation with `input_x`,
            the data type is same as `input_x`, the shape is `indices.shape + input_x.shape[1:]`.

    Outputs:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `indices` is not an int32 or an int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape + input_x.shape[1:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.
        RuntimeError: On the Ascend platform, the input data dimension of `input_x` , `indices`
                      and `updates` is greater than 8 dimensions.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore
        >>> from mindspore import Tensor, Parameter
        >>> from mindspore import ops
        >>> input_x = Parameter(Tensor(np.zeros((2, 3)), mindspore.float32), name="input_x")
        >>> indices = Tensor(np.array([1, 0]), mindspore.int32)
        >>> update = Tensor(np.arange(6).reshape((2, 3)), mindspore.float32)
        >>> scatter_min = ops.ScatterMin()
        >>> output = scatter_min(input_x, indices, update)
        >>> print(output)
        [[0. 0. 0.]
         [0. 0. 0.]]
    """
    return scatter_min_(input_x, indices, updates)


def scatter_div(input_x, indices, updates):
    r"""
    Updates the value of the input tensor through the divide operation.

    Using given values to update tensor value through the div operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    for each :math:`i, ..., j` in `indices.shape`:

    .. math::

        \text{input_x}[\text{indices}[i, ..., j], :] \mathrel{/}= \text{updates}[i, ..., j, :]

    Inputs of `input_x` and `updates` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
          The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index to do min operation whose data type must be mindspore.int32 or
          mindspore.int64.
        updates (Tensor): The tensor doing the min operation with `input_x`,
          the data type is same as `input_x`, the shape is `indices.shape + input_x.shape[1:]`.

    Outputs:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `indices` is not an int32 or an int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape + input_x.shape[1:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.
        RuntimeError: On the Ascend platform, the input data dimension of `input_x` , `indices`
                      and `updates` is greater than 8 dimensions.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([[6.0, 6.0, 6.0], [2.0, 2.0, 2.0]]), mindspore.float32), name="x")
        >>> indices = Tensor(np.array([0, 1]), mindspore.int32)
        >>> updates = Tensor(np.array([[2.0, 2.0, 2.0], [2.0, 2.0, 2.0]]), mindspore.float32)
        >>> scatter_div = ops.ScatterDiv()
        >>> output = scatter_div(input_x, indices, updates)
        >>> print(output)
        [[3. 3. 3.]
         [1. 1. 1.]]
        >>> # for input_x will be updated after the operation is completed. input_x need to be re-initialized.
        >>> input_x = Parameter(Tensor(np.array([[105.0, 105.0, 105.0],
        ...                                      [315.0, 315.0, 315.0]]), mindspore.float32), name="x")
        >>> # for indices = [[0, 1], [1, 1]]
        >>> # step 1: [0, 1]
        >>> # input_x[0] = [105.0, 105.0, 105.0] / [1.0, 1.0, 1.0] = [105.0, 105.0, 105.0]
        >>> # input_x[1] = [315.0, 315.0, 315.0] / [3.0, 3.0, 3.0] = [105.0, 105.0, 105.0]
        >>> # step 2: [1, 1]
        >>> # input_x[1] = [105.0, 105.0, 105.0] / [5.0, 5.0, 5.0] = [21.0, 21.0, 21.0]
        >>> # input_x[1] = [21.0, 21.0, 21.0] / [7.0, 7.0, 7.0] = [3.0, 3.0, 3.0]
        >>> indices = Tensor(np.array([[0, 1], [1, 1]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1.0, 1.0, 1.0], [3.0, 3.0, 3.0]],
        ...                            [[5.0, 5.0, 5.0], [7.0, 7.0, 7.0]]]), mindspore.float32)
        >>> scatter_div = ops.ScatterDiv()
        >>> output = scatter_div(input_x, indices, updates)
        >>> print(output)
        [[105. 105. 105.]
         [  3.   3.   3.]]
        >>> # for input_x will be updated after the operation is completed. input_x need to be re-initialized.
        >>> input_x = Parameter(Tensor(np.array([[105.0, 105.0, 105.0],
        ...                                      [315.0, 315.0, 315.0]]), mindspore.float32), name="x")
        >>> # for indices = [[1, 0], [1, 1]]
        >>> # step 1: [1, 0]
        >>> # input_x[0] = [105.0, 105.0, 105.0] / [3.0, 3.0, 3.0] = [35.0, 35.0, 35.0]
        >>> # input_x[1] = [315.0, 315.0, 315.0] / [1.0, 1.0, 1.0] = [315.0, 315.0, 315.0]
        >>> # step 2: [1, 1]
        >>> # input_x[1] = [315.0, 315.0, 315.0] / [5.0, 5.0, 5.0] = [63.0 63.0 63.0]
        >>> # input_x[1] = [63.0 63.0 63.0] / [7.0, 7.0, 7.0] = [9.0, 9.0, 9.0]
        >>> indices = Tensor(np.array([[1, 0], [1, 1]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1.0, 1.0, 1.0], [3.0, 3.0, 3.0]],
        ...                            [[5.0, 5.0, 5.0], [7.0, 7.0, 7.0]]]), mindspore.float32)
        >>> scatter_div = ops.ScatterDiv()
        >>> output = scatter_div(input_x, indices, updates)
        >>> print(output)
        [[35. 35. 35.]
         [ 9.  9.  9.]]
    """
    return scatter_div_(input_x, indices, updates)


def scatter_nd(indices, updates, shape):
    r"""
    Scatters a tensor into a new tensor depending on the specified indices.

    Creates an empty tensor with the given `shape`, and set values by scattering the update tensor
    depending on indices. The empty tensor has rank :math:`P` and `indices` has rank :math:`Q` where :math:`Q \ge 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where :math:`N \le P`.

    The last dimension of `indices` (with length :math:`N` ) indicates slices along the :math:`N` th dimension of the
    empty tensor.

    `updates` is a tensor of rank :math:`Q-1+P-N`,
    its shape is: :math:`(i_0, i_1, ..., i_{Q-2}, shape_N, ..., shape_{P-1})`.

    The following figure shows the calculation process of inserting two slices in the first dimension of a rank-3
    with two matrices of new values:

    .. image:: ScatterNd.png

    Args:
        indices (Tensor): The index of scattering in the new tensor with int32 or int64 data type.
            The rank of indices must be at least 2 and :math:`indices\_shape[-1] \le len(shape)`.
        updates (Tensor): The source Tensor to be scattered.
            It has shape :math:`indices\_shape[:-1] + shape[indices\_shape[-1]:]`.
        shape (tuple[int]): Define the shape of the output tensor, has the same data type as indices.
            The shape of `shape` is :math:`(x_1, x_2, ..., x_R)`, and the length of 'shape' is greater than
            or equal to 2. In other words, the shape of `shape` is at least :math:`(x_1, x_2)`.
            And the value of any element in `shape` must be greater than or equal to 1.
            In other words, :math:`x_1 \ge 1`, :math:`x_2 \ge 1`.

    Returns:
        Tensor, the new tensor, has the same type as `update` and the same shape as `shape`.

    Raises:
        TypeError: If `shape` is not a tuple.
        ValueError: If any element of `shape` is less than 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2],
        ...                             [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[1, 1, 1, 1], [2, 2, 2, 2],
        ...                             [3, 3, 3, 3], [4, 4, 4, 4]]]), mindspore.float32)
        >>> shape = (4, 4, 4)
        >>> output = ops.scatter_nd(indices, updates, shape)
        >>> print(output)
        [[[1. 1. 1. 1.]
          [2. 2. 2. 2.]
          [3. 3. 3. 3.]
          [4. 4. 4. 4.]]
         [[0. 0. 0. 0.]
          [0. 0. 0. 0.]
          [0. 0. 0. 0.]
          [0. 0. 0. 0.]]
         [[1. 1. 1. 1.]
          [2. 2. 2. 2.]
          [3. 3. 3. 3.]
          [4. 4. 4. 4.]]
         [[0. 0. 0. 0.]
          [0. 0. 0. 0.]
          [0. 0. 0. 0.]
          [0. 0. 0. 0.]]]
        >>> indices = Tensor(np.array([[0, 1], [1, 1]]), mindspore.int32)
        >>> updates = Tensor(np.array([3.2, 1.1]), mindspore.float32)
        >>> shape = (3, 3)
        >>> output = ops.scatter_nd(indices, updates, shape)
        >>> # In order to facilitate understanding, explain the operator pseudo-operation process step by step:
        >>> # Step 1: Generate an empty Tensor of the specified shape according to the shape
        >>> # [
        >>> #     [0. 0. 0.]
        >>> #     [0. 0. 0.]
        >>> #     [0. 0. 0.]
        >>> # ]
        >>> # Step 2: Modify the data at the specified location according to the indicators
        >>> # 0th row of indices is [0, 1], 0th row of updates is 3.2.
        >>> # means that the empty tensor in the 0th row and 1st col set to 3.2
        >>> # [
        >>> #     [0. 3.2. 0.]
        >>> #     [0. 0.   0.]
        >>> #     [0. 0.   0.]
        >>> # ]
        >>> # 1th row of indices is [1, 1], 1th row of updates is 1.1.
        >>> # means that the empty tensor in the 1th row and 1st col set to 1.1
        >>> # [
        >>> #     [0. 3.2. 0.]
        >>> #     [0. 1.1  0.]
        >>> #     [0. 0.   0.]
        >>> # ]
        >>> # The final result is as follows:
        >>> print(output)
        [[0. 3.2 0.]
         [0. 1.1 0.]
         [0. 0.  0.]]
    """
    return scatter_nd_(indices, updates, shape)


def scatter_update(input_x, indices, updates):
    r"""
    Updates tensor values by using input indices and value.

    Using given values to update tensor value, along with the input indices.

    for each `i, ..., j` in `indices.shape`:

    .. math::

        \text{input_x}[\text{indices}[i, ..., j], :] = \text{updates}[i, ..., j, :]

    Inputs of `input_x` and `updates` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        input_x (Parameter) - The target tensor, with data type of Parameter.
          The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor) - The index of input tensor. With int32 or int64 data type.
          If there are duplicates in indices, the order for updating is undefined.
        updates (Tensor) - The tensor to update the input tensor, has the same type as input,
          and updates.shape = indices.shape + input_x.shape[1:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `indices` is not an int32 or an int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape + input_x.shape[1:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> np_x = np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]])
        >>> input_x = mindspore.Parameter(Tensor(np_x, mindspore.float32), name="x")
        >>> indices = Tensor(np.array([0, 1]), mindspore.int32)
        >>> np_updates = np.array([[2.0, 1.2, 1.0], [3.0, 1.2, 1.0]])
        >>> updates = Tensor(np_updates, mindspore.float32)
        >>> op = ops.scatter_update()
        >>> output = op(input_x, indices, updates)
        >>> print(output)
        [[2. 1.2  1.]
         [3. 1.2  1.]]
    """
    scatter_update_inner = _get_cache_prim(P.ScatterUpdate)()
    return scatter_update_inner(input_x, indices, updates)


def scatter_nd_add(input_x, indices, updates, use_locking=False):
    r"""
    Applies sparse addition to individual values or slices in a tensor.

    Using given values to update tensor value through the add operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    `input_x` has rank P and `indices` has rank Q where `Q >= 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where `N <= P`.

    The last dimension of `indices` (with length `N` ) indicates slices along the `N` th dimension of `input_x`.

    `updates` is a tensor of rank `Q-1+P-N`. Its shape is:
    :math:`(i_0, i_1, ..., i_{Q-2}, x\_shape_N, ..., x\_shape_{P-1})`.

    Inputs of `input_x` and `updates` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower priority data type will be converted to
    the relatively highest priority data type.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index to do min operation whose data type must be mindspore.int32 or mindspore.int64.
            The rank of indices must be at least 2 and `indices.shape[-1] <= len(shape)`.
        updates (Tensor): The tensor doing the addition operation with `input_x`,
            the data type is same as `input_x`, the shape is `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        use_locking (bool): Whether to protect the assignment by a lock. Default: False.

    Returns:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `use_locking` is not a bool.
        TypeError: If `indices` is not an int32 or an int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([1, 2, 3, 4, 5, 6, 7, 8]), mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[2], [4], [1], [7]]), mindspore.int32)
        >>> updates = Tensor(np.array([6, 7, 8, 9]), mindspore.float32)
        >>> output = ops.scatter_nd_add(input_x, indices, updates, False)
        >>> print(output)
        [ 1. 10.  9.  4. 12.  6.  7. 17.]
        >>> input_x = Parameter(Tensor(np.zeros((4, 4, 4)), mindspore.int32))
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]]]), mindspore.int32)
        >>> output = ops.scatter_nd_add(input_x, indices, updates, False)
        >>> print(output)
        [[[1 1 1 1]
          [2 2 2 2]
          [3 3 3 3]
          [4 4 4 4]]
         [[0 0 0 0]
          [0 0 0 0]
          [0 0 0 0]
          [0 0 0 0]]
         [[5 5 5 5]
          [6 6 6 6]
          [7 7 7 7]
          [8 8 8 8]]
         [[0 0 0 0]
          [0 0 0 0]
          [0 0 0 0]
          [0 0 0 0]]]
    """
    scatter_nd_add_inner = _get_cache_prim(P.ScatterNdAdd)(use_locking)
    return scatter_nd_add_inner(input_x, indices, updates)


def scatter_nd_sub(input_x, indices, updates, use_locking=False):
    r"""
    Applies sparse subtraction to individual values or slices in a tensor.

    Using given values to update tensor value through the subtraction operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    `input_x` has rank P and `indices` has rank Q where `Q >= 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where `N <= P`.

    The last dimension of `indices` (with length `N` ) indicates slices along the `N` th dimension of `input_x`.

    `updates` is a tensor of rank `Q-1+P-N`. Its shape is:
    :math:`(i_0, i_1, ..., i_{Q-2}, x\_shape_N, ..., x\_shape_{P-1})`.

    Inputs of `input_x` and `updates` comply with the implicit type conversion rules to make the data types consistent.
    If they have different data types, the lower priority data type will be converted to the
    relatively highest priority data type.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index of input tensor, with int32 or int64 data type.
            The rank of indices must be at least 2 and `indices.shape[-1] <= len(shape)`.
        updates (Tensor): The tensor doing the subtraction operation with `input_x`, has the same type as input.
            The shape is `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        use_locking (bool): Whether to protect the assignment by a lock. Default: False.

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `use_locking` is not a bool.
        TypeError: If `indices` is not an int32 or int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([1, 2, 3, 4, 5, 6, 7, 8]), mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[2], [4], [1], [7]]), mindspore.int32)
        >>> updates = Tensor(np.array([6, 7, 8, 9]), mindspore.float32)
        >>> output = ops.scatter_nd_sub(input_x, indices, updates, False)
        >>> print(output)
        [ 1. -6. -3.  4. -2.  6.  7. -1.]
        >>> input_x = Parameter(Tensor(np.zeros((4, 4, 4)), mindspore.int32))
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]]]), mindspore.int32)
        >>> output = ops.scatter_nd_sub(input_x, indices, updates, False)
        >>> print(output)
        [[[-1 -1 -1 -1]
          [-2 -2 -2 -2]
          [-3 -3 -3 -3]
          [-4 -4 -4 -4]]
         [[ 0  0  0  0]
          [ 0  0  0  0]
          [ 0  0  0  0]
          [ 0  0  0  0]]
         [[-5 -5 -5 -5]
          [-6 -6 -6 -6]
          [-7 -7 -7 -7]
          [-8 -8 -8 -8]]
         [[ 0  0  0  0]
          [ 0  0  0  0]
          [ 0  0  0  0]
          [ 0  0  0  0]]]
    """
    scatter_nd_sub_inner = _get_cache_prim(P.ScatterNdSub)(use_locking)
    return scatter_nd_sub_inner(input_x, indices, updates)


def scatter_nd_mul(input_x, indices, updates, use_locking=False):
    r"""
    Applies sparse multiplication to individual values or slices in a tensor.

    Using given values to update parameter value through the multiplication operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    `input_x` has rank P and `indices` has rank Q, where `Q >= 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where `N <= P`.

    The last dimension of `indices` (with length `N` ) indicates slices along the `N` th dimension of `input_x`.

    `updates` is a tensor of rank `Q-1+P-N`. Its shape is:
    :math:`(i_0, i_1, ..., i_{Q-2}, x\_shape_N, ..., x\_shape_{P-1})`.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)`, where :math:`*` means any number of additional dimensions.
        indices (Tensor): The index to do multiplication operation whose data type must be mindspore.int32.
            The rank of indices must be at least 2 and `indices.shape[-1] <= len(shape)`.
        updates (Tensor): The tensor to do the multiplication operation with `input_x`.
            The data type is same as `input_x`, and the shape is `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        use_locking (bool): Whether to protect the assignment by a lock. Default: False.

    Returns:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `use_locking` is not a bool.
        TypeError: If `indices` is not an int32.
        TypeError: If dtype of `input_x` and `updates` are not the same.
        ValueError: If the shape of `updates` is not equal to `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([1, 2, 3, 4, 5, 6, 7, 8]), mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[2], [4], [1], [7]]), mindspore.int32)
        >>> updates = Tensor(np.array([6, 7, 8, 9]), mindspore.float32)
        >>> scatter_nd_mul = ops.ScatterNdMul()
        >>> output = scatter_nd_mul(input_x, indices, updates)
        >>> print(output)
        [ 1. 16. 18.  4. 35.  6.  7. 72.]
        >>> input_x = Parameter(Tensor(np.ones((4, 4, 4)), mindspore.int32))
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]]]), mindspore.int32)
        >>> output = ops.scatter_nd_mul(input_x, indices, updates)
        >>> print(output)
        [[[1 1 1 1]
          [2 2 2 2]
          [3 3 3 3]
          [4 4 4 4]]
         [[1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]]
         [[5 5 5 5]
          [6 6 6 6]
          [7 7 7 7]
          [8 8 8 8]]
         [[1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]]]
    """
    scatter_nd_mul_inner = _get_cache_prim(ScatterNdMul)(use_locking)
    return scatter_nd_mul_inner(input_x, indices, updates)


def scatter_nd_div(input_x, indices, updates, use_locking=False):
    r"""
    Applying sparse division to individual values or slices in a tensor.

    Using given values to update tensor value through the div operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    `input_x` has rank P and `indices` has rank Q, where `Q >= 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where `N <= P`.

    The last dimension of `indices` (with length `N` ) indicates slices along the `N` th dimension of `input_x`.

    `updates` is a tensor of rank `Q-1+P-N`. Its shape is:
    :math:`(i_0, i_1, ..., i_{Q-2}, x\_shape_N, ..., x\_shape_{P-1})`.

    Inputs of `input_x` and `updates` comply with the implicit type of conversion rules to make the data types
    consistent.
    If they have different data types, the lower priority data type will be converted to the
    relatively higher priority data type.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)`, where :math:`*` means any number of additional dimensions.
        indices (Tensor): The index to do div operation whose data type must be mindspore.int32 or mindspore.int64.
            The rank of indices must be at least 2 and `indices.shape[-1] <= len(shape)`.
        updates (Tensor): The tensor to do the div operation with `input_x`.
            The data type is same as `input_x`, and the shape is `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        use_locking (bool): Whether to protect the assignment by a lock. Default: False.

    Returns:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `use_locking` is not a bool.
        TypeError: If `indices` is not an int32 or an int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([1, 2, 3, 4, 5, 6, 7, 8]), mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[2], [4], [1], [7]]), mindspore.int32)
        >>> updates = Tensor(np.array([6, 7, 8, 9]), mindspore.float32)
        >>> output = ops.scatter_nd_div(input_x, indices, updates, False)
        >>> print(output)
        [1.         0.25       0.5        4.         0.71428573 6.
         7.         0.8888889 ]
        >>> input_x = Parameter(Tensor(np.ones((4, 4, 4)), mindspore.float32))
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]]]), mindspore.float32)
        >>> output = ops.scatter_nd_div(input_x, indices, updates, False)
        >>> print(output)
        [[[1.         1.         1.         1.        ]
          [0.5        0.5        0.5        0.5       ]
          [0.33333334 0.33333334 0.33333334 0.33333334]
          [0.25       0.25       0.25       0.25      ]]
         [[1.         1.         1.         1.        ]
          [1.         1.         1.         1.        ]
          [1.         1.         1.         1.        ]
          [1.         1.         1.         1.        ]]
         [[0.2        0.2        0.2        0.2       ]
          [0.16666667 0.16666667 0.16666667 0.16666667]
          [0.14285715 0.14285715 0.14285715 0.14285715]
          [0.125      0.125      0.125      0.125     ]]
         [[1.         1.         1.         1.        ]
          [1.         1.         1.         1.        ]
          [1.         1.         1.         1.        ]
          [1.         1.         1.         1.        ]]]
    """
    scatter_nd_div_inner = _get_cache_prim(P.ScatterNdDiv)(use_locking)
    return scatter_nd_div_inner(input_x, indices, updates)


def scatter_nd_max(input_x, indices, updates, use_locking=False):
    r"""
    Applying sparse maximum to individual values or slices in a tensor.

    Using given values to update parameter value through the max operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    `input_x` has rank P and `indices` has rank Q where `Q >= 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where `N <= P`.

    The last dimension of `indices` (with length `N` ) indicates slices along the `N` th dimension of `input_x`.

    `updates` is a tensor of rank `Q-1+P-N`. Its shape is:
    :math:`(i_0, i_1, ..., i_{Q-2}, x\_shape_N, ..., x\_shape_{P-1})`.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)`, where :math:`*` means any number of additional dimensions.
        indices (Tensor): The index to do maximum operation whose data type must be mindspore.int32.
            The rank of indices must be at least 2 and `indices.shape[-1] <= len(shape)`.
        updates (Tensor): The tensor to do the max operation with `input_x`.
            The data type is same as `input_x`, and the shape is `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        use_locking (bool): Whether to protect the assignment by a lock. Default: False.

    Returns:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `use_locking` is not a bool.
        TypeError: If `indices` is not an int32.
        TypeError: If dtype of `input_x` and `updates` are not the same.
        ValueError: If the shape of `updates` is not equal to `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.ones(8) * 10, mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[2], [4], [1], [7]]), mindspore.int32)
        >>> updates = Tensor(np.array([6, 7, 8, 9]), mindspore.float32)
        >>> output = ops.scatter_nd_max(input_x, indices, updates, False)
        >>> print(output)
        [ 1. 8. 6.  4. 7.  6.  7. 9.]
        >>> input_x = Parameter(Tensor(np.ones((4, 4, 4)) * 10, mindspore.int32))
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]]]), mindspore.int32)
        >>> output = ops.scatter_nd_max(input_x, indices, updates, False)
        >>> print(output)
        [[[1 1 1 1]
          [2 2 2 2]
          [3 3 3 3]
          [4 4 4 4]]
         [[1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]]
         [[5 5 5 5]
          [6 6 6 6]
          [7 7 7 7]
          [8 8 8 8]]
         [[1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]
          [1 1 1 1]]]
    """
    scatter_nd_max_inner = _get_cache_prim(ScatterNdMax)(use_locking)
    return scatter_nd_max_inner(input_x, indices, updates)


def scatter_nd_min(input_x, indices, updates, use_locking=False):
    r"""
    Applying sparse minimum to individual values or slices in a tensor.

    Using given values to update tensor value through the min operation, along with the input indices.
    This operation outputs the `input_x` after the update is done, which makes it convenient to use the updated value.

    `input_x` has rank P and `indices` has rank Q where `Q >= 2`.

    `indices` has shape :math:`(i_0, i_1, ..., i_{Q-2}, N)` where `N <= P`.

    The last dimension of `indices` (with length `N` ) indicates slices along the `N` th dimension of `input_x`.

    `updates` is a tensor of rank `Q-1+P-N`. Its shape is:
    :math:`(i_0, i_1, ..., i_{Q-2}, x\_shape_N, ..., x\_shape_{P-1})`.

    Inputs of `input_x` and `updates` comply with the implicit type of conversion rules to make the data types
    consistent.
    If they have different data types, the lower priority data type will be converted to the
    relatively higher priority data type.

    Args:
        input_x (Parameter): The target tensor, with data type of Parameter.
            The shape is :math:`(N,*)`, where :math:`*` means any number of additional dimensions.
        indices (Tensor): The index to do min operation whose data type must be mindspore.int32 or mindspore.int64.
            The rank of indices must be at least 2 and `indices.shape[-1] <= len(shape)`.
        updates (Tensor): The tensor to do the min operation with `input_x`.
            The data type is same as `input_x`, and the shape is `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        use_locking (bool): Whether to protect the assignment by a lock. Default: False.

    Returns:
        Tensor, the updated `input_x`, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `use_locking` is not a bool.
        TypeError: If `indices` is not an int32 or an int64.
        ValueError: If the shape of `updates` is not equal to `indices.shape[:-1] + x.shape[indices.shape[-1]:]`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                      is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.ones(8) * 10, mindspore.float32), name="x")
        >>> indices = Tensor(np.array([[2], [4], [1], [7]]), mindspore.int32)
        >>> updates = Tensor(np.array([6, 7, 8, 9]), mindspore.float32)
        >>> output = ops.scatter_nd_min(input_x, indices, updates, False)
        >>> print(output)
        [10.  8.  6. 10.  7. 10. 10.  9.]
        >>> input_x = Parameter(Tensor(np.ones((4, 4, 4)) * 10, mindspore.int32))
        >>> indices = Tensor(np.array([[0], [2]]), mindspore.int32)
        >>> updates = Tensor(np.array([[[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]],
        ...                            [[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]]]), mindspore.int32)
        >>> output = ops.scatter_nd_min(input_x, indices, updates, False)
        >>> print(output)
        [[[ 1  1  1  1]
          [ 2  2  2  2]
          [ 3  3  3  3]
          [ 4  4  4  4]]
         [[10 10 10 10]
          [10 10 10 10]
          [10 10 10 10]
          [10 10 10 10]]
         [[ 5  5  5  5]
          [ 6  6  6  6]
          [ 7  7  7  7]
          [ 8  8  8  8]]
         [[10 10 10 10]
          [10 10 10 10]
          [10 10 10 10]
          [10 10 10 10]]]
    """
    scatter_nd_min_inner = _get_cache_prim(P.ScatterNdMin)(use_locking)
    return scatter_nd_min_inner(input_x, indices, updates)


def gather(input_params, input_indices, axis):
    r"""
    Returns the slice of the input tensor corresponding to the elements of `input_indices` on the specified `axis`.

    The following figure shows the calculation process of Gather commonly:

    .. image:: Gather.png

    where params represents the input `input_params`, and indices represents the index to be sliced `input_indices`.

    .. note::
         1. The value of input_indices must be in the range of `[0, input_param.shape[axis])`, the result is undefined
            out of range.

         2. The data type of input_params cannot be
            `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ on Ascend
            platform currently.

    Args:
        input_params (Tensor): The original Tensor. The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        input_indices (Tensor): Index tensor to be sliced, the shape of tensor is :math:`(y_1, y_2, ..., y_S)`.
            Specifies the indices of elements of the original Tensor. The data type can be int32 or int64.
        axis (int): Specifies the dimension index to gather indices.

    Returns:
        Tensor, the shape of tensor is
        :math:`input\_params.shape[:axis] + input\_indices.shape + input\_params.shape[axis + 1:]`.

    Raises:
        TypeError: If `axis` is not an int.
        TypeError: If `input_params` is not a tensor.
        TypeError: If `input_indices` is not a tensor of type int.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> # case1: input_indices is a Tensor with shape (5, ).
        >>> input_params = Tensor(np.array([1, 2, 3, 4, 5, 6, 7]), mindspore.float32)
        >>> input_indices = Tensor(np.array([0, 2, 4, 2, 6]), mindspore.int32)
        >>> axis = 0
        >>> output = ops.gather(input_params, input_indices, axis)
        >>> print(output)
        [1. 3. 5. 3. 7.]
        >>> # case2: input_indices is a Tensor with shape (2, 2). When the input_params has one dimension,
        >>> # the output shape is equal to the input_indices shape.
        >>> input_indices = Tensor(np.array([[0, 2], [2, 6]]), mindspore.int32)
        >>> axis = 0
        >>> output = ops.gather(input_params, input_indices, axis)
        >>> print(output)
        [[ 1. 3.]
         [ 3. 7.]]
        >>> # case3: input_indices is a Tensor with shape (2, ) and
        >>> # input_params is a Tensor with shape (3, 4) and axis is 0.
        >>> input_params = Tensor(np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]), mindspore.float32)
        >>> input_indices = Tensor(np.array([0, 2]), mindspore.int32)
        >>> axis = 0
        >>> output = ops.gather(input_params, input_indices, axis)
        >>> print(output)
        [[1.  2.  3.  4.]
         [9. 10. 11. 12.]]
        >>> # case4: input_indices is a Tensor with shape (2, ) and
        >>> # input_params is a Tensor with shape (3, 4) and axis is 1.
        >>> input_params = Tensor(np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]), mindspore.float32)
        >>> input_indices = Tensor(np.array([0, 2]), mindspore.int32)
        >>> axis = 1
        >>> output = ops.gather(input_params, input_indices, axis)
        >>> print(output)
        [[1.  3.]
         [5.  7.]
         [9. 11.]]
    """
    return gather_(input_params, input_indices, axis)


def gather_d(x, dim, index):
    """
    Gathers elements along an axis specified by dim.

    Refer to :func:`mindspore.ops.gather_elements` for more detail.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([[1, 2], [3, 4]]), mindspore.int32)
        >>> index = Tensor(np.array([[0, 0], [1, 0]]), mindspore.int32)
        >>> dim = 1
        >>> output = ops.gather_d(x, dim, index)
        >>> print(output)
        [[1 1]
         [4 3]]
    """
    return gather_d_(x, dim, index)


def gather_elements(x, dim, index):
    """
    Gathers elements along an axis specified by dim.

    For a 3-D tensor, the output is:

    .. code-block::

        output[i][j][k] = x[index[i][j][k]][j][k]  # if dim == 0

        output[i][j][k] = x[i][index[i][j][k]][k]  # if dim == 1

        output[i][j][k] = x[i][j][index[i][j][k]]  # if dim == 2

    `x` and `index` have the same length of dimensions, and all dimensions except `dim` have the same size.
    If `dim` = i, `x` is an n-D tensor with shape :math:`(z_0, z_1, ..., z_i, ..., z_{n-1})`,
    the `index` must be an n-D tensor with shape :math:`(z_0, z_1, ..., y, ..., z_{n-1})`
    where `y`>=1 and the output will have the same shape with `index`.

    Args:
        x (Tensor): The input tensor.
        dim (int): The axis along which to index. It must be int32 or int64. The value range is [-x_rank, x_rank).
        index (Tensor): The indices of elements to gather. It can be one of the following data types:
            int32, int64. The value range of each index element is [-x_rank[dim], x_rank[dim]).

    Returns:
        Tensor, the shape of tensor is :math:`(z_1, z_2, ..., z_{n-1})`, has the same data type with `x`.

    Raises:
        TypeError: If dtype of `dim` or `index` is neither int32 nor int64.
        ValueError: If length of shape of `x` is not equal to length of shape of `index`.
        ValueError: If the size of the dimension except `dim` is not equal between `x` and `index`.
        ValueError: If the value of `dim` is not in the expected range.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore
        >>> from mindspore import Tensor
        >>> x = Tensor(np.array([[1, 2], [3, 4]]), mindspore.int32)
        >>> index = Tensor(np.array([[0, 0], [1, 0]]), mindspore.int32)
        >>> dim = 1
        >>> output = mindspore.ops.gather_elements(x, dim, index)
        >>> print(output)
        [[1 1]
         [4 3]]
    """
    return gather_d_(x, dim, index)


def gather_nd(input_x, indices):
    r"""
    Gathers slices from a tensor by indices.

    Using given indices to gather slices from a tensor with a specified shape.

    `indices` is an K-dimensional integer tensor. Supposes it as a (K-1)-dimensional tensor and each element of it
    defines a slice of `input_x`:

    .. math::
        output[(i_0, ..., i_{K-2})] = input\_x[indices[(i_0, ..., i_{K-2})]]

    The last dimension of `indices` can not more than the rank of `input_x`:
    :math:`indices.shape[-1] <= input\_x.rank`.

    Args:
        input_x (Tensor): The target tensor to gather values.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index tensor, with int32 or int64 data type.

    Returns:
        Tensor, has the same type as `input_x` and the shape is
        :math:`indices\_shape[:-1] + input\_x\_shape[indices\_shape[-1]:]`.

    Raises:
        ValueError: If length of shape of `input_x` is less than the last dimension of `indices`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> indices = Tensor(np.array([[0, 0], [1, 1]]), mindspore.int32)
        >>> output = ops.gather_nd(input_x, indices)
        >>> print(output)
        [-0.1  0.5]
    """
    return gather_nd_(input_x, indices)


def tensor_scatter_add(input_x, indices, updates):
    """
    Creates a new tensor by adding the values from the positions in `input_x` indicated by
    `indices`, with values from `updates`. When multiple values are given for the same
    index, the updated result will be the sum of all values. This operation is almost
    equivalent to using ScatterNdAdd, except that the updates are applied on output `Tensor`
    instead of input `Parameter`.

    The last axis of `indices` is the depth of each index vectors. For each index vector,
    there must be a corresponding value in `updates`. The shape of `updates` should be
    equal to the shape of `input_x[indices]`. For more details, see use cases.

    Note:
        If some values of the `indices` are out of bound, instead of raising an index error,
        the corresponding `updates` will not be updated to `input_x`.

    Args:
        - **input_x** (Tensor) - The target tensor. The dimension of input_x must be no less than indices.shape[-1].
        - **indices** (Tensor) - The index of input tensor whose data type is int32 or int64.
          The rank must be at least 2.
        - **updates** (Tensor) - The tensor to update the input tensor, has the same type as input,
          and updates. Shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If dtype of `indices` is neither int32 nor int64.
        ValueError: If length of shape of `input_x` is less than the last dimension of shape of `indices`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor, nn
        >>> from mindspore import ops
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> indices = Tensor(np.array([[0, 0], [0, 0]]), mindspore.int32)
        >>> updates = Tensor(np.array([1.0, 2.2]), mindspore.float32)
        >>> output = ops.tensor_scatter_add(input_x, indices, updates)
        >>> print(output)
        [[ 3.1  0.3  3.6]
         [ 0.4  0.5 -3.2]]
    """

    return tensor_scatter_add_(input_x, indices, updates)


def tensor_scatter_sub(input_x, indices, updates):
    """
    Creates a new tensor by subtracting the values from the positions in `input_x` indicated by
    `indices`, with values from `updates`. When multiple values are provided for the same
    index, the result of the update will be to subtract these values respectively. This operation is almost
    equivalent to using :class:`mindspore.ops.ScatterNdSub` , except that the updates are applied on output `Tensor`
    instead of input `Parameter`.

    The last axis of `indices` is the depth of each index vectors. For each index vector,
    there must be a corresponding value in `updates`. The shape of `updates` should be
    equal to the shape of `input_x[indices]`. For more details, see use cases.

    Note:
        If some values of the `indices` are out of bound, instead of raising an index error,
        the corresponding `updates` will not be updated to `input_x`.

    Args:
        input_x (Tensor): The target tensor. The dimension of input_x must be no less than indices.shape[-1].
        indices (Tensor): The index of input tensor whose data type is int32 or int64.
            The rank must be at least 2.
        updates (Tensor): The tensor to update the input tensor, has the same type as input,
            and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If dtype of `indices` is neither int32 nor int64.
        ValueError: If length of shape of `input_x` is less than the last dimension of shape of `indices`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> indices = Tensor(np.array([[0, 0], [0, 0]]), mindspore.int32)
        >>> updates = Tensor(np.array([1.0, 2.2]), mindspore.float32)
        >>> output = ops.tensor_scatter_sub(input_x, indices, updates)
        >>> print(output)
        [[-3.3000002  0.3        3.6      ]
         [ 0.4        0.5       -3.2      ]]
    """

    return tensor_scatter_sub_(input_x, indices, updates)


def tensor_scatter_max(input_x, indices, updates):
    """
    By comparing the value at the position indicated by `indices` in `x` with the value in the `updates`,
    the value at the index will eventually be equal to the largest one to create a new tensor.

    The last axis of the index is the depth of each index vector. For each index vector,
    there must be a corresponding value in `updates`. The shape of `updates` should be
    equal to the shape of input_x[indices].
    For more details, see use cases.

    Note:
        If some values of the `indices` are out of bound, instead of raising an index error,
        the corresponding `updates` will not be updated to `input_x`.

    Args:
        input_x (Tensor): The target tensor. The dimension of input_x must be no less than indices.shape[-1].
        indices (Tensor): The index of input tensor whose data type is int32 or int64.
            The rank must be at least 2.
        updates (Tensor): The tensor to update the input tensor, has the same type as input,
            and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

        Tensor, has the same shape and type as `input_x`.
    Raises:
        TypeError: If dtype of `indices` is neither int32 nor int64.
        ValueError: If length of shape of `input_x` is less than the last dimension of shape of `indices`.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> indices = Tensor(np.array([[0, 0], [0, 0]]), mindspore.int32)
        >>> updates = Tensor(np.array([1.0, 2.2]), mindspore.float32)
        >>> # Next, demonstrate the approximate operation process of this operator:
        >>> # 1, indices[0] = [0, 0], indices[1] = [0, 0]
        >>> # 2, And input_x[0, 0] = -0.1
        >>> # 3, So input_x[indices] = [-0.1, -0.1]
        >>> # 4, Satisfy the above formula: input_x[indices].shape=(2) == updates.shape=(2)
        >>> op = ops.TensorScatterMax()
        >>> # 5, Perform the max operation for the first time:
        >>> #      first_input_x = Max(input_x[0][0], updates[0]) = [[2.2, 0.3, 3.6], [0.4, 0.5, -3.2]]
        >>> # 6, Perform the max operation for the second time:
        >>> #      second_input_x = Max(input_x[0][0], updates[0]) = [[2.2, 0.3, 3.6], [0.4, 0.5, -3.2]]
        >>> output = op(input_x, indices, updates)
        >>> print(output)
        [[ 2.2  0.3  3.6]
         [ 0.4  0.5 -3.2]]
    """
    return tensor_scatter_max_(input_x, indices, updates)


def tensor_scatter_min(input_x, indices, updates):
    """
    By comparing the value at the position indicated by `indices` in `input_x` with the value in the `updates`,
    the value at the index will eventually be equal to the smallest one to create a new tensor.

    The last axis of the index is the depth of each index vector. For each index vector,
    there must be a corresponding value in `updates`. The shape of `updates` should be
    equal to the shape of `input_x[indices]`. For more details, see case below.

    Note:
        If some values of the `indices` are out of range, instead of raising an index error,
        the corresponding `updates` will not be hw to `input_x`.

    Args:
        input_x (Tensor): The input tensor. The dimension of input_x must be no less than indices.shape[-1].
        indices (Tensor): The index of input tensor whose data type is int32 or int64.
            The rank must be at least 2.
        updates (Tensor): The tensor to update the input tensor, has the same type as input,
            and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If dtype of `indices` is neither int32 nor int64.
        ValueError: If length of shape of `input_x` is less than the last dimension of shape of `indices`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]).astype('float32'))
        >>> indices = Tensor(np.array([[0, 0], [0, 0]]).astype('int32'))
        >>> updates = Tensor(np.array([1.0, 2.2]).astype('float32'))
        >>> output = x.tensor_scatter_min(indices, updates)
        >>> print(output)
        [[ -0.1  0.3  3.6]
        [ 0.4  0.5 -3.2]]
    """
    return tensor_scatter_min_(input_x, indices, updates)


def tensor_scatter_elements(input_x, indices, updates, axis=0, reduction="none"):
    """
    Updates the value of the input tensor through the reduction operation.

    tensor_scatter_elements takes three inputs data, updates, and indices of the same rank r >= 1,
    an optional attribute axis that identifies an axis of data (default is 0),  and another optional attribute reduction
    that identifies reduction operation. When reduction is set to "none", the update value will be assigned to the
    output value according to the indices. When reduction is set to "add", the update value will be added to the output
    value according to the indices.

    For a 3-D tensor, the output is:

    .. code-block::

    output[indices[i][j][k]][j][k] = updates[i][j][k]  # if axis == 0, reduction == "none"

    output[i][indices[i][j][k]][k] += updates[i][j][k]  # if axis == 1, reduction == "add"

    output[i][j][indices[i][j][k]] = updates[i][j][k]  # if axis == 2, reduction == "none"

    .. warning::
        The order in which updates are applied is nondeterministic, meaning that if there
        are multiple index vectors in `indices` that correspond to the same position, the
        value of that position in the output will be nondeterministic.

    .. note::
        If some values of the `indices` are out of bound, instead of raising an index error,
        the corresponding `updates` will not be updated to `input_x`.

    Args:
        input_x (Tensor): The target tensor.
          The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        indices (Tensor): The index to do add operation whose data type must be mindspore.int32 or
          mindspore.int64. Same rank as input_x. And accepted range is [-s, s) where s is the size along axis.
        updates (Tensor): The tensor doing the add operation with `input_x`, has the same type as input_x,
          and update.shape should be equal to indices.shape.
        axis (int): Which axis to scatter, default is 0. Accepted range is [-r, r) where r = rank(input_x).
        reduction (string): Which reduction operation to scatter, default is "none". Other option: "add".

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If `indices` is neither int32 nor int64.
        ValueError: If anyone of the rank among `input_x`, `indices` and `updates` less than 1.
        ValueError: If the shape of `updates` is not equal to the shape of `indices`.
        ValueError: If the rank of `updates` is not equal to the rank of `input_x`.
        RuntimeError: If the data type of `input_x` and `updates` conversion of Parameter
                        is required when data type conversion of Parameter is not supported.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Parameter(Tensor(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), mindspore.float32), name="input_x")
        >>> indices = Tensor(np.array([[1, 0, 2], [0, 2, 1]]), mindspore.int32)
        >>> updates = Tensor(np.array([[1, 1, 1], [1, 1, 1]]), mindspore.float32)
        >>> axis = 0
        >>> reduction = "add"
        >>> output = tensor_scatter_elements(input_x, indices, updates, axis, reduction)
        >>> print(output)
        [[ 2.0  3.0  3.0]
         [ 5.0  5.0  7.0]
         [ 7.0  9.0  10.0]]
        >>> input_x = Parameter(Tensor(np.array([[1, 2, 3, 4, 5]]), mindspore.int32), name="x")
        >>> indices = Tensor(np.array([[2, 4]]), mindspore.int32)
        >>> updates = Tensor(np.array([[8, 8]]), mindspore.int32)
        >>> axis = 1
        >>> reduction = "none"
        >>> output = tensor_scatter_elements(input_x, indices, updates, axis, reduction)
        >>> print(output)
        [[ 1  2  8  4  8]]
    """
    tensor_scatter_elements_ = TensorScatterElements(axis, reduction)
    return tensor_scatter_elements_(input_x, indices, updates)


def space_to_batch_nd(input_x, block_size, paddings):
    r"""
    Divides a tensor's spatial dimensions into blocks and combines the block sizes with the original batch.

    This operation will divide spatial dimensions into blocks with `block_size`,
    and after division, the output tensor's spatial dimension is the corresponding number of blocks.
    The output tensor's batch dimension is the product of the original batch and the product of `block_size`.
    Before division, the spatial dimensions of the input are zero padded according to paddings if necessary.
    Assume input shape is :math:`(n, c_1, ... c_k, w_1, ..., w_M)` with
    :math:`block\_size` and :math:`paddings`. Then the shape of the output tensor will be
    :math:`(n', c_1, ... c_k, w'_1, ..., w'_M)`, where

    .. math::
        \begin{array}{ll} \\
            n' = n*(block\_size[0] * ... * block\_size[M]) \\
            w'_i = (w_i + paddings[i][0] + paddings[i][1])//block\_size[i]
        \end{array}

    Args:
        input_x (Tensor): The input tensor. It must be a 4-D tensor on Ascend.
        block_size (Union[list(int), tuple(int), int]): The block size of dividing block with all value greater
            than 1. If `block_size` is a tuple or list, the length of `block_size` is M corresponding to the
            number of spatial dimensions. If `block_size` is an int, the block size of M dimensions are the same,
            equal to `block_size`. M must be 2 on Ascend.
        paddings (Union[tuple, list]): The padding values for spatial dimensions, containing M subtraction list.
            Each contains 2 integer values. All values must be greater than 0.
            `paddings[i]` specifies the paddings for the spatial dimension i,
            which corresponds to the input dimension i + offset.
            It is required that input_shape[i+offset]+paddings[i][0]+paddings[i][1] is divisible by block_size[i].
            M must be 2 on Ascend.

    Returns:
        Tensor, the output tensor with the same data type as input.

    Raises:
        ValueError: If `block_size` is not one dimensional when `block_size` is a list or tuple.
        ValueError: If the length of `block_size` is not 2 on Ascend.
        ValueError: If the element of `block_size` is not an integer larger than 1.
        ValueError: If shape of `paddings` is not (2, M), where M is the length of `block_size`.
        ValueError: If the element of `paddings` is not an integer larger than 0.
        TypeError: If `block_size` is not one of list, tuple, int.
        TypeError: If `paddings` is neither list nor tuple.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> block_size = [2, 2]
        >>> paddings = [[0, 0], [0, 0]]
        >>> input_x = Tensor(np.array([[[[1, 2], [3, 4]]]]), mindspore.float32)
        >>> output = ops.space_to_batch_nd(input_x, block_size, paddings)
        >>> print(output)
        [[[[1.]]]
         [[[2.]]]
         [[[3.]]]
         [[[4.]]]]
    """
    _space_to_batch_nd = _get_cache_prim(P.SpaceToBatchND)(block_size, paddings)
    return _space_to_batch_nd(input_x)


def batch_to_space_nd(input_x, block_shape, crops):
    r"""
    Divides batch dimension with blocks and interleaves these blocks back into spatial dimensions.

    This operation will divide batch dimension N into blocks with block_shape, the output tensor's N dimension
    is the corresponding number of blocks after division. The output tensor's H, W dimension is the product of
    original H, W dimension and block_shape with given amount to crop from dimension, respectively.

    Args:
        input_x (Tensor): The input tensor. It must be greater or equal to 4-D tensor(equal to 4-D tensor on Ascend),
            batch dimension must be divisible by product of `block_shape`. The data type is float16 or float32.
        block_shape (Union[list(int), tuple(int), int]): The block shape of dividing block with all value greater
            than 1. If `block_shape` is a tuple or list, the length of `block_shape` is M corresponding to the
            number of spatial dimensions. If `block_shape` is an int, the block size of M dimensions are the same,
            equal to `block_shape`. M must be 2.
        crops (Union[list(int), tuple(int)]): The crop value for H and W dimension, containing 2 subtraction list,
            each containing 2 int value.
            All values must be >= 0. crops[i] specifies the crop values for spatial dimension i, which corresponds to
            input dimension i+2. It is required that

            :math:`input\_shape[i+2]*block\_shape[i] > crops[i][0]+crops[i][1]`

    Returns:
        Tensor, the output tensor with the same type as input. Assume input shape is (n, c, h, w) with block_shape
        and crops. The output shape will be (n', c', h', w'), where

        :math:`n' = n//(block\_shape[0]*block\_shape[1])`

        :math:`c' = c`

        :math:`h' = h*block\_shape[0]-crops[0][0]-crops[0][1]`

        :math:`w' = w*block\_shape[1]-crops[1][0]-crops[1][1]`

    Raises:
        TypeError: If `block_shape` is not one of list, tuple, int.
        TypeError: If `crops` is neither list nor tuple.
        ValueError: If `block_shape` is not one dimensional when `block_shape` is a list or tuple.
        ValueError: If length of `block_shape` or `crops` is not equal to 2.
        ValueError: If the element of `block_shape` is not an integer larger than 1.
        ValueError: If shape of `crops` is not (M, 2), where M is the length of `block_shape`.
        ValueError: If the element of `crops` is not an integer larger than 0.

    Supported Platforms:
        ``Ascend`` ``CPU``

    Examples:
        >>> block_shape = [2, 2]
        >>> crops = [[0, 0], [0, 0]]
        >>> input_x = Tensor(np.array([[[[1]]], [[[2]]], [[[3]]], [[[4]]]]), mindspore.float32)
        >>> output = ops.batch_to_space_nd(input_x, block_shape, crops)
        >>> print(output)
        [[[[1.  2.]
           [3.  4.]]]]
    """
    _batch_to_space_nd = _get_cache_prim(P.BatchToSpaceND)(block_shape, crops)
    return _batch_to_space_nd(input_x)


def nonzero(x):
    """
    Return a tensor of the positions of all non-zero values.

    Args:
        x (int): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`. The data type is Number or Bool.

    Returns:
        y (Tensor): The shape of tensor is 2-D. The data type is int64.

    Raises:
       TypeError: If `x` is not Tensor.
       ValueError: If 'x' dim equal to 0.

    Supported Platforms:
       ``GPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> import mindspore.ops as ops
        >>> x = Tensor(np.array([[[1,  0], [-5, 0]]]), mindspore.int32)
        >>> nonzero = ops.nonzero()
        >>> output = nonzero(x)
        >>> print(output)
        [[0 0 0]
         [0 1 0]]
    """
    return nonzero_(x)


def matrix_diag(x, k=0, num_rows=-1, num_cols=-1, padding_value=0, align="RIGHT_LEFT"):
    r"""
    Returns a Tensor with the contents in `x` as k[0]-th to k[1]-th diagonals of a matrix, with everything else padded
    with `padding_value`. `num_rows` and `num_cols` specify the dimension of the innermost matrix of the output. If both
    are not specified, the op assumes the innermost matrix of output Tensor is square and infers its size from `k` and
    the innermost dimension of `x`. If the `num_rows` and `num_cols` specify only one of them, the operator will derive
    the smallest legal value as the dimension of output. Moreover, when only one diagonal is given
    (k is an integer or k[0] == k[1]), the first to the second innermost dimension of `x` is the batch size. Otherwise,
    the second innermost dimension is not a part of batch size.

    Args:
        x (Tensor): The diagonal Tensor.
        k (Union[int, Tensor], optional): A Tensor of type int32. Diagonal offsets. Positive value means superdiagonal,
          0 refers to the main diagonal, and negative value means subdiagonals. `k` can be a single integer
          (for a single diagonal) or a pair of integers specifying the low and high ends of a matrix band. k[0] must not
          be larger than k[1]. The value must be in the range of given or derivated `num_rows` and `num_cols`, meaning
          value of k must be in (-num_rows, num_cols). Default: 0.
        num_rows (Union[int, Tensor], optional): A Tensor of type int32 with only one value. The number of rows of the
          output Tensor. If `num_rows` is -1, indicating that the innermost matrix of the output Tensor is a square
          matrix, and the real number of rows will be derivated by other inputs. That is
          :math:`num_rows = x.shape[-1] - min(k[1], 0)`. Otherwise, the value must be equal or greater than
          :math:`x.shape[-1] - min(k[1], 0)`. Default: -1.
        num_cols (Union[int, Tensor], optional): A Tensor of type int32 with only one value. The number of columns of
          the output Tensor. If `num_cols` is -1, indicating that the innermost matrix of the output Tensor is a square
          matrix, and the real number of columns will be derivated by other inputs. That is
          :math:`num_cols = x.shape[-1] + max(k[0], 0)`. Otherwise, the value must be equal or greater than
          :math:`x.shape[-1] - min(k[1], 0)`.  Default: -1.
        padding_value (Union[int, float, Tensor], optional): A Tensor with only one value. Have the same dtype as x.
          The number to fill the area outside the specified diagonal band.  Default: 0.
        align (str): An optional string from: "RIGHT_LEFT"(default), "LEFT_RIGHT", "LEFT_LEFT", "RIGHT_RIGHT". Align
          is a string specifying how superdiagonals and subdiagonals should be aligned, respectively. "RIGHT_LEFT"
          aligns superdiagonals to the right (left-pads the row) and subdiagonals to the left (right-pads the row).

    Returns:
        A Tensor. Has the same type as `x`.
        Suppose `x` has r dimensions with shape `(I, J, ..., M, N)`. The output Tensor has rank r + 1 with shape
        `(I, J, ..., M, num_rows, num_cols)` when only one diagonal is given (k is an integer or k[0] == k[1]).
        Otherwise, it has rank r with shape `(I, J, ..., num_rows, num_cols)`.

    Raises:
        TypeError: If `x` is not Tensor.
        TypeError: If input `x` and `padding_value` are not the same dtype.
        TypeError: If `k`, `num_rows` or `num_cols` is not int32 dtype.
        ValueError: If rank of `k` is not equal to 0 or 1.
        ValueError: If rank of `num_rows`, `num_cols` or `padding_value` is not equal to 0.
        ValueError: If size of `k` is not equal to 1 or 2.
        ValueError: If the value of `k` is not in (-num_rows, num_cols).
        ValueError: If k[1] is not greater equal to k[0] when k[0] != k[1].
        ValueError: If rank of `x` is not greater than or is equal to 1 when k is an integer or k[0] == k[1].
        ValueError: If rank of `x` is not greater than or is equal to 2 when k[0] != k[1].
        ValueError: If x.shape[-2] is not equal to k[1] - k[0] + 1 when k[0] != k[1].
        ValueError: If `num_rows` and `num_cols` do not match the dimensions of `x` and the values of `k`.
        ValueError: If `align` is not a string or not in the valid set of values.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import mindspore
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> x = Tensor(np.array([[8, 9, 0],
        ...                      [1, 2, 3],
        ...                      [0, 4, 5]]), mindspore.float32)
        >>> k =Tensor(np.array([-1, 1]), mindspore.int32)
        >>> num_rows = Tensor(np.array(3), mindspore.int32)
        >>> num_cols = Tensor(np.array(3), mindspore.int32)
        >>> padding_value = Tensor(np.array(11), mindspore.float32)
        >>> output = ops.matrix_diag(x, k, num_rows, num_cols, padding_value, align='LEFT_RIGHT')
        >>> print(output)
        [[ 1.  8. 11.]
         [ 4.  2.  9.]
         [11.  5.  3.]]
        >>> print(output.shape)
        (3, 3)
    """
    if isinstance(k, int) and not isinstance(k, bool):
        k = cast_(k, mstype.int32)
    if isinstance(num_rows, int) and not isinstance(num_rows, bool):
        num_rows = cast_(num_rows, mstype.int32)
    if isinstance(num_cols, int) and not isinstance(num_cols, bool):
        num_cols = cast_(num_cols, mstype.int32)
    if isinstance(padding_value, (float, int)) and not isinstance(padding_value, bool):
        padding_value = cast_(padding_value, x.dtype)
    matrix_diag_v3 = _get_cache_prim(MatrixDiagV3)(align)
    return matrix_diag_v3(x, k, num_rows, num_cols, padding_value)


def matrix_diag_part(x, k=0, padding_value=0, align="RIGHT_LEFT"):
    r"""
    Returns the diagonal part of input tensor.
    Returns a tensor with the k[0]-th to k[1]-th diagonals of `x`. Some diagonals are shorter than
    max_diag_len and need to be padded. Input k and padding_value must be const Tensor when taking Graph mode.

    Args:
        x (Tensor): The input Tensor with rank r, where r >= 2.
        k (Union[int, Tensor], optional): A Tensor of type int32. Diagonal offset(s). Positive value means
          superdiagonal, 0 refers to the main diagonal, and negative value means subdiagonals. k can be a single integer
          (for a single diagonal) or a pair of integers specifying the low and high ends of a matrix band. k[0] must not
          be larger than k[1]. The value of k has restructions, meaning value of k must be in
          (-x.shape[-2], x.shape[-1]).
        padding_value (Union[int, float, Tensor], optional): A Tensor with only one value. Have the same dtype as x.
          The number to fill the area outside the specified diagonal band. Default: 0.
        align (str): An optional string from: "RIGHT_LEFT"(default), "LEFT_RIGHT", "LEFT_LEFT", "RIGHT_RIGHT". Align
          is a string specifying how superdiagonals and subdiagonals should be aligned, respectively. "RIGHT_LEFT"
          aligns superdiagonals to the right (left-pads the row) and subdiagonals to the left (right-pads the row).

    Returns:
        A Tensor. Has the same type as `x`.
        Assume `x` has r dimensions :math:`[I, J, ..., L, M, N]`. Let `max_diag_len` be the maximum length among all
        diagonals to be extracted, :math:`max_diag_len = min(M + min(k[1], 0), N + min(-k[0], 0))`
        Let `num_diags` be the number of diagonals to extract, :math:`num_diags = k[1] - k[0] + 1`.
        If :math:`num_diags == 1`, the output tensor is of rank r - 1 with shape :math:`[I, J, ..., L, max_diag_len]`
        Otherwise, the output tensor has rank r with dimensions :math:`[I, J, ..., L, num_diags, max_diag_len]`

    Raises:
        TypeError: If `x` is not Tensor.
        TypeError: If input `x` and `padding_value` are not the same dtype.
        TypeError: If `k` is not int32 dtype.
        ValueError: If `align` is not a string or not in the valid range.
        ValueError: If rank of `k` is not equal to 0 or 1.
        ValueError: If rank of `padding_value` is not equal to 0.
        ValueError: If rank of `x` is not greater equal to 2.
        ValueError: If size of `k` is not equal to 1 or 2.
        ValueError: If k[1] is not greater equal to k[0] in case the size of `k` is 2.
        ValueError: If the value of `k` is not in (-x.shape[-2], x.shape[-1]).

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([[1, 2, 3, 4],
        ...                      [5, 6, 7, 8],
        ...                      [9, 8, 7, 6]]), mindspore.float32)
        >>> k =Tensor(np.array([1, 3]), mindspore.int32)
        >>> padding_value = Tensor(np.array(9), mindspore.float32)
        >>> output = ops.matrix_diag_part(x, k, padding_value, align='RIGHT_LEFT')
        >>> print(output)
        [[9. 9. 4.]
         [9. 3. 8.]
         [2. 7. 6.]]
        >>> print(output.shape)
        (3, 3)
    """
    matrix_diag_part_v3 = _get_cache_prim(MatrixDiagPartV3)(align)
    return matrix_diag_part_v3(x, k, padding_value)


def meshgrid(inputs, indexing='xy'):
    """
    Generates coordinate matrices from given coordinate tensors.

    Given N one-dimensional coordinate tensors, returns a tuple outputs of N N-D
    coordinate tensors for evaluating expressions on an N-D grid.

    Args:
        inputs (Union[tuple]): A Tuple of N 1-D Tensor objects.
            The length of input should be greater than 1. The data type is Number.
        indexing ('xy', 'ij', optional): Cartesian ('xy', default) or
            matrix ('ij') indexing of output. In the 2-D case with
            inputs of length `M` and `N`, the outputs are of shape `(N, M)`
            for 'xy' indexing and `(M, N)` for 'ij' indexing. In the 3-D
            case with inputs of length `M`, `N` and `P`, outputs are of shape
            `(N, M, P)` for 'xy' indexing and `(M, N, P)` for 'ij' indexing.

    Returns:
        Tensors, A Tuple of N N-D Tensor objects. The data type is the same with the Inputs.

    Raises:
        TypeError: If `indexing` is not a str or `inputs` is not a tuple.
        ValueError: If `indexing` is neither 'xy' nor 'ij'.

    Supported Platforms:
        ``Ascend`` ``CPU`` ``GPU``

    Examples:
        >>> import numpy as np
        >>> from mindspore import Tensor
        >>> import mindspore.ops as ops
        >>> x = Tensor(np.array([1, 2, 3, 4]).astype(np.int32))
        >>> y = Tensor(np.array([5, 6, 7]).astype(np.int32))
        >>> z = Tensor(np.array([8, 9, 0, 1, 2]).astype(np.int32))
        >>> inputs = (x, y, z)
        >>> output = ops.meshgrid(inputs, indexing='xy')
        >>> print(output)
        (Tensor(shape=[3, 4, 5], dtype=Int32, value=
         [[[1, 1, 1, 1, 1],
           [2, 2, 2, 2, 2],
           [3, 3, 3, 3, 3],
           [4, 4, 4, 4, 4]],
          [[1, 1, 1, 1, 1],
           [2, 2, 2, 2, 2],
           [3, 3, 3, 3, 3],
           [4, 4, 4, 4, 4]],
          [[1, 1, 1, 1, 1],
           [2, 2, 2, 2, 2],
           [3, 3, 3, 3, 3],
           [4, 4, 4, 4, 4]]]),
         Tensor(shape=[3, 4, 5], dtype=Int32, value=
         [[[5, 5, 5, 5, 5],
           [5, 5, 5, 5, 5],
           [5, 5, 5, 5, 5],
           [5, 5, 5, 5, 5]],
          [[6, 6, 6, 6, 6],
           [6, 6, 6, 6, 6],
           [6, 6, 6, 6, 6],
           [6, 6, 6, 6, 6]],
          [[7, 7, 7, 7, 7],
           [7, 7, 7, 7, 7],
           [7, 7, 7, 7, 7],
           [7, 7, 7, 7, 7]]]),
         Tensor(shape=[3, 4, 5], dtype=Int32, value=
         [[[8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2]],
          [[8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2]],
          [[8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2],
           [8, 9, 0, 1, 2]]]))
    """
    meshgrid_op = _get_cache_prim(P.Meshgrid)(indexing)
    return meshgrid_op(inputs)


def broadcast_to(x, shape):
    """
    Broadcasts input tensor to a given shape.
    Input shape can be broadcast to target shape if for each dimension pair they are either equal or input is one or
    the target dimension is -1. In case of -1 in target shape, it will be replaced by the input shape's value
    in that dimension.
    When input shape is broadcast to target shape, it starts with the trailing
    dimensions. If there is a -1 in the target shape, the -1 cannot be in a leading,
    non-existing dimension.

    Args:
        x (Tensor): The input tensor. The data type should be one of the following types:
                    float16, float32, int32, int8, uint8, bool.
                    The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.
        shape (tuple): The target shape to broadcast. Can be fully specified, or have -1 in one position
                       where it will be substituted by the input tensor's shape in that position, see example.

    Returns:
        Tensor, with the given `shape` and the same data type as `x`.

    Raises:
        TypeError: If `shape` is not a tuple.
        ValueError: If the target and input shapes are incompatible, or if a - 1 in the target shape is in an invalid
                    location.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore.ops.function import broadcast_to
        >>> from mindspore import Tensor
        >>> shape = (2, 3)
        >>> x = Tensor(np.array([1, 2, 3]).astype(np.float32))
        >>> output = broadcast_to(x, shape)
        >>> print(output)
        [[1. 2. 3.]
         [1. 2. 3.]]
        >>> shape = (-1, 2)
        >>> x = Tensor(np.array([[1], [2]]).astype(np.float32))
        >>> output = broadcast_to(x, shape)
        >>> print(output)
        [[1. 1.]
         [2. 2.]]
    """
    _broadcast_to = _get_cache_prim(P.BroadcastTo)(shape)
    return _broadcast_to(x)


def unsorted_segment_min(x, segment_ids, num_segments):
    r"""
    Computes the minimum of a tensor along segments.

    The following figure shows the calculation process of unsorted_segment_min:

    .. image:: UnsortedSegmentMin.png

    .. math::

        \text { output }_i=\text{min}_{j \ldots} \text { data }[j \ldots]

    where :math:`min` over tuples :math:`j...` such that :math:`segment_ids[j...] == i`.

    Note:
        - If the segment_id i is absent in the segment_ids, then output[i] will be filled with
          the maximum value of the x's type.
        - The `segment_ids` must be non-negative tensor.

    Args:
        x (Tensor): The shape is :math:`(x_1, x_2, ..., x_R)`. With float16, float32 or int32 data type.
        segment_ids (Tensor): A `1-D` tensor whose shape is :math:`(x_1)`,
                              the value must be non-negative tensor. The data type must be int32.
        num_segments (int): The value specifies the number of distinct `segment_ids`.

    Returns:
        Tensor, set the number of `num_segments` as `N`, the shape is :math:`(N, x_2, ..., x_R)`.

    Raises:
        TypeError: If `num_segments` is not an int.
        ValueError: If length of shape of `segment_ids` is not equal to 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> import numpy as np
        >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6], [4, 2, 1]]).astype(np.float32))
        >>> segment_ids = Tensor(np.array([0, 1, 1]).astype(np.int32))
        >>> num_segments = 2
        >>> output = ops.unsorted_segment_min(x, segment_ids, num_segments)
        >>> print(output)
        [[1. 2. 3.]
         [4. 2. 1.]]
    """
    unsorted_segment_min_ = P.UnsortedSegmentMin()
    return unsorted_segment_min_(x, segment_ids, num_segments)


def unsorted_segment_max(x, segment_ids, num_segments):
    r"""
    Computes the maximum along segments of a tensor.

    The following figure shows the calculation process of unsorted_segment_max:

    .. image:: UnsortedSegmentMax.png

    .. math::

        \text { output }_i=\text{max}_{j \ldots} \text { data }[j \ldots]

    where :math:`max` over tuples :math:`j...` such that :math:`segment\_ids[j...] == i`.

    Note:
        - If the segment_id i is absent in the segment_ids, then output[i] will be filled with
          the minimum value of the x's type.
        - The `segment_ids` must be non-negative tensor.

    Args:
        x (Tensor): The shape is :math:`(x_1, x_2, ..., x_R)`. With float16, float32 or int32 data type.
        segment_ids (Tensor): A `1-D` tensor whose shape is :math:`(x_1)`,
                              the value must be non-negative tensor. The data type must be int32.
        num_segments (int): The value specifies the number of distinct `segment_ids`.

    Returns:
        Tensor, set the number of `num_segments` as `N`, the shape is :math:`(N, x_2, ..., x_R)`.

    Raises:
        TypeError: If `num_segments` is not an int.
        ValueError: If length of shape of `segment_ids` is not equal to 1.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> import numpy as np
        >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6], [4, 2, 1]]).astype(np.float32))
        >>> segment_ids = Tensor(np.array([0, 1, 1]).astype(np.int32))
        >>> num_segments = 2
        >>> output = ops.unsorted_segment_max(x, segment_ids, num_segments)
        >>> print(output)
        [[1. 2. 3.]
         [4. 5. 6.]]
    """
    unsorted_segment_max_ = P.UnsortedSegmentMax()
    return unsorted_segment_max_(x, segment_ids, num_segments)


def unsorted_segment_prod(x, segment_ids, num_segments):
    r"""
    Computes the product of a tensor along segments.

    The following figure shows the calculation process of UnsortedSegmentProd:

    .. image:: UnsortedSegmentProd.png

    Note:
        - If the segment_id i is absent in the segment_ids, then output[i] will be filled with 1.
        - The `segment_ids` must be non-negative tensor.

    Args:
        x (Tensor): The shape is :math:`(x_1, x_2, ..., x_R)`. With float16, float32 or int32 data type.
        segment_ids (Tensor): A `1-D` tensor whose shape is :math:`(x_1)`,
                              the value must be non-negative tensor. The data type must be int32.
        num_segments (int): The value specifies the number of distinct `segment_ids`.

    Returns:
        Tensor, set the number of `num_segments` as `N`, the shape is :math:`(N, x_2, ..., x_R)`.

    Raises:
        TypeError: If `num_segments` is not an int.
        ValueError: If length of shape of `segment_ids` is not equal to 1.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
        >>> from mindspore import Tensor
        >>> from mindspore import ops
        >>> import numpy as np
        >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6], [4, 2, 1]]).astype(np.float32))
        >>> segment_ids = Tensor(np.array([0, 1, 0]).astype(np.int32))
        >>> num_segments = 2
        >>> output = ops.unsorted_segment_prod(x, segment_ids, num_segments)
        >>> print(output)
        [[4. 4. 3.]
         [4. 5. 6.]]
    """
    unsorted_segment_prod_ = P.UnsortedSegmentProd()
    return unsorted_segment_prod_(x, segment_ids, num_segments)


def adaptive_max_pool2d(input_x, output_size, return_indices=False):
    r"""
    adaptive_max_pool2d operation.

    This operator applies a 2D adaptive max pooling to an input signal composed of multiple input planes.
    That is, for any input size, the size of the specified output is H x W.
    The number of output features is equal to the number of input planes.

    The input and output data format can be "NCHW" and "CHW". N is the batch size, C is the number of channels,
    H is the feature height, and W is the feature width.

    .. math::

        \begin{align}
        h_{start} &= floor(i * H_{in} / H_{out})\\
        h_{end} &= ceil((i + 1) * H_{in} / H_{out})\\
        w_{start} &= floor(j * W_{in} / W_{out})\\
        w_{end} &= ceil((j + 1) * W_{in} / W_{out})\\
        Output(i,j) &= {\max Input[h_{start}:h_{end}, w_{start}:w_{end}]}
        \end{align}

    Args:
        input_x (Tensor) - The input of adaptive_max_pool2d, which is a 3D or 4D tensor,
          with float16, float32 or float64 data type.

        output_size (Union[int, tuple]): The target output size is H x W.
            ouput_size can be a tuple, or a single H for H x H, and H and W can be int or None
            which means the output size is the same as the input.

        return_indices (bool): If `return_indices` is True, the indices of max value would be output.
            Default: False.

    Returns:
        Tensor, with the same type as the `input_x`.

        Shape of the output is `input_x_shape[:len(input_x_shape) - len(out_shape)] + out_shape`.

    Raises:
        TypeError: If `output_size` is not int or tuple.
        TypeError: If `input_x` is not a tensor.
        TypeError: If `return_indices` is not a bool.
        TypeError: If dtype of `input_x` is not float16, float32 or float64.
        ValueError: If `output_size` is a tuple and the length of `output_size` is not 2.
        ValueError: If the dimension of `input_x` is not NCHW or CHW.

    Supported Platforms:
        ``GPU``

    Examples:
        >>> # case 1: output_size=(None, 2)
        >>> input_x = Tensor(np.array([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
        ...                            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
        ...                            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]), mindspore.float32)
        >>> output = F.adaptive_max_pool2d(input_x, (None, 2))
        >>> print(output)
        [[[2. 3.]
          [5. 6.]
          [8. 9.]]
         [[2. 3.]
          [5. 6.]
          [8. 9.]]
         [[2. 3.]
          [5. 6.]
          [8. 9.]]]
        >>> # case 2: output_size=2
        >>> output = F.adaptive_max_pool2d(input_x, 2)
        >>> print(output)
        [[[5. 6.]
          [8. 9.]]
         [[5. 6.]
          [8. 9.]]
         [[5. 6.]
          [8. 9.]]]
        >>> # case 3: output_size=(1, 2)
        >>> output = F.adaptive_max_pool2d(input_x, (1, 2))
        >>> print(output)
        [[[8. 9.]]
         [[8. 9.]]
         [[8. 9.]]]
    """
    _adaptive_max_pool2d = _get_cache_prim(AdaptiveMaxPool2D)(output_size, return_indices)
    return _adaptive_max_pool2d(input_x)


def index_fill(x, dim, index, value):
    """
    Fills the elements under the dim dimension of the self tensor with the input value
    by selecting the indices in the order given in index.
    """
    if isinstance(dim, int) and not isinstance(dim, bool):
        dim = cast_(dim, mstype.int32)
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        value = cast_(value, x.dtype)
    return index_fill_(x, dim, index, value)


##############################
# Type Conversion Functions.
##############################


def scalar_cast(input_x, input_y):
    """
    Casts the input scalar to another type.

    Args:
        input_x (scalar): The input scalar. Only constant value is allowed.
        input_y (mindspore.dtype): The type to be cast. Only constant value is allowed.

    Returns:
        Scalar. The type is the same as the python type corresponding to `input_y`.

    Raises:
        TypeError: If neither `input_x` nor `input_y` is a constant value.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> output = ops.scalar_cast(255.0, mindspore.int32)
        >>> print(output)
        255
    """
    return scalar_cast_(input_x, input_y)


def tensor_scatter_mul(input_x, indices, updates):
    """
    Creates a new tensor by multiplying the values from the positions in `input_x` indicated by
    `indices`, with values from `updates`. When divided values are provided for the same
    index, the result of the update will be to divided these values respectively. Except that
    the updates are applied on output `Tensor` instead of input `Parameter`.

    The last axis of `indices` is the depth of each index vectors. For each index vector,
    there must be a corresponding value in `updates`. The shape of `updates` should be
    equal to the shape of `input_x[indices]`. For more details, see use cases.

    Note:
        - If some values of the `indices` are out of bound, CPU backend will raise an index error.
          GPU backend will not raise and index error
          and the corresponding `updates` will not be updated to `input_x`.

    Args:
        input_x (Tensor): The target tensor. The dimension of input_x must be no less than indices.shape[-1].
        indices (Tensor): The index of input tensor whose data type is int32 or int64.
            The rank must be at least 2.
        updates (Tensor): The tensor to update the input tensor, has the same type as input,
            and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If dtype of `indices` is neither int32 nor int64.
        ValueError: If length of shape of `input_x` is less than the last dimension of shape of `indices`.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> indices = Tensor(np.array([[0, 0], [0, 0]]), mindspore.int32)
        >>> updates = Tensor(np.array([1.0, 2.2]), mindspore.float32)
        >>> # Next, demonstrate the approximate operation process of this operator:
        >>> # 1, indices[0] = [0, 0], indices[1] = [0, 0]
        >>> # 2, And input_x[0, 0] = -0.1
        >>> # 3, So input_x[indices] = [-0.1, -0.1]
        >>> # 4, Satisfy the above formula: input_x[indices].shape=(2) == updates.shape=(2)
        >>> # 5, Perform the multiply operation for the first time:
        >>> #      first_input_x = input_x[0][0] * updates[0] = [[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]
        >>> # 6, Perform the multiply operation for the second time:
        >>> #      second_input_x = input_x[0][0] * updates[1] = [[-0.22, 0.3, 3.6], [0.4, 0.5, -3.2]]
        >>> output = ops.tensor_scatter_mul(input_x, indices, updates)
        >>> print(output)
        [[-0.22  0.3   3.6  ]
         [ 0.4   0.5   -3.2 ]]
    """
    return tensor_scatter_mul_(input_x, indices, updates)


def tensor_scatter_div(input_x, indices, updates):
    """
    Creates a new tensor by dividing the values from the positions in `input_x` indicated by
    `indices`, with values from `updates`. When divided values are provided for the same
    index, the result of the update will be to divided these values respectively. Except that
    the updates are applied on output `Tensor` instead of input `Parameter`.

    The last axis of `indices` is the depth of each index vectors. For each index vector,
    there must be a corresponding value in `updates`. The shape of `updates` should be
    equal to the shape of `input_x[indices]`. For more details, see use cases.

    Note:
        - If some values of the `indices` are out of bound, instead of raising an index error,
          the corresponding `updates` will not be updated to `input_x`.
        - The operator can't handle division by 0 exceptions, so the user needs to make sure
          there is no 0 value in `updates`.

    Args:
        - **input_x** (Tensor) - The target tensor. The dimension of input_x must be no less than indices.shape[-1].
        - **indices** (Tensor) - The index of input tensor whose data type is int32 or int64.
          The rank must be at least 2.
        - **updates** (Tensor) - The tensor to update the input tensor, has the same type as input,
          and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

    Returns:
        Tensor, has the same shape and type as `input_x`.

    Raises:
        TypeError: If dtype of `indices` is neither int32 nor int64.
        ValueError: If length of shape of `input_x` is less than the last dimension of shape of `indices`.

    Supported Platforms:
        ``GPU`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore
        >>> from mindspore import Tensor, nn, ops
        >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
        >>> indices = Tensor(np.array([[0, 0], [0, 0]]), mindspore.int32)
        >>> updates = Tensor(np.array([1.0, 2.0]), mindspore.float32)
        >>> output = ops.tensor_scatter_div(input_x, indices, updates)
        >>> print(output)
        [[-0.05  0.3  3.6  ]
         [ 0.4   0.5  -3.2 ]]
    """
    return tensor_scatter_div_(input_x, indices, updates)


def scalar_to_array(input_x):
    """
    Converts a scalar to a `Tensor`.

    Args:
        input_x (Union[int, float]): The input is a scalar. Only constant value is allowed.

    Returns:
        Tensor. 0-D Tensor and the content is the input.

    Raises:
        TypeError: If `input_x` is neither int nor float.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = 1.0
        >>> print(type(input_x))
        <class 'float'>
        >>> output = ops.scalar_to_array(input_x)
        >>> print(type(output))
        <class 'mindspore.common.tensor.Tensor'>
        >>> print(output)
        1.0
    """
    return scalar_to_array_(input_x)


def scalar_to_tensor(input_x, dtype=mstype.float32):
    """
    Converts a scalar to a `Tensor`, and converts the data type to the specified type.

    Args:
        input_x (Union[int, float]): The input is a scalar. Only constant value is allowed.
        dtype (mindspore.dtype): The target data type. Default: mindspore.float32. Only
            constant value is allowed.

    Returns:
        Tensor. 0-D Tensor and the content is the input.

    Raises:
        TypeError: If `input_x` is neither int nor float.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> data = 1
        >>> output = ops.scalar_to_tensor(data, mindspore.float32)
        >>> print(output)
        1.0
    """
    return scalar_to_tensor_(input_x, dtype)


def tuple_to_array(input_x):
    """
    Converts a tuple to a tensor.

    If the type of the first number in the tuple is integer, the data type of the output tensor is int.
    Otherwise, the data type of the output tensor is float.

    Args:
        input_x (tuple): A tuple of numbers. These numbers have the same type. Only constant value is allowed.
            The shape is :math:`(N,*)` where :math:`*` means,any number of additional dimensions.

    Returns:
        Tensor, if the input tuple contains `N` numbers, then the shape of the output tensor is (N,).

    Raises:
        TypeError: If `input_x` is not a tuple.
        ValueError: If length of `input_x` is less than or equal to 0.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = (1,2,3)
        >>> print(type(input_x))
        <class 'tuple'>
        >>> output = ops.tuple_to_array(input_x)
        >>> print(type(output))
        <class 'mindspore.common.tensor.Tensor'>
        >>> print(output)
        [1 2 3]
    """
    return tuple_to_array_(input_x)


def masked_select(x, mask):
    """
    Returns a new 1-D Tensor which indexes the `x` tensor according to the boolean `mask`.
    The shapes of the `mask` tensor and the `x` tensor don't need to match, but they must be broadcastable.

    Args:
        x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        mask (Tensor[bool]): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.

    Returns:
        A 1-D Tensor, with the same type as `x`.

    Raises:
        TypeError: If `x` or `mask` is not a Tensor.
        TypeError: If dtype of `mask` is not bool.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore.ops as ops
        >>> from mindspore import Tensor
        >>> x = Tensor(np.array([1, 2, 3, 4]), mindspore.int64)
        >>> mask = Tensor(np.array([1, 0, 1, 0]), mindspore.bool_)
        >>> output = ops.masked_select(x, mask)
        >>> print(output)
        [1 3]
    """
    return masked_select_(x, mask)


def masked_fill(input_x, mask, value):
    """
    Fills elements of Tensor with value where mask is True.
    The shapes of `input_x` and `mask` need to be the same or broadcastable.

    Args:
        input_x (Tensor): The source Tensor whose data type is one of float16, float32, int8, int32.
        mask (Tensor[bool]): The boolean mask.
        value (Union[float, Tensor]): The value to fill in with, which dtype is the same as `input_x`.

    Returns:
        Tensor, has the same type and shape as `input_x`.

    Raises:
        TypeError: If dtype of `mask` is not bool.
        TypeError: If `input_x` or `mask` is not a Tensor.
        ValueError: If the shapes of `input_x` and `mask` could not be broadcast.
        TypeError: If dtype of `input_x` or `value` is not one of float16, float32, int8, int32.
        TypeError: If dtype of `value` is different from that of `input_x`.
        TypeError: If `value` is neither float number nor Tensor.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input = Tensor(np.array([1., 2., 3., 4.]), mindspore.float32)
        >>> mask = Tensor(np.array([True, True, False, True]), mindspore.bool_)
        >>> output = ops.masked_fill(input, mask, 0.5)
        >>> print(output)
        [0.5 0.5 3.  0.5]
    """
    return masked_fill_(input_x, mask, value)


def diag(input_x):
    r"""
    Constructs a diagonal tensor with a given diagonal values.

    Assume `input_x` has dimensions :math:`[D_1,... D_k]`, the output is a tensor of
    rank 2k with dimensions :math:`[D_1,..., D_k, D_1,..., D_k]` where:
    :math:`output[i_1,..., i_k, i_1,..., i_k] = input_x[i_1,..., i_k]` and 0 everywhere else.

    Args:
        input_x (Tensor): The input tensor.

    Returns:
        Tensor, has the same dtype as the `input_x`.

    Raises:
        TypeError: If `input_x` is not a Tensor.
        ValueError: If rank of `input_x` is less than 1.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
        >>> from mindspore import Tensor
        >>> import mindspore.ops as ops
        >>> input_x = Tensor([1, 2, 3, 4])
        >>> output = ops.diag(input_x)
        >>> print(output)
        [[1, 0, 0, 0],
         [0, 2, 0, 0],
         [0, 0, 3, 0],
         [0, 0, 0, 4]]
    """
    return diag_(input_x)


def col2im(input_x, output_size, kernel_size, dilation, padding_value, stride):
    """
    Combines an array of sliding local blocks into a large containing tensor.

    Args:
        input_x (Tensor): 4D tensor with data type float16 or float.
        output_size (Tensor): 1D tensor with 2 elements of data type int.
        kernel_size (Union[int, tuple[int], list[int]]): The size of the kernel, should be two int
            for height and width. If type is int, it means that height equal with width. Must be specified.
        dilation (Union[int, tuple[int], list[int]]): The size of the dilation, should be two int
            for height and width. If type is int, it means that height equal with width. Default: 1.
        padding_value (Union[int, tuple[int], list[int]]): The size of the padding, should be two int
            for height and width. If type is int, it means that height equal with width. Default: 1.
        stride (Union[int, tuple[int], list[int]]): The size of the stride, should be two int
            for height and width. If type is int, it means that height equal with width. Default: 0.

    Returns:
        A 4D Tensor, with same type as 'input_x'.

    Raises:
        TypeError: If :attr:`kernel_size`, `dilation`, `padding_value`, `stride` data type is not in
            Union[int, tuple[int], list[int]].
        ValueError: If :attr:`kernel_size`, `dilation`, `padding_value`, `stride` value is not
            greater than zero or elements number more than 2.
        ValueError: If :attr:`padding_value` value is less than zero or elements number more than 2.
        ValueError: If input_x.shape[2] != kernel_size[0] * kernel_size[1].
        ValueError: If input_x.shape[3] does not match the calculated number of sliding blocks.

    Supported Platforms:
        ``GPU``

    Examples:
        >>> import numpy as np
        >>> import mindspore.ops as ops
        >>> from mindspore import Tensor
        >>> x = Tensor(input_data=np.random.rand(16, 16, 4, 25), dtype=mstype.float32)
        >>> output_size = Tensor(input_data=[8, 8], dtype=mstype.int32)
        >>> output = ops.col2im(x, output_size, [2, 2], [2, 2], [2, 2], [2, 2])
        >>> print(output.shape)
        (16, 16, 8, 8)
    """
    c2i = _get_cache_prim(Col2Im)(kernel_size, dilation, padding_value, stride)
    return c2i(input_x, output_size)


def split(input_x, axis=0, output_num=1):
    r"""
    Splits the input tensor into output_num of tensors along the given axis and output numbers.

    The `input_x` tensor will be split into equally sized sub-tensors.
    This requires that `input_x.shape(axis)` is divisible by `output_num`.

    Args:
        input_x (Tensor): The shape of tensor is :math:`(x_1, x_2, ..., x_R)`.
        axis (int): Index of the split position. Default: 0.
        output_num (int): The number of output tensors. Must be positive int. Default: 1.

    Returns:
        tuple[Tensor], the shape of each output tensor is the same, which is
        :math:`(y_1, y_2, ..., y_S)`. And the data type is the same with `input_x`.

    Raises:
        TypeError: If `axis` or `output_num` is not an int.
        ValueError: If `axis` is out of the range [-len(`input_x.shape`), len(`input_x.shape`)),
            or if the `output_num` is less than or equal to 0.
        ValueError: If `input_x.shape(axis)` is not divisible by `output_num`.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> x = Tensor(np.array([[1, 1, 1, 1], [2, 2, 2, 2]]), mindspore.int32)
        >>> print(x)
        [[1 1 1 1]
         [2 2 2 2]]
        >>> output = ops.split(x, 1, 2)
        >>> print(output)
        (Tensor(shape=[2, 2], dtype=Int32, value=
        [[1, 1],
         [2, 2]]), Tensor(shape=[2, 2], dtype=Int32, value=
        [[1, 1],
         [2, 2]]))
        >>> output = ops.split(x, 1, 4)
        >>> print(output)
        (Tensor(shape=[2, 1], dtype=Int32, value=
        [[1],
         [2]]), Tensor(shape=[2, 1], dtype=Int32, value=
        [[1],
         [2]]), Tensor(shape=[2, 1], dtype=Int32, value=
        [[1],
         [2]]), Tensor(shape=[2, 1], dtype=Int32, value=
        [[1],
         [2]]))
    """
    split_ = _get_cache_prim(P.Split)(axis, output_num)
    return split_(input_x)


def max(input_x, axis=0, keep_dims=False):
    """
    Calculates the maximum value with the corresponding index.

    Calculates the maximum value along with the given axis for the input tensor. It returns the maximum values and
    indices.

    Note:
        In auto_parallel and semi_auto_parallel mode, the first output index can not be used.

    .. warning::
        - If there are multiple maximum values, the index of the first maximum value is used.
        - The value range of "axis" is [-dims, dims - 1]. "dims" is the dimension length of "input_x".

    Also see: class: `mindspore.ops.ArgMaxWithValue`.

    Args:
        input_x (Tensor) - The input tensor, can be any dimension. Set the shape of input tensor as
          :math:`(x_1, x_2, ..., x_N)`. And the data type only support mindspore.float16 or float32.
        axis (int): The dimension to reduce. Default: 0.
        keep_dims (bool): Whether to reduce dimension, if true, the output will keep same dimension with the input,
                          the output will reduce dimension if false. Default: False.

    Returns:
        tuple (Tensor), tuple of 2 tensors, containing the corresponding index and the maximum value of the input
        tensor.

        - index (Tensor) - The index for the maximum value of the input tensor. If `keep_dims` is true, the shape of
          output tensors is :math:`(x_1, x_2, ..., x_{axis-1}, 1, x_{axis+1}, ..., x_N)`. Otherwise, the shape is
          :math:`(x_1, x_2, ..., x_{axis-1}, x_{axis+1}, ..., x_N)` .
        - output_x (Tensor) - The maximum value of input tensor, with the same shape as index.

    Raises:
        TypeError: If `keep_dims` is not a bool.
        TypeError: If `axis` is not an int.

    Supported Platforms:
        ``Ascend`` ``GPU`` ``CPU``

    Examples:
        >>> input_x = Tensor(np.array([0.0, 0.4, 0.6, 0.7, 0.1]), mindspore.float32)
        >>> index, output = ops.max(input_x)
        >>> print(index, output)
        3 0.7
        >>> index, output = ops.max(input_x, keep_dims=True)
        >>> print(index, output)
        [3] [0.7]
    """
    argmax_with_value_op = P.ArgMaxWithValue(axis, keep_dims)
    return argmax_with_value_op(input_x)


__all__ = [
    'unique',
    'unique_consecutive',
    'eye',
    'matrix_band_part',
    'padding',
    'fill',
    'fill_',
    'fills',
    'tile',
    'size',
    'ger',
    'ones',
    'ones_like',
    'shape',
    'shape_',
    'dyn_shape',
    'rank',
    'range',
    'reshape',
    'reshape_',
    'flatten',
    'tensor_slice',
    'slice',
    'concat',
    'scalar_cast',
    'scalar_to_array',
    'scalar_to_tensor',
    'space_to_batch_nd',
    'batch_to_space_nd',
    'tuple_to_array',
    'expand_dims',
    'transpose',
    'scatter_nd',
    'scatter_nd_add',
    'scatter_nd_sub',
    'scatter_nd_mul',
    'scatter_nd_div',
    'scatter_nd_max',
    'scatter_nd_min',
    'tensor_scatter_add',
    'tensor_scatter_sub',
    'tensor_scatter_mul',
    'tensor_scatter_div',
    'tensor_scatter_max',
    'tensor_scatter_min',
    'tensor_scatter_elements',
    'unsorted_segment_min',
    'unsorted_segment_max',
    'unsorted_segment_prod',
    'gather',
    'gather_d',
    'gather_elements',
    'gather_nd',
    'one_hot',
    'masked_fill',
    'masked_select',
    'scatter_add',
    'scatter_max',
    'scatter_min',
    'scatter_div',
    'scatter_update',
    'select',
    'nonzero',
    'matrix_diag',
    'matrix_diag_part',
    'diag',
    'meshgrid',
    'adaptive_max_pool2d',
    'meshgrid',
    'broadcast_to',
    'col2im',
    'split',
    "index_fill",
    'max',
]
__all__.sort()
