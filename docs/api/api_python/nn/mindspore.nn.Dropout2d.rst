mindspore.nn.Dropout2d
======================

.. py:class:: mindspore.nn.Dropout2d(p=0.5)

    在训练期间，以服从伯努利分布的概率 `p` 随机将输入Tensor的某些通道归零。（对于形状为 `NCHW` 的四维Tensor，其通道特征图指的是后两维 `HW` 形状的二维特征图）。
    例如，在批处理输入中 :math:`i\_th` 批， :math:`j\_th` 通道的 `input[i, j]` `2D` Tensor 是一个待处理数据。
    每个通道将会独立依据伯努利分布概率 `p` 来确定是否被清零。

    `Dropout2d` 可以提高通道特征映射之间的独立性。

    更多参考详见 :func:`mindspore.ops.dropout2d`。
