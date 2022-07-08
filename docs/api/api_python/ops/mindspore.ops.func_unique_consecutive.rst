mindspore.ops.unique_consecutive
================================

.. py:function:: mindspore.ops.unique_consecutive(x, return_idx=False, return_counts=False, axis=None)

    对输入张量中连续且重复的元素去重。

    **参数：**

    - **x** (Tensor) - 输入Tensor。
    - **return_idx** (bool, optional) - 是否返回每个去重元素在输入中所在的连续序列的末尾位置的索引。默认值：False。
    - **return_counts** (bool, optional) - 是否返回每个去重元素在输入所在的连续序列的计数。默认值：False。
    - **axis** (int, optional) - 维度。如果为None，则对输入进行展平操作。如果指定，必须是int32或int64类型。默认值：None。

    **返回：**

    Tensor或包含Tensor对象的元组（ `output` 、 `idx` 、 `counts` ）。 

    - `output` 为去重后的输出，与 `x` 具有相同的数据类型。
    - 如果 `return_idx` 为 True，则返回张量 `idx` ，shape与 `x` 相同，表示每个去重元素在输入中所在的连续序列的末尾位置的索引。
    - 如果 `return_counts` 为 True，则返回张量 `counts` ，表示每个去重元素在输入中所在的连续序列的计数。

    **异常：**

    - **TypeError** - `x` 不是Tensor。
    - **RuntimeError** – `axis` 不在 `[-ndim, ndim-1]` 范围内。
