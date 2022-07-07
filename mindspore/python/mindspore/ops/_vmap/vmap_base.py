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

"""vmap base functions"""

import mindspore.numpy as mnp
from mindspore.ops import operations as P
from mindspore.ops import functional as F
from mindspore.ops import constexpr
from mindspore.ops.operations import _grad_ops as G
from .._register_for_op import Registry
from ..composite import _VmapGeneralPreprocess
from ..primitive import Primitive
from ..operations.random_ops import UniformCandidateSampler
from ...common import Tensor

vmap_rules_getters = Registry()
vmap_rules = Registry()


def get_vmap_rule(prim, axis_size):
    """get vmap rule function by primitive obj or prim name for c++"""
    out = vmap_rules_getters.get(prim, None)
    if out:
        return out(prim, axis_size)
    return vmap_rules.get(prim, None)


@constexpr
def _get_broadcast_shape_without_axis(x_shape, y_shape):
    """Get the broadcast shape for _handle_broadcasting."""
    x_len = len(x_shape)
    y_len = len(y_shape)

    if x_len >= y_len:
        return x_shape

    # scalar case
    if not x_len:
        return (1,) * y_len

    broadcast_shape = ()
    x_index = x_len - 1

    for i in range(y_len - 1, 0, -1):
        if x_index == 0:
            broadcast_shape = (1,) + broadcast_shape
        elif x_shape[x_index] == y_shape[i] or y_shape[i] == 1 or x_shape[x_index] == 1:
            broadcast_shape = (x_shape[x_index],) + broadcast_shape
            x_index -= 1
        else:
            broadcast_shape = (1,) + broadcast_shape

    finnal_shape = (x_shape[0],) + tuple(broadcast_shape)
    return finnal_shape


def _handle_broadcasting(x, x_shape, y_shape):
    """Handle the broadcasting shape."""
    broadcast_shape = _get_broadcast_shape_without_axis(x_shape, y_shape)
    return F.reshape(x, broadcast_shape)


@constexpr
def _raise_value_error(info, param=None):
    """Constexpr for raise_value_error."""
    if param is None:
        raise ValueError(info)
    raise ValueError(info + f"{param}")


@constexpr
def _get_broadcast_shape(x_shape, dst, axis_size):
    """Get the target shape for broadcast array."""
    x_ndim = len(x_shape)
    broadcast_ndim = x_ndim + 1

    if dst < -broadcast_ndim or dst >= broadcast_ndim:
        _raise_value_error("Destination axis {} is out of bounds for array of dimension"
                           " [{}, {}).".format(dst, -broadcast_ndim, broadcast_ndim))
    if dst < 0:
        dst = broadcast_ndim + dst

    target_shape = list(x_shape)
    target_shape.insert(dst, axis_size)
    return tuple(target_shape)


def _broadcast_by_axis(x, dst: int, axis_size: int):
    """
    Broadcasts an array or scaler to a new shape alone the destination axis.

    Args:
        x (Tensor or Scalar): The input tensor or scalar. The data type should be one of the following types: float16,
            float32, int32, int8, uint8, bool.
        dst (int): The destination axis to broadcast.
        axis_size (int): The size of the destination axis to be broadcast.

    Returns:
        Tensor, array after broadcast along the destination axis.

    Raises:
        ValueError: If destination axes are out of the range of ``[-ndim, ndim)``, ``ndim = x.ndim + 1``.
    """
    if not isinstance(x, Tensor):
        if dst in (0, -1):
            x = [x] * axis_size
            return Tensor(x)
        _raise_value_error("Destination axis {} is out of bounds for array of dimension [-1, 0).".format(dst))

    x_shape = F.shape(x)
    target_shape = _get_broadcast_shape(x_shape, dst, axis_size)
    x = F.expand_dims(x, dst)
    return P.BroadcastTo(target_shape)(x)


def vmap_bind_all_none(inputs):
    results = ()
    if isinstance(inputs, tuple):
        for res in inputs:
            results = results + ((res, None),)
        return results
    return (inputs, None)


vmap_general_preprocess = _VmapGeneralPreprocess()


def vmap_unstack(dim, val):
    return P.Unstack(dim)(val)


