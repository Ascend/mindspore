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

"""math_ops vmap impl."""
from __future__ import absolute_import

import mindspore.numpy as mnp
from mindspore.ops import operations as P
from mindspore.ops import functional as F
from mindspore.ops import constexpr
from mindspore.common import Tensor
from mindspore.ops.operations import math_ops
from mindspore.ops.operations import linalg_ops
from mindspore.ops.operations import _inner_ops
from mindspore.ops.operations import _grad_ops as G
from ..primitive import Primitive
from .._vmap.vmap_base import vmap_rules_getters, vmap_general_preprocess, get_assign_vmap_rule, \
    get_unop_vmap_rule, _raise_value_error, _bdim_at_front, _broadcast_by_axis, _handle_broadcasting, \
    get_unary_grad_vmap_rule, _vmap_clone_prim, _bdim_at_any
from ..operations.math_ops import (Bernoulli, BesselJ0, BesselJ1, BesselK0, BesselK0e, BesselY0, BesselY1, BesselK1,
                                   BesselK1e)


@constexpr
def _broadcast_shape(nd, x_ndim, x_shape):
    return x_shape + (1,) * (nd - x_ndim)


@vmap_rules_getters.register(P.Add)
@vmap_rules_getters.register(P.Sub)
@vmap_rules_getters.register(P.Mul)
@vmap_rules_getters.register(P.Div)
@vmap_rules_getters.register(P.Xdivy)
@vmap_rules_getters.register(P.RealDiv)
@vmap_rules_getters.register(P.FloorDiv)
@vmap_rules_getters.register(P.Maximum)
@vmap_rules_getters.register(P.Minimum)
@vmap_rules_getters.register(P.Atan2)
@vmap_rules_getters.register(P.Pow)
@vmap_rules_getters.register(P.Mod)
@vmap_rules_getters.register(P.Equal)
@vmap_rules_getters.register(P.GreaterEqual)
@vmap_rules_getters.register(P.Greater)
@vmap_rules_getters.register(P.LessEqual)
@vmap_rules_getters.register(P.Less)
@vmap_rules_getters.register(P.NotEqual)
@vmap_rules_getters.register(P.LogicalOr)
@vmap_rules_getters.register(P.LogicalAnd)
@vmap_rules_getters.register(P.BitwiseAnd)
@vmap_rules_getters.register(P.BitwiseOr)
@vmap_rules_getters.register(P.BitwiseXor)
@vmap_rules_getters.register(P.IsClose)
def get_broadcast_binary_op_vmap_rule(prim, axis_size):
    """VmapRule for binary operations with broadcasting, such as `Add` and `Sub`."""

    def vmap_rule(x_bdim, y_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim, y_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        y, y_dim = y_bdim
        x_shape = F.shape(x)
        y_shape = F.shape(y)
        if x_dim == y_dim and x_shape == y_shape:
            out = prim(x, y)
            return (out, x_dim)

        if F.rank(x):
            x = _bdim_at_front(x, x_dim, 1)
        if F.rank(y):
            y = _bdim_at_front(y, y_dim, 1)
        x_shape = F.shape(x)
        y_shape = F.shape(y)
        x = _handle_broadcasting(x, x_shape, y_shape)
        y = _handle_broadcasting(y, y_shape, x_shape)

        out = prim(x, y)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(P.Cdist)
def get_cdist_vmap_rule(prim, axis_size):
    """VmapRule for `cdist` operation."""
    if hasattr(prim, 'batch_rank'):
        batch_rank = prim.batch_rank + 1
    else:
        batch_rank = 1

    batch_prim = _vmap_clone_prim(prim)
    batch_prim.add_prim_attr("batch_rank", batch_rank)

    def vmap_rule(x_bdim, y_bdim):
        x, x_dim = x_bdim
        y, y_dim = y_bdim

        if x_dim is None and y_dim is None:
            out = prim(x, y)
            return (out, None)
        x = _bdim_at_front(x, x_dim, axis_size)
        y = _bdim_at_front(y, y_dim, axis_size)

        out = batch_prim(x, y)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(math_ops.Lerp)
def get_lerp_vamp_rule(prim, axis_size):
    """VmapRule for ternary operations with broadcasting, such as `Lerp` ."""

    def broadcast_a_b_shape(a_bdim, b_bdim):
        a, a_dim = a_bdim
        b, b_dim = b_bdim
        if F.rank(a):
            a = _bdim_at_front(a, a_dim, 1)

        if F.rank(b):
            b = _bdim_at_front(b, b_dim, 1)
        a_shape = F.shape(a)
        b_shape = F.shape(b)
        a = _handle_broadcasting(a, a_shape, b_shape)
        b = _handle_broadcasting(b, b_shape, a_shape)
        return a, b

    def vmap_rule(start_bdim, end_bdim, weight_bdim):
        is_all_none, result = vmap_general_preprocess(prim, start_bdim, end_bdim, weight_bdim)
        if is_all_none:
            return result
        start, start_dim = start_bdim
        end, end_dim = end_bdim
        weight, weight_dim = weight_bdim
        start_shape = F.shape(start)
        end_shape = F.shape(end)
        # Just broadcast end shape to start.
        if not isinstance(weight, Tensor):
            if start_dim == end_dim and start_shape == end_shape:
                out = prim(start, end, weight)
                return out, start_dim
            start, end = broadcast_a_b_shape(start_bdim, end_bdim)
        # Both broadcast end and weight to start.
        else:
            weight_shape = F.shape(weight)
            if (start_dim == end_dim and start_dim == weight_dim) and (
                    start_shape == end_shape and start_shape == weight_shape):
                out = prim(start, end, weight)
                return out, start_dim
            start, end = broadcast_a_b_shape(start_bdim, end_bdim)
            start, weight = broadcast_a_b_shape(start_bdim, weight_bdim)
        out = prim(start, end, weight)
        return out, 0

    return vmap_rule


@vmap_rules_getters.register(G.MaximumGradGrad)
@vmap_rules_getters.register(G.MinimumGradGrad)
def get_broadcast_grad_grad_vmap_rule(prim, axis_size):
    """VmapRule for GradGrad operations with broadcasting."""

    def vmap_rule(x1_bdim, x2_bdim, dx1_bdim, dx2_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x1_bdim, x2_bdim, dx1_bdim, dx2_bdim)
        if is_all_none:
            return result

        x1, x1_dim = x1_bdim
        x2, x2_dim = x2_bdim
        dx1, dx1_dim = dx1_bdim
        dx2, dx2_dim = dx2_bdim
        x1_shape = F.shape(x1)
        x2_shape = F.shape(x2)
        dx1_shape = F.shape(dx1)
        dx2_shape = F.shape(dx2)

        if x1_dim == x2_dim and dx1_dim == dx2_dim and x1_dim == dx1_dim \
            and x1_shape == x2_shape and dx1_shape == dx2_shape:
            sopd_x1, sopd_x2, sopd_grad = prim(x1, x2, dx1, dx2)
            return (sopd_x1, x1_dim), (sopd_x2, x1_dim), (sopd_grad, x1_dim)

        if F.rank(x1):
            x1 = _bdim_at_front(x1, x1_dim, 1)
        if F.rank(x2):
            x2 = _bdim_at_front(x2, x2_dim, 1)
        if F.rank(dx1):
            dx1 = _bdim_at_front(dx1, dx2_dim, 1)
        if F.rank(dx2):
            dx2 = _bdim_at_front(dx2, dx2_dim, 1)
        x1_shape = F.shape(x1)
        x2_shape = F.shape(x2)
        dx1_shape = F.shape(dx1)
        dx2_shape = F.shape(dx2)
        x1 = _handle_broadcasting(x1, x1_shape, x2_shape)
        x2 = _handle_broadcasting(x2, x2_shape, x1_shape)
        dx1 = _handle_broadcasting(dx1, dx1_shape, dx2_shape)
        dx2 = _handle_broadcasting(dx2, dx2_shape, dx1_shape)
        sopd_x1, sopd_x2, sopd_grad = prim(x1, x2, dx1, dx2)
        return (sopd_x1, 0), (sopd_x2, 0), (sopd_grad, 0)

    return vmap_rule


@vmap_rules_getters.register(Bernoulli)
def get_bernoulli_op_vmap_rule(prim, axis_size):
    """VmapRule for Bernoulli operation."""

    def vmap_rule(x_bdim, p_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim, p_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        p, p_dim = p_bdim
        if F.rank(x):
            x = _bdim_at_front(x, x_dim, 1)

        if isinstance(p, Tensor) and F.rank(p):
            p = _bdim_at_front(p, p_dim, 1)
            x_shape = F.shape(x)
            p_shape = F.shape(p)
            p = _handle_broadcasting(p, p_shape, x_shape)

        out = prim(x, p)
        return out, 0

    return vmap_rule


@vmap_rules_getters.register(P.AddN)
def get_add_n_vmap_rule(prim, axis_size):
    """VmapRule for AddN operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)

    def vmap_rule(*inputs_bdim):
        is_all_none, result = vmap_general_preprocess(prim, *inputs_bdim)
        if is_all_none:
            return result

        if not isinstance(inputs_bdim, (tuple, list)):
            _raise_value_error("The 'x' of P.AddN is neither tuple nor list.")

        args = inputs_bdim[0]
        vals = ()
        for each_arg in args:
            x, bdim = each_arg
            x = _bdim_at_front(x, bdim, axis_size)
            vals = vals + (x,)

        out = prim(vals)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(P.MatMul)
@vmap_rules_getters.register(P.BatchMatMul)
def get_matmul_vmap_rule(prim, axis_size):
    """VmapRule for `*MatMul` operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)
        transpose_a = False
        transpose_b = False
    else:
        transpose_a = prim.transpose_a
        transpose_b = prim.transpose_b
    batch_matmul = P.BatchMatMul(transpose_a, transpose_b)

    def vmap_rule(a_bdim, b_bdim):
        is_all_none, result = vmap_general_preprocess(prim, a_bdim, b_bdim)
        if is_all_none:
            return result

        a, a_dim = a_bdim
        b, b_dim = b_bdim
        a = _bdim_at_front(a, a_dim, axis_size)
        b = _bdim_at_front(b, b_dim, axis_size)

        out = batch_matmul(a, b)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(P.math_ops.MatrixSolve)
def get_matrix_solve_vmap_rule(prim, axis_size):
    """VmapRule for `*MatMul` operation."""
    if isinstance(prim, str):
        adjoint = False
    else:
        adjoint = prim.adjoint

    def vmap_rule(matrix_bdim, rhs_bdim):
        is_all_none, result = vmap_general_preprocess(prim, matrix_bdim, rhs_bdim)
        if is_all_none:
            return result

        matrix, matrix_dim = matrix_bdim
        rhs, rhs_dim = rhs_bdim
        matrix = _bdim_at_front(matrix, matrix_dim, axis_size)
        rhs = _bdim_at_front(rhs, rhs_dim, axis_size)

        out = F.matrix_solve(matrix, rhs, adjoint)
        return out, 0

    return vmap_rule


@vmap_rules_getters.register(P.BroadcastTo)
def get_broadcast_to_vmap_rule(prim, axis_size):
    """VmapRule for `BroadcastTo` operation."""
    shape = prim.shape

    def vmap_rule(operand_bdim):
        is_all_none, result = vmap_general_preprocess(prim, operand_bdim)
        if is_all_none:
            return result

        x, dim = operand_bdim
        x = mnp.moveaxis(x, dim, 0)
        axis_size = F.shape(x)[0]
        batch_shape = (axis_size,) + shape

        out = P.BroadcastTo(batch_shape)(x)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(P.InplaceAdd)
@vmap_rules_getters.register(P.InplaceSub)
@vmap_rules_getters.register(P.InplaceUpdate)
def get_inplace_ops_vmap_rule(prim, axis_size):
    """VmapRule for `InplaceAdd`, `InplaceSub`, `InplaceUpdate` operation."""

    def vmap_rule(x_bdim, v_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim, v_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        v, v_dim = v_bdim
        if x_dim is None:
            x = _broadcast_by_axis(x, -1, axis_size)
        else:
            x = mnp.moveaxis(x, x_dim, -1)
        if v_dim is None:
            v = _broadcast_by_axis(v, -1, axis_size)
        else:
            v = mnp.moveaxis(v, v_dim, -1)
        out = prim(x, v)
        return (out, out.ndim - 1)

    return vmap_rule


@constexpr
def _get_reduce_batch_axis(axis, x_dim, x_ndim):
    """get batch_axis for reduce* operation."""
    # For axis, it's value in Union[int, list, tuple]
    if isinstance(axis, int):
        axis = (axis,)

    batch_axis = ()
    if axis:
        for index in axis:
            if index < x_dim:
                batch_axis = batch_axis + (index,)
            else:
                batch_axis = batch_axis + (index + 1,)
    else:
        batch_axis_list = [index for index in range(x_ndim)]
        del batch_axis_list[x_dim]
        batch_axis = tuple(batch_axis_list)
    return batch_axis


@constexpr
def _get_reduce_out_dim(keep_dims, x_dim, x_ndim, batch_axis):
    """get out_dim for reduce* operation."""
    if keep_dims:
        out_dim = x_dim
    else:
        out_dim = 0
        for i in range(x_ndim):
            if i == x_dim:
                break
            if i in batch_axis:
                continue
            else:
                out_dim += 1
    return out_dim


@vmap_rules_getters.register(P.ReduceSum)
@vmap_rules_getters.register(P.ReduceMax)
@vmap_rules_getters.register(P.ReduceMin)
@vmap_rules_getters.register(P.ReduceMean)
@vmap_rules_getters.register(P.ReduceProd)
def get_reducer_vmap_rule(prim, axis_size):
    """VmapRule for reduce operations, such as `ReduceSum`."""
    keep_dims = prim.keep_dims
    prim_name = prim.name

    def vmap_rule(operand_bdim, axis_bdim):
        is_all_none, result = vmap_general_preprocess(prim, operand_bdim, axis_bdim)
        if is_all_none:
            return result

        x, x_dim = operand_bdim
        axis, axis_dim = axis_bdim
        if axis_dim is not None:
            _raise_value_error("The source axis of `axis` in `{}` must be None, "
                               "but got {}.".format(prim_name, axis_dim))

        x_ndim = F.rank(x)
        batch_axis = _get_reduce_batch_axis(axis, x_dim, x_ndim)

        out = prim(x, batch_axis)
        out_dim = _get_reduce_out_dim(keep_dims, x_dim, x_ndim, batch_axis)
        return (out, out_dim)

    return vmap_rule


@vmap_rules_getters.register(P.IndexAdd)
def get_index_add_vmap_rule(prim, axis_size):
    """VmapRule for IndexAdd."""
    axis = prim.axis

    @constexpr
    def _get_index_add_batch_axis(axis, x_dim, x_ndim):
        """get batch_axis for IndexAdd."""
        # case1: batch not exists
        if x_dim is None:
            return axis
        # case2: batch exists
        x_ndim_orig = x_ndim - 1
        if x_dim < -x_ndim or x_dim >= x_ndim:
            raise ValueError("The batch dimension of 'x' in 'IndexAdd' must be in range [{}, {}), but got {}"
                             .format(-x_ndim, x_ndim, x_dim))
        if x_dim < 0:
            x_dim = x_dim + x_ndim
        if axis < -x_ndim_orig or axis >= x_ndim_orig:
            raise ValueError("'axis' of 'IndexAdd' must be in range [{}, {}), but got {}"
                             .format(-x_ndim_orig, x_ndim_orig, axis))
        if axis < 0:
            axis = axis + x_ndim_orig
        if x_dim > axis:
            return axis
        return axis + 1

    def vmap_rule(x_bdim, indices_bdim, y_bdim, u_monad):
        x, x_dim = x_bdim
        indices, indices_dim = indices_bdim
        y, y_dim = y_bdim

        if indices_dim is not None:
            _raise_value_error("The batch dimension of 'indices' in 'IndexAdd' must be None, but got {}."
                               .format(indices_dim))
        if x_dim is None and y_dim is not None:
            _raise_value_error("The batch dimension of 'x' in 'IndexAdd' is None, so the batch dimension of 'y' "
                               "must be None, but got {}. ".format(y_dim))

        # update axis
        new_axis = _get_index_add_batch_axis(axis, x_dim, F.rank(x))
        op = P.IndexAdd(new_axis)

        if x_dim == y_dim:
            out = op(x, indices, y, u_monad)
            return (out, x_dim)
        if y_dim is None:
            y = _broadcast_by_axis(y, x_dim, axis_size)
        else:
            y = mnp.moveaxis(y, y_dim, x_dim)
        out = op(x, indices, y, u_monad)
        return (out, x_dim)

    return vmap_rule


@vmap_rules_getters.register(linalg_ops.Svd)
def get_svd_vmap_rule(prim, axis_size):
    """VmapRule for 'Svd' operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)
        compute_uv = True
    else:
        compute_uv = prim.compute_uv

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        x = _bdim_at_front(x, x_dim, axis_size)
        s, u, v = prim(x)
        if compute_uv:
            return (s, 0), (u, 0), (v, 0)
        return (s, 0), (u, None), (v, None)

    return vmap_rule


@vmap_rules_getters.register(math_ops.LpNorm)
def get_lp_norm_vmap_rule(prim, axis_size):
    """VmapRule for 'LpNorm' operation."""
    axis = prim.axis
    p = prim.p
    keep_dims = prim.keep_dims
    epsilon = prim.epsilon

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result
        x, x_dim = x_bdim
        x_ndim = F.rank(x)
        # LpNorm is a reduction class op, so just reuse the common function.
        batch_axis = _get_reduce_batch_axis(axis, x_dim, x_ndim)
        lp_norm_op = math_ops.LpNorm(batch_axis, p, keep_dims, epsilon)
        out = lp_norm_op(x)
        out_dim = _get_reduce_out_dim(keep_dims, x_dim, x_ndim, batch_axis)
        return out, out_dim

    return vmap_rule


@vmap_rules_getters.register(P.Renorm)
def get_renorm_rule(prim, axis_size):
    """VmapRule for Renorm"""
    pnorm = prim.p
    axis = prim.dim
    maxnorm = prim.maxnorm

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result

        x, batch_dim = x_bdim
        batch_dim = batch_dim if batch_dim >= 0 else batch_dim + F.rank(x)
        src_dim = batch_dim
        origin_axis = axis if axis >= 0 else axis + F.rank(x) - 1
        if batch_dim <= origin_axis:
            actual_axis = origin_axis + 1
            des_dim = actual_axis - 1
            x = mnp.moveaxis(x, src_dim, des_dim)
            from_shape = F.shape(x)
            to_shape = from_shape[:actual_axis - 1] + \
                       (from_shape[actual_axis - 1] * from_shape[actual_axis],) + from_shape[actual_axis + 1:]
        else:
            actual_axis = origin_axis
            des_dim = actual_axis + 1
            x = mnp.moveaxis(x, src_dim, des_dim)
            from_shape = F.shape(x)
            to_shape = from_shape[:actual_axis] + \
                       (from_shape[actual_axis] * from_shape[actual_axis + 1],) + from_shape[actual_axis + 2:]
        x = F.reshape(x, to_shape)
        op = P.Renorm(int(pnorm), origin_axis, maxnorm)
        out = op(x)
        out = F.reshape(out, from_shape)
        out = mnp.moveaxis(out, des_dim, src_dim)
        return (out, batch_dim)

    return vmap_rule


@vmap_rules_getters.register(P.LinSpace)
def get_linspace_rule(prim, axis_size):
    """VmapRule for `LinSpace` operation."""
    if hasattr(prim, 'batch_rank'):
        batch_rank = prim.batch_rank + 1
    else:
        batch_rank = 1

    batch_linspace = P.LinSpace()
    batch_linspace.add_prim_attr('batch_rank', batch_rank)
    prim_name = batch_linspace.name

    def vmap_rule(start_bdim, stop_bdim, num_bdim):
        is_all_none, result = vmap_general_preprocess(prim, start_bdim, stop_bdim, num_bdim)
        if is_all_none:
            return result

        start, start_dim = start_bdim
        stop, stop_dim = stop_bdim
        num, num_dim = num_bdim

        if num_dim is not None:
            _raise_value_error("The source axis of `num` in `{}` must be None, "
                               "but got {}.".format(prim_name, num_dim))

        out_dim = start_dim
        if start_dim != stop_dim:
            if start_dim is None:
                start = _bdim_at_any(start, start_dim, stop_dim, axis_size)
                out_dim = stop_dim
            else:
                stop = _bdim_at_any(stop, stop_dim, start_dim, axis_size)

        result = batch_linspace(start, stop, num)
        return result, out_dim

    return vmap_rule


@vmap_rules_getters.register(math_ops.MatrixDeterminant)
def get_matrix_determinant_vmap_rule(prim, axis_size):
    """VmapRule for `MatrixDeterminant` operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result
        x, x_dim = x_bdim
        x_ndim = F.rank(x)
        if x_ndim - 2 <= x_dim:
            x = _bdim_at_front(x, x_dim, axis_size)
            out = prim(x)
            return out, 0
        out = prim(x)
        return out, x_dim

    return vmap_rule


@vmap_rules_getters.register(math_ops.LogMatrixDeterminant)
def get_log_matrix_determinant_vmap_rule(prim, axis_size):
    """VmapRule for `LogMatrixDeterminant` operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result
        x, x_dim = x_bdim
        x_ndim = F.rank(x)
        if x_ndim - 2 <= x_dim:
            x = _bdim_at_front(x, x_dim, axis_size)
            sign, determinant = prim(x)
            return (sign, 0), (determinant, 0)
        sign, determinant = prim(x)
        return (sign, x_dim), (determinant, x_dim)

    return vmap_rule


@vmap_rules_getters.register(P.Cummax)
@vmap_rules_getters.register(_inner_ops.Cummin)
def get_cum_min_max_vmap_rule(prim, axis_size):
    """VmapRule for `Cummax` and `Cummin` operation."""

    cum_fun_map = {
        "Cummin": _inner_ops.Cummin,
        "Cummax": P.Cummax,
    }
    axis = prim.axis
    prim_name = prim.name
    prim_class = cum_fun_map.get(prim_name)

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        old_x_ndim = F.rank(x) - 1
        old_axis = axis if axis >= 0 else axis + old_x_ndim
        new_axis = old_axis if old_axis < x_dim else old_axis + 1
        value, index = prim_class(new_axis)(x)
        return (value, x_dim), (index, x_dim)

    return vmap_rule


get_assign_vmap_rule = vmap_rules_getters.register(P.AssignAdd)(get_assign_vmap_rule)
get_assign_vmap_rule = vmap_rules_getters.register(P.AssignSub)(get_assign_vmap_rule)
# Unary vmap
get_unop_vmap_rule = vmap_rules_getters.register(P.Abs)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.ACos)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Acosh)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Asin)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Asinh)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Atan)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Atanh)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Cos)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Cosh)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Sin)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Sinh)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Tan)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Tanh)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Ceil)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Erf)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Erfc)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Erfinv)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Exp)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Expm1)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Floor)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Log)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Log1p)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.LogicalNot)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Mish)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Neg)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Reciprocal)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Inv)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Invert)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Rint)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Round)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Rsqrt)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Sigmoid)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Sqrt)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Sign)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Real)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Imag)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.IsNan)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.IsInf)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.IsFinite)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselJ0)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselJ1)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.BesselI0)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.BesselI0e)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselK0)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselK0e)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselY0)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselY1)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.BesselI1)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.BesselI1e)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselK1)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(BesselK1e)(get_unop_vmap_rule)
# UnaryGrad vmap
get_unary_grad_vmap_rule = vmap_rules_getters.register(G.InvGrad)(get_unary_grad_vmap_rule)
