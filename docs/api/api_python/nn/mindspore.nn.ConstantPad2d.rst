mindspore.nn.ConstantPad2d
==========================

.. py:class:: mindspore.nn.ConstantPad2d(padding, value)

    将给定的常量填充到多维输入数据的最后两维。

    **参数：**

    - **padding** (Union[int, tuple]) - 对输入的最后两维进行填充的大小。如果padding的类型为int，则在输入最后两维的前后均填充 `padding` 大小，如果padding为长度为4的tuple，形如(padding_0, padding_1, padding_2, padding_3)，那么输入 `x` 对应输出的最后一维的shape为 :math:`padding\_0 + x.shape[-1] + padding\_1` ，输入 `x` 对应输出的倒数第二维的shape为 :math:`padding\_2 + x.shape[-2] + padding\_3` ，输出的其余维度与输入保持一致。
    - **value** (Union[int, float]) - 填充值。

    **返回：**

    Tensor，填充后的Tensor。

    **异常：**

    - **TypeError** - `padding` 既不是tuple或者int。
    - **TypeError** - `value` 既不是int，也不是float。
    - **ValueError** - tuple类型的 `padding` 长度大于4或者长度不是2的倍数。
    - **ValueError** - 填充后输出的维度不是正数。
