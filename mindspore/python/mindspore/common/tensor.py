# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""Tensor implementation."""
import numbers

import numpy as np
from mindspore.communication.management import get_rank, get_group_size
from mindspore import context

from mindspore import log as logger
from . import dtype as mstype
from ._register_for_tensor import tensor_operator_registry
from .._c_expression import COOTensor as COOTensor_
from .._c_expression import CSRTensor as CSRTensor_
from .._c_expression import RowTensor as RowTensor_
from .._c_expression import Tensor as Tensor_
from .._checkparam import Rel
from .._checkparam import Validator as validator

__all__ = ['Tensor', 'RowTensor', 'SparseTensor', 'COOTensor', 'CSRTensor']
np_types = (np.int8, np.int16, np.int32, np.int64,
            np.uint8, np.uint16, np.uint32, np.uint64, np.float16,
            np.float32, np.float64, np.bool_, np.complex64, np.complex128)


class Tensor(Tensor_):
    """
    Tensor is a data structure that stores an n-dimensional array.

    Args:
        input_data (Union[Tensor, float, int, bool, tuple, list, numpy.ndarray]): The data to be stored. It can be
            another Tensor, Python number or NumPy ndarray. Default: None.
        dtype (:class:`mindspore.dtype`): Used to indicate the data type of the output Tensor. The argument should
            be defined in `mindspore.dtype`. If it is None, the data type of the output Tensor will be the same
            as the `input_data`. Default: None.
        shape (Union[tuple, list, int]): Used to indicate the shape of the output Tensor. The argument should be
            a list of integers, a tuple of integers or an integer. If `input_data` is available,
            `shape` doesn't need to be set. Default: None.
        init (Initializer): The information of init data.
            'init' is used for delayed initialization in parallel mode. Usually, it is not recommended to use
            'init' interface to initialize Tensor in the other conditions. If 'init' interface is used to initialize
            Tensor, the `Tensor.init_data` API needs to be called to convert `Tensor` to the actual data.
            Default: None.
        internal (bool): Whether it is created by the framework.
            'True' means that the tensor is created by framework.
            'False' means that the tensor is created by user.
            Default: False

    Outputs:
        Tensor.

    Examples:
        >>> import numpy as np
        >>> import mindspore as ms
        >>> from mindspore import Tensor
        >>> from mindspore.common.initializer import One
        >>> # initialize a tensor with numpy.ndarray
        >>> t1 = Tensor(np.zeros([1, 2, 3]), ms.float32)
        >>> print(t1)
        [[[0. 0. 0.]
        [0. 0. 0.]]]
        >>> print(type(t1))
        <class 'mindspore.common.tensor.Tensor'>
        >>> print(t1.shape)
        (1, 2, 3)
        >>> print(t1.dtype)
        Float32
        >>>
        >>> # initialize a tensor with a float scalar
        >>> t2 = Tensor(0.1)
        >>> print(t2)
        0.1
        >>> print(type(t2))
        <class 'mindspore.common.tensor.Tensor'>
        >>> print(t2.shape)
        ()
        >>> print(t2.dtype)
        Float32
        >>>
        >>> # initialize a tensor with a tuple
        >>> t3 = Tensor((1, 2))
        >>> print(t3)
        [1 2]
        >>> print(type(t3))
        <class 'mindspore.common.tensor.Tensor'>
        >>> print(t3.shape)
        (2,)
        >>> print(t3.dtype)
        Int64
        ...
        >>> # initialize a tensor with init
        >>> t4 = Tensor(shape = (1, 3), dtype=ms.float32, init=One())
        >>> print(t4)
        [[1. 1. 1.]]
        >>> print(type(t4))
        <class 'mindspore.common.tensor.Tensor'>
        >>> print(t4.shape)
        (1, 3)
        >>> print(t4.dtype)
        Float32
    """
    delta_seed = 0

    def __init__(self, input_data=None, dtype=None, shape=None, init=None, internal=False):
        self.init_finished = False
        if internal:
            Tensor_.__init__(self, input_data)
        else:
            # If input data is numpy number, convert it to np array
            if isinstance(input_data, np_types):
                input_data = np.array(input_data)

            if isinstance(shape, numbers.Number):
                shape = (shape,)

            _check_tensor_input(input_data, dtype, shape, init)

            # If input_data is tuple/list/numpy.ndarray, it's support in check_type method.
            if (isinstance(shape, (list, tuple)) and None in shape) or init is not None:
                shape = _check_tensor_dynamic_shape(dtype, shape, init)
                Tensor_.__init__(self, dtype, shape)
            else:
                validator.check_value_type('input_data', input_data,
                                           (Tensor_, np.ndarray, np.str_, list, tuple, float, int, bool, complex),
                                           'Tensor')
                valid_dtypes = (np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64,
                                np.float16, np.float32, np.float64, np.bool_, np.str_, np.complex64, np.complex128)
                if isinstance(input_data, np.ndarray) and input_data.dtype not in valid_dtypes and \
                        input_data.dtype.kind != 'U' and input_data.dtype.kind != 'S':  # Support dtype np.str_
                    raise TypeError(f"For Tensor, the input_data is a numpy array, "
                                    f"but it's data type: {input_data.dtype} is not in supported list: "
                                    f"{list(i.__name__ for i in valid_dtypes)}.")
                if isinstance(input_data, np.ndarray) and input_data.dtype.kind == "S" and \
                        input_data.shape and context.get_context("enable_ge"):
                    raise TypeError("For binary string input in GE mode, the shape of the data must be ()")
                if isinstance(input_data, (tuple, list)) and np.array(input_data).dtype not in valid_dtypes:
                    raise TypeError(
                        f"For Tensor, the input_data is {input_data} that contain unsupported element.")

                if dtype is not None:
                    validator.check_type_name(
                        'dtype', dtype, mstype.number_type + (mstype.bool_, mstype.string), "Tensor")
                else:
                    dtype = self._set_default_dtype(input_data, dtype)

                if isinstance(input_data, np.ndarray) and (not input_data.flags['FORC']):
                    input_data = np.ascontiguousarray(input_data)

                if dtype is not None:
                    Tensor_.__init__(self, input_data, dtype)
                else:
                    Tensor_.__init__(self, input_data)

        self.virtual_flag = False
        self.init = init
        self.init_finished = True

        # if cur Tensor is a index value of another Tensor,
        # parent_tensor_ set to another Tensor
        # index_of_parent_ will set to the index
        self.parent_tensor_ = None
        self.index_of_parent_ = None

    @staticmethod
    def _set_default_dtype(input_data, dtype):
        if isinstance(input_data, (float, list, tuple)):
            if np.array(input_data).dtype == np.float64:
                return mstype.float32
        return dtype

    def __deepcopy__(self, memodict):
        new_obj = Tensor(self)
        new_obj.init = self.init
        new_obj.virtual_flag = self.virtual_flag
        return new_obj

    def __repr__(self):
        if self.init_finished:
            Tensor_.data_sync(self, True)
            return Tensor_.__repr__(self)
        return ''

    def __eq__(self, other):
        if not isinstance(other, (int, float, Tensor)):
            return False
        # bool type is not supported for `Equal` operator in backend.
        if self.dtype == mstype.bool_ or (isinstance(other, Tensor) and other.dtype == mstype.bool_):
            if isinstance(other, Tensor):
                return Tensor(np.array(self.asnumpy() == other.asnumpy()))
            return Tensor(np.array(self.asnumpy() == other))
        return tensor_operator_registry.get('__eq__')(self, other)

    def __ne__(self, other):
        if not isinstance(other, (int, float, Tensor)):
            return True
        #  bool type is not supported for `NotEqual` operator in backend.
        if self.dtype == mstype.bool_ or (isinstance(other, Tensor) and other.dtype == mstype.bool_):
            return Tensor(np.array(self.asnumpy() != other.asnumpy()))
        return tensor_operator_registry.get('__ne__')(self, other)

    def __hash__(self):
        return hash(id(self))

    def __neg__(self):
        out = tensor_operator_registry.get('__neg__')(self)
        return out

    def __invert__(self):
        out = tensor_operator_registry.get('__logical_not__')(self)
        return out

    def __bool__(self):
        data = self.asnumpy()
        if data.shape == ():
            return bool(data)
        if data.shape == (1,):
            return bool(data[0])
        raise ValueError("The truth value of an array with several elements is ambiguous.")

    @staticmethod
    def _convert_scalar_(data, func, message):
        if data.shape == ():
            return func(data)
        if data.shape == (1,):
            return func(data[0])
        raise ValueError(message)

    def __int__(self):
        data = self.asnumpy()
        return self._convert_scalar_(data, int, "Only one element tensors can be converted to Python scalars")

    def __float__(self):
        data = self.asnumpy()
        return self._convert_scalar_(data, float, "Only one element tensors can be converted to Python scalars")

    def __index__(self):
        data = self.asnumpy()
        if not (data.dtype == "int8"
                or data.dtype == "int16"
                or data.dtype == "int32"
                or data.dtype == "int64"
                or data.dtype == "bool"):
            raise ValueError("Only integer tensors of a single element can be converted to an index.")
        return self._convert_scalar_(data, int,
                                     "Only integer tensors of a single element can be converted to an index.")

    def __pos__(self):
        return self

    def __abs__(self):
        data = abs(self.asnumpy())
        if isinstance(data, np.number):
            data = np.array(data)
        return Tensor(data)

    def __add__(self, other):
        return tensor_operator_registry.get('__add__')(self, other)

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return tensor_operator_registry.get('__sub__')(self, other)

    def __rsub__(self, other):
        return tensor_operator_registry.get('__sub__')(other, self)

    def __isub__(self, other):
        return self.__sub__(other)

    def __mul__(self, other):
        return tensor_operator_registry.get('__mul__')(self, other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return tensor_operator_registry.get('__truediv__')(self, other)

    def __rtruediv__(self, other):
        return tensor_operator_registry.get('__truediv__')(other, self)

    def __mod__(self, other):
        return tensor_operator_registry.get('__mod__')(self, other)

    def __rmod__(self, other):
        return tensor_operator_registry.get('__mod__')(other, self)

    def __imod__(self, other):
        return self.__mod__(other)

    def __pow__(self, other):
        return tensor_operator_registry.get('__pow__')(self, other)

    def __rpow__(self, other):
        return tensor_operator_registry.get('__rpow__')(self, other)

    def __floordiv__(self, other):
        return tensor_operator_registry.get('__floordiv__')(self, other)

    def __rfloordiv__(self, other):
        return tensor_operator_registry.get('__floordiv__')(other, self)

    def __ifloordiv__(self, other):
        return self.__floordiv__(other)

    def __lt__(self, other):
        out = tensor_operator_registry.get('__lt__')(self, other)
        return out

    def __le__(self, other):
        out = tensor_operator_registry.get('__le__')(self, other)
        return out

    def __getitem__(self, index):
        out = tensor_operator_registry.get('__getitem__')(self, index)
        if out is not self:
            out.parent_tensor_ = self
            out.index_of_parent_ = index
        return out

    def __setitem__(self, index, value):
        out = tensor_operator_registry.get('__setitem__')(self, index, value)
        self.assign_value(out)
        if self.parent_tensor_ is not None and self.index_of_parent_ is not None:
            self.parent_tensor_.__setitem__(self.index_of_parent_, self)
        return self

    def __gt__(self, other):
        out = tensor_operator_registry.get('__gt__')(self, other)
        return out

    def __ge__(self, other):
        out = tensor_operator_registry.get('__ge__')(self, other)
        return out

    def __len__(self):
        out = tensor_operator_registry.get('shape')(self)
        if out:
            return out[0]
        raise TypeError("Not support len of a 0-D tensor")

    def __str__(self):
        if self.dtype == mstype.type_none:
            return "Unknown Tensor type!"
        return str(self.asnumpy())

    @property
    def shape(self):
        """Returns the shape of the tensor as a tuple."""
        return self._shape

    @property
    def dtype(self):
        """Return the dtype of the tensor (:class:`mindspore.dtype`)."""
        return self._dtype

    @property
    def size(self):
        """Returns the total number of elements in tensor."""
        return self._size

    @property
    def ndim(self):
        """Return the number of tensor dimensions."""
        return len(self._shape)

    @property
    def has_init(self):
        """Whether tensor is initialized."""
        return self.init is not None

    @property
    def itemsize(self):
        """Return the length of one tensor element in bytes."""
        return self._itemsize

    @property
    def strides(self):
        """Return the tuple of bytes to step in each dimension when traversing a tensor."""
        return self._strides

    @property
    def nbytes(self):
        """Return the total number of bytes taken by the tensor."""
        return self._nbytes

    @property
    def T(self):
        """Return the transposed tensor."""
        return self.transpose()

    @staticmethod
    def from_numpy(array):
        """
        Convert numpy array to Tensor without copy data.

        Args:
            array (numpy.array): The input array.

        Returns:
            Tensor, has the same data type as input array.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = np.array([1, 2])
            >>> output = Tensor.from_numpy(x)
            >>> print(output)
            [1 2]
        """
        return Tensor(Tensor_.from_numpy(array))

    def assign_value(self, value):
        """
        Assign another tensor value to this tensor.

        Args:
            value (Tensor): Tensor for assignment.

        Returns:
            Tensor, Tensor that's been assigned.
        """
        self.assign_value_cpp(value)
        return self

    def item(self, index=None):
        """
        Get the item at the specified index of the tensor.

        Note:
            Tensor.item returns a Tensor scalar instead of a Python scalar.

        Args:
            index (Union[None, int, tuple(int)]): The index in Tensor. Default: None.

        Returns:
            A Tensor scalar, dtype is the same with the original Tensor.

        Raises:
            ValueError: If the length of the `index` is not equal to self.ndim.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[1,2,3],[4,5,6]], dtype=np.float32))
            >>> x = x.item((0,1))
            >>> print(x)
            2.0

        """
        output = tensor_operator_registry.get('item')(self, index)
        return output

    def itemset(self, *args):
        r"""
        Insert scalar into a tensor (scalar is cast to tensor's dtype, if possible).

        There must be at least 1 argument, and define the last argument as item.
        Then, tensor.itemset(\*args) is equivalent to :math:`tensor[args] = item`.

        Args:
            args (Union[(numbers.Number), (int/tuple(int), numbers.Number)]): The arguments that
                specify the index and value. If `args` contain one argument (a scalar),
                it is only used in case tensor is of size 1. If `args` contain two
                arguments, the last argument is the value to be set and must be a
                scalar, the first argument specifies a single tensor element location.
                It is either an int or a tuple.

        Returns:
            A new tensor that doesn't affect the original tensor, with value set by :math:`tensor[args] = item`.

        Raises:
            ValueError: If the length of the first argument is not equal to self.ndim.
            IndexError: If only one argument is provided, and the original Tensor is not scalar.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[1,2,3],[4,5,6]], dtype=np.float32))
            >>> print(x.itemset((0,1), 4))
            [[1. 4. 3.]
            [4. 5. 6.]]
            >>> print(x)
            [[1. 2. 3.]
            [4. 5. 6.]]
        """
        output = tensor_operator_registry.get('itemset')(self, *args)
        return output

    def asnumpy(self):
        """
        Convert tensor to numpy array. Returns self tensor as a NumPy ndarray. This tensor and the returned ndarray
        share the same underlying storage. Changes to self tensor will be reflected in the ndarray.

        Returns:
            A numpy ndarray which shares the same underlying storage with the tensor.

        Examples:
            >>> from mindspore import Tensor
            >>> import numpy as np
            >>> x = Tensor(np.array([1, 2], dtype=np.float32))
            >>> y = x.asnumpy()
            >>> y[0] = 11
            >>> print(x)
            [11.  2.]
            >>> print(y)
            [11.  2.]
        """
        self._init_check()
        return Tensor_.asnumpy(self)

    def flush_from_cache(self):
        """
        Flush cache data to host if tensor is cache enable.

        Examples:
            >>> from mindspore import Tensor
            >>> import numpy as np
            >>> x = Tensor(np.array([1, 2], dtype=np.float32))
            >>> y = x.flush_from_cache()
            >>> print(y)
            None
        """
        self._init_check()
        Tensor_._flush_from_cache(self)

    def all(self, axis=(), keep_dims=False):
        """
        Check all tensor elements along a given axis evaluate to True.

        Args:
            axis (Union[None, int, tuple(int)]): Dimensions of reduction.
                When the axis is None or empty tuple, reduce all dimensions. When the axis is int or
                tuple(int), if the dimension of Tensor is dim, the value range is [-dim, dim). Default: ().
            keep_dims (bool): Whether to keep the reduced dimensions. Default: False.

        Returns:
            Tensor, if all tensor elements along the given axis evaluate to True, its value is True,
            otherwise its value is False. If the axis is None or empty tuple, reduce all dimensions.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.any`: Check any tensor element along a given axis evaluate to True.

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor([True, True, False])
            >>> output = a.all()
            >>> print(output)
            False
        """

        self._init_check()
        if axis is None:
            axis = ()
        return tensor_operator_registry.get('all')(keep_dims)(self, axis)

    def any(self, axis=(), keep_dims=False):
        """
        Check any tensor element along a given axis evaluate to True.

        Args:
            axis (Union[None, int, tuple(int)]): Dimensions of reduction.
                When the axis is None or empty tuple, reduce all dimensions. When the axis is int or
                tuple(int), if the dimension of Tensor is dim, the value range is [-dim, dim). Default: ().
            keep_dims (bool): Whether to keep the reduced dimensions. Default: False.

        Returns:
            Tensor, if any tensor element along the given axis evaluates to True, its value is True,
            otherwise its value is False. If the axis is None or empty tuple, reduce all dimensions.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.all`: Check all tensor elements along a given axis evaluate to True.

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor([True, True, False])
            >>> output = a.any()
            >>> print(output)
            True
        """

        self._init_check()
        if axis is None:
            axis = ()
        return tensor_operator_registry.get('any')(keep_dims)(self, axis)

    def view(self, *shape):
        """
        Reshape the tensor according to the input shape. It's the same as :func:`mindspore.Tensor.reshape`,
        implemented by the underlying reshape operator.

        Args:
            shape (Union[tuple(int), int]): Dimension of the output tensor.

        Returns:
            Tensor, which dimension is the input shape's value.

        Examples:
            >>> from mindspore import Tensor
            >>> import numpy as np
            >>> a = Tensor(np.array([[1, 2, 3], [2, 3, 4]], dtype=np.float32))
            >>> output = a.view((3, 2))
            >>> print(output)
            [[1. 2.]
            [3. 2.]
            [3. 4.]]
        """
        self._init_check()
        if not shape:
            raise ValueError("The shape variable should not be empty")
        if isinstance(shape[0], tuple):
            if len(shape) != 1:
                raise ValueError(f"Only one tuple is needed, but got {shape}")
            shape = shape[0]
        return tensor_operator_registry.get('reshape')()(self, shape)

    def bitwise_and(self, x):
        """
        Returns bitwise `and` of two tensors element-wise.

        Refer to :func:`mindspore.ops.bitwise_and` for more detail.

        Args:
            x (Tensor): The input tensor.

        Returns:
            Tensor, has the same type as the `x`.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> import numpy as np
            >>> a = Tensor(np.array([0, 0, 1, -1, 1, 1, 1]), mindspore.int16)
            >>> b = Tensor(np.array([0, 1, 1, -1, -1, 2, 3]), mindspore.int16)
            >>> output = a.bitwise_and(b)
            >>> print(output)
            [ 0  0  1 -1  1  0  1]
        """
        self._init_check()
        return tensor_operator_registry.get('bitwise_and')(self, x)

    def bitwise_or(self, x):
        """
        Returns bitwise `or` of two tensors element-wise.

        Refer to :func:`mindspore.ops.bitwise_or` for more detail.

        Args:
            x (Tensor): The input tensor.

        Returns:
            Tensor, has the same type as the `x`.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> import numpy as np
            >>> a = Tensor(np.array([0, 0, 1, -1, 1, 1, 1]), mindspore.int16)
            >>> b = Tensor(np.array([0, 1, 1, -1, -1, 2, 3]), mindspore.int16)
            >>> output = a.bitwise_or(b)
            >>> print(output)
            [ 0  1  1 -1 -1  3  3]
        """
        self._init_check()
        return tensor_operator_registry.get('bitwise_or')(self, x)

    def bitwise_xor(self, x):
        """
        Returns bitwise `xor` of two tensors element-wise.

        Refer to :func:`mindspore.ops.bitwise_xor` for more detail.

        Args:
            x (Tensor): The input tensor.

        Returns:
            Tensor, has the same type as the `x`.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> import numpy as np
            >>> a = Tensor(np.array([0, 0, 1, -1, 1, 1, 1]), mindspore.int16)
            >>> b = Tensor(np.array([0, 1, 1, -1, -1, 2, 3]), mindspore.int16)
            >>> output = a.bitwise_xor(b)
            >>> print(output)
            [ 0  1  0  0 -2  3  2]
        """
        self._init_check()
        return tensor_operator_registry.get('bitwise_xor')(self, x)

    def scatter_mul(self, indices, updates):
        """
        Creates a new tensor by multiplying the values from the positions in self tensor indicated by
        `indices`, with values from `updates`. When divided values are provided for the same
        index, the result of the update will be to divided these values respectively. Except that
        the updates are applied on output `Tensor` instead of input `Parameter`.
        The variable `input_x` refers to self tensor.

        The last axis of `indices` is the depth of each index vectors. For each index vector,
        there must be a corresponding value in `updates`. The shape of `updates` should be
        equal to the shape of `input_x[indices]`. For more details, see use cases.

        Note:
            - If some values of the `indices` are out of bound, CPU backend will raise an index error.
              GPU backend will not raise and index error
              and the corresponding `updates` will not be updated to self tensor.

        Args:
            indices (Tensor): The index of input tensor whose data type is int32 or int64.
                The rank must be at least 2.
            updates (Tensor): The tensor to update the input tensor, has the same type as input,
                and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

        Returns:
            Tensor, has the same shape and type as self tensor.

        Raises:
            TypeError: If dtype of `indices` is neither int32 nor int64.
            ValueError: If length of shape of self tensor is less than the last dimension of shape of `indices`.

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
            >>> output = input_x.scatter_mul(indices, updates)
            >>> print(output)
            [[-0.22  0.3   3.6  ]
             [ 0.4   0.5   -3.2 ]]
        """
        self._init_check()
        return tensor_operator_registry.get('tensor_scatter_mul')(self, indices, updates)

    def scatter_div(self, indices, updates):
        """
        Creates a new tensor by dividing the values from the positions in self tensor indicated by
        `indices`, with values from `updates`. When divided values are provided for the same
        index, the result of the update will be to divided these values respectively. Except that
        the updates are applied on output `Tensor` instead of input `Parameter`.

        The last axis of `indices` is the depth of each index vectors. For each index vector,
        there must be a corresponding value in `updates`. The shape of `updates` should be
        equal to the shape of `input_x[indices]`, the variable `input_x` refers to self tensor.
        For more details, see use cases.

        Note:
            - If some values of the `indices` are out of bound, instead of raising an index error,
              the corresponding `updates` will not be updated to `input_x`.
            - The operator can't handle division by 0 exceptions, so the user needs to make sure
              there is no 0 value in `updates`.

        Args:
            indices (Tensor): The index of input tensor whose data type is int32 or int64.
                The rank must be at least 2.
            updates (Tensor): The tensor to update the input tensor, has the same type as input,
                and updates.shape should be equal to indices.shape[:-1] + input_x.shape[indices.shape[-1]:].

        Returns:
            Tensor, has the same shape and type as self tensor.

        Raises:
            TypeError: If dtype of `indices` is neither int32 nor int64.
            ValueError: If length of shape of self tensor is less than the last dimension of shape of `indices`.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]).astype('float32'))
            >>> indices = Tensor(np.array([[0, 0], [0, 0]]).astype('int32'))
            >>> updates = Tensor(np.array([1.0, 2.0]).astype('float32'))
            >>> output = input_x.scatter_div(indices, updates)
            >>> print(output)
            [[-0.05  0.3  3.6  ]
             [ 0.4   0.5  -3.2 ]]
        """
        self._init_check()
        return tensor_operator_registry.get('tensor_scatter_div')(self, indices, updates)

    def ger(self, x):
        """
        Ger product of `self` and `x`. Calculate the outer product of two arrays. If `self` is a 1D
        Tensor of shape :math:`(m,)` and `x` is a 1D Tensor of shape :math:`(n,)`, then `output` must be a Tensor of
        shape :math:`(m * n)`.

        Refer to :func:`mindspore.ops.ger` for more detail.

        Args:
            x (Tensor): input Tensor, with dtype of float16 or float32.

        Returns:
            Tensor, output matrix with the same dtype as inputs.With `self` shape :math:`(m,)` and
            `x` shape of :math:`(n,)`, the `output` has shape :math:`(m, n)`.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> x1 = Tensor([1., 2., 3., 4.], mindspore.float32)
            >>> x2 = Tensor([1., 2., 3.], mindspore.float32)
            >>> output = x1.ger(x2)
            >>> print(output)
            [[ 1.  2.  3.]
             [ 2.  4.  6.]
             [ 3.  6.  9.]
             [ 4.  8. 12.]]
        """
        self._init_check()
        return tensor_operator_registry.get('ger')(self, x)

    def broadcast_to(self, shape):
        """
        Broadcasts input tensor to a given shape.
        Input shape can be broadcast to target shape if for each dimension pair they are either equal or input is
        one or the target dimension is -1. In case of -1 in target shape, it will be replaced by the input
        shape's value in that dimension.
        When input shape is broadcast to target shape, it starts with the trailing
        dimensions. If there is a -1 in the target shape, the -1 cannot be in a leading,
        non-existing dimension.

        Args:
            shape (tuple): The target shape to broadcast. Can be fully specified, or have -1 in one position
                           where it will be substituted by the input tensor's shape in that position, see example.

        Returns:
            Tensor, with the given `shape` and the same data type as `self`.

        Raises:
            TypeError: If `shape` is not a tuple.
            ValueError: If the target and input shapes are incompatible, or if a - 1
                        in the target shape is in an invalid location.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> from mindspore import dtype as mstype
            >>> shape = (2, 3)
            >>> x = Tensor(np.array([1, 2, 3]).astype(np.float32))
            >>> output = x.broadcast_to(shape)
            >>> print(output)
            [[1. 2. 3.]
             [1. 2. 3.]]
            >>> shape = (-1, 2)
            >>> x = Tensor(np.array([[1], [2]]).astype(np.float32))
            >>> output = x.broadcast_to(shape)
            >>> print(output)
            [[1. 1.]
             [2. 2.]]
        """
        self._init_check()
        return tensor_operator_registry.get('broadcast_to')(shape)(self)

    def expand_as(self, x):
        """
        Expand the dimension of target tensor to the dimension of input tensor.

        Args:
            x (Tensor): The input tensor. The shape of the input tensor must obey
                the broadcasting rule.

        Returns:
            Tensor, has the same dimension as input tensor.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> from mindspore import dtype as mstype
            >>> x = Tensor([1, 2, 3], dtype=mstype.float32)
            >>> y = Tensor(np.ones((2, 3)), dtype=mstype.float32)
            >>> output = x.expand_as(y)
            >>> print(output)
            [[1. 2. 3.]
            [1. 2. 3.]]
        """
        self._init_check()
        return tensor_operator_registry.get('broadcast_to')(x.shape)(self)

    def tan(self):
        """
        Computes tangent of `x` element-wise.

        .. math::

            out_i = tan(x_i)

        Returns:
            Tensor, has the same shape as self.

        Raises:
            TypeError: If self is not a Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor([-1.0, 0.0, 1.0]).astype("float32")
            >>> output = a.tan()
            >>> print(output)
            [-1.5574081 0. 1.5574081]
        """
        self._init_check()
        return tensor_operator_registry.get('tan')()(self)

    def cosh(self):
        r"""
        Computes hyperbolic cosine of `x` element-wise.

        .. math::

            out_i = \cosh(x_i)

        Returns:
            Tensor, has the same shape as `x`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor(np.array([0.24, 0.83, 0.31, 0.09]), mindspore.float32)
            >>> output = a.cosh()
            >>> print(output)
            [1.0289385 1.364684 1.048436 1.0040528]
        """
        self._init_check()
        return tensor_operator_registry.get('cosh')()(self)

    def abs(self):
        """
        Return absolute value element-wisely.

        Returns:
            Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor([1.1, -2.1]).astype("float32")
            >>> output = a.abs()
            >>> print(output)
            [1.1 2.1]
        """
        self._init_check()
        return tensor_operator_registry.get('abs')()(self)

    def ceil(self):
        """
        Rounds a tensor up to the closest integer element-wise.

        Returns:
            Tensor.

        Raises:
            TypeError: If dtype of self tensor is not float16 or float32.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor([1.1, 2.5, -1.5]).astype("float32")
            >>> output = a.ceil()
            >>> print(output)
            [ 2.  3. -1.]
        """
        self._init_check()
        return tensor_operator_registry.get('ceil')()(self)

    def lerp(self, end, weight):
        """
        Does a linear interpolation of two tensors start and end based on a float or tensor weight.

        If `weight` is a tensor, the shapes of two inputs need to be broadcast;
        If `weight` is a float, the shapes of `end` need to be broadcast.

        Args:
            end (Tensor): The tensor with the ending points. Data type must be float16 or float32.
            weight (Union[float, Tensor]): The weight for the interpolation formula. Must be a float
                or a scalar tensor with float16 or float32 data type.

        Returns:
            Tensor, has the same type and shape as self tensor.

        Raises:
            TypeError: If `end` is not a tensor.
            TypeError: If `weight` is neither scalar(float) nor tensor.
            TypeError: If dtype of `end` is neither float16 nor float32.
            TypeError: If dtype of `weight` is neither float16 nor float32 when it is a tensor.
            TypeError: If self tensor and `end` have different data types.
            TypeError: If self tensor, `end` and `weight` have different data types when `weight` is a tensor.
            ValueError: If `end` could not be broadcast to tensor with shape of self tensor.
            ValueError: If `weight` could not be broadcast to tensor with shapes of `end` when it is a tensor.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> start = Tensor(np.array([1., 2., 3., 4.]), mindspore.float32)
            >>> end = Tensor(np.array([10., 10., 10., 10.]), mindspore.float32)
            >>> output = start.lerp( end, 0.5)
            >>> print(output)
            [5.5 6. 6.5 7. ]
        """
        self._init_check()
        return tensor_operator_registry.get('lerp')(self, end, weight)

    def norm(self, axis, p=2, keep_dims=False, epsilon=1e-12):
        """
        Returns the matrix norm or vector norm of a given tensor.

        Args:
            axis (Union[int,list,tuple]): Specifies which dimension or dimensions of input to calculate the norm across.
            p (int): The order of norm. Default: 2.
            keep_dims (bool): Whether the output tensors have dim retained or not. Default: False.
            epsilon (float): A value added to the denominator for numerical stability. Default: 1e-12.

        Returns:
            Tensor, has the same dtype as self tensor, which shape depends on the args axis.
            For example, if the size of input is (2, 3, 4), axis is [0, 1], Outputs' shape will be (4,).

        Raises:
            TypeError: If dtype of self tensor is not one of: float16, float32.
            TypeError: If `p` is not an int.
            TypeError: If `axis` is not an int, a tuple or a list.
            TypeError: If `axis` is a tuple or a list, but the element of `axis` is not an int.
            TypeError: If `keep_dims` is not a bool.
            TypeError: If `epsilon` is not a float.
            ValueError: If the element of `axis` is out of the range [-len(input_x.shape), len(input_x.shape)).
                input_x refers to self tensor.
            ValueError: If the length of shape of `axis` is bigger than the length of shape of self tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> input_x = Tensor(np.array([[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]).astype(np.float32))
            >>> output = input_x.norm([0, 1], p=2)
            >>> print(output)
            [ 9.165152 10.954452]
        """
        self._init_check()
        return tensor_operator_registry.get('norm')(self, axis, p, keep_dims, epsilon)

    def renorm(self, p, dim, maxnorm):
        """
        Renormalizes the sub-tensors along dimension `dim`, and each sub-tensor's p-norm should not exceed the
        'maxnorm'. The values of current sub-tensor don't need change if the p-norm of the sub-tensor is less than
        `maxnorm`. Otherwise the sub-tensor needs to be modified to the original value of the corresponding position
        divided by the p-norm of the substensor and then multiplied by `maxnorm`.

        Args:
            p (float): Power of norm calculation.
            dim (int): The dimension that expected to get the slice-tensor.
            maxnorm (float): Max norm.

        Returns:
            Tensor, has the same dtype and shape as itself.

        Raises:
            TypeError: If dtype of `p` is not int.
            TypeError: If dtype of `dim` is not int.
            TypeError: If dtype of `maxnorm` is not float32.
            ValueError: If the value of `p` less than 1.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]]), mindspore.float32)
            >>> y = x.renorm(p=1, dim=0, maxnorm=5.)
            >>> print(y)
            [[1.       1.        1.        1.       ]
            [1.6666666 1.6666666 1.6666666 1.6666666]
            [1.6666667 1.6666667 1.6666667 1.6666667]]
        """
        self._init_check()
        return tensor_operator_registry.get("renorm")(self, p, dim, maxnorm)

    def approximate_equal(self, other, tolerance=1e-5):
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
            other (Tensor): Second tensor to compare, with data type belongs to float32, float16.
            tolerance (float): The maximum deviation that two elements can be considered equal. Default: 1e-05.

        Returns:
            Tensor, has the same shape as self tensor, and the data type is bool.

        Raises:
            TypeError: If `tolerance` is not a float.
            RuntimeError: If the data type of `x`, `y` conversion of Parameter is given
                        but data type conversion of Parameter is not supported.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> from mindspore.ops.function.math_func imsport approximate_equal
            >>> ...
            >>> tol = 2.
            >>> x = Tensor(np.array([1, 2, 3]), mstype.float32)
            >>> y = Tensor(np.array([2, 4, 6]), mstype.float32)
            >>> output = Tensor(x).approximate_equal(Tensor(y), tol)
            >>> print(output)
            [ True  False  False]
        """
        validator.check_isinstance("x", self, Tensor)
        validator.check_isinstance("y", other, Tensor)
        validator.check_isinstance("tolerance", tolerance, float)
        self._init_check()
        input_x = self.copy() if self.dtype == mstype.float32 else self.astype(mstype.float16)
        input_y = other.copy() if other.dtype == mstype.float32 else other.astype(mstype.float16)
        return tensor_operator_registry.get('__lt__')(tensor_operator_registry.get('abs')()(
            tensor_operator_registry.get('__sub__')(input_x, input_y)
        ), tolerance)


    def matrix_determinant(self):
        """
        Computes the determinant of one or more square matrices.

        Returns:
            y (Tensor): The shape is `x_shape[:-2]`, the dtype is same as self tensor. `x` refer to self tensor.

        Raises:
            TypeError: If self tensor is not a Tensor.
            TypeError: If dtype of self tensor not float32, float64, complex64 or complex128.
            ValueError: If the last two dimensions of self tensor is not same size.
            ValueError: If the dimension of self tensor is less than 2.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> input_x = Tensor(np.array([[[-4.5, -1.5], [7.0, 6.0]], [[2.5, 0.5], [3.0, 9.0]]]), mindspore.float32)
            >>> output = input_x.matrix_determinant()
            >>> print(output)
            [-16.5 21. ]
        """
        self._init_check()
        return tensor_operator_registry.get('matrix_determinant')(self)

    def log_matrix_determinant(self):
        """
        Computes the sign and the log of the absolute value of the determinant of one or more square matrices.

        Returns:
            sign (Tensor): The signs of the log determinants. The shape is `x_shape[:-2]`,
                the dtype is same as self tensor. `x` refer to self tensor.
            y (Tensor): The absolute values of the log determinants. The shape is `x_shape[:-2]`, the dtype is same
                as self tensor. `x` refer to self tensor.

        Raises:
            TypeError: If self tensor is not a Tensor.
            TypeError: If dtype of self tensor not float32, float64, complex64 or complex128.
            ValueError: If the last two dimensions of self tensor is not same size.
            ValueError: If the dimension of self tensor is less than 2.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> input_x = Tensor(np.array([[[-4.5, -1.5], [7.0, 6.0]], [[2.5, 0.5], [3.0, 9.0]]]), mindspore.float32)
            >>> output = input_x.log_matrix_determinant()
            >>> print(output)
            (Tensor(shape=[2], dtype=Float32, value= [-1.00000000e+00,  1.00000000e+00]), Tensor(shape=[2],
            dtype=Float32, value= [ 2.80336046e+00,  3.04452229e+00]))
        """
        self._init_check()
        return tensor_operator_registry.get('log_matrix_determinant')(self)

    def isclose(self, x2, rtol=1e-05, atol=1e-08, equal_nan=False):
        """
        Returns a boolean Tensor where two Tensors are element-wise equal within a tolerance.

        Note:
            On Ascend, input arrays containing inf or NaN are not supported. Therefore, when the input is NaN or inf,
            the result is uncertain. And `equal_nan` must be True on Ascend.

        Args:
            x2 (Tensor): Second Tensor to compare, with data type belongs to float32, float16, int32.
            rtol (float, optional): Relative tolerance. Default: 1e-05.
            atol (float, optional): Absolute tolerance. Default: 1e-08.
            equal_nan (bool, optional): If True, then two NaNs will be considered equal. Default: False.

        Returns:
            A bool Tensor, with the shape as broadcasted result of the input Tensor and `x2`.

        Raises:
            TypeError: If either of self Tensor and `x2` is not Tensor.
            TypeError: If either of self Tensor and `x2` is not float16, float32 or int32.
            TypeError: If either of `atol` and `rtol` is not float.
            TypeError: If `equal_nan` is not bool.
            TypeError: If the dtype of self Tensor is not same as the `x2`.
            ValueError: If self Tensor and `x2` can not be broadcast.
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
        self._init_check()
        return tensor_operator_registry.get('isclose')(self, x2, rtol, atol, equal_nan)

    def inv(self):
        r"""
        Computes Reciprocal of this Tensor element-wise.

        .. math::
            out_i = \frac{1}{x_{i} }

        Returns:
            Tensor, has the same type and shape as self Tensor.

        Raises:
            TypeError: If dtype of this Tensor is not one of float16, float32, int32.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([0.25, 0.4, 0.31, 0.52]), mindspore.float32)
            >>> output = x.inv()
            >>> print(output)
            [4.        2.5       3.2258065 1.923077 ]
        """
        self._init_check()
        return tensor_operator_registry.get('inv')(self)

    def invert(self):
        r"""
        Flips all bits of this Tensor element-wise.

        .. math::
            out_i = ~x_{i}

        Returns:
            Tensor, has the same shape as as self Tensor.

        Raises:
            TypeError: If dtype of this Tensor is neither int16 nor uint16.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([25, 4, 13, 9]), mindspore.int16)
            >>> output = x.invert()
            >>> print(output)
            [-26 -5 -14 -10]
        """
        self._init_check()
        return tensor_operator_registry.get('invert')(self)

    def pow(self, power):
        r"""
        Calculate the power of Tensor.

        .. math::

            out_{i} = x_{i} ^{ y_{i}}

        Note:
            - The current Tensor and `power` comply with the implicit type conversion rules to make the data
              types consistent.
            - Dtypes of the current Tensor and power cannot be bool at the same time, and the shapes of them
              can be broadcast.

        Args:
            power (Union[Tensor, number.Number, bool]): The power value, should be a number.Number or bool value,
                or a Tensor whose data type is number or bool\_.

        Returns:
            Tensor, the shape is the same as the one after broadcasting,
                and the data type is the one with higher precision or higher digits among `Tensor` and `power`.

        Raises:
            TypeError: If `power` is not one of the following: Tensor, number.Number or bool.
            ValueError: If the shape of the current Tensor and `power` are different.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([1.0, 2.0, 4.0]), mindspore.float32)
            >>> y = 3.0
            >>> output = x.pow(y)
            >>> print(output)
            [ 1.  8. 64.]
            >>>
            >>> x = Tensor(np.array([1.0, 2.0, 4.0]), mindspore.float32)
            >>> y = Tensor(np.array([2.0, 4.0, 3.0]), mindspore.float32)
            >>> output = x.pow(y)
            >>> print(output)
            [ 1. 16. 64.]
        """
        self._init_check()
        return tensor_operator_registry.get('pow')()(self, power)

    def mean(self, axis=(), keep_dims=False):
        """
        Reduce a dimension of a tensor by averaging all elements in the dimension.

        Args:
            axis (Union[None, int, tuple(int), list(int)]): Dimensions of reduction.
                When the axis is None or empty tuple, reduce all dimensions. When the axis is int, tuple(int) or
                list(int), if the dimension of Tensor is dim, the value range is [-dim, dim). Default: ().
            keep_dims (bool): Whether to keep the reduced dimensions. Default: False.

        Returns:
            Tensor, has the same data type as input tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.std`: Compute the standard deviation along the specified axis.

            :func:`mindspore.Tensor.var`: Compute the variance along the specified axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([1, 2, 3], dtype=np.float32))
            >>> output = input_x.mean()
            >>> print(output)
            2.0
        """
        self._init_check()
        if axis is None:
            axis = ()
        return tensor_operator_registry.get('mean')(keep_dims)(self, axis)

    def prod(self, axis=(), keep_dims=False):
        """
        Reduce a dimension of a tensor by product all elements in the dimension.

        Args:
            axis (Union[None, int, tuple(int), list(int)]): Dimensions of reduction.
                When the axis is None or empty tuple, reduce all dimensions. When the axis is int, tuple(int) or
                list(int), if the dimension of Tensor is dim, the value range is [-dim, dim). Default: ().
            keep_dims (bool): Whether to keep the reduced dimensions. Default: False.

        Returns:
            Tensor, has the same data type as input tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([1, 2, 3], dtype=np.float32))
            >>> output = input_x.prod()
            >>> print(output)
            6.0
        """
        self._init_check()
        return tensor_operator_registry.get('reduce_prod')(self, axis, keep_dims)

    def select(self, condition, y):
        r"""
        The conditional tensor determines whether the corresponding element in the output must be
        selected from the current Tensor (if true) or :math:`y` (if false) based on the value of each element.

        It can be defined as:

        .. math::
            out_i = \begin{cases}
            tensor_i, & \text{if } condition_i \\
            y_i, & \text{otherwise}
            \end{cases}

        Args:
            condition (Tensor[bool]): The condition tensor, decides which element is chosen.
              The shape is the same as the current Tensor.
            y (Union[Tensor, int, float]): If y is Tensor, the shape is the same as the current Tensor.
              If y is an int or a float, it will be cast to the type of int32 or float32, and broadcast to the same
              shape as the Tensor.

        Returns:
            Tensor, has the same shape as the current Tensor.

        Raises:
            TypeError: If `y` is not a Tensor, an int or a float.
            ValueError: The shapes of inputs are different.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> # 1) y is Tensor
            >>>
            >>> cond = Tensor([True, False])
            >>> x = Tensor([2,3], mindspore.float32)
            >>> y = Tensor([1,2], mindspore.float32)
            >>> output = x.select(cond, y)
            >>> print(output)
            [2. 2.]
            >>> # 2) y is a float
            >>> cond = Tensor([True, False])
            >>> x = Tensor([2,3], mindspore.float32)
            >>> y = 2.0
            >>> output = x.select(cond, y)
            >>> print(output)
            [2. 2.]
        """
        self._init_check()
        if not isinstance(condition, Tensor):
            raise TypeError(f"For 'Tensor.select', the argument 'condition' should be Tensor,"
                            f" but got {type(condition)}.")
        if not isinstance(y, (Tensor, int, float)):
            raise TypeError(f"For 'Tensor.select', the argument 'y' should be Tensor, int or float,"
                            f" but got {type(y)}.")
        if isinstance(y, int) and self.dtype != mstype.int32:
            raise TypeError(f"For 'Tensor.select', if the argument 'y' is int,"
                            f" then the tensor type should be int32 but got {self.dtype}")
        if isinstance(y, float) and self.dtype != mstype.float32:
            raise TypeError(f"For 'Tensor.select', if the argument 'y' is float,"
                            f" then the tensor type should be float32 but got {self.dtype}")
        input_y = y
        if isinstance(y, (int, float)):
            input_y = tensor_operator_registry.get('zeros_like')()(self) + y
            if isinstance(y, int):
                input_y = tensor_operator_registry.get('cast')(input_y, mstype.int32)
            else:
                input_y = tensor_operator_registry.get('cast')(input_y, mstype.float32)
        return tensor_operator_registry.get('select')(condition, self, input_y)

    def transpose(self, *axes):
        r"""
        Return a tensor with axes transposed.

        - For a 1-D tensor, this has no effect, as a transposed vector is simply the same vector.
        - For a 2-D tensor, this is a standard matrix transpose.
        - For an n-D tensor, if axes are given, their order indicates how the axes are permuted.

        If axes are not provided and ``tensor.shape = (i[0], i[1],...i[n-2], i[n-1])``,
        then ``tensor.transpose().shape = (i[n-1], i[n-2], ... i[1], i[0])``.

        Args:
            axes(Union[None, tuple(int), list(int), int], optional): If axes is None or
                blank, the method will reverse the order of the axes. If axes is tuple(int)
                or list(int), tensor.transpose() will transpose the tensor to the new axes order.
                If axes is int, this form is simply intended as a convenience alternative to the
                tuple/list form.

        Returns:
            Tensor, has the same dimension as input tensor, with axes suitably permuted.

        Raises:
            TypeError: If input arguments have types not specified above.
            ValueError: If the number of `axes` is not equal to Tensor's ndim.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((1,2,3), dtype=np.float32))
            >>> x = x.transpose()
            >>> print(x.shape)
            (3, 2, 1)
        """
        self._init_check()
        perm = validator.check_transpose_axis(axes, self.ndim)
        return tensor_operator_registry.get('transpose')()(self, perm)

    def col2im(self, output_size, kernel_size, dilation, padding_value, stride):
        """
        Combines an array of sliding local blocks into a large containing tensor.

        Args:
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
            A 4D Tensor, with same type as input 'x'.

        Raises:
            TypeError: If :attr:`kernel_size`, `dilation`, `padding_value`, `stride` data type is not in
                Union[int, tuple[int], list[int]].
            ValueError: If :attr:`kernel_size`, `dilation`, `stride` value is less than zero or elements
                number more than 2.
            ValueError: If :attr:`padding_value` value is not greater than zero or elements number more than 2.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> x = Tensor(input_data=np.random.rand(16, 16, 4, 25), dtype=mstype.float32)
            >>> output_size = Tensor(input_data=[8, 8], dtype=mstype.int32)
            >>> y = x.col2im(output_size, kernel_size=[2, 2], dilation=[2, 2], padding_value=[2, 2], stride=[2, 2])
            >>> print(y.shape)
            (16, 16, 8, 8)
        """
        self._init_check()
        return tensor_operator_registry.get('col2im')(self, output_size, kernel_size, dilation, padding_value, stride)

    def reshape(self, *shape):
        """
        Give a new shape to a tensor without changing its data.

        Args:
            shape(Union[int, tuple(int), list(int)]): The new shape should be compatible
                with the original shape. If an integer, then the result will be a 1-D
                tensor of that length. One shape dimension can be -1. In this case, the
                value is inferred from the length of the tensor and remaining dimensions.

        Returns:
            Tensor, with new specified shape.

        Raises:
            TypeError: If new shape is not integer, list or tuple.
            ValueError: If new shape is not compatible with the original shape.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> from mindspore import dtype as mstype
            >>> x = Tensor([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]], dtype=mstype.float32)
            >>> output = x.reshape((3, 2))
            >>> print(output)
            [[-0.1  0.3]
            [ 3.6  0.4]
            [ 0.5 -3.2]]
        """
        self._init_check()
        new_shape = validator.check_reshape_shp(shape)
        return tensor_operator_registry.get('reshape')()(self, new_shape)

    def ravel(self):
        """
        Return a contiguous flattened tensor.

        Returns:
            Tensor, a 1-D tensor, containing the same elements of the input.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.reshape`: Give a new shape to a tensor without changing its data.

            :func:`mindspore.Tensor.flatten`: Return a copy of the tensor collapsed into one dimension.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((2,3,4), dtype=np.float32))
            >>> output = x.ravel()
            >>> print(output.shape)
            (24,)
        """
        self._init_check()
        reshape_op = tensor_operator_registry.get('reshape')()
        return reshape_op(self, (-1,))

    def round(self):
        """
        Returns half to even of the tensor element-wise.

        Returns:
            Tensor, has the same shape and type as the Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([0.8, 1.5, 2.3, 2.5, -4.5]), mindspore.float32)
            >>> output = x.round()
            >>> print(output)
            [ 1.  2.  2.  2. -4.]
        """
        self._init_check()
        return tensor_operator_registry.get('round')()(self)

    def flatten(self, order='C'):
        r"""
        Return a copy of the tensor collapsed into one dimension.

        Args:
            order (str, optional): Can choose between 'C' and 'F'. 'C' means to
                flatten in row-major (C-style) order. 'F' means to flatten in column-major
                (Fortran-style) order. Default: 'C'.

        Returns:
            Tensor, has the same data type as input.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Raises:
            TypeError: If `order` is not string type.
            ValueError: If `order` is string type, but not 'C' or 'F'.

        See also:
            :func:`mindspore.Tensor.reshape`: Give a new shape to a tensor without changing its data.

            :func:`mindspore.Tensor.ravel`: Return a contiguous flattened tensor.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((2,3,4), dtype=np.float32))
            >>> output = x.flatten()
            >>> print(output.shape)
            (24,)
        """
        self._init_check()
        reshape_op = tensor_operator_registry.get('reshape')()
        trans_op = tensor_operator_registry.get('transpose')()

        order = validator.check_flatten_order(order)
        if order == 'C':
            return reshape_op(self, (-1,))

        perm = tuple(range(self.ndim - 1, -1, -1))
        return reshape_op(trans_op(self, perm), (-1,))

    def narrow(self, axis, start, length):
        """
        Returns a narrowed tensor from input tensor.
        The dimension axis is input from start to start + length.

        Args:
            axis (int): the axis along which to narrow.
            start (int): the starting dimension.
            length (int): the distance to the ending dimension.

        Returns:
            Tensor.

            - output (Tensors) - The narrowed tensor.

        Raises:
            TypeError: axis is not integer.
            TypeError: start is not integer.
            TypeError: length is not integer.
            ValueError: axis is not in the range of [0, ndim-1].
            ValueError: start is not in the range of [0, shape[axis]-1].
            ValueError: start+length is greater than shape[axis]-1.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import mindspore
            >>> from mindspore import Tensor
            >>> x = Tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]], mindspore.int32)
            >>> output = x.narrow(0, 0, 2)
            >>> print(output)
            [[ 1 2 3]
             [ 4 5 6]]
            >>> output = x.narrow(1, 1, 2)
            >>> print(output)
            [[ 2 3]
             [ 5 6]
             [ 8 9]]
        """
        self._init_check()
        return tensor_operator_registry.get('narrow')(self, axis, start, length)

    def swapaxes(self, axis1, axis2):
        """
        Interchange two axes of a tensor.

        Args:
            axis1 (int): First axis.
            axis2 (int): Second axis.

        Returns:
            Transposed tensor, has the same data type as the input.

        Raises:
            TypeError: If `axis1` or `axis2` is not integer.
            ValueError: If `axis1` or `axis2` is not in the range of :math:`[-ndim, ndim-1]`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((2,3,4), dtype=np.float32))
            >>> output = x.swapaxes(0, 2)
            >>> print(output.shape)
            (4,3,2)
        """
        self._init_check()
        axis1, axis2 = validator.check_swapaxes_axis((axis1, axis2), self.ndim)

        if axis1 == axis2:
            return self
        if axis1 > axis2:
            axis1, axis2 = axis2, axis1

        perm = tuple(range(0, self.ndim))
        if axis2 + 1 < self.ndim:
            new_perm = perm[0:axis1] + perm[axis2:axis2 + 1] + \
                perm[axis1 + 1:axis2] + perm[axis1:axis1 + 1] + perm[axis2 + 1:]
        else:
            new_perm = perm[0:axis1] + perm[axis2:axis2 + 1] + \
                perm[axis1 + 1:axis2] + perm[axis1:axis1 + 1]

        return tensor_operator_registry.get('transpose')()(self, new_perm)

    def squeeze(self, axis=None):
        """
        Remove the dimension of shape 1 from the Tensor

        Args:
            axis (Union[None, int, list(int), tuple(int)], optional): Selects a subset of the entries of
                length one in the shape. If an axis is selected with shape entry greater than one,
                an error is raised. Default is None.

        Returns:
            Tensor, with all or a subset of the dimensions of length 1 removed.

        Raises:
            TypeError: If input arguments have types not specified above.
            ValueError: If axis is greater than one.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.expand_as`: Expand the dimension of target tensor to the dimension of input tensor.

            :func:`mindspore.Tensor.reshape`: Give a new shape to a tensor without changing its data.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((1,2,2), dtype=np.float32))
            >>> print(x)
            [[[1. 1.]
            [1. 1.]]]
            >>> print(x.shape)
            (1, 2, 2)
            >>> y = x.squeeze()
            >>> print(y)
            [[1. 1.]
            [1. 1.]]
            >>> print(y.shape)
            (2, 2)
            >>> y = x.squeeze(axis=0)
            >>> print(y)
            [[1. 1.]
            [1. 1.]]
            >>> print(y.shape)
            (2, 2)
        """
        self._init_check()
        if axis is None:
            return tensor_operator_registry.get('squeeze')(self)
        new_shape = validator.prepare_shape_for_squeeze(self.shape, axis)
        return tensor_operator_registry.get('reshape')()(self, new_shape)

    def expand_dims(self, axis):
        """
        Insert a dimension of shape 1 at the specified axis of Tensor

        Args:
            axis (int): the axis at which to insert the singleton dimension.

        Returns:
            Tensor, with inserted dimension of length 1.

        Raises:
            TypeError: If axis is not an int.
            ValueError: If axis is not in range [-self.ndim - 1, self.ndim + 1).

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((2,2), dtype=np.float32))
            >>> print(x)
            [[1. 1.]
            [1. 1.]]
            >>> print(x.shape)
            (2, 2)
            >>> y = x.expand_dims(axis=0)
            >>> print(y)
            [[[1. 1.]
            [1. 1.]]]
            >>> print(y.shape)
            (1, 2, 2)
        """
        self._init_check()
        validator.check_is_int(axis, 'axis')
        validator.check_int_range(axis, -self.ndim - 1, self.ndim + 1, Rel.INC_LEFT, 'axis')
        return tensor_operator_registry.get('expand_dims')(self, axis)

    def astype(self, dtype, copy=True):
        """
        Return a copy of the tensor, cast to a specified type.

        Args:
            dtype (Union[:class:`mindspore.dtype`, numpy.dtype, str]): Designated tensor dtype, can be in
                format of :class:`mindspore.dtype.float32` or :class:`numpy.float32` or `float32`.
            copy (bool, optional): By default, astype always returns a newly allocated
                tensor. If this is set to false, the input tensor is returned instead
                of a copy. Default: True.

        Returns:
            Tensor, with the designated dtype.

        Raises:
            TypeError: If the specified dtype cannot be understood.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.ones((1,2,2,1), dtype=np.float32))
            >>> x = x.astype("int32")
            >>> print(x.dtype)
            Int32
        """
        self._init_check()
        dtype = _check_astype_and_convert(dtype)
        if not copy and dtype == self.dtype:
            return self
        return tensor_operator_registry.get('cast')(self, dtype)

    def argmax(self, axis=None):
        """
        Return the indices of the maximum values along an axis.

        Args:
            axis (int, optional): By default, the index is into
                the flattened tensor, otherwise along the specified axis. Default: None.

        Returns:
            Tensor, indices into the input tensor. It has the same
            shape as self.shape with the dimension along axis removed.

        Raises:
            ValueError: If the axis is out of range.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.argmin`: Return the indices of the minimum values along an axis.

            :func:`mindspore.Tensor.min`: Return the minimum of a tensor or minimum along an axis.

            :func:`mindspore.Tensor.max`: Return the maximum of a tensor or maximum along an axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.arange(10, 16).reshape(2, 3).astype("float32"))
            >>> print(a.argmax())
            5
        """
        # P.Argmax only supports float
        a = self.astype(mstype.float32)
        if axis is None:
            a = a.ravel()
            axis = 0
        else:
            axis = validator.check_axis_in_range(axis, a.ndim)
        return tensor_operator_registry.get('argmax')(axis)(a)

    def argmin(self, axis=None):
        """
        Return the indices of the minimum values along an axis.

        Args:
            axis (int, optional): By default, the index is into
                the flattened tensor, otherwise along the specified axis. Default: None.

        Returns:
            Tensor, indices into the input tensor. It has the same
            shape as self.shape with the dimension along axis removed.

        Raises:
            ValueError: If the axis is out of range.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.argmax`: Return the indices of the maximum values along an axis.

            :func:`mindspore.Tensor.min`: Return the minimum of a tensor or minimum along an axis.

            :func:`mindspore.Tensor.max`: Return the maximum of a tensor or maximum along an axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.arange(10, 16).reshape(2, 3).astype("float32"))
            >>> print(a.argmin())
            0
        """
        # P.Argmin only supports float
        a = self.astype(mstype.float32)
        if axis is None:
            a = a.ravel()
            axis = 0
        else:
            axis = validator.check_axis_in_range(axis, a.ndim)
        # P.Argmin is currently not supported
        return tensor_operator_registry.get('argmax')(axis)(tensor_operator_registry.get('__neg__')(a))

    def cumsum(self, axis=None, dtype=None):
        """
        Return the cumulative sum of the elements along a given axis.

        Note:
            If ``self.dtype`` is :class:`int8`, :class:`int16` or :class:`bool`, the result
            `dtype` will be elevated to :class:`int32`, :class:`int64` is not supported.

        Args:
            axis (int, optional): Axis along which the cumulative sum is computed. The
                default (None) is to compute the cumsum over the flattened array.
            dtype (:class:`mindspore.dtype`, optional): If not specified, stay the same as original
                tensor, unless it has an integer dtype with a precision less than :class:`float32`.
                In that case, :class:`float32` is used. Default: None.

        Raises:
            ValueError: If the axis is out of range.

        Returns:
            Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.sum`: Return sum of tensor elements over a given axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.ones((3,3)).astype("float32"))
            >>> output = a.cumsum(axis=0)
            >>> print(output)
            [[1. 1. 1.]
            [2. 2. 2.]
            [3. 3. 3.]]
        """
        x = self
        original_dtype = x.dtype
        # If original tensor is int, and has precision less then int32, convert to int32
        if x.dtype in (mstype.bool_, mstype.int8, mstype.int16, mstype.uint8, mstype.int16):
            x = x.astype(mstype.int32)
        if axis is None:
            x = x.ravel()
            axis = 0
        validator.check_axis_in_range(axis, x.ndim)
        if dtype is not None and original_dtype != dtype:
            return tensor_operator_registry.get('cumsum')()(x, axis).astype(dtype, copy=False)
        return tensor_operator_registry.get('cumsum')()(x, axis)

    def cummin(self, axis):
        r"""
        Returns a tuple (values,indices) where 'values' is the cumulative minimum value of self Tensor
        along the dimension `axis`, and `indices` is the index location of each minimum value.

        .. math::
            \begin{array}{ll} \\
                y{i} = min(x{1}, x{2}, ... , x{i})
            \end{array}

        Args:
            axis (int): The dimension to do the operation over. The value of `axis` must be in the range
                `[-x.ndim, x.ndim - 1]`.

        Returns:
            tuple [Tensor], tuple of 2 Tensors, containing the cumulative minimum of elements and the index,
            The shape of each output tensor is the same as self Tensor.

        Raises:
            TypeError: If `axis` is not an int.
            ValueError: If `axis` is out the range of `[-x.ndim, x.ndim - 1]`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor, ops
            >>> import mindspore
            >>> a = Tensor([-0.2284, -0.6628,  0.0975,  0.2680, -1.3298, -0.4220], mindspore.float32)
            >>> output = a.cummin(axis=0)
            >>> print(output[0])
            [-0.2284 -0.6628 -0.6628 -0.6628 -1.3298 -1.3298]
            >>> print(output[1])
            [0 1 1 1 4 4]
        """
        return tensor_operator_registry.get('cummin')(self, axis)

    def cummax(self, axis):
        r"""
        Returns a tuple (values,indices) where 'values' is the cumulative maximum value of self Tensor
        along the dimension `axis`, and `indices` is the index location of each maximum value.

        .. math::
            \begin{array}{ll} \\
                y{i} = max(x{1}, x{2}, ... , x{i})
            \end{array}

        Args:
            axis (int): The dimension to do the operation over. The value of `axis` must be in the range
                `[-x.ndim, x.ndim - 1]`.

        Returns:
            tuple [Tensor], tuple of 2 Tensors, containing the cumulative maximum of elements and the index,
            The shape of each output tensor is the same as self Tensor.

        Raises:
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
            >>> output = x.cummax(axis=0)
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
        return tensor_operator_registry.get('cummax')(self, axis)

    def index_fill(self, dim, index, value):
        """
        Fills the elements under the dim dimension of the self tensor with the input value
        by selecting the indices in the order given in index.
        """
        return tensor_operator_registry.get('index_fill')(self, dim, index, value)

    def inplace_update(self, v, indices):
        """
        Update some rows of a tensor with values of v according to the specified indices.

        Args:
            v (Tensor): A tensor with the same type and same dimension size except the first dimension, which must be
              the same as the size of indices.
            indices (Union[int, tuple]): Indices into the left-most dimension determining which rows to be updated.

        Returns:
            Tensor, with updated values.

        Raises:
            TypeError: if indices is not int or tuple.
            TypeError: if indices is tuple but any of its element is not int.
            ValueError: the Tensor shape is different from that of v.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> import mindspore
            >>> x = Tensor(np.array([[1, 2], [3, 4], [5, 6]]), mindspore.float32)
            >>> v = Tensor(np.array([[0.1, 0.2], [0.3, 0.4]]), mindspore.float32)
            >>> indices = (0, 1)
            >>> output = x.inplace_update(v, indices)
            >>> print(output)
            [[0.1 0.2]
             [0.3 0.4]
             [5.  6. ]]
        """
        self._init_check()
        return tensor_operator_registry.get('inplace_update')(indices)(self, v)

    def copy(self):
        """
        Return a copy of the tensor.

        Note:
            The current implementation does not support `order` argument.

        Returns:
            Copied tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.ones((3,3)).astype("float32"))
            >>> output = a.copy()
            >>> print(output)
            [[1. 1. 1.]
            [1. 1. 1.]
            [1. 1. 1.]]
        """
        if self.size == 0:
            return self
        origin_dtype = self.dtype
        x = self
        logical_not_op = tensor_operator_registry.get('logical_not')()
        if origin_dtype == mstype.bool_:
            return logical_not_op(logical_not_op(x))
        if origin_dtype != mstype.float64:
            x = x.astype("float32")
        x = x / 1.0
        x = x.astype(origin_dtype)
        return x

    def max(self, axis=None, keepdims=False, initial=None, where=True):
        """
        Return the maximum of a tensor or maximum along an axis.

        Args:
            axis (Union[None, int, tuple of ints], optional): Axis or
                axes along which to operate. By default, flattened input is used. If
                this is a tuple of ints, the maximum is selected over multiple axes,
                instead of a single axis or all the axes as before. Default: None.
            keepdims (bool, optional):
                If this is set to True, the axes which are reduced are left in the
                result as dimensions with size one. With this option, the result will
                broadcast correctly against the input array. Default: False.
            initial (scalar, optional):
                The minimum value of an output element. Must be present to allow
                computation on empty slice. Default: None.
            where (bool Tensor, optional):
                A boolean tensor which is broadcasted to match the dimensions of array,
                and selects elements to include in the reduction. If non-default value
                is passed, initial must also be provided. Default: True.

        Returns:
            Tensor or scalar, maximum of input tensor. If `axis` is None, the result is a scalar
            value. If `axis` is given, the result is a tensor of dimension ``self.ndim - 1``.

        Raises:
            TypeError: If arguments have types not specified above.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.argmin`: Return the indices of the minimum values along an axis.

            :func:`mindspore.Tensor.argmax`: Return the indices of the maximum values along an axis.

            :func:`mindspore.Tensor.min`: Return the minimum of a tensor or minimum along an axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.arange(4).reshape((2, 2)).astype('float32'))
            >>> output = a.max()
            >>> print(output)
            3.0
        """
        reduce_ = tensor_operator_registry.get("reduce")
        reduce_max = tensor_operator_registry.get("reduce_max")
        maximum = tensor_operator_registry.get("maximum")
        return reduce_(self, reduce_max(keepdims), cmp_fn=maximum(), axis=axis, keepdims=keepdims,
                       initial=initial, where=where)

    def min(self, axis=None, keepdims=False, initial=None, where=True):
        """
        Return the minimum of a tensor or minimum along an axis.

        Args:
            axis (Union[None, int, tuple of ints], optional): Axis or
                axes along which to operate. By default, flattened input is used. If
                this is a tuple of ints, the minimum is selected over multiple axes,
                instead of a single axis or all the axes as before. Default: None.
            keepdims (bool, optional):
                If this is set to True, the axes which are reduced are left in the
                result as dimensions with size one. With this option, the result will
                broadcast correctly against the input tensor. Default: False.
            initial (scalar, optional):
                The maximum value of an output element. Must be present to allow
                computation on empty slice. Default: None.
            where (bool Tensor, optional):
                A boolean tensor which is broadcasted to match the dimensions of tensor,
                and selects elements to include in the reduction. If non-default value
                is passed, initial must also be provided. Default: True.

        Returns:
            Tensor or scalar, minimum of input tensor. If the axis is None, the result is a scalar
            value. If `axis` is given, the result is a tensor of dimension ``self.ndim - 1``.

        Raises:
            TypeError: If arguments have types not specified above.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.argmin`: Return the indices of the minimum values along an axis.

            :func:`mindspore.Tensor.argmax`: Return the indices of the maximum values along an axis.

            :func:`mindspore.Tensor.max`: Return the maximum of a tensor or maximum along an axis.

        Examples:
            >>> from mindspore import Tensor
            >>> import mindspore.numpy as np
            >>> a = Tensor(np.arange(4).reshape((2,2)).astype('float32'))
            >>> output = a.min()
            >>> print(output)
            0.0
        """
        reduce_ = tensor_operator_registry.get("reduce")
        reduce_min = tensor_operator_registry.get("reduce_min")
        minimum = tensor_operator_registry.get("minimum")
        return reduce_(self, reduce_min(keepdims), cmp_fn=minimum(), axis=axis, keepdims=keepdims,
                       initial=initial, where=where)

    def scatter_add(self, indices, updates):
        """
        Creates a new tensor by adding the values from the positions in self tensor indicated by
        `indices`, with values from `updates`. When multiple values are given for the same
        index, the updated result will be the sum of all values. This operation is almost
        equivalent to using ScatterNdAdd, except that the updates are applied on output `Tensor`
        instead of input `Parameter`.

        The last axis of `indices` is the depth of each index vectors. For each index vector,
        there must be a corresponding value in `updates`. The shape of `updates` should be
        equal to the shape of `self[indices]`. For more details, see use cases.

        Note:
            If some values of the `indices` are out of bound, instead of raising an index error,
            the corresponding `updates` will not be updated to self tensor.

        Args:
            indices (Tensor): The index of input tensor whose data type is int32 or int64.
                The rank must be at least 2.
            updates (Tensor): The tensor to update the input tensor, has the same type as self tensor,
                and updates. Shape should be equal to indices.shape[:-1] + self.shape[indices.shape[-1]:].

        Returns:
            Tensor, has the same shape and type as self tensor.

        Raises:
            TypeError: If dtype of `indices` is neither int32 nor int64.
            ValueError: If length of shape of self tensor is less than the last dimension of shape of `indices`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]).astype('float32'))
            >>> indices = Tensor(np.array([[0, 0], [0, 0]]).astype('int32'))
            >>> updates = Tensor(np.array([1.0, 2.2]).astype('float32'))
            >>> output = x.scatter_add(indices, updates)
            >>> print(output)
            [[ 3.1  0.3  3.6]
            [ 0.4  0.5 -3.2]]
        """
        self._init_check()
        return tensor_operator_registry.get("tensor_scatter_add")()(self, indices, updates)

    def scatter_sub(self, indices, updates):
        """
        Creates a new tensor by subtracting the values from the positions in self tensor indicated by
        `indices`, with values from `updates`. When multiple values are provided for the same
        index, the result of the update will be to subtract these values respectively. This operation is almost
        equivalent to using :class:`mindspore.ops.ScatterNdSub` , except that the updates are applied on output `Tensor`
        instead of input `Parameter`.

        The last axis of `indices` is the depth of each index vectors. For each index vector,
        there must be a corresponding value in `updates`. The shape of `updates` should be
        equal to the shape of `self[indices]`. For more details, see use cases.

        Note:
            If some values of the `indices` are out of bound, instead of raising an index error,
            the corresponding `updates` will not be updated to `input_x`, the variable `input_x` refers to self tensor.

        Args:
            indices (Tensor): The index of input tensor whose data type is int32 or int64.
                The rank must be at least 2.
            updates (Tensor): The tensor to update the input tensor, has the same type as input,
                and updates.shape should be equal to indices.shape[:-1] + self.shape[indices.shape[-1]:].

        Returns:
            Tensor, has the same shape and type as self tensor.

        Raises:
            TypeError: If dtype of `indices` is neither int32 nor int64.
            ValueError: If length of shape of self tensor is less than the last dimension of shape of `indices`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]).astype('float32'))
            >>> indices = Tensor(np.array([[0, 0], [0, 0]]).astype('int32'))
            >>> updates = Tensor(np.array([1.0, 2.2]).astype('float32'))
            >>> output = x.scatter_sub(indices, updates)
            >>> print(output)
            [[-3.3000002  0.3        3.6      ]
            [ 0.4        0.5       -3.2      ]]
        """
        self._init_check()
        return tensor_operator_registry.get('tensor_scatter_sub')()(self, indices, updates)

    def scatter_min(self, indices, updates):
        """
        By comparing the value at the position indicated by `indices` in self tensor with the value in the `updates`,
        the value at the index will eventually be equal to the smallest one to create a new tensor.

        The last axis of the index is the depth of each index vector. For each index vector,
        there must be a corresponding value in `updates`. The shape of `updates` should be
        equal to the shape of `input_x[indices]`. For more details, see case below.

        Note:
            If some values of the `indices` are out of range, instead of raising an index error,
            the corresponding `updates` will not be updated to `input_x`.

        Args:
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
            >>> output = x.scatter_min(indices, updates)
            >>> print(output)
            [[ -0.1  0.3  3.6]
            [ 0.4  0.5 -3.2]]
        """
        self._init_check()
        return tensor_operator_registry.get('tensor_scatter_min')()(self, indices, updates)

    def fill(self, value):
        """
        Fill the tensor with a scalar value.

        Note:
            Unlike Numpy, tensor.fill() will always return a new tensor, instead of
            filling the original tensor.

        Args:
            value (Union[None, int, float, bool]): All elements of a will be assigned this value.

        Returns:
            Tensor, with the original dtype and shape.

        Raises:
            TypeError: If input arguments have types not specified above.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.arange(4).reshape((2,2)).astype('float32'))
            >>> print(a.fill(1.0))
            [[1. 1.]
            [1. 1.]]
        """
        if value is None:
            if self.dtype not in (mstype.float16, mstype.float32, mstype.float64):
                raise TypeError("For 'Tensor.fill', if the argument 'value' is None, the type of the original "
                                "tensor must be float, but got {}.".format(self.dtype))
            value = Tensor(float('nan')).astype("float32")
            return tensor_operator_registry.get("tile")()(value, self.shape).astype(self.dtype)
        if not isinstance(value, (int, float, bool)):
            raise TypeError("For 'Tensor.fill', the type of the argument 'value' must be int, float or bool, "
                            "but got {}.".format(type(value)))
        return tensor_operator_registry.get("fill")(self.dtype, self.shape, value)

    def fills(self, value):
        """
        Create a tensor of the same shape and type as the input tensor and fill it with specified value.

        Note:
            Unlike Numpy, tensor.fills() will always returns a new tensor, instead of
            filling the original tensor.

        Args:
            value (Union[int, float, Tensor]): All elements of the output tensor will be assigned this value. The
                type should be int, float or 0-dimensional tensor.

        Returns:
            Tensor, with the same shape and type as input tensor.

        Raises:
            TypeError: If `value` has types not specified above.
            RuntimeError: If `value` cannot be converted to the same type as `x`.
            ValueError: If `value` is a tensor and the length of dimension is not 0.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.arange(4).reshape((2, 2)).astype('float32'))
            >>> print(x.fills(1.0))
            [[1. 1.]
            [1. 1.]]
        """
        self._init_check()
        return tensor_operator_registry.get('fills')(self, value)

    def masked_fill(self, mask, value):
        """
        Fills elements of self tensor with value where mask is True.
        The shapes of self tensor and `mask` need to be the same or broadcastable.

        Args:
            mask (Tensor[bool]): The boolean mask.
            value (Union[float, Tensor]): The value to fill in with, which dtype is the same as self.

        Returns:
            Tensor, has the same type and shape as self.

        Raises:
            TypeError: If `mask` is not a Tensor.
            TypeError: If dtype of `mask` is not bool.
            ValueError: If the shapes of self tensor and `mask` could not be broadcast.
            TypeError: If dtype of self tensor or `value` is not one of float16, float32, int8, int32.
            TypeError: If dtype of `value` is different from that of self.
            TypeError: If `value` is neither float number nor Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.arange(4)).astype('float32')
            >>> print(a)
            [0. 1. 2. 3.]
            >>> mask = Tensor([False, False, True, True])
            >>> print(a.masked_fill(mask, 0.0))
            [0. 1. 0. 0.]
        """
        self._init_check()
        if not isinstance(mask, Tensor):
            raise TypeError("For 'Tensor.masked_fill', the type of the argument 'mask' must be Tensor, but "
                            "got {}.".format(type(mask)))
        validator.check_type_name('mask', mask.dtype, [mstype.bool_], "Tensor")
        return tensor_operator_registry.get("masked_fill")(self, mask, value)

    def ptp(self, axis=None, keepdims=False):
        """
        The name of the function comes from the acronym for "peak to peak". Calculate the difference between the
        maximum value and the minimum value along the axis.

        Note:
            Numpy argument `out` is not supported.

        Args:
            axis (Union[None, int, tuple(int)]): Axis or axes along which the range is computed.
                The default is to compute the variance of the flattened tensor. Default: None.
            keepdims (bool): If this is set to True, the axes which are reduced are left in the result as
                dimensions with size one. With this option, the result will broadcast correctly against the tensor.
                Default is False.

        Returns:
            Tensor.

        Raises:
            TypeError: If `self` is not a tensor, or `axis` and `keepdims` have types not specified above.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> x = Tensor([[4.0, 9.0, 2.0, 10.0], [6.0, 9.0, 7.0, 12.0]]).astype("float32")
            >>> print(x.ptp(axis=1))
            [8. 6.]
            >>> print(x.ptp(axis=0))
            [2. 0. 5. 2.]
        """
        if not isinstance(keepdims, bool):
            raise TypeError("For 'Tensor.ptp', the type of the argument 'keepdims' must be bool, "
                            "but got {}.".format(type(keepdims)))
        if axis is None:
            axis = ()
        else:
            validator.check_axis_type(axis, True, True, False)
            axis = validator.check_axis_valid(axis, self.ndim)

        return self.max(axis, keepdims) - self.min(axis, keepdims)

    def clip(self, xmin, xmax, dtype=None):
        """
        Clips (limits) the values in a Tensor.

        Given an interval, values outside the interval are clipped to the interval edges.
        For example, if an interval of :math:`[0, 1]` is specified, values smaller than 0 become 0,
        and values larger than 1 become 1.

        Note:
            Currently, clip with `xmin=nan` or `xmax=nan` is not supported.

        Args:
            xmin (Tensor, scalar, None): Minimum value. If None, clipping is not performed
                on the lower interval edge. Not more than one of `xmin` and `xmax` may be None.
            xmax (Tensor, scalar, None): Maximum value. If None, clipping is not performed
                on the upper interval edge. Not more than one of `xmin` and `xmax` may be None.
                If `xmin` or `xmax` are tensors, then `xmin`, `xmax` and the given tensor
                will be broadcasted to match their shapes.
            dtype (:class:`mindspore.dtype`, optional): Overrides the dtype of the
                output Tensor. Default is None.

        Returns:
            Tensor, a tensor with the elements of the input tensor, but where values
            < `xmin` are replaced with `xmin`, and those > `xmax` with `xmax`.

        Raises:
            TypeError: If inputs have types not specified above.
            ValueError: If the shapes of `x1` and `x2` cannot broadcast, or both `xmin` and `xmax` are `None`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> x = Tensor([1, 2, 3, -4, 0, 3, 2, 0]).astype("float32")
            >>> y = x.clip(0, 2)
            >>> print(y)
            [1. 2. 2. 0. 0. 2. 2. 0.]
            >>> t = Tensor([1, 1, 1, 1, 1, 1, 1, 1])
            >>> y = x.clip(t, 2)
            >>> print(y)
            [1. 2. 2. 1. 1. 2. 2. 1.]
        """
        if xmin is None and xmax is None:
            raise ValueError("For 'Tensor.clip', the argument 'xmin' and 'xman' cannot all be None.")
        x = self
        # F.maximum/minimum does not support when both operands are scalar
        if xmin is not None:
            xmin = Tensor(xmin).astype(x.dtype)
            if x.ndim == 0 and xmin.ndim == 0:
                x = tensor_operator_registry.get("maximum")()(x.reshape((1,)), xmin).squeeze()
            else:
                x = tensor_operator_registry.get("maximum")()(x, xmin)
        if xmax is not None:
            xmax = Tensor(xmax).astype(x.dtype)
            if x.ndim == 0 and xmax.ndim == 0:
                x = tensor_operator_registry.get("minimum")()(x.reshape((1,)), xmax).squeeze()
            else:
                x = tensor_operator_registry.get("minimum")()(x, xmax)
        if dtype is not None and dtype != x.dtype:
            return x.astype(dtype)
        return x

    def _init_check(self):
        if self.has_init:
            self.init_data()
        return self

    def init_data(self, slice_index=None, shape=None, opt_shard_group=None):
        """
        Get the tensor format data of this Tensor.

        Note:
            The init_data function can be called once for the same tensor.

        Args:
            slice_index (int): Slice index of a parameter's slices.
                It is used when initialize a slice of a parameter, it guarantees that devices
                using the same slice can generate the same tensor. Default: None.
            shape (list[int]): Shape of the slice, it is used when initialize a slice of the parameter. Default: None.
            opt_shard_group(str): Optimizer shard group which is used in auto or semi auto parallel mode
                to get one shard of a parameter's slice. Default: None.

        Returns:
            Initialized Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import mindspore as ms
            >>> from mindspore.common.initializer import initializer, Constant
            >>> x = initializer(Constant(1), [2, 2], ms.float32)
            >>> out = x.init_data()
            >>> print(out)
            [[1. 1.]
             [1. 1.]]
        """
        if self.init is None:
            raise TypeError("init_data must be set Tensor.init, init can't be None")

        if shape is None:
            shape = self.shape

        try:
            data = np.ndarray(shape, dtype=mstype.dtype_to_nptype(self.dtype))
        except ValueError:
            msg = "Error shape={}".format(shape)
            logger.critical(msg)
            raise ValueError(msg)

        class seed_context:
            """Set and restore seed."""

            def __init__(self, init):
                self.init = init
                from .seed import get_seed
                global_seed = get_seed()
                self._np_seed = np.random.get_state()[1][0]
                self.need_set_seed = (slice_index is not None)
                self._global_seed = global_seed
                self._device_num = 1
                if self.need_set_seed:
                    self._device_num = get_group_size()

            def __enter__(self):
                if self.need_set_seed:
                    self.seed = self.init.seed
                    if self._global_seed is not None:
                        np.random.seed(slice_index + self._global_seed)
                        self.init.seed = slice_index + self._global_seed
                    else:
                        np.random.seed(slice_index + Tensor.delta_seed)
                        self.init.seed = slice_index + Tensor.delta_seed
                        Tensor.delta_seed += self._device_num

            def __exit__(self, ptype, value, trace):
                if self.need_set_seed:
                    np.random.seed(self._np_seed)
                    self.init.seed, _ = self.seed

        with seed_context(self.init):
            self.init(data)
        if opt_shard_group:
            rank = get_rank(opt_shard_group)
            size = get_group_size(opt_shard_group)
            data = np.split(data, size)[rank]
        self.init = None
        self.assign_value(Tensor_.from_numpy(data))
        return self

    def to_tensor(self, slice_index=None, shape=None, opt_shard_group=None):
        """
        Return init_data() and get the tensor format data of this Tensor.

        Note:
            The usage of `to_tensor` is deprecated. Please use `init_data`.

        Args:
            slice_index (int): Slice index of a parameter's slices.
                It is used when initialize a slice of a parameter, it guarantees that devices
                using the same slice can generate the same tensor. Default: None.
            shape (list[int]): Shape of the slice, it is used when initialize a slice of the parameter. Default: None.
            opt_shard_group(str): Optimizer shard group which is used in auto or semi auto parallel mode
                to get one shard of a parameter's slice. Default: None.

        Returns:
            Initialized Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import mindspore as ms
            >>> from mindspore.common.initializer import initializer, Constant
            >>> x = initializer(Constant(1), [2, 2], ms.float32)
            >>> out = x.to_tensor()
            >>> print(out)
            [[1. 1.]
             [1. 1.]]
        """
        logger.warning("WARN_DEPRECATED: The usage of to_tensor is deprecated."
                       " Please use init_data")
        return self.init_data(slice_index, shape, opt_shard_group)

    def resize(self, *new_shape):
        """
        Changes shape and size of tensor in-place.

        If the shape of the new tensor is larger than the shape of the original tensor, the new tensor will be filled
        with 0. And if the shape of the new tensor is smaller than the shape of the original tensor, the new tensor is
        filled with the elements of the original tensor in order.

        Note:
            Instead of changing the size of the input tensor and returns nothing as in numpy,
            this method returns a new Tensor with the input size.
            Numpy argument `refcheck` is not supported.

        Args:
            new_shape (Union[ints, tuple of ints]): Shape of resized tensor.

        Returns:
            Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.reshape`: Give a new shape to a tensor without changing its data.

            :func:`mindspore.Tensor.repeat`: Repeat elements of a tensor.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32))
            >>> y = x.resize(3, 3)
            >>> print(y)
            [[1. 2. 3.]
            [4. 5. 6.]
            [0. 0. 0.]]
            >>> y = x.resize(2, 2)
            >>> print(y)
            [[1. 2.]
            [3. 4.]]
        """
        if not new_shape:
            return self
        if len(new_shape) == 1:
            if isinstance(new_shape[0], tuple):
                new_shape = new_shape[0]
        flattened = self.ravel()
        cur_size = flattened.size
        new_size = tensor_operator_registry.get('shape_mul')(new_shape)
        diff_size = new_size - cur_size
        if diff_size > 0:
            pad_val = tensor_operator_registry.get('fill')(self.dtype, (diff_size,), 0)
            res = tensor_operator_registry.get('concatenate')(0)((flattened, pad_val))
        else:
            res = flattened[:new_size]
        return res.reshape(new_shape)

    def diagonal(self, offset=0, axis1=0, axis2=1):
        """
        Return specified diagonals.

        Args:
            offset (int, optional): Offset of the diagonal from the main diagonal.
                Can be positive or negative. Defaults to main diagonal.
            axis1 (int, optional): Axis to be used as the first axis of the 2-D
                sub-arrays from which the diagonals should be taken. Defaults to
                first axis (0).
            axis2 (int, optional): Axis to be used as the second axis of the 2-D
                sub-arrays from which the diagonals should be taken. Defaults to
                second axis.

        Returns:
            Tensor, if Tensor is 2-D, return a 1-D Tensor containing the diagonal.

        Raises:
            ValueError: If the input tensor has less than two dimensions.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.trace`: Return the sum along diagonals of the tensor.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.arange(4).reshape(2, 2))
            >>> print(a)
            [[0 1]
            [2 3]]
            >>> output = a.diagonal()
            >>> print(output)
            [0 3]
        """
        ndim = self.ndim
        if ndim < 2:
            raise ValueError("For 'Tensor.diagonal', the original tensor requires at least two dimensions, "
                             "but got {}.".format(ndim))
        dtype = self.dtype

        axes = validator.check_axis_valid((axis1, axis2), ndim)
        perm = ()
        for i in range(ndim):
            if i not in axes:
                perm += (i,)
        perm += axes
        a = self.transpose(perm)

        shape = a.shape
        n, m = shape[-2:]

        e = tensor_operator_registry.get('eye')(n, m, dtype)
        if offset >= m or offset <= -n:
            e = tensor_operator_registry.get('fill')(dtype, (n, m), 0)
        elif offset != 0:
            e = e.astype(mstype.float32)
            if offset > 0:
                e_left = tensor_operator_registry.get('fill')(dtype, (n, offset), 0)
                e_right = e[..., 0:m - offset:1]
                e = tensor_operator_registry.get('concatenate')(1)((e_left, e_right)).astype(dtype)
            elif offset < 0:
                e_upper = tensor_operator_registry.get('fill')(dtype, (-offset, m), 0)
                e_lower = e[0:n + offset:1, ...]
                e = tensor_operator_registry.get('concatenate')(0)((e_upper, e_lower)).astype(dtype)
        e = tensor_operator_registry.get('broadcast_to')(shape)(e)

        prod = tensor_operator_registry.get('__mul__')(a, e)
        res = tensor_operator_registry.get('reduce_sum')(prod.astype(mstype.float32), -1)

        begin = ()
        for i in range(ndim - 2):
            begin += (0,)
        last_dim_begin = max(0, -offset)
        begin += (last_dim_begin,)
        size = res.shape[:-1]
        last_dim_end = min(
            shape[-2], max(0, shape[-1] - offset)) - last_dim_begin
        if last_dim_end <= 0:
            return Tensor([])
        size += (last_dim_end,)
        res = tensor_operator_registry.get('tensor_slice')(res, begin, size)
        return res.astype(dtype)

    def trace(self, offset=0, axis1=0, axis2=1, dtype=None):
        """
        Return the sum along diagonals of the tensor.

        Args:
            offset (int, optional): Offset of the diagonal from the main diagonal.
                Can be positive or negative. Defaults to main diagonal.
            axis1 (int, optional): Axis to be used as the first axis of the 2-D
                sub-arrays from which the diagonals should be taken. Defaults to
                first axis (0).
            axis2 (int, optional): Axis to be used as the second axis of the 2-D
                sub-arrays from which the diagonals should be taken. Defaults to
                second axis.
            dtype (:class:`mindspore.dtype`, optional): defaults to None. Overrides the dtype of the
                output Tensor.

        Returns:
            Tensor, the sum along diagonals.

        Raises:
            ValueError: If the input tensor has less than two dimensions.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.diagonal`: Return specified diagonals.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.eye(3, dtype=np.float32))
            >>> print(x.trace())
            3.0
        """
        d = self.diagonal(offset, axis1=axis1, axis2=axis2)
        shape = d.shape
        if dtype is None:
            dtype = d.dtype
        if shape[-1] == 0:
            return tensor_operator_registry.get('fill')(dtype, shape[:-1], 0)
        res = tensor_operator_registry.get('reduce_sum')(d.astype(mstype.float32), -1)
        return res.astype(dtype)

    def take(self, indices, axis=None, mode='clip'):
        """
        Takes elements from a tensor along an axis.

        Args:
            indices (Tensor): The indices with shape `(Nj...)` of the values to extract.
            axis (int, optional): The axis over which to select values. By default,
                the flattened input tensor is used. Default: `None`.
            mode ('raise', 'wrap', 'clip', optional): Default: "clip".

                'raise' – Raises an error;

                'wrap' – Wraps around;

                'clip' – Clips to the range. 'clip' mode means that all indices that are
                too large are replaced by the index that addresses the last element
                along that axis. Note that this disables indexing with negative numbers.

                Default: 'clip'.

        Returns:
            Tensor, the indexed result.

        Raises:
            ValueError: If `axis` is out of range, or `mode` has values other than ('raise', 'wrap', 'clip')

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.array([4, 3, 5, 7, 6, 8]))
            >>> indices = Tensor(np.array([0, 1, 4]))
            >>> output = a.take(indices)
            >>> print(output)
            [4 3 6]
        """
        if mode not in ('raise', 'wrap', 'clip'):
            raise ValueError(f"For 'Tensor.take', the argument 'mode' should be one of in ['raise', 'wrap', 'clip'],"
                             f" but got {mode}.")
        if axis is None:
            a = self.ravel()
            axis = 0
        else:
            a = self
        ndim = a.ndim
        validator.check_axis_in_range(axis, ndim)
        axis = axis + ndim if axis < 0 else axis

        shape_a = a.shape
        shape_indices = indices.shape
        size_indices = indices.size
        indices = tensor_operator_registry.get('check_indices')(shape_a[axis], indices, mode)

        # reshapes indices to shape (Ni..., Nj..., Nk)
        shape_ni = shape_a[:axis]
        shape_nk = shape_a[axis + 1:]
        shape_out = shape_ni + shape_indices + shape_nk
        shape_indices = tuple(size_indices if i == axis else 1 for i in range(ndim))
        indices = indices.reshape(shape_indices)
        shape_indices = shape_ni + (indices.size,) + shape_nk
        indices = tensor_operator_registry.get('broadcast_to')(shape_indices)(indices)

        res = tensor_operator_registry.get('gather_d')(a, axis, indices)
        return res.reshape(shape_out)

    def choose(self, choices, mode='clip'):
        """
        Construct a tensor from an index tensor and a list of tensors to choose from.

        Args:
            choices (Union[tuple, list, Tensor]): Choice tensors. The input tensor and all of the
                `choices` must be broadcasted to the same shape. If `choices` is itself a tensor,
                then its outermost dimension (i.e., the one corresponding to ``choices.shape[0]``)
                is taken as defining the "sequence".
            mode ('raise', 'wrap', 'clip', optional): Specifies how indices outside
                ``[0, n-1]`` will be treated:

                'raise' – Raises an error;

                'wrap' – Wraps around;

                'clip' – Clips to the range. 'clip' mode means that values greater than n-1 are mapped to n-1.
                Note that this disables indexing with negative numbers.

                Default: 'clip'.

        Returns:
            Tensor, the merged result.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Raises:
            ValueError: If the input tensor and any of the `choices` cannot be broadcast.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> choices = [[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23], [30, 31, 32, 33]]
            >>> x = Tensor(np.array([2, 3, 1, 0]))
            >>> print(x.choose(choices))
            [20 31 12  3]
        """
        if isinstance(choices, Tensor):
            shape_choice = validator.infer_out_shape(self.shape, choices.shape[1:])
            choices = tensor_operator_registry.get('broadcast_to')((choices.shape[0],) + shape_choice)(choices)
        else:
            # broadcasts choices to the same shape if choices is a sequence
            choicelist = []
            shapes = ()
            for choice in choices:
                if not isinstance(choice, Tensor):
                    choice = tensor_operator_registry.get('make_tensor')(choice)
                shapes += (choice.shape,)
                choicelist.append(choice)
            shape_choice = validator.infer_out_shape(self.shape, *shapes)
            tmp = []
            for choice in choicelist:
                tmp.append(tensor_operator_registry.get('broadcast_to')(shape_choice)(choice))
            choices = tensor_operator_registry.get('stack')(0)(tmp)

        if self.ndim == 0 or choices.ndim == 0:
            raise ValueError(f"For 'Tensor.choose', the original tensor and the argument 'choices' cannot be scalars."
                             f" Their dimensions should all be > 0, but got the original tensor's dimension "
                             f"{self.ndim}, 'choices' dimension {choices.ndim}.")
        a = tensor_operator_registry.get('broadcast_to')(shape_choice)(self)
        dtype = choices.dtype
        # adjusts dtype for F.tensor_mul and F.gather_nd
        a = a.astype(mstype.int32)
        choices = choices.astype(mstype.int32)
        a = tensor_operator_registry.get('check_indices')(choices.shape[0], a, mode, allow_negative_index=False)

        grids = []
        ndim = len(a.shape)
        for i in range(ndim):
            dim_grid = Tensor(list(range(a.shape[i])), mstype.int32)
            dim_shape = validator.expanded_shape(ndim, a.shape[i], i)
            dim_grid = tensor_operator_registry.get('broadcast_to')(a.shape)(dim_grid.reshape(dim_shape))
            grids.append(dim_grid)
        grid = tensor_operator_registry.get('stack')(-1)(grids)
        indices = tensor_operator_registry.get('concatenate')(-1)((a.reshape(a.shape + (1,)), grid))
        return tensor_operator_registry.get('gather_nd')(choices, indices).astype(dtype)

    def searchsorted(self, v, side='left', sorter=None):
        """
        Finds indices where elements should be inserted to maintain order.

        Args:
            v (Union[int, float, bool, list, tuple, Tensor]): Values to insert into the tensor.
            side ('left', 'right', optional): If 'left', the index of the first suitable
                location found is given. If 'right', return the last such index. If there is
                no suitable index, return either 0 or N (where N is the length of the tensor).
                Default: 'left'.
            sorter (Union[int, float, bool, list, tuple, Tensor]): 1-D optional tensor of
                integer indices that sort the tensor into ascending order. They are typically
                the result of argsort. Default: None.

        Returns:
            Tensor, array of insertion points with the same shape as `v`.

        Raises:
            ValueError: If argument for `side` or `sorter` is invalid.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([1, 2, 3, 4, 5]))
            >>> print(x.searchsorted(3))
            2
        """
        if side not in ('left', 'right'):
            raise ValueError(f"For 'Tensor.searchsorted', the argument 'side' should be one of in "
                             f"['left', 'right'], but got {side}.")
        a = self.astype(mstype.float32)
        if not isinstance(v, Tensor):
            v = tensor_operator_registry.get('make_tensor')(v)
        shape = v.shape
        if sorter is not None:
            if not isinstance(sorter, (int, float, bool, list, tuple, Tensor)):
                raise TypeError("For Tensor.searchsorted, the type of the argument 'sorter' must be one of 'int', "
                                "'float', 'bool', 'list', 'tuple', 'Tensor', but got {}.".format(type(sorter)))
            if not isinstance(sorter, Tensor):
                sorter = tensor_operator_registry.get('make_tensor')(sorter)
            if sorter.ndim != 1 or sorter.size != a.size:
                raise ValueError('sorter must be 1-D array with the same size as the Tensor')
            sorter = sorter.reshape(sorter.shape + (1,))
            a = tensor_operator_registry.get('gather_nd')(a, sorter)
        less_op = tensor_operator_registry.get('__le__') if side == 'left' else tensor_operator_registry.get('__lt__')
        i = tensor_operator_registry.get('fill')(mstype.int32, shape, 0)
        j = tensor_operator_registry.get('fill')(mstype.int32, shape, a.size)

        sort_range = tuple(range(validator.get_log2_size(tensor_operator_registry.get('shape_mul')(a.shape) + 1)))
        for _ in sort_range:
            mid = (i - -j) // 2
            mask = less_op(v, tensor_operator_registry.get('gather_nd')(a, mid.reshape(mid.shape + (1,))))
            i = tensor_operator_registry.get('select')(mask, i, mid)
            j = tensor_operator_registry.get('select')(mask, mid, j)
        return j

    def gather_nd(self, indices):
        r"""
        Gathers slices from a input tensor by indices.
        Using given indices to gather slices from a input tensor with a specified shape.
        input tensor's shape is :math:`(N,*)` where :math:`*` means any number of additional dimensions. For convenience
        define it as `input_x`, the variable `input_x` refers to input tensor.
        `indices` is an K-dimensional integer tensor. Suppose that it is a (K-1)-dimensional tensor and each element
        of it defines a slice of input tensor:

        .. math::
            output[(i_0, ..., i_{K-2})] = input\_x[indices[(i_0, ..., i_{K-2})]]

        The last dimension of `indices` can not more than the rank of input tensor:
        :math:`indices.shape[-1] <= input\_x.rank`.

        Args:
            indices (Tensor): The index tensor that gets the collected elements, with int32 or int64 data type.

        Returns:
            Tensor, has the same type as input tensor and the shape is
            :math:`indices\_shape[:-1] + input\_x\_shape[indices\_shape[-1]:]`.

        Raises:
            ValueError: If length of shape of input tensor is less than the last dimension of `indices`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> input_x = Tensor(np.array([[-0.1, 0.3, 3.6], [0.4, 0.5, -3.2]]), mindspore.float32)
            >>> indices = Tensor(np.array([[0, 0], [1, 1]]), mindspore.int32)
            >>> output = input_x.gather_nd(indices)
            >>> print(output)
            [-0.1  0.5]
        """
        self._init_check()
        validator.check_value_type('indices', indices, (Tensor_,), 'Tensor.gather_nd')
        return tensor_operator_registry.get('gather_nd')(self, indices)

    def gather(self, input_indices, axis):
        r"""
        Returns the slice of the input tensor corresponding to the elements of `input_indices` on the specified `axis`.
        The shape of input tensor is :math:`(x_1, x_2, ..., x_R)`. For convenience, define it as `input_params`,
        the variable `input_params` refers to input tensor.

        The following figure shows the calculation process of Gather commonly:

        .. image:: Gather.png

        where params represents the input `input_params`, and indices represents the index to be sliced `input_indices`.

        .. note::
            1.The value of `input_indices` must be in the range of `[0, input_param.shape[axis])`, the result
                is undefined out of range.

            2.The data type of `input_params` cannot be
                `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ on Ascend
                platform currently.

        Args:
            input_indices (Tensor): Index tensor to be sliced, the shape of tensor is :math:`(y_1, y_2, ..., y_S)`.
                Specifies the indices of elements of the original Tensor. The data type can be int32 or int64.
            axis (int): Specifies the dimension index to gather indices.

        Returns:
            Tensor, the shape of tensor is
            :math:`input\_params.shape[:axis] + input\_indices.shape + input\_params.shape[axis + 1:]`.

        Raises:
            TypeError: If `axis` is not an int.
            TypeError: If `input_indices` is not a tensor of type int.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> # case1: input_indices is a Tensor with shape (5, ).
            >>> input_params = Tensor(np.array([1, 2, 3, 4, 5, 6, 7]), mindspore.float32)
            >>> input_indices = Tensor(np.array([0, 2, 4, 2, 6]), mindspore.int32)
            >>> axis = 0
            >>> output = input_params.gather(input_indices, axis)
            >>> print(output)
            [1. 3. 5. 3. 7.]
            >>> # case2: input_indices is a Tensor with shape (2, 2). When the input_params has one dimension,
            >>> # the output shape is equal to the input_indices shape.
            >>> input_indices = Tensor(np.array([[0, 2], [2, 6]]), mindspore.int32)
            >>> axis = 0
            >>> output = input_params.gather(input_indices, axis)
            >>> print(output)
            [[ 1. 3.]
             [ 3. 7.]]
            >>> # case3: input_indices is a Tensor with shape (2, ) and
            >>> # input_params is a Tensor with shape (3, 4) and axis is 0.
            >>> input_params = Tensor(np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]), mindspore.float32)
            >>> input_indices = Tensor(np.array([0, 2]), mindspore.int32)
            >>> axis = 0
            >>> output = input_params.gather(input_indices, axis)
            >>> print(output)
            [[1.  2.  3.  4.]
             [9. 10. 11. 12.]]
            >>> # case4: input_indices is a Tensor with shape (2, ) and
            >>> # input_params is a Tensor with shape (3, 4) and axis is 1.
            >>> input_params = Tensor(np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]), mindspore.float32)
            >>> input_indices = Tensor(np.array([0, 2]), mindspore.int32)
            >>> axis = 1
            >>> output = input_params.gather(input_indices, axis)
            >>> print(output)
            [[1.  3.]
             [5.  7.]
             [9. 11.]]
        """
        self._init_check()
        validator.check_is_int(axis, 'axis')
        return tensor_operator_registry.get('gather')(self, input_indices, axis)

    def var(self, axis=None, ddof=0, keepdims=False):
        """
        Compute the variance along the specified axis.

        The variance is the average of the squared deviations from the mean, i.e.,
        :math:`var = mean(abs(x - x.mean())**2)`.

        Return the variance, which is computed for the flattened array by default,
        otherwise over the specified axis.

        Note:
            Numpy arguments `dtype`, `out` and `where` are not supported.

        Args:
            axis (Union[None, int, tuple(int)]): Axis or axes along which the variance is computed.
                The default is to compute the variance of the flattened array. Default: `None`.
            ddof (int): Means Delta Degrees of Freedom. Default: 0.
                The divisor used in calculations is :math:`N - ddof`, where :math:`N` represents the number of elements.
            keepdims (bool): Default: `False`.

        Returns:
            Variance tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.mean`: Reduce a dimension of a tensor by averaging all elements in the dimension.

            :func:`mindspore.Tensor.std`: Compute the standard deviation along the specified axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([1., 2., 3., 4.], np.float32))
            >>> output = input_x.var()
            >>> print(output)
            1.25
        """
        if 0 in self.shape:
            return Tensor(float('nan'), self.dtype)
        if not isinstance(ddof, int):
            raise TypeError("For 'Tensor.var', the type of the argument 'ddof' must be int, but got "
                            "{}.".format(type(ddof)))
        if not isinstance(keepdims, bool):
            raise TypeError("For 'Tensor.var', the type of the argument 'keepdims' must be bool, but "
                            "got {}.".format(type(keepdims)))

        if axis is None:
            axis = ()
        else:
            axis = validator.check_and_canonicalize_axes(axis, self.ndim)
        x_mean = tensor_operator_registry.get('mean')(True)(self, axis)
        x_sub = tensor_operator_registry.get('__sub__')(self, x_mean)
        x_pow = tensor_operator_registry.get('__pow__')(x_sub, 2)
        x_sum = tensor_operator_registry.get('sum')(bool(keepdims))(x_pow, axis)
        nums = 1
        if axis == ():
            nums = self.size
        else:
            for ax in axis:
                nums *= self.shape[ax]
        return tensor_operator_registry.get('__truediv__')(x_sum, nums - ddof)

    def std(self, axis=None, ddof=0, keepdims=False):
        """
        Compute the standard deviation along the specified axis.

        The standard deviation is the square root of the average of the squared deviations
        from the mean, i.e., :math:`std = sqrt(mean(abs(x - x.mean())**2))`.

        Return the standard deviation, which is computed for the flattened array by default,
        otherwise over the specified axis.

        Note:
            Numpy arguments `dtype`, `out` and `where` are not supported.

        Args:
            axis (Union[None, int, tuple(int)]): Axis or axes along which the standard
                deviation is computed. Default: `None`.

                If `None`, compute the standard deviation of the flattened array.
            ddof (int): Means Delta Degrees of Freedom. The divisor used in calculations is :math:`N - ddof`,
                where :math:`N` represents the number of elements. Default: 0.
            keepdims: Default: `False`.

        Returns:
            Standard deviation tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.mean`: Reduce a dimension of a tensor by averaging all elements in the dimension.

            :func:`mindspore.Tensor.var`: Compute the variance along the specified axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([1, 2, 3, 4], dtype=np.float32))
            >>> output = input_x.std()
            >>> print(output)
            1.118034
        """
        x_var = self.var(axis, ddof, keepdims)
        return tensor_operator_registry.get('__pow__')(x_var, 0.5)

    def sum(self, axis=None, dtype=None, keepdims=False, initial=None):
        """
        Return sum of tensor elements over a given axis.

        Note:
            Numpy arguments `out`, `where`, `casting`, `order`, `subok`, `signature`, and
            `extobj` are not supported.

        Args:
            axis (Union[None, int, tuple(int)]): Axis or axes along which a sum is performed. Default: None.
                If None, sum all the elements of the input tensor.
                If the axis is negative, it counts from the last to the first axis.
                If the axis is a tuple of ints, a sum is performed on all the axes specified in the tuple
                instead of a single axis or all the axes as before.
            dtype (:class:`mindspore.dtype`, optional): defaults to None. Overrides the dtype of the
                output Tensor.
            keepdims (bool): If this is set to True, the axes which are reduced are left in the result as
                dimensions with size one. With this option, the result will broadcast correctly against the input array.
                If the default value is passed, then keepdims will not be passed through to the sum method of
                sub-classes of ndarray, however any non-default value will be. If the sub-class method does not
                implement keepdims any exceptions will be raised. Default: `False`.
            initial (scalar): Starting value for the sum. Default: `None`.

        Returns:
            Tensor. A tensor with the same shape as input, with the specified axis removed.
            If the input tensor is a 0-d array, or if the axis is None, a scalar is returned.

        Raises:
            TypeError: If input is not array_like, or `axis` is not int or tuple of ints,
                or `keepdims` is not integer, or `initial` is not scalar.
            ValueError: If any axis is out of range or duplicate axes exist.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.cumsum`: Return the cumulative sum of the elements along a given axis.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([-1, 0, 1]).astype(np.float32))
            >>> print(input_x.sum())
            0.0
            >>> input_x = Tensor(np.arange(10).reshape(2, 5).astype(np.float32))
            >>> print(input_x.sum(axis=1))
            [10. 35.]
        """
        input_x = self.astype(mstype.int32) if self.dtype == mstype.bool_ else self
        dtype = input_x.dtype if dtype is None else dtype
        if not isinstance(keepdims, int):
            raise TypeError("For 'Tensor.sum', the type of the argument 'keepdims' must be int, but "
                            "got {}.".format(type(keepdims)))
        if initial is not None and not isinstance(initial, (int, float, bool)):
            raise TypeError("For 'Tensor.sum', when the argument 'initial' is not None, it must be int, "
                            "float or bool, but got {}.".format(type(initial)))
        if axis is None:
            axis = ()
        else:
            axis = validator.check_and_canonicalize_axes(axis, self.ndim)

        if not validator.check_type_support(input_x.dtype, 'GPU', (mstype.float64, mstype.float32, mstype.float16)):
            input_x = input_x.astype(mstype.float32)
        if 0 in self.shape:
            input_x = tensor_operator_registry.get('make_tensor')([0], self.dtype)
        res = tensor_operator_registry.get('sum')(bool(keepdims))(input_x, axis)
        if initial is not None:
            res += initial
        return res.astype(dtype)

    def repeat(self, repeats, axis=None):
        """
        Repeat elements of a tensor.

        Args:
            repeats (Union[int, tuple, list]): The number of repetitions for each element.
                `repeats` is broadcasted to fit the shape of the given axis.
            axis (int, optional): The axis along which to repeat values. By default,
                use the flattened input tensor, and return a flat output tensor. Default: None.

        Returns:
            Tensor, has the same shape as input tensor except along the given axis.

        Raises:
            ValueError: If the axis is out of range.
            TypeError: If arguments have types not specified above.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        See also:
            :func:`mindspore.Tensor.reshape`: Give a new shape to a tensor without changing its data.

            :func:`mindspore.Tensor.resize`: Changes shape and size of tensor in-place.

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array(3))
            >>> print(x.repeat(4))
            [3 3 3 3]
            >>> x = Tensor(np.array([[1, 2],[3, 4]]))
            >>> print(x.repeat(2))
            [1 1 2 2 3 3 4 4]
            >>> print(x.repeat(3, axis=1))
            [[1 1 1 2 2 2]
            [3 3 3 4 4 4]]
            >>> print(x.repeat([1,2], axis=0))
            [[1 2]
            [3 4]
            [3 4]]
        """
        if not isinstance(repeats, (tuple, list)):
            repeats = (repeats,)
        for index, element in enumerate(repeats):
            if not isinstance(element, int):
                raise TypeError(f"For 'Tensor.repeat', each element in {repeats} should be int, but got "
                                f"{type(element)} at index {index}.")
        input_x = self
        if axis is None:
            input_x = self.ravel()
            axis = 0
        if axis is not None and not isinstance(axis, int):
            raise TypeError(f"For 'Tensor.repeat', the argument 'axis' should be int, but got {type(axis)}.")
        validator.check_axis_in_range(axis, input_x.ndim)
        axis = axis + input_x.ndim if axis < 0 else axis

        if len(repeats) == 1:
            repeats = repeats[0]
            if repeats == 0:
                return Tensor_(input_x.dtype, (0,))
            return tensor_operator_registry.get('repeat_elements')(input_x, repeats, axis)
        size = input_x.shape[axis]
        if len(repeats) != size:
            raise ValueError(f"For 'Tensor.repeat', the length of 'repeats' must be the same as the shape of the "
                             f"original tensor in the 'axis' dimension, but got the length of 'repeats' "
                             f"{len(repeats)}, the shape of the original tensor in the 'axis' dimension {size}.")
        subs = tensor_operator_registry.get('split')(axis, size)(input_x)
        repeated_subs = []
        for sub, rep in zip(subs, repeats):
            if rep != 0:
                repeated_subs.append(tensor_operator_registry.get('repeat_elements')(sub, rep, axis))
        return tensor_operator_registry.get('concatenate')(axis)(repeated_subs)

    def bernoulli(self, p=0.5, seed=-1):
        """
        Randomly set the elements of output to 0 or 1 with the probability of P which follows the Bernoulli
        distribution.

        .. math::

            out_{i} ~ Bernoulli(p_{i})

        Args:
            p (Union[Tensor, float], optional): The shape of p need to be broadcast. The elements of p represent the
                                                probability of setting 1 for the corresponding broadcast position of
                                                the current Tensor. Default: 0.5.
            seed (int, optional): The seed value for random generating. Default: -1.

        Returns:
            Tensor, with the same shape and type as x.

        Raises:
            TypeError: If dtype of Tensor is not one of: int8, uint8, int16, int32，int64，bool, float32, float64.
            TypeError: If dtype of `p` is not one of: float32, float64.
            TypeError: If dtype of `seed` is not an int.
            ValueError: If `p` is not in range [0, 1].
            ValueError: If `seed` is less than 0.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> import mindspore
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> input_x = Tensor(np.array([1, 2, 3]), mindspore.int8)
            >>> output = input_x.bernoulli(p=1.0)
            >>> print(output)
            [1 1 1]
            >>> input_p = Tensor(np.array([0.0, 1.0, 1.0]), mindspore.float32)
            >>> output = input_x.bernoulli(input_p)
            >>> print(output)
            [0 1 1]
        """
        self._init_check()
        validator.check_is_int(seed, 'seed')
        return tensor_operator_registry.get('bernoulli')(self, p, seed)

    def random_categorical(self, num_sample=None, seed=0, dtype=mstype.int64):
        r"""
        Generates random samples from a given categorical distribution tensor.

        Args:
            dtype (mindspore.dtype): The type of output. Its value must be one of mindspore.int16,
                mindspore.int32 and mindspore.int64. Default: mindspore.int64.

        Inputs:
            - **logits** (Tensor) - The input tensor. 2-D Tensor with shape [batch_size, num_classes].
            - **num_sample** (int) - Number of sample to be drawn. Only constant values is allowed.
            - **seed** (int) - Random seed. Default: 0. Only constant values is allowed.

        Outputs:
            - **output** (Tensor) - The output Tensor with shape [batch_size, num_samples].

        Raises:
            TypeError: If `dtype` is not one of the following: mindspore.int16, mindspore.int32, mindspore.int64.
            TypeError: If `logits` is not a Tensor.
            TypeError: If neither `num_sample` nor `seed` is an int.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import mindspore
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.random.random((10, 5)).astype(np.float32))
            >>> output = x.random_categorical(x, 8)
            >>> result = output.shape
            >>> print(result)
            (10, 8)
        """
        self._init_check()
        validator.check_is_int(num_sample, 'num_sample')
        validator.check_is_int(seed, 'seed')
        return tensor_operator_registry.get('random_categorical')(self, num_sample, seed, dtype)

    def masked_select(self, mask):
        """
        Returns a new 1-D Tensor which indexes the self tensor according to the boolean `mask`.
        The shapes of the `mask` tensor and the self tensor don't need to match, but they must be broadcastable.

        Args:
            mask (Tensor[bool]): The boolean Tensor.

        Returns:
            A 1-D Tensor, with the same type as self.

        Raises:
            TypeError: If `mask` is not a bool Tensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([1, 2, 3, 4]), mindspore.int64)
            >>> mask = Tensor(np.array([1, 0, 1, 0]), mindspore.bool_)
            >>> output = x.masked_select(mask)
            >>> print(output)
            [1 3]
        """
        self._init_check()
        return tensor_operator_registry.get('masked_select')(self, mask)

    def gather_elements(self, dim, index):
        """
        Gathers elements along an axis specified by dim.
        Refer to :func:`mindspore.ops.gather_elements` for more detail.

        Args:
            dim (int): The axis along which to index. It must be int32 or int64. The value range is [-x_rank, x_rank).
            index (Tensor): The indices of elements to gather. It can be one of the following data types:
                int32, int64. The value range of each index element is [-x_rank[dim], x_rank[dim]).

        Returns:
            Tensor, has the same shape as index tensor and same data type as input tensor.

        Raises:
            TypeError: If dtype of `dim` or `index` is neither int32 nor int64.
            ValueError: If length of shape of current tensor is not equal to length of shape of `index`.
            ValueError: If the size of the dimension except `dim` is not equal between current tensor and `index`.
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
            >>> output = x.gather_elements(dim, index)
            >>> print(output)
            [[1 1]
             [4 3]]
        """
        self._init_check()
        validator.check_value_type('index', index, (Tensor_,), 'Tensor.gather_elements')
        return tensor_operator_registry.get('gather_elements')(self, dim, index)

    def nonzero(self):
        """
        Return a tensor of the positions of all non-zero values.

        Returns:
            Tensor, a 2-D tensor, containing the positions of all non-zero values of the input.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[[1,  0], [-5, 0]]]), mindspore.int32)
            >>> output = x.nonzero()
            >>> print(output)
            [[0 0 0]
             [0 1 0]]
        """
        self._init_check()
        return tensor_operator_registry.get('nonzero')(self)

    def svd(self, full_matrices=False, compute_uv=True):
        """
        Refer to :func:`mindspore.ops.svd` for more detail.

        Args:
            full_matrices (bool, optional): If true, compute full-sized :math:`U` and :math:`V`. If false, compute
                                            only the leading P singular vectors. P is the minimum of M and N.
                                            M, N is the row, col of the input matrix. Default: False.
            compute_uv (bool, optional): If true, compute the left and right singular vectors.
                                         If false, compute only the singular values. Default: True.

        Returns:
            - **s**  (Tensor) - Singular values. The shape is :math:`(*, P)`.
            - **u**  (Tensor) - Left singular vectors. If compute_uv is False, u will not be returned.
              The shape is :math:`(*, M, P)`. If full_matrices is True, the shape will be :math:`(*, M, M)`.
            - **v**  (Tensor) - Right singular vectors. If compute_uv is False, v will not be returned.
              The shape is :math:`(*, P, N)`. If full_matrices is True, the shape will be :math:`(*, N, N)`.

        Raises:
            TypeError: If full_matrices or compute_uv is not the type of bool.
            TypeError: If the rank of input less than 2.
            TypeError: If the type of input is not one of the following dtype: mstype.float32, mstype.float64.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> a = Tensor(np.array([[1, 2], [-4, -5], [2, 1]]).astype(np.float32))
            >>> s, u, v = a.svd(full_matrices=True, compute_uv=True)
            >>> print(s)
            [7.0652833 1.0400811]
            >>> print(u)
            [[-0.30821884 -0.48819494 0.8164968 ]
            [ 0.9061333 0.1107057 0.40824825]
            [-0.28969547 0.86568475 0.408248 ]]
            >>> print(v)
            [[-0.6386359 0.7695091]
            [-0.7695091 -0.6386359]]
        """
        svd_op = tensor_operator_registry.get("svd")
        if compute_uv:
            return svd_op(full_matrices, compute_uv)(self)

        s, _, _ = svd_op(full_matrices, compute_uv)(self)
        return s

    def hardshrink(self, lambd=0.5):
        r"""
        Apply the Hard Shrink function for tensor. Calculates the output according to the input elements.

        The formula is defined as follows:

        .. math::
            \text{HardShrink}(x) =
            \begin{cases}
            x, & \text{ if } x > \lambda \\
            x, & \text{ if } x < -\lambda \\
            0, & \text{ otherwise }
            \end{cases}

        Args:
            lambd (float): The threshold :math:`\lambda` defined by the Hard Shrink formula. Default: 0.5.

        Returns:
            Tensor, has the same shape and data type as self.

        Raises:
            TypeError: If `lambd` is not a float.
            TypeError: If dtype of the input tensor is neither float16 nor float32.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> import mindspore as ms
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[0.5,  1,  2.0], [0.0533, 0.0776, -2.1233]]), ms.float32)
            >>> print(x.hardshrink())
            [[ 0.      1.      2.    ]
            [ 0.      0.     -2.1233]]
        """
        self._init_check()
        return tensor_operator_registry.get('hardshrink')(lambd)(self)

    def soft_shrink(self, lambd=0.5):
        r"""
        Apply the soft shrink function for a tensor. Calculates the output according to the input elements.

        The formula is defined as follows:

        .. math::
            \text{SoftShrink}(x) =
            \begin{cases}
            x - \lambda, & \text{ if } x > \lambda \\
            x + \lambda, & \text{ if } x < -\lambda \\
            0, & \text{ otherwise }
            \end{cases}

        Args:
            lambd(float): the :math:`\lambda` must be no less than zero. Default: 0.5.

        Returns:
            Tensor, has the same shape and data type as self.

        Raises:
            TypeError: If lambd is not a float.
            TypeError: If input_x is not a Tensor.
            TypeError: If dtype of input_x is neither float16 nor float32.
            ValueError: If lambd is less than 0.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> a = Tensor([[ 0.5297,  0.7871,  1.1754], [ 0.7836,  0.6218, -1.1542]]).astype("float32")
            >>> output = a.soft_shrink()
            >>> print(output)
            [[ 0.02979  0.287    0.676  ]
             [ 0.2837   0.1216  -0.6543 ]]
        """
        self._init_check()
        return tensor_operator_registry.get('soft_shrink')(lambd)(self)

    def to_coo(self):
        """
        Convert a Tensor to COOTensor.

        Note:
            Only 2-D tensor is supported for now.

        Returns:
            COOTensor, a 2-D coo_tensor, containing:
            indices: the positions of all non-zero values of the input.
            values: the non-zero values of the dense tensor.
            shape: the shape of the coo_tensor.

        Raises:
            ValueError: If input tensor is not 2-D.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> import numpy as np
            >>> import mindspore
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[1,  0], [-5, 0]]), mindspore.float32)
            >>> output = x.to_coo()
            >>> print(output.indices, output.values, output.shape)
            [[0 0]
             [1 0]] [ 1. -5.] (2, 2)

        """
        self._init_check()
        return tensor_operator_registry.get('dense_to_sparse_coo')(self)

    def to_csr(self):
        """
        Convert a Tensor to CSRTensor.

        Note:
            Only 2-D tensor is supported for now.

        Returns:
            CSRTensor, a 2-D csr_tensor, containing:
            indptr: indicates the start and end point for `values` in each row.
            indices: the column positions of all non-zero values of the input.
            values: the non-zero values of the dense tensor.
            shape: the shape of the csr_tensor.

        Raises:
            ValueError: If input tensor is not 2-D.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> import numpy as np
            >>> import mindspore
            >>> from mindspore import Tensor
            >>> x = Tensor(np.array([[1,  0], [-5, 0]]), mindspore.float32)
            >>> output = x.to_csr()
            >>> print(output.indptr, output.indices, output.values, output.shape)
            [0 1 2] [0 0] [ 1. -5.] (2, 2)
        """
        self._init_check()
        return tensor_operator_registry.get('dense_to_sparse_csr')(self)

    def unsorted_segment_min(self, segment_ids, num_segments):
        r"""
        Computes the minimum of a tensor along segments.

        Note:
            - If the segment_id i is absent in the segment_ids, then output[i] will be filled with
              the maximum value of the type of self.
            - The `segment_ids` must be non-negative tensor.

        Args:
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
            >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6], [4, 2, 1]]).astype(np.float32))
            >>> segment_ids = Tensor(np.array([0, 1, 1]).astype(np.int32))
            >>> num_segments = 2
            >>> output = x.unsorted_segment_min(segment_ids, num_segments)
            >>> print(output)
            [[1. 2. 3.]
             [4. 2. 1.]]
        """
        self._init_check()
        return tensor_operator_registry.get('unsorted_segment_min')(self, segment_ids, num_segments)

    def unsorted_segment_max(self, segment_ids, num_segments):
        r"""
        Computes the maximum along segments of a tensor.

        Note:
            - If the segment_id i is absent in the segment_ids, then output[i] will be filled with
              the minimum value of the type of self.
            - The `segment_ids` must be non-negative tensor.

        Args:
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
            >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6], [4, 2, 1]]).astype(np.float32))
            >>> segment_ids = Tensor(np.array([0, 1, 1]).astype(np.int32))
            >>> num_segments = 2
            >>> output = x.unsorted_segment_max(segment_ids, num_segments)
            >>> print(output)
            [[1. 2. 3.]
             [4. 5. 6.]]
        """
        self._init_check()
        return tensor_operator_registry.get('unsorted_segment_max')(self, segment_ids, num_segments)

    def unsorted_segment_prod(self, segment_ids, num_segments):
        r"""
        Computes the product of a tensor along segments.

        Note:
            - If the segment_id i is absent in the segment_ids, then output[i] will be filled with 1.
            - The `segment_ids` must be non-negative tensor.

        Args:
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
            >>> x = Tensor(np.array([[1, 2, 3], [4, 5, 6], [4, 2, 1]]).astype(np.float32))
            >>> segment_ids = Tensor(np.array([0, 1, 0]).astype(np.int32))
            >>> num_segments = 2
            >>> output = x.unsorted_segment_prod(segment_ids, num_segments)
            >>> print(output)
            [[4. 4. 3.]
             [4. 5. 6.]]
        """
        self._init_check()
        return tensor_operator_registry.get('unsorted_segment_prod')(self, segment_ids, num_segments)

    def unique_consecutive(self, return_idx=False, return_counts=False, axis=None):
        """
        Returns the elements that are unique in each consecutive group of equivalent elements in the input tensor.

        Args:
            return_idx (bool, optional): Whether to return the indices of the end position of each element in the
                original input list in the returned unique list. Default: False.
            return_counts (bool, optional): Whether to return the counts of each unique element. Default: False.
            axis (int, optional): The dimension to apply unique. If None, the unique of the flattened input is
                returned. If specified, it must be int32 or int64. Default: None.

        Returns:
            A tensor or a tuple of tensors containing tensor objects (`output`, `idx`, `counts`). `output` has the
            same type as the input tensor and is used to represent the output list of unique scalar elements. If
            `return_idx` is True, there will be an additional returned tensor, `idx`, which has the same shape as
            the inupt tensor and represents the index of where the element in the original input maps to the position
            in the output. If `return_counts` is True, there will be an additional returned tensor, `counts`, which
            represents the number of occurrences for each unique value or tensor.

        Raises:
            RuntimeError: If `axis` is not in the range of :math:`[-ndim, ndim-1]`.

        Supported Platforms:
            ``GPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> from mindspore import dtype as mstype
            >>> x = Tensor(np.array([1, 1, 2, 2, 3, 1, 1, 2]), mstype.int32)
            >>> output, idx, counts = x.unique_consecutive(return_idx=True, return_counts=True, axis=None)
            >>> print(output)
            [1 2 3 1 2]
            >>> print(idx)
            [0 0 1 1 2 3 3 4]
            >>> print(counts)
            [2 2 1 2 1]
        """
        self._init_check()
        output, idx, counts = tensor_operator_registry.get("unique_consecutive")(return_idx, return_counts, axis)(self)
        if return_idx and return_counts:
            return output, idx, counts
        if return_idx:
            return output, idx
        if return_counts:
            return output, counts
        return output

    def unique_with_pad(self, pad_num):
        """
        Returns unique elements and relative indexes in 1-D tensor, filled with padding num.

        The basic function is the same as the Unique operator, but the UniqueWithPad operator adds a Pad function.
        The returned tuple(`y`, `idx`) after the self tensor is processed by the unique operator,
        in which the shapes of `y` and `idx` are mostly not equal. Therefore, in order to solve the above situation,
        the UniqueWithPad operator will fill the `y` Tensor with the `pad_num` specified by the user
        to make it have the same shape as the Tensor `idx`.

        Args:
            pad_num (int): Pad num. The data type is an int.

        Returns:
            tuple(Tensor), tuple of 2 tensors, `y` and `idx`.

            - y (Tensor) - The unique elements filled with pad_num, the shape and data type same as self tensor.
            - idx (Tensor) - The index of each value of self tensor in the unique output `y`,
                            the shape and data type same as self tensor.

        Raises:
            TypeError: If dtype of self tensor is neither int32 nor int64.
            ValueError: If length of shape of self tensor is not equal to 1.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import numpy as np
            >>> from mindspore import Tensor
            >>> from mindspore import dtype as mstype
            >>> x = Tensor(np.array([1, 1, 2, 2, 3, 1]), mstype.int32)
            >>> output, idx = x.unique_with_pad(pad_num=0)
            >>> print(output)
            [1 2 3 0 0 0]
            >>> print(idx)
            [0 0 1 1 2 0]
        """
        self._init_check()
        return tensor_operator_registry.get("unique_with_pad")()(self, pad_num)

    def diag(self):
        r"""
        Constructs a diagonal tensor with a given diagonal values.

        Assume self tensor has dimensions :math:`[D_1,... D_k]`, the output is a tensor of
        rank 2k with dimensions :math:`[D_1,..., D_k, D_1,..., D_k]` where:
        :math:`output[i_1,..., i_k, i_1,..., i_k] = self[i_1,..., i_k]` and 0 everywhere else.

        Returns:
            Tensor, has the same dtype as self tensor.

        Raises:
            ValueError: If rank of self tensor is less than 1.

        Supported Platforms:
            ``Ascend`` ``GPU``

        Examples:
            >>> from mindspore import Tensor
            >>> x = Tensor([1, 2, 3, 4])
            >>> output = x.diag()
            >>> print(output)
            [[1, 0, 0, 0],
             [0, 2, 0, 0],
             [0, 0, 3, 0],
             [0, 0, 0, 4]]
        """
        self._init_check()
        return tensor_operator_registry.get('diag')()(self)

    def xdivy(self, y):
        """
        Divides self tensor by the input tensor element-wise. Returns zero when self is zero.

        self and `y` comply with the implicit type conversion rules to make the data types consistent.
        'y' must be tensor or scalar, When y is tensor, dtypes of self and y cannot be bool at the same time,
        and the shapes of them could be broadcast. When y is scalar, the scalar could only be a constant.

        Args:
            - **y** (Union[Tensor, Number, bool]) - The second input is a number,
              or a bool when the first input is a tensor, or a tensor whose data type is float16,
              float32, float64, complex64, complex128 or bool.

        Returns:
            Tensor, the shape is the same as the one after broadcasting,
            and the data type is the one with higher precision or higher digits among the two inputs.

        Raises:
            TypeError: If `y` is not one of the following: Tensor, Number, bool.
            TypeError: If dtype of self and 'y' is not in [float16, float32, float64, complex64, complex128, bool].
            ValueError: If self could not be broadcast to a tensor with shape of `y`.
            RuntimeError: If the data type of `y` conversion of Parameter is given
                          but data type conversion of Parameter is not supported.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([2, 4, -1]), mindspore.float32)
            >>> y = Tensor(np.array([2, 2, 2]), mindspore.float32)
            >>> output = x.xdivy(y)
            >>> print(output)
            [ 1.   2.  -0.5]
        """
        self._init_check()
        return tensor_operator_registry.get("xdivy")()(self, y)

    def split(self, axis=0, output_num=1):
        """
        Splits a tensor into output_num of tensors along the given axis and output numbers.

        The tensor will be split into equally sized sub-tensors.
        This requires that `self.shape(axis)` is divisible by `output_num`.

        Args:
            axis (int): Index of the split position. Default: 0.
            output_num (int): The number of output tensors. Must be positive int. Default: 1.

        Returns:
            tuple[Tensor], the shape of each output tensor is the same, which is
            :math:`(y_1, y_2, ..., y_S)`. And the data type is the same with the tensor.

        Raises:
            TypeError: If `axis` or `output_num` is not an int.
            ValueError: If `axis` is out of the range [-len(`self.shape`), len(`self.shape`)),
                or if the `output_num` is less than or equal to 0.
            ValueError: If `self.shape(axis)` is not divisible by `output_num`.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([[1, 1, 1, 1], [2, 2, 2, 2]]), mindspore.int32)
            >>> print(x)
            [[1 1 1 1]
             [2 2 2 2]]
            >>> output = x.split(1, 2)
            >>> print(output)
            (Tensor(shape=[2, 2], dtype=Int32, value=
            [[1, 1],
             [2, 2]]), Tensor(shape=[2, 2], dtype=Int32, value=
            [[1, 1],
             [2, 2]]))
        """
        return tensor_operator_registry.get('split')(axis, output_num)(self)

    def standard_laplace(self, seed=0, seed2=0):
        r"""
        Construct a tensor with random numbers according to the Laplace random number distribution (mean=0, lambda=1).
        It is defined as:

        .. math::
            \text{f}(x) = \frac{1}{2}\exp(-|x|),

        Args:
            seed (int): Random seed. Default: 0.
            seed2 (int): Random seed2. Default: 0.

        Returns:
            Tensor, has the same dtype and shape as self tensor.

        Raises:
            TypeError: If neither seed nor seed2 is an int.
            TypeError: If shape is not a tuple.
            ValueError: If shape is not a constant value.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> from mindspore import Tensor
            >>> x = Tensor([1, 2, 3, 4])
            >>> output = x.standard_laplace()
            >>> print(output.shape)
            (1, 2, 3, 4)
        """
        self._init_check()
        validator.check_is_int(seed, 'seed')
        validator.check_is_int(seed2, 'seed2')
        return tensor_operator_registry.get('standard_laplace')(seed=seed, seed2=seed2)(self.shape)


    def xlogy(self, y):
        r"""
        Computes the first input tensor multiplied by the logarithm of second input tensor element-wise.
        Returns zero when self tensor is zero. The data type of the self tensor should be
        `number <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_ or
        `bool_ <https://www.mindspore.cn/docs/en/master/api_python/mindspore.html#mindspore.dtype>`_.
        To make it clear, the following content will use `x` to represent the self tensor.

        .. math::

            out_i = x_{i}\ln{y_{i}}

        Inputs of `x` and `y` comply with the implicit type conversion rules to make the data types consistent.
        The inputs must be two tensors or one tensor and one scalar.
        When the inputs are two tensors,
        dtypes of them cannot be bool at the same time, and the shapes of them could be broadcast.
        When the inputs are one tensor and one scalar,
        the scalar could only be a constant.

        Args:
            - **y** (Union[Tensor, number.Number, bool]) - The `y` input is a number.Number or
              a bool or a tensor whose data type is number or bool.

        Returns:
            Tensor, the shape is the same as the one after broadcasting,
            and the data type is the one with higher precision or higher digits among the two inputs.

        Raises:
            TypeError: If `y` is not a number.Number or a bool or a Tensor.
            TypeError: If dtype of `x` and 'y' is not in [float16, float32, float64] .
            ValueError: If `x` could not be broadcast to a tensor with shape of `y`.

        Supported Platforms:
            ``Ascend`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([-5, 0, 4]), mindspore.float32)
            >>> y = Tensor(np.array([2, 2, 2]), mindspore.float32)
            >>> print(x.xlogy(y))
            [-3.465736   0.        2.7725887]
        """
        return tensor_operator_registry.get("xlogy")()(self, y)


    def erf(self):
        r"""
        Computes the Gauss error function of self tensor element-wise.
        Refer to :func:`mindspore.ops.erf` for more details.

        Returns:
            Tensor, has the same shap dtype as the self Tensor.

        Raises:
            TypeError: If dtype of self tensor is not float16 or float32.

        Supported Platforms:
            ``Ascend`` ``GPU``  ``CPU``

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> x = Tensor(np.array([-1, 0, 1, 2, 3]), mindspore.float32)
            >>> output = x.erf()
            >>> print(output)
            [-0.8427168   0.          0.8427168   0.99530876  0.99997765]
        """
        return tensor_operator_registry.get("erf")()(self)


    def erfc(self):
        r"""
        Computes the complementary error function of self tensor element-wise.
        Refer to :func:`mindspore.ops.erfc` for more details.

        Returns:
            Tensor, has the same shap dtype as the self tensor.

        Raises:
            TypeError: If dtype of self tensor is not float16 or float32.

        Supported Platforms:
            ``Ascend`` ``GPU``  ``CPU``

        Examples:
            >>> x = Tensor(np.array([-1, 0, 1, 2, 3]), mindspore.float32)
            >>> output = x.erfc()
            >>> print(output)
            [1.8427168e+00 1.0000000e+00 1.5728319e-01 4.6912432e-03 2.2351742e-05]
        """
        return tensor_operator_registry.get("erfc")()(self)


class RowTensor(RowTensor_):
    """
    A sparse representation of a set of tensor slices at given indices.

    An RowTensor is typically used to represent a subset of a larger
    tensor dense of shape [L0, D1, .. , DN] where L0 >> D0.

    The values in indices are the indices in the first dimension of the slices
    that have been extracted from the larger tensor.

    The dense tensor dense represented by an RowTensor slices has
    `dense[slices.indices[i], :, :, :, ...] = slices.values[i, :, :, :, ...]`.

    For example, if indices is [0], values is [[1, 2]], dense_shape is
    (3, 2), then the dense representation of the row tensor will be:

    .. code-block::

        [[1, 2],
         [0, 0],
         [0, 0]]

    Note:
        This is an experimental feature and is subjected to change.

    Args:
        indices (Tensor): A 1-D integer Tensor of shape [D0]. Default: None.
        values (Tensor): A Tensor of any dtype of shape [D0, D1, ..., Dn]. Default: None.
        dense_shape (tuple(int)): An integer tuple which contains the shape
            of the corresponding dense tensor. Default: None.
        row_tensor (RowTensor): A RowTensor object. Default: None.

    Returns:
        RowTensor, composed of `indices`, `values`, and `dense_shape`.

    Examples:
        >>> import mindspore as ms
        >>> from mindspore import Tensor, RowTensor
        >>> indices = Tensor([0])
        >>> values = Tensor([[1, 2]], dtype=ms.float32)
        >>> shape = (3, 2)
        >>> x = RowTensor(indices, values, shape)
        >>> print(x.values)
        [[1. 2.]]
        >>> print(x.indices)
        [0]
        >>> print(x.dense_shape)
        (3, 2)
    """

    def __init__(self, indices=None, values=None, shape=None, row_tensor=None):
        """Init RowTensor"""
        self.init_finished = False
        # Directly init a RowTensor from another RowTensor
        if row_tensor is not None:
            if not isinstance(row_tensor, (RowTensor, RowTensor_)):
                raise TypeError(f"Expect input `row_tensor` to be a RowTensor, but got {type(row_tensor)}")
            if not (indices is None and values is None and shape is None):
                raise TypeError("If input `row_tensor` is provided, `indices`, `values`, `shapes` should all be `None`")
            RowTensor_.__init__(self, row_tensor)
        # Init a RowTensor from indices, values and shape
        else:
            RowTensor_.__init__(self, indices, values, shape)
        self.init_finished = True

    def __repr__(self):
        """Avoid PyTest Segfault when RowTensor is not initialized."""
        if self.init_finished:
            return RowTensor_.__repr__(self)
        return ''

    @property
    def indices(self):
        """Return RowTensor's indices."""
        return Tensor(self._indices)

    @property
    def values(self):
        """Return RowTensor's non-zero values."""
        return Tensor(self._values)

    @property
    def dense_shape(self):
        """Return RowTensor's shape."""
        return self._shape


class SparseTensor(COOTensor_):
    """
    A sparse representation of a set of nonzero elements from a tensor at given indices.

    SparseTensor can only be used in the `Cell`'s construct method.

    For a tensor dense, its SparseTensor(indices, values, dense_shape) has
    `dense[indices[i]] = values[i]`.

    For example, if indices is [[0, 1], [1, 2]], values is [1, 2], dense_shape is
    (3, 4), then the dense representation of the sparse tensor will be:

    .. code-block::

        [[0, 1, 0, 0],
         [0, 0, 2, 0],
         [0, 0, 0, 0]]

    Note:
        The interface is deprecated from version 1.7 and will be removed in a future version.
        Please use 'COOTensor' instead.

    Args:
        indices (Tensor): A 2-D integer Tensor of shape `[N, ndims]`,
            where N and ndims are the number of `values` and number of dimensions in
            the SparseTensor, respectively.
        values (Tensor): A 1-D tensor of any type and shape `[N]`, which
            supplies the values for each element in `indices`.
        shape (tuple(int)): A integer tuple of size `ndims`,
            which specifies the shape of the sparse tensor.

    Returns:
        SparseTensor, composed of `indices`, `values`, and `shape`.

    Examples:
        >>> import mindspore as ms
        >>> import mindspore.nn as nn
        >>> from mindspore import Tensor, SparseTensor
        >>> indices = Tensor([[0, 1], [1, 2]])
        >>> values = Tensor([1, 2], dtype=ms.float32)
        >>> shape = (3, 4)
        >>> x = SparseTensor(indices, values, shape)
        >>> print(x.values)
        [1. 2.]
        >>> print(x.indices)
        [[0 1]
         [1 2]]
        >>> print(x.shape)
        (3, 4)
    """

    def __init__(self, indices, values, shape):
        "Init COOTensor"
        print("WARNING: 'SparseTensor' is deprecated from version 1.7 and will be removed in a future version. " +
              "Please use 'COOTensor' instead.")
        if not (isinstance(indices, Tensor) and isinstance(values, Tensor) and isinstance(shape, tuple)):
            raise TypeError("Inputs must follow: COOTensor(indices, values, shape).")
        COOTensor_.__init__(self, indices, values, shape)

    @property
    def indices(self):
        return Tensor(self._indices)

    @property
    def values(self):
        return Tensor(self._values)

    @property
    def shape(self):
        return self._shape


class COOTensor(COOTensor_):
    """
    A sparse representation of a set of nonzero elements from a tensor at given indices.

    For a tensor dense, its COOTensor(indices, values, shape) has
    `dense[indices[i]] = values[i]`.

    For example, if indices is [[0, 1], [1, 2]], values is [1, 2], shape is
    (3, 4), then the dense representation of the sparse tensor will be:

    .. code-block::

        [[0, 1, 0, 0],
         [0, 0, 2, 0],
         [0, 0, 0, 0]]

    Note:
        This is an experimental feature and is subjected to change.
        Currently, duplicate coordinates in the indices will not be coalesced.

    Args:
        indices (Tensor): A 2-D integer Tensor of shape `[N, ndims]`,
            where N and ndims are the number of `values` and number of dimensions in
            the COOTensor, respectively. Currently, `ndims` must be 2.
            Please make sure that the indices are in range of the given shape.
        values (Tensor): A 1-D tensor of any type and shape `[N]`, which
            supplies the values for each element in `indices`.
        shape (tuple(int)): A integer tuple of size `ndims`,
            which specifies the dense_shape of the sparse tensor.
        coo_tensor (COOTensor): A COOTensor object.

    Returns:
        COOTensor, composed of `indices`, `values`, and `shape`.

    Examples:
        >>> import mindspore as ms
        >>> import mindspore.nn as nn
        >>> from mindspore import Tensor, COOTensor
        >>> indices = Tensor([[0, 1], [1, 2]], dtype=ms.int32)
        >>> values = Tensor([1, 2], dtype=ms.float32)
        >>> shape = (3, 4)
        >>> x = COOTensor(indices, values, shape)
        >>> print(x.values)
        [1. 2.]
        >>> print(x.indices)
        [[0 1]
         [1 2]]
        >>> print(x.shape)
        (3, 4)
    """

    def __init__(self, indices=None, values=None, shape=None, coo_tensor=None):
        "Init COOTensor"
        self.init_finished = False
        # Directly init a COOTensor from another COOTensor
        if coo_tensor is not None:
            if not isinstance(coo_tensor, (COOTensor, COOTensor_)):
                raise TypeError(f"Expect input `coo_tensor` to be a COOTensor, but got {type(coo_tensor)}")
            if not (indices is None and values is None and shape is None):
                raise TypeError("If input `coo_tensor` is provided, `indices`, `values`, `shapes` should all be `None`")
            COOTensor_.__init__(self, coo_tensor)
        # Init a COOTensor from indices, values and shape
        else:
            validator.check_coo_tensor_input(indices, values, shape)
            validator.check_coo_tensor_shape(indices.shape, values.shape, shape)
            validator.check_coo_tensor_dtype(indices.dtype)
            if not (indices < Tensor(shape, mstype.int32)).all() or (indices < Tensor(0, mstype.int32)).any():
                raise ValueError("All the indices should be non-negative integer and in range of the given shape!")
            COOTensor_.__init__(self, indices, values, shape)
        self.init_finished = True

    def __repr__(self):
        """Avoid PyTest Segfault when COOTensor is not initialized."""
        if self.init_finished:
            return COOTensor_.__repr__(self)
        return ''

    @property
    def indices(self):
        """Return COOTensor's indices."""
        return Tensor(self._indices)

    @property
    def values(self):
        """Return COOTensor's non-zero values."""
        return Tensor(self._values)

    @property
    def shape(self):
        """Return COOTensor's shape."""
        return self._shape

    def to_csr(self):
        """
        Converts COOTensor to CSRTensor.

        Returns:
            CSRTensor.

        Supported Platforms:
            ``GPU`` ``CPU``
        """
        row_indices = self.indices[:, 0]
        col_indices = self.indices[:, 1]
        idx_dtype = self.indices.dtype
        row_indices, sort_idx = tensor_operator_registry.get("sort")(
            row_indices.astype(mstype.float32))
        row_indices = row_indices.astype(idx_dtype)
        col_indices = col_indices[sort_idx]
        values = self.values[sort_idx]
        indptr = tensor_operator_registry.get("coo2csr")(row_indices, self.shape[0])
        return CSRTensor(indptr, col_indices, values, self.shape)

    def to_dense(self):
        """
        Converts COOTensor to Dense Tensor.

        Returns:
            Tensor.

        Supported Platforms:
            ``GPU``
        """
        zeros_tensor = tensor_operator_registry.get("zeros")(self.shape, self.values.dtype)
        return tensor_operator_registry.get("tensor_scatter_add")()(
            zeros_tensor, self.indices, self.values)

    @property
    def dtype(self):
        """Return the dtype of the values of COOTensor (:class:`mindspore.dtype`)."""
        return self._dtype

    @property
    def size(self):
        """Return the number of non-zero values."""
        return self.values.size

    @property
    def itemsize(self):
        """Return the length of one tensor element in bytes."""
        return self.values.itemsize

    @property
    def ndim(self):
        """Return the number of tensor dimensions."""
        return len(self.shape)

    def astype(self, dtype):
        """
        Return a copy of the COOTensor, cast its values to a specified type.

        Args:
            dtype (Union[:class:`mindspore.dtype`, numpy.dtype, str]): Designated tensor dtype.

        Returns:
            COOTensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import mindspore as ms
            >>> from mindspore import Tensor, COOTensor
            >>> indices = Tensor([[0, 1], [1, 2]], dtype=ms.int32)
            >>> values = Tensor([1, 2], dtype=ms.float32)
            >>> shape = (3, 4)
            >>> coo_tensor = COOTensor(indices, values, shape)
            >>> print(coo_tensor.astype(ms.float64).dtype)
            Float64
        """
        data = self.values.astype(dtype)
        return COOTensor(self.indices, data, self.shape)

    def to_tuple(self):
        """
        Return indices, values and shape as a tuple.

        Returns:
            Tuple.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``
        """
        return self.indices, self.values, self.shape

    def abs(self):
        """
        Return absolute value element-wisely.

        Returns:
            COOTensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``
        """
        data = self.values.abs()
        return COOTensor(self.indices, data, self.shape)


class CSRTensor(CSRTensor_):
    """
    Constructs a sparse tensor in CSR (Compressed Sparse Row) format, with specified
    values indicated by `values` and row and column positions indicated by `indptr`
    and `indices`.

    For example, if indptr is [0, 1, 2, 2], indices is [1, 2], values is [1., 2.], shape is
    (3, 4), then the dense representation of the sparse tensor will be:

    .. code-block::

        [[0., 1., 0., 0.],
         [0., 0., 2., 0.],
         [0., 0., 0., 0.]]

    Note:
        This is an experimental feature and is subjected to change.
        If the length of values or indices exceeds the range indicated by indptr, its behavior will be undefined.

    Args:
        indptr (Tensor): 1-D Tensor of shape `[M]`, which equals to `shape[0] + 1`, which indicates the
            start and end point for `values` in each row. Default: None. If provided,
            must be :class:`mindspore.int16`, :class:`mindspore.int32` or :class:`mindspore.int64`.
        indices (Tensor): 1-D Tensor of shape `[N]`, which has the same length as `values`. `indices`
            indicates the which column `values` should be placed. Default: None. If provided,
            must be :class:`mindspore.int16`, :class:`mindspore.int32` or :class:`mindspore.int64`.
        values (Tensor): Tensor, which has the same length as `indices` (values.shape[0] == indices.shape[0]).
            `values`  stores the data for CSRTensor. Default: None.
        shape (Tuple): A tuple indicates the shape of the CSRTensor, and `shape[0]` must equal to `M - 1`,
            which all equal to number of rows of the CSRTensor. Default: None.
        csr_tensor (CSRTensor): A CSRTensor object.  Values' feature dimension should match with
            CSRTensor's feature dimension (values.shape[1:] == csr_tensor.shape[2:]). Default: None.

    Outputs:
        CSRTensor, with shape defined by `shape`, and dtype inferred from `value`.

    Examples:
        >>> import mindspore as ms
        >>> from mindspore import Tensor, CSRTensor
        >>> # initialize a csr_tensor with indptr, indices, values and shape
        >>> indptr = Tensor([0, 1, 2], dtype=ms.int32)
        >>> indices = Tensor([0, 1], dtype=ms.int32)
        >>> values = Tensor([1, 2], dtype=ms.float32)
        >>> shape = (2, 4)
        >>> csr_tensor = CSRTensor(indptr, indices, values, shape)
        >>> # access a data member of CSRTensor
        >>> print(indptr == csr_tensor.indptr)
        [ True  True  True]
    """

    def __init__(self, indptr=None, indices=None, values=None, shape=None, csr_tensor=None):
        "Init CSRTensor"
        self.init_finished = False
        # Directly init a CSRTensor from another CSRTensor
        if csr_tensor is not None:
            if not isinstance(csr_tensor, (CSRTensor, CSRTensor_)):
                raise TypeError(f"Expect input `csr_tensor` to be a CSRTensor, but got {type(csr_tensor)}")
            if not (indptr is None and indices is None and values is None and shape is None):
                raise TypeError(
                    "If input `csr_tensor` is provided, `indptr`, `indices`, `values`, `shapes` should all be `None`")
            CSRTensor_.__init__(self, csr_tensor)
        # Init a CSRTensor from indptr, indices, values and shape
        else:
            validator.check_csr_tensor_input(indptr, indices, values, shape)
            validator.check_csr_tensor_shape(indptr.shape, indices.shape, values.shape, shape)
            validator.check_csr_tensor_dtype(indptr.dtype, indices.dtype)
            CSRTensor_.__init__(self, indptr, indices, values, shape)
        setattr(self, "__ms_mutable__", True)
        self.init_finished = True

    def __repr__(self):
        """Avoid PyTest Segfault when CSRTensor is not initialized."""
        if self.init_finished:
            return CSRTensor_.__repr__(self)
        return ''

    def __mul__(self, other):
        res = tensor_operator_registry.get('csr_mul')(self, other)
        return CSRTensor(self.indptr, self.indices, res, self.shape)

    def __div__(self, other):
        res = tensor_operator_registry.get('csr_div')(self, other)
        return CSRTensor(self.indptr, self.indices, res, self.shape)

    def __truediv__(self, other):
        return self.__div__(other)

    @property
    def indptr(self):
        """Return CSRTensor's row indices pointers."""
        return Tensor(self._indptr)

    @property
    def indices(self):
        """Return CSRTensor's column indices."""
        return Tensor(self._indices)

    @property
    def values(self):
        """Return CSRTensor's non-zero values."""
        return Tensor(self._values)

    @property
    def shape(self):
        """Return CSRTensor's shape."""
        return self._shape

    @property
    def dtype(self):
        """Return the dtype of the values of CSRTensor (:class:`mindspore.dtype`)."""
        return self._dtype

    @property
    def size(self):
        """Return the number of non-zero values."""
        return self.values.size

    @property
    def itemsize(self):
        """Return the length of one tensor element in bytes."""
        return self.values.itemsize

    @property
    def ndim(self):
        """Return the number of tensor dimensions."""
        return len(self.shape)

    def to_tuple(self):
        """
        Return indptr, indices, values and shape as a tuple.

        Returns:
            Tuple.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``
        """
        return self.indptr, self.indices, self.values, self.shape

    def to_coo(self):
        """
        Converts CSRTensor to COOTensor.

        Note:
            Currently only supports CPU backend with LLVM 12.0.1 installed.

        Returns:
            COOTensor.

        Supported Platforms:
            ``GPU`` ``CPU``
        """
        row_indices = tensor_operator_registry.get("csr2coo")(self.indptr, self.values.shape[0])
        coo_indices = tensor_operator_registry.get("stack")(1)((row_indices, self.indices))
        return COOTensor(coo_indices, self.values, self.shape)

    def to_dense(self):
        """
        Converts CSRTensor to Dense Tensor.

        Returns:
            Tensor.

        Supported Platforms:
            ``GPU``
        """
        coo_tensor = self.to_coo()
        return coo_tensor.to_dense()

    def astype(self, dtype):
        """
        Return a copy of the CSRTensor, cast its values to a specified type.

        Args:
            dtype (Union[:class:`mindspore.dtype`, numpy.dtype, str]): Designated tensor dtype.

        Returns:
            CSRTensor.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``

        Examples:
            >>> import mindspore as ms
            >>> from mindspore import Tensor, CSRTensor
            >>> indptr = Tensor([0, 1, 2], dtype=ms.int32)
            >>> indices = Tensor([0, 1], dtype=ms.int32)
            >>> values = Tensor([1, 2], dtype=ms.float32)
            >>> shape = (2, 4)
            >>> csr_tensor = CSRTensor(indptr, indices, values, shape)
            >>> print(csr_tensor.astype(ms.float64).dtype)
            Float64
        """
        data = self.values.astype(dtype)
        return CSRTensor(self.indptr, self.indices, data, self.shape)

    def mv(self, dense_vector):
        """
        Sparse matrix-vector multiplication.

        Note:
            Currently only supports CPU backend with LLVM 12.0.1 installed.

        Args:
            dense_vector (Tensor): A dense Tensor, its shape must be (csr_tensor.shape[1], 1)

        Returns:
            Tensor.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor, CSRTensor
            >>> from mindspore import dtype as mstype
            >>> indptr = Tensor([0, 1, 2], dtype=mstype.int32)
            >>> indices = Tensor([0, 1], dtype=mstype.int32)
            >>> values = Tensor([2, 1], dtype=mstype.float32)
            >>> dense_shape = (2, 4)
            >>> csr_tensor = CSRTensor(indptr, indices, values, dense_shape)
            >>> dense = Tensor([[1], [1], [1], [1]], dtype=mstype.float32)
            >>> print(csr_tensor.mv(dense))
            [[2.]
            [1.]]
        """
        validator.check_value_type('dense_vector', dense_vector, (Tensor_,), 'CSRTensor.mv')
        return tensor_operator_registry.get("csr_mv")(self, dense_vector)

    def mm(self, dense_matrix):
        """
        Sparse matrix-matrix multiplication.

        Note:
            Currently only supports CPU backend with LLVM 12.0.1 installed.

        Args:
            dense_matrix (Tensor): A dense Tensor, its shape[0] should be equal to csr_tensor.shape[1]

        Returns:
            Tensor.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor, CSRTensor
            >>> from mindspore import dtype as mstype
            >>> indptr = Tensor([0, 1, 2], dtype=mstype.int32)
            >>> indices = Tensor([0, 1], dtype=mstype.int32)
            >>> values = Tensor([2, 1], dtype=mstype.float32)
            >>> dense_shape = (2, 4)
            >>> csr_tensor = CSRTensor(indptr, indices, values, dense_shape)
            >>> dense_matrix = Tensor([[1., 2.], [1, 2.], [1, 2.], [1., 2.]], dtype=mstype.float32)
            >>> print(csr_tensor.mm(dense_matrix))
            [[2. 4.]
            [1. 2.]]
        """
        validator.check_value_type('dense_matrix', dense_matrix, (Tensor_,), 'CSRTensor.mm')
        return tensor_operator_registry.get("csr_mm")()(self.indptr, self.indices, self.values, \
                                                        self.shape, dense_matrix)

    def sum(self, axis):
        """
        Reduces a dimension of a CSRTensor by summing all elements in the dimension.

        Note:
            Currently only supports CPU backend with LLVM 12.0.1 installed.

        Args:
            axis (int): The dimensions to reduce.

        Returns:
            Tensor, the dtype is the same as `CSRTensor.values`.

        Supported Platforms:
            ``GPU`` ``CPU``

        Examples:
            >>> from mindspore import Tensor, CSRTensor
            >>> from mindspore import dtype as mstype
            >>> indptr = Tensor([0, 1, 2], dtype=mstype.int32)
            >>> indices = Tensor([0, 1], dtype=mstype.int32)
            >>> values = Tensor([2, 1], dtype=mstype.float32)
            >>> dense_shape = (2, 4)
            >>> csr_tensor = CSRTensor(indptr, indices, values, dense_shape)
            >>> print(csr_tensor.sum(1))
            [[2.]
            [1.]]
        """
        return tensor_operator_registry.get("csr_reduce_sum")(self, axis)

    def abs(self):
        """
        Return absolute value element-wisely.

        Returns:
            CSRTensor, with all values being non-negative.

        Supported Platforms:
            ``Ascend`` ``GPU`` ``CPU``
        """
        data = self.values.abs()
        return CSRTensor(self.indptr, self.indices, data, self.shape)


def _vm_compare(*args):
    """Implement `vm_compare` for tensor."""
    obj_str = args[-1]
    if obj_str == "shape":
        fn = getattr(args[0].asnumpy(), obj_str)
        return fn
    if len(args) == 2:
        fn = getattr(args[0].asnumpy(), obj_str)
        return Tensor(fn())
    if isinstance(args[0], Tensor):
        fn = getattr(args[0].asnumpy(), obj_str)
        y = args[1].asnumpy() if isinstance(args[1], Tensor) else args[1]
    else:
        obj_str = "__r" + obj_str[2:]
        fn = getattr(args[1].asnumpy(), obj_str)
        y = args[0]
    return Tensor(np.array(fn(y)))


def _check_tensor_input(input_data=None, dtype=None, shape=None, init=None):
    """Check the tensor input."""
    if input_data is not None and shape is not None:
        raise ValueError("If input_data is available, shape doesn't need to be set")

    if init is not None and (shape is None or dtype is None):
        raise ValueError("init, dtype and shape must have values at the same time.")

    if input_data is not None:
        if isinstance(input_data, np.ndarray) and input_data.ndim > 1 and input_data.size == 0:
            raise ValueError("input_data can not contain zero dimension.")
        if isinstance(input_data, (tuple, list)) and np.array(input_data).ndim > 1 \
                and np.array(input_data).size == 0:
            raise ValueError("input_data can not contain zero dimension.")

    if shape is not None and not (hasattr(init, "__enable_zero_dim__") and init.__enable_zero_dim__) and 0 in shape:
        raise ValueError("Shape can not contain zero value.")


def _check_tensor_dynamic_shape(dtype=None, shape=None, init=None):
    """Check if the tensor has dynamic shape."""
    shape_list = list(shape)
    if len(shape_list) >= 1:
        shape_replaced_list = [-1 if i is None else i for i in shape_list]
        if isinstance(shape, tuple):
            shape = tuple(shape_replaced_list)
        if isinstance(shape, list):
            shape = shape_replaced_list
    if -1 in shape and (dtype is None or init is not None):
        raise ValueError("If setting dynamic shape, dtype must not be None, init must be None")
    return shape


def _check_astype_and_convert(dtype):
    """Check whether dtype is a valid input, and convert to mstype"""
    all_types = mstype.__dtype__ + ["int", "float", "bool"]
    if isinstance(dtype, str):
        if dtype.lower() not in all_types:
            raise TypeError(f"For Tensor.astype, the string input type must be one of {all_types}, "
                            f"but got '{dtype}'.")
        dtype = mstype.pytype_to_dtype(np.dtype(dtype.lower()))
    elif isinstance(dtype, type):
        dtype = mstype.pytype_to_dtype(dtype)
    elif not dtype in mstype.number_type + (mstype.bool_,):
        raise TypeError(
            f"For Tensor.astype, the input type must be one of {list(mstype.number_type + (mstype.bool_,) + np_types)},"
            f" but got '{dtype}'.")
    return dtype

tensor_operator_registry.register('vm_compare', _vm_compare)
