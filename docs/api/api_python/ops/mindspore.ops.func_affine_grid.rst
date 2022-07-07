mindspore.ops.affine_grid
=========================

.. py:function:: mindspore.ops.affine_grid(theta, output_size, align_corners)

    给定一批仿射矩阵 theta，生成 2D 或 3D 流场（采样网格）。

    **参数：**

    - **theta** (Tensor) - 仿射矩阵输入，其形状为 (N, 2, 3) 用于 2D 或 (N, 3, 4) 用于 3D。
    - **output_size** (Tensor) - 目标输出图像大小。 其值为 (N, C, H, W) 用于 2D 或 (N, C, D, H, W) 用于 3D。示例：`Tensor([32, 3, 24, 24], mindspore.int32)`。
    - **align_corners** (bool) - 在几何上，我们将输入的像素视为正方形而不是点。如果设置为True，则极值 -1 和 1 被认为是指输入角像素的中心点。如果设置为False，则它们被认为是指输入角像素的角点，从而使采样与分辨率无关。默认值：False。

    **返回：**

    Tensor，其数据类型与 `theta` 相同，其形状为 (N, H, W, 2) 用于 2D 或 (N, D, H, W, 3) 用于 3D。

    **异常：**

    - **TypeError** - `theta` 或 `output_size` 不是Tensor。
    - **ValueError** - `theta` 的形状不是 (N, 2, 3) 或 (N, 3, 4)。
    - **ValueError** - `output_size` 的维度不是 1，长度不是 4 或 5。
    - **ValueError** - `theta` 的形状是 (N, 2, 3)，`output_size` 的维度却不是4； `theta` 的形状是 (N, 3, 4)，`output_size` 的维度却不是5。
    - **ValueError** - `output_size` 的第一个值不等于 `theta` 的第一维的长度。
