mindspore.set_context
======================

.. py:function:: mindspore.set_context(**kwargs)

    设置运行环境的context。

    在运行程序之前，应配置context。如果没有配置，默认情况下将根据设备目标进行自动设置。

    .. note::
        设置属性时，必须输入属性名称。

    某些配置适用于特定的设备，有关详细信息，请参见下表：

    +-------------------------+------------------------------+----------------------------+
    | 功能分类                |    配置参数                  |          硬件平台支持      |
    +=========================+==============================+============================+
    | 系统配置                |   device_id                  |   CPU/GPU/Ascend           |
    |                         +------------------------------+----------------------------+
    |                         |   device_target              |   CPU/GPU/Ascend           |
    |                         +------------------------------+----------------------------+
    |                         |  max_device_memory           |  GPU/Ascend                |
    |                         +------------------------------+----------------------------+
    |                         |  variable_memory_max_size    |  Ascend                    |
    |                         +------------------------------+----------------------------+
    |                         |  mempool_block_size          |  GPU/Ascend                |
    +-------------------------+------------------------------+----------------------------+
    | 调试配置                |  save_graphs                 |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  save_graphs_path            |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  enable_dump                 |  Ascend                    |
    |                         +------------------------------+----------------------------+
    |                         |  save_dump_path              |  Ascend                    |
    |                         +------------------------------+----------------------------+
    |                         |  print_file_path             |  Ascend                    |
    |                         +------------------------------+----------------------------+
    |                         |  env_config_path             |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  precompile_only             |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  reserve_class_name_in_scope |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  pynative_synchronize        |  GPU/Ascend                |
    +-------------------------+------------------------------+----------------------------+
    | 执行控制                |   mode                       |   CPU/GPU/Ascend           |
    |                         +------------------------------+----------------------------+
    |                         |  enable_graph_kernel         |  Ascend/GPU                |
    |                         +------------------------------+----------------------------+
    |                         |  graph_kernel_flags          |  Ascend/GPU                |
    |                         +------------------------------+----------------------------+
    |                         |  enable_reduce_precision     |  Ascend                    |
    |                         +------------------------------+----------------------------+
    |                         |  auto_tune_mode              |  Ascend                    |
    |                         +------------------------------+----------------------------+
    |                         |  check_bprop                 |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  max_call_depth              |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  grad_for_scalar             |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  enable_compile_cache        |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  runtime_num_threads         |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  compile_cache_path          |  CPU/GPU/Ascend            |
    |                         +------------------------------+----------------------------+
    |                         |  disable_format_transform    |  GPU                       |
    +-------------------------+------------------------------+----------------------------+

    **参数：**

    - **device_id** (int) - 表示目标设备的ID，其值必须在[0, device_num_per_host-1]范围中，且 `device_num_per_host` 的值不应超过4096。默认值：0。
    - **device_target** (str) - 表示待运行的目标设备，支持'Ascend'、'GPU'和'CPU'。如果未设置此参数，则使用MindSpore包对应的后端设备。
    - **max_device_memory** (str) - 设置设备可用的最大内存。格式为"xxGB"。默认值：1024GB。实际使用的内存大小是设备的可用内存和 `max_device_memory` 值中的最小值。
    - **variable_memory_max_size** (str) - 此参数已弃用，将被删除。请使用 `max_device_memory` 。
    - **mempool_block_size** (str) - 设置PyNative模式下设备内存池的块大小。格式为“xxGB”。默认值：1GB。最小值是1GB。实际使用的内存池块大小是设备的可用内存和 `mempool_block_size` 值中的最小值。
    - **save_graphs** (bool) - 表示是否保存计算图。默认值：False。当 `save_graphs` 属性设为True时， `save_graphs_path` 属性用于设置中间编译图的存储路径。默认情况下，计算图保存在当前目录下。
    - **save_graphs_path** (str) - 表示保存计算图的路径。默认值："."。如果指定的目录不存在，系统将自动创建该目录。在分布式训练中，图形将被保存到 `save_graphs_path/rank_${rank_id}/` 目录下。 `rank_id` 为集群中当前设备的ID。
    - **enable_dump** (bool) - 此参数已弃用，将在下一版本中删除。
    - **save_dump_path** (str) - 此参数已弃用，将在下一版本中删除。
    - **print_file_path** (str)：该路径用于保存打印数据。使用时 :class:`mindspore.ops.Print` 可以打印输入的张量或字符串信息，使用方法 :func:`mindspore.parse_print` 解析保存的文件。如果设置了此参数，打印数据保存到文件，未设置将显示到屏幕。如果保存的文件已经存在，则将添加时间戳后缀到文件中。将数据保存到文件解决了屏幕打印中的数据丢失问题, 如果未设置，将报告错误:"prompt to set the upper absolute path"。
    - **env_config_path** (str) - 通过 `context.set_context(env_config_path="./mindspore_config.json")` 来设置MindSpore环境配置文件路径。

      配置Running Data Recorder：

      - **enable**：表示在发生故障时是否启用Running Data Recorder去收集和保存训练中的关键数据。设置为True时，将打开Running Data Recorder。设置为False时，将关闭Running Data Recorder。
      - **mode**：指定在GRAPH_MODE(0)还是PYNATIVE_MODE(1)下运行，两种模式均支持所有后端。默认值：GRAPH_MODE(0)。
      - **path**：设置Running Data Recorder保存数据的路径。当前路径必须是一个绝对路径。

      内存重用：

      - **mem_Reuse**：表示内存复用功能是否打开。设置为True时，将打开内存复用功能。设置为False时，将关闭内存复用功能。
        有关running data recoder和内存复用配置详细信息，请查看 `配置RDR和内存复用 <https://www.mindspore.cn/tutorials/experts/zh-CN/master/debug/custom_debug.html>`_。


    - **precompile_only** (bool) - 表示是否仅预编译网络。默认值：False。设置为True时，仅编译网络，而不执行网络。
    - **reserve_class_name_in_scope** (bool) - 表示是否将网络类名称保存到所属ScopeName中。默认值：True。每个节点都有一个ScopeName。子节点的ScopeName是其父节点。如果 `reserve_class_name_in_scope` 设置为True，则类名将保存在ScopeName中的关键字“net-”之后。例如：

      Default/net-Net1/net-Net2 (reserve_class_name_in_scope=True)

      Default/net/net (reserve_class_name_in_scope=False)

    - **pynative_synchronize** (bool) - 表示是否在PyNative模式下启动设备同步执行。默认值：False。设置为False时，将在设备上异步执行算子。当算子执行出错时，将无法定位特定错误脚本代码的位置。当设置为True时，将在设备上同步执行算子。这将降低程序的执行性能。此时，当算子执行出错时，可以根据错误的调用栈来定位错误脚本代码的位置。
    - **mode** (int) - 表示在GRAPH_MODE(0)或PYNATIVE_MODE(1)模式中的运行。默认值：GRAPH_MODE(0)。GRAPH_MODE或PYNATIVE_MODE可以通过 `mode` 属性设置，两种模式都支持所有后端。默认模式为GRAPH_MODE。
    - **enable_graph_kernel** (bool) - 表示开启图算融合去优化网络执行性能。默认值：False。如果 `enable_graph_kernel` 设置为True，则可以启用加速。有关图算融合的详细信息，请查看 `使能图算融合 <https://www.mindspore.cn/docs/zh-CN/master/design/graph_fusion_engine.html>`_ 。
    - **graph_kernel_flags** (str) - 图算融合的优化选项，当与enable_graph_kernel冲突时，它的优先级更高。其仅适用于有经验的用户。例如，context.set_context(graph_kernel_flags="--opt_level=2 --dump_as_text")。一些常用选项：

      - **opt_level**：设置优化级别。默认值：2。当opt_level的值大于0时，启动图算融合。可选值包括：

        - 0：关闭图算融合。
        - 1：启动算子的基本融合。
        - 2：包括级别1的所有优化，并打开更多的优化，如CSE优化算法、算术简化等。
        - 3：包括级别2的所有优化，并打开更多的优化，如SitchingFusion、ParallelFusion等。在某些场景下，该级别的优化激进且不稳定。使用此级别时要小心。

      - **dump_as_text**：将关键过程的详细信息生成文本文件保存到"graph_kernel_dump"目录里。默认值：False。

        有关更多选项，可以参考实现代码。

    - **enable_reduce_precision** (bool) - 表示是否开启降低精度计算。默认值：True。设置为True时，不支持用户指定的精度，且精度将自动更改。设置为False时，如果未指定用例的精度，则会报错并退出。
    - **auto_tune_mode** (str) - 表示算子构建时的自动调整模式，以获得最佳的切分性能。默认值：NO_TUNE。其值必须在['RL', 'GA', 'RL,GA']范围中。

      - RL：强化学习调优。
      - GA：遗传算法调优。
      - RL，GA：当RL和GA优化同时打开时，工具会根据网络模型中的不同算子类型自动选择RL或GA。RL和GA的顺序没有区别。（自动选择）。


      有关启用算子调优工具设置的更多信息，请查看 `使能算子调优工具 <https://www.mindspore.cn/tutorials/experts/zh-CN/master/debug/auto_tune.html>`_。

    - **check_bprop** (bool) - 表示是否检查反向传播节点，以确保反向传播节点输出的形状(shape)和数据类型与输入参数相同。默认值：False。
    - **max_call_depth** (int) - 指定函数调用的最大深度。其值必须为正整数。默认值：1000。当嵌套Cell太深或子图数量太多时，需要设置 `max_call_depth` 参数。系统最大堆栈深度应随着 `max_call_depth` 的调整而设置为更大的值，否则可能会因为系统堆栈溢出而引发 "core dumped" 异常。
    - **grad_for_scalar** (bool)：  表示是否获取标量梯度。默认值：False。当 `grad_for_scalar` 设置为True时，则可以导出函数的标量输入。由于后端目前不支持伸缩操作，所以该接口只支持在前端可推演的简单操作。
    - **enable_compile_cache** (bool) - 表示是否加载或者保存前端编译的图。当 `enable_compile_cache` 被设置为True时，在第一次执行的过程中，一个硬件无关的编译缓存会被生成并且导出为一个MINDIR文件。当该网络被再次执行时，如果 `enable_compile_cache` 仍然为True并且网络脚本没有被更改，那么这个编译缓存会被加载。注意目前只支持有限的Python脚本更改的自动检测，这意味着可能有正确性风险。默认值：False。这是一个实验特性，可能会被更改或者删除。
    - **compile_cache_path** (str) - 保存前端图编译缓存的路径。默认值："."。如果目录不存在，系统会自动创建这个目录。缓存会被保存到如下目录： `compile_cache_path/rank_${rank_id}/` 。 `rank_id` 是集群上当前设备的ID。
    - **runtime_num_threads** (int) - 运行时线程池的线程数控制。 默认值为30。
    - **disable_format_transform** (bool) - 表示是否取消NCHW到NHWC的自动格式转换功能。当fp16的网络性能不如fp32的时，可以设置 `disable_format_transform` 为True，以尝试提高训练性能。默认值：False。

    **异常：**

    **ValueError**：输入key不是上下文中的属性。
