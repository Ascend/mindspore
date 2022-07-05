mindspore.nn.SparseTensorDenseMatmul
=====================================

.. py:class:: mindspore.nn.SparseTensorDenseMatmul(adjoint_st=False, adjoint_dt=False)

    稀疏矩阵 `a` 乘以稠密矩阵 `b` 。稀疏矩阵和稠密矩阵的秩必须等于2。

    **参数：**

    - **adjoint_st** (bool) - 如果为True，则在乘法之前转置稀疏Tensor。默认值：False。
    - **adjoint_dt** (bool) - 如果为True，则在乘法之前转置稠密Tensor。默认值：False。

    **输入：**

    - **indices** (Tensor) - 二维Tensor，表示元素在稀疏Tensor中的位置。支持int32、int64，每个元素值都应该是非负的。shape为 :math:`(n, 2)` 。
    - **values** (Tensor) - 一维Tensor，表示 `indices` 位置上对应的值。支持float16、float32、float64、int32、int64。shape为 :math:`(n,)` 。
    - **sparse_shape** (tuple) - 指定稀疏Tensor的shape，由两个正整数组成，表示稀疏Tensor的shape为 :math:`(N, C)` 。
    - **dense** (Tensor) - 二维Tensor，数据类型与 `values` 相同。
      如果 `adjoint_st` 为False， `adjoint_dt` 为False，则shape必须为 :math:`(C, M)` 。
      如果 `adjoint_st` 为False， `adjoint_dt` 为True，则shape必须为 :math:`(M, C)` 。
      如果 `adjoint_st` 为True， `adjoint_dt` 为False，则shape必须为 :math:`(N, M)` 。
      如果 `adjoint_st` 为True， `adjoint_dt` 为True，则shape必须为 :math:`(M, N)` 。

    **输出：**

    Tensor，数据类型与 `values` 相同。如果 `adjoint_st` 为False，则shape为 :math:`(N, M)` 。如果 `adjoint_st` 为True，则shape为 :math:`(C, M)` 。

    **异常：**

    - **TypeError** - `adjoint_st` 或 `adjoint_dt` 的类型不是bool，或者 `indices`、 `values` 、 `dense` 的数据类型不符合参数说明。
    - **ValueError** - `sparse_shape` 、 `indices` 、 `values` 、 `dense` 的shape不符合参数说明。