def vmap_general_output_process(output):
    """ Match output to axis 0"""
    vals_out_tuple = ()
    if isinstance(output[0], tuple):
        for res in zip(**output):
            if not isinstance(res[0], Tensor):
                _raise_value_error("The output of the operator is not of the Tensor type, "
                                   "a specific vmap rule is required.")
            out = F.stack(res)
            vals_out_tuple = vals_out_tuple + ((out, 0),)
    else:
        out = F.stack(output)
        vals_out_tuple = vals_out_tuple + (out, 0)
    return vals_out_tuple


def vmap_monad_rule(prim, axis_size):
    """
    When the monad primitive does not registered the relevant specific VmapRule, it attempts to get
    this the general monad rule. Currently, only all inputs with the source axis of `None` can be
    supported.
    """
    if isinstance(prim, str):
        prim_name = prim
        prim = Primitive(prim)
    else:
        prim_name = prim.name

    def vmap_rule(*args):
        vals = ()
        args_len = len(args)
        for index, val_bdim in enumerate(args, 1):
            # Only the monad tag can not be tuple
            if index == args_len:
                vals = vals + (val_bdim,)
            if not isinstance(val_bdim, tuple):
                _raise_value_error("vmap currently not support the side effect op: {}.".format(prim_name))
            else:
                val, dim = val_bdim
                if dim is not None:
                    _raise_value_error("vmap currently not support the side effect op: {}.".format(prim_name))
                vals = vals + (val,)
        out = prim(*vals)
        return (out, None)

    return vmap_rule


def _bdim_at_any(x, src, dst, axis_size):
    """
    Moves source axes of an array to the dst axis, and other axes remain in their original order. If the source axes
    is 'None', broadcasts the array at dst axis with axis_size.

    Args:
        x (Tensor or Scalar): The input tensor or scalar. The data type should be one of the following types: float16,
            float32, int32, int8, uint8, bool.
        src (int or None): The source axis needs to be moved.
        dst (int): The destination axis needs to be moved to.
        axis_size (int): The size of the dst axis to be broadcast.

    Returns:
        Tensor, array with moved axes.
    """
    if src is None:
        return _broadcast_by_axis(x, dst, axis_size)
    return mnp.moveaxis(x, src, dst)


def _bdim_at_front(x, src, axis_size):
    """
    Moves source axes of an array to the foremost, and other axes remain in their original order. If the source axes
    is 'None', broadcasts the array at foremost axis with axis_size.

    Args:
        x (Tensor or Scalar): The input tensor or scalar. The data type should be one of the following types: float16,
            float32, int32, int8, uint8, bool.
        src (int or None): The source axis needs to be moved.
        axis_size (int): The size of the foremost axis to be broadcast.

    Returns:
        Tensor, array with moved axes.
    """
    return _bdim_at_any(x, src, 0, axis_size)


def _bdim_at_back(x, src, axis_size):
    """
    Moves source axes of an array to the last, and other axes remain in their original order. If the source axes
    is 'None', broadcasts the array at foremost axis with axis_size.

    Args:
        x (Tensor or Scalar): The input tensor or scalar. The data type should be one of the following types: float16,
            float32, int32, int8, uint8, bool.
        src (int or None): The source axis needs to be moved.
        axis_size (int): The size of the last axis to be broadcast.

    Returns:
        Tensor, array with moved axes.
    """
    return _bdim_at_any(x, src, -1, axis_size)


def get_assign_vmap_rule(prim, axis_size):
    """VmapRule for `Assign*` operations, such as `Assign` and `AssignAdd`."""
    if isinstance(prim, str):
        prim_name = prim
        prim = Primitive(prim)
    else:
        prim_name = prim.name

    def vmap_rule(variable_bdim, value_bdim, u_monad):
        var, var_dim = variable_bdim
        val, val_dim = value_bdim

        if var_dim is None:
            if val_dim is not None:
                _raise_value_error("The source axis of `variable` is None, but the source "
                                   "axis of `value` is not None. The execution order of "
                                   "operator `{}` cannot be guaranteed.".format(prim_name))
        else:
            if val_dim is None:
                val = _broadcast_by_axis(val, var_dim, axis_size)
            else:
                val = mnp.moveaxis(val, val_dim, var_dim)
        out = prim(var, val, u_monad)
        return (out, var_dim)

    return vmap_rule


