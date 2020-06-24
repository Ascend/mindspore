# Copyright 2020 Huawei Technologies Co., Ltd
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
# ==============================================================================
import numpy as np

import mindspore.dataset as ds


def test_map_reorder_pass_0():
    def generator_mc(maxid=1):
        for _ in range(maxid):
            yield (np.array([0]), np.array([1]))

    # Generator -> Map
    data0 = ds.GeneratorDataset(generator_mc, ["col0", "col1"])

    data0 = data0.map(input_columns="col0", output_columns="out", columns_order=["col1", "out"],
                      operations=(lambda x: x))

    for item in data0.create_tuple_iterator():  # each data is a dictionary
        assert item == [np.array(1), np.array(0)]


def test_map_reorder_pass_1():
    def generator_mc(maxid=1):
        for _ in range(maxid):
            yield (np.array([0]), np.array([1]), np.array([2]))

    # Three map and zip
    data0 = ds.GeneratorDataset(generator_mc, ["a0", "a1", "a2"])
    data0 = data0.map(input_columns="a0", columns_order=["a2", "a1", "a0"], operations=(lambda x: x))
    data1 = ds.GeneratorDataset(generator_mc, ["b0", "b1", "b2"])
    data1 = data1.map(input_columns="b0", columns_order=["b1", "b2", "b0"], operations=(lambda x: x))
    data2 = ds.zip((data0, data1))
    data2 = data2.map(input_columns="a0", columns_order=["b2", "a2", "b1", "a1", "b0", "a0"], operations=(lambda x: x))

    for item in data2.create_tuple_iterator():
        assert item == [np.array(2), np.array(2), np.array(1), np.array(1), np.array(0), np.array(0)]


def test_global_shuffle_pass():

    FILES = ["../data/dataset/testTFTestAllTypes/test.data"]
    SCHEMA_FILE = "../data/dataset/testTFTestAllTypes/datasetSchema.json"

    ds.config.set_seed(1)
    data1 = ds.TFRecordDataset(FILES, schema=SCHEMA_FILE, shuffle=ds.Shuffle.GLOBAL)
    data2 = ds.TFRecordDataset(FILES, schema=SCHEMA_FILE, shuffle=ds.Shuffle.FILES)
    data2 = data2.shuffle(10000)

    for d1, d2 in zip(data1, data2):
        for t1, t2 in zip(d1, d2):
            assert np.array_equal(t1, t2)

    ds.config.set_seed(1)
    DATA_ALL_FILE = "../data/dataset/testTextFileDataset/*"
    data1 = ds.TextFileDataset(DATA_ALL_FILE, shuffle=ds.Shuffle.GLOBAL)
    data2 = ds.TextFileDataset(DATA_ALL_FILE, shuffle=ds.Shuffle.FILES)
    data2 = data2.shuffle(10000)

    for d1, d2 in zip(data1, data2):
        for t1, t2 in zip(d1, d2):
            assert np.array_equal(t1, t2)

    ds.config.set_seed(1)
    TRAIN_FILE = '../data/dataset/testCLUE/afqmc/train.json'
    data1 = ds.CLUEDataset(TRAIN_FILE, task='AFQMC', usage='train', shuffle=ds.Shuffle.GLOBAL)
    data2 = ds.CLUEDataset(TRAIN_FILE, task='AFQMC', usage='train', shuffle=ds.Shuffle.FILES)
    data2 = data2.shuffle(10000)

    for d1, d2 in zip(data1, data2):
        for t1, t2 in zip(d1, d2):
            assert np.array_equal(t1, t2)


if __name__ == "__main__":
    test_map_reorder_pass_0()
    test_map_reorder_pass_1()
    test_global_shuffle_pass()
