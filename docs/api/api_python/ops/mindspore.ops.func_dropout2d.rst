mindspore.ops.dropout2d
=======================

.. py:function:: mindspore.ops.dropout2d(x, p=0.5)

    在训练期间，以服从伯努利分布的概率 `p` 随机将输入Tensor的某些通道归零。（对于形状为 `NCHW` 的四维Tensor，
    其通道特征图指的是后两维 `HW` 形状的二维特征图）。
    例如，在批处理输入中 :math:`i_th` 批， :math:`j_th` 通道的 `input[i, j]` `2D` Tensor 是一个待处理数据。
    每个通道将会独立依据伯努利分布概率 `p` 来确定是否被清零。
    论文 `Dropout: A Simple Way to Prevent Neural Networks from Overfitting <http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf>`_ 中提出了该技术，并证明其能有效地减少过度拟合，防止神经元共适应。更多详细信息，请参见 `Improving neural networks by preventing co-adaptation of feature detectors <https://arxiv.org/pdf/1207.0580.pdf>`_ 。

    `dropout2d` 可以提高通道特征映射之间的独立性。

    **参数：**

    - **x** (tensor) - 一个形状为 math:`(N, C, H, W)` 的 `4D` Tensor，其中N是批处理大小，`C` 是的通道数，`H` 是特征高度，`W` 是特征宽度。其数据类型应为int8、int16、int32、int64、float16或float32。
    - **p** (float) - 通道的丢弃概率，介于 0 和 1 之间，例如 `p` = 0.8，意味着80%的清零概率。默认值：0.5。

    **返回：**

    Tensor，具有与输入 `x` 相同的形状和数据类型。
    掩码（Tensor），形状与 `x` 相同，数据类型为bool。

    **异常：**

    - **TypeError** - `x` 不是Tensor。
    - **TypeError** - `x` 的数据类型不是int8、int16、int32、int64、float16或float32。
    - **TypeError** - `p` 的数据类型不是float。
    - **ValueError** - `p` 值不在 `[0，1]` 之间。
    - **ValueError** - `x` 的维度不等于4。