def get_unop_vmap_rule(prim, axis_size):
    """VmapRule for unary operations, such as `Sin` and `Cos`."""
    if isinstance(prim, str):
        prim = Primitive(prim)

    def vmap_rule(x_bdim):
        var, dim = x_bdim
        out = prim(var)
        return (out, dim)

    return vmap_rule


def get_unsupported_dynamic_vmap_rule(prim, axis_size):
    """
    Vmaprule for the dynamic shape operator whose output shape can not be determined,
    which means the output shape of every batch will be different, so the operator can not support vmap.
    Forexample, the `Unique` operator, whose output shape is also base on the value of the input.
    Otherwise, the other dynamic shape operators need to implement their own vmaprules.
    """
    if isinstance(prim, str):
        prim_name = prim
        prim = Primitive(prim)
    else:
        prim_name = prim.name

    def get_all_dims(*params_bdim):
        dims = []
        for bdim in params_bdim:
            _, dim = bdim
            dims.append(dim)

        return dims

    def vmap_rule(*params_bdim):
        is_all_none, result = vmap_general_preprocess(prim, params_bdim)

        if not is_all_none:
            dims = get_all_dims(*params_bdim)
            _raise_value_error("For operator {}, all axis should be none, but got {}".format(prim_name, dims))

        return result

    return vmap_rule


def get_unary_grad_vmap_rule(prim, axis_size):
    """VmapRule for `UnaryGrad`."""
    if isinstance(prim, str):
        prim = Primitive(prim)

    def vmap_rule(x_bdim, dout_bdim):
        x, x_dim = x_bdim
        dout, dout_dim = dout_bdim
        x_shape = F.shape(x)
        dout_shape = F.shape(dout)
        if x_dim == dout_dim and x_shape == dout_shape:
            out = prim(x, dout)
            return (out, x_dim)

        # This branch means (x_dim is None) and (dout_dim is not None).
        if x_dim is None:
            x = _broadcast_by_axis(x, dout_dim, axis_size)
            out_dim = dout_dim
        # This branch means (x_dim is not None) and (dout_dim is None).
        elif dout_dim is None:
            dout = _broadcast_by_axis(dout, x_dim, axis_size)
            out_dim = x_dim
        # This branch means (x_dim is not None) and (dout_dim is not None).
        else:
            dout = mnp.moveaxis(dout, dout_dim, x_dim)
            out_dim = x_dim
        out = prim(x, dout)
        return (out, out_dim)

    return vmap_rule


@constexpr
def _vmap_update_prim_attr(prim, attr_name, attr_value):
    """
    Set new value for attribute of the primitive.
    Note: when this function is called, the value of "attr_name" will be modified globally,
          even the value of the same prim called before. So a new prim should be created before call this function.
          >>> new_prim = _vmap_clone_prim(prim)
          >>> _vmap_update_prim_attr(new_prim, "group", 1)
    """
    prim.add_prim_attr(attr_name, attr_value)


def _vmap_clone_prim(prim):
    """
    Cloning a new primitive object same as `prim`.
    """
    new_ops = _ops_vmap_clone_prim_dict.get(prim.name, None)
    if new_ops is None:
        ValueError("Failed to get the primitive object of {} from `_ops_vmap_clone_prim_dict`. Please register "
                   "the primitive object in the dictionary.".format(prim.name))
    init_args = prim.init_attrs
    cloned = new_ops(**init_args)

    for name in prim.attrs:
        value = prim.attrs[name]
        cloned.add_attr(name, value)

    if hasattr(prim, 'instance_name'):
        cloned.set_prim_instance_name(prim.instance_name)

    return cloned

_ops_vmap_clone_prim_dict = {"ApplyAdadelta": P.ApplyAdadelta,
                             "ApplyFtrl": P.ApplyFtrl,
                             "ApplyProximalAdagrad": P.ApplyProximalAdagrad,
                             "ApplyAdamWithAmsgrad": P.ApplyAdamWithAmsgrad,
                             "ApplyPowerSign": P.ApplyPowerSign,
                             "ApplyAdagradDA": P.ApplyAdagradDA,
                             "UniformCandidateSampler": UniformCandidateSampler,
                             "CdistGrad": G.CdistGrad,
                             "Cdist": P.Cdist}
