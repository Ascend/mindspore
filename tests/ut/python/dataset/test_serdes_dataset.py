# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""
Testing dataset serialize and deserialize in DE
"""
import filecmp
import glob
import json
import os
import pytest

import numpy as np

import mindspore.common.dtype as mstype
import mindspore.dataset as ds
import mindspore.dataset.transforms as transforms
import mindspore.dataset.vision as vision
from mindspore import log as logger
from mindspore.dataset.vision import Inter
from util import config_get_set_num_parallel_workers, config_get_set_seed


def test_serdes_imagefolder_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with dataset pipeline that simulates ResNet50
    Expectation: Output verified for multiple deserialized pipelines
    """
    data_dir = "../data/dataset/testPK/data"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    # define data augmentation parameters
    rescale = 1.0 / 255.0
    shift = 0.0
    resize_height, resize_width = 224, 224
    weights = [1.0, 0.1, 0.02, 0.3, 0.4, 0.05, 1.2, 0.13, 0.14, 0.015, 0.16, 1.1]

    # Constructing DE pipeline
    sampler = ds.WeightedRandomSampler(weights, 11)
    child_sampler = ds.SequentialSampler()
    sampler.add_child(child_sampler)
    data1 = ds.ImageFolderDataset(data_dir, sampler=sampler)
    data1 = data1.repeat(1)
    data1 = data1.map(operations=[vision.Decode()], input_columns=["image"])
    rescale_op = vision.Rescale(rescale, shift)

    resize_op = vision.Resize((resize_height, resize_width), Inter.LINEAR)
    data1 = data1.map(operations=[rescale_op, resize_op], input_columns=["image"])
    data1_1 = ds.TFRecordDataset(["../data/dataset/testTFTestAllTypes/test.data"], num_samples=6).batch(2).repeat(10)
    data1 = data1.zip(data1_1)

    # Serialize the dataset pre-processing pipeline.
    # data1 should still work after saving.
    ds.serialize(data1, "imagenet_dataset_pipeline.json")
    ds1_dict = ds.serialize(data1)
    assert validate_jsonfile("imagenet_dataset_pipeline.json") is True

    # Print the serialized pipeline to stdout
    ds.show(data1)

    # Deserialize the serialized json file
    data2 = ds.deserialize(json_filepath="imagenet_dataset_pipeline.json")

    # Serialize the pipeline we just deserialized.
    # The content of the json file should be the same to the previous serialize.
    ds.serialize(data2, "imagenet_dataset_pipeline_1.json")
    assert validate_jsonfile("imagenet_dataset_pipeline_1.json") is True
    assert filecmp.cmp('imagenet_dataset_pipeline.json', 'imagenet_dataset_pipeline_1.json')
    assert data1.get_dataset_size() == data2.get_dataset_size()

    # Deserialize the latest json file again
    data3 = ds.deserialize(json_filepath="imagenet_dataset_pipeline_1.json")
    data4 = ds.deserialize(input_dict=ds1_dict)
    num_samples = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2, item3, item4 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                                          data2.create_dict_iterator(num_epochs=1, output_numpy=True),
                                          data3.create_dict_iterator(num_epochs=1, output_numpy=True),
                                          data4.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        np.testing.assert_array_equal(item1['image'], item3['image'])
        np.testing.assert_array_equal(item1['label'], item2['label'])
        np.testing.assert_array_equal(item1['label'], item3['label'])
        np.testing.assert_array_equal(item3['image'], item4['image'])
        np.testing.assert_array_equal(item3['label'], item4['label'])
        num_samples += 1

    logger.info("Number of data in data1: {}".format(num_samples))
    assert num_samples == 11

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    # Remove the generated json file
    if remove_json_files:
        delete_json_files("imagenet_dataset_pipeline")


def test_serdes_mnist_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with MnistDataset pipeline
    Expectation: Output verified for multiple deserialized pipelines
    """
    data_dir = "../data/dataset/testMnistData"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.MnistDataset(data_dir, num_samples=100)
    one_hot_encode = transforms.OneHot(10)  # num_classes is input argument
    data1 = data1.map(operations=one_hot_encode, input_columns="label")

    # batch_size is input argument
    data1 = data1.batch(batch_size=10, drop_remainder=True)

    ds.serialize(data1, "mnist_dataset_pipeline.json")
    assert validate_jsonfile("mnist_dataset_pipeline.json") is True

    data2 = ds.deserialize(json_filepath="mnist_dataset_pipeline.json")
    ds.serialize(data2, "mnist_dataset_pipeline_1.json")
    assert validate_jsonfile("mnist_dataset_pipeline_1.json") is True
    assert filecmp.cmp('mnist_dataset_pipeline.json', 'mnist_dataset_pipeline_1.json')

    data3 = ds.deserialize(json_filepath="mnist_dataset_pipeline_1.json")

    num = 0
    for data1, data2, data3 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                                   data2.create_dict_iterator(num_epochs=1, output_numpy=True),
                                   data3.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(data1['image'], data2['image'])
        np.testing.assert_array_equal(data1['image'], data3['image'])
        np.testing.assert_array_equal(data1['label'], data2['label'])
        np.testing.assert_array_equal(data1['label'], data3['label'])
        num += 1

    logger.info("mnist total num samples is {}".format(str(num)))
    assert num == 10

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("mnist_dataset_pipeline")


def test_serdes_cifar10_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with Cifar10Dataset pipeline
    Expectation: Output verified for multiple deserialized pipelines
    """
    data_dir = "../data/dataset/testCifar10Data"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.Cifar10Dataset(data_dir, num_samples=10, shuffle=False)
    data1 = data1.take(6)

    trans = [
        vision.RandomCrop((32, 32), (4, 4, 4, 4)),
        vision.Resize((224, 224)),
        vision.Rescale(1.0 / 255.0, 0.0),
        vision.Normalize([0.4914, 0.4822, 0.4465], [0.2023, 0.1994, 0.2010], True),
        vision.HWC2CHW()
    ]

    type_cast_op = transforms.TypeCast(mstype.int32)
    data1 = data1.map(operations=type_cast_op, input_columns="label")
    data1 = data1.map(operations=trans, input_columns="image")
    data1 = data1.batch(3, drop_remainder=True)
    data1 = data1.repeat(1)
    # json files are needed for create iterator, remove_json_files = False
    data2 = util_check_serialize_deserialize_file(data1, "cifar10_dataset_pipeline", False)
    num_samples = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_samples += 1

    assert num_samples == 2

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("cifar10_dataset_pipeline")


def test_serdes_celeba_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with CelebADataset pipeline
    Expectation: Output verified for multiple deserialized pipelines
    """
    data_dir = "../data/dataset/testCelebAData/"
    data1 = ds.CelebADataset(data_dir, decode=True, num_shards=1, shard_id=0)
    # define map operations
    data1 = data1.repeat(2)
    center_crop = vision.CenterCrop((80, 80))
    pad_op = vision.Pad(20, fill_value=(20, 20, 20))
    data1 = data1.map(operations=[center_crop, pad_op], input_columns=["image"], num_parallel_workers=8)
    # json files are needed for create iterator, remove_json_files = False
    data2 = util_check_serialize_deserialize_file(data1, "celeba_dataset_pipeline", False)

    num_samples = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_samples += 1

    assert num_samples == 8
    if remove_json_files:
        delete_json_files("celeba_dataset_pipeline")


def test_serdes_csv_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with CSVDataset pipeline
    Expectation: Output verified for multiple deserialized pipelines
    """
    data_dir = "../data/dataset/testCSV/1.csv"
    data1 = ds.CSVDataset(
        data_dir,
        column_defaults=["1", "2", "3", "4"],
        column_names=['col1', 'col2', 'col3', 'col4'],
        shuffle=False)
    columns = ["col1", "col4", "col2"]
    data1 = data1.project(columns=columns)
    # json files are needed for create iterator, remove_json_files = False
    data2 = util_check_serialize_deserialize_file(data1, "csv_dataset_pipeline", False)

    num_samples = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['col1'], item2['col1'])
        np.testing.assert_array_equal(item1['col2'], item2['col2'])
        np.testing.assert_array_equal(item1['col4'], item2['col4'])
        num_samples += 1

    assert num_samples == 3
    if remove_json_files:
        delete_json_files("csv_dataset_pipeline")


def test_serdes_voc_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with VOCDataset pipeline
    Expectation: Output verified for multiple deserialized pipelines
    """
    data_dir = "../data/dataset/testVOC2012"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    # define map operations
    random_color_adjust_op = vision.RandomColorAdjust(brightness=(0.5, 0.5))
    random_rotation_op = vision.RandomRotation((0, 90), expand=True, resample=Inter.BILINEAR, center=(50, 50),
                                               fill_value=150)

    data1 = ds.VOCDataset(data_dir, task="Detection", usage="train", decode=True)
    data1 = data1.map(operations=random_color_adjust_op, input_columns=["image"])
    data1 = data1.map(operations=random_rotation_op, input_columns=["image"])
    data1 = data1.skip(2)
    # json files are needed for create iterator, remove_json_files = False
    data2 = util_check_serialize_deserialize_file(data1, "voc_dataset_pipeline", False)

    num_samples = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_samples += 1

    assert num_samples == 7

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("voc_dataset_pipeline")


def test_serdes_zip_dataset(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize with zipped pipeline
    Expectation: Output verified for multiple deserialized pipelines
    """
    files = ["../data/dataset/testTFTestAllTypes/test.data"]
    schema_file = "../data/dataset/testTFTestAllTypes/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    ds0 = ds.TFRecordDataset(files, schema=schema_file, shuffle=ds.Shuffle.GLOBAL)
    data1 = ds.TFRecordDataset(files, schema=schema_file, shuffle=ds.Shuffle.GLOBAL)
    data2 = ds.TFRecordDataset(files, schema=schema_file, shuffle=ds.Shuffle.FILES)
    data2 = data2.shuffle(10000)
    data2 = data2.rename(input_columns=["col_sint16", "col_sint32", "col_sint64", "col_float",
                                        "col_1d", "col_2d", "col_3d", "col_binary"],
                         output_columns=["column_sint16", "column_sint32", "column_sint64", "column_float",
                                         "column_1d", "column_2d", "column_3d", "column_binary"])
    data3 = ds.zip((data1, data2))
    ds.serialize(data3, "zip_dataset_pipeline.json")
    assert validate_jsonfile("zip_dataset_pipeline.json") is True
    assert validate_jsonfile("zip_dataset_pipeline_typo.json") is False

    data4 = ds.deserialize(json_filepath="zip_dataset_pipeline.json")
    ds.serialize(data4, "zip_dataset_pipeline_1.json")
    assert validate_jsonfile("zip_dataset_pipeline_1.json") is True
    assert filecmp.cmp('zip_dataset_pipeline.json', 'zip_dataset_pipeline_1.json')

    rows = 0
    for d0, d3, d4 in zip(ds0.create_tuple_iterator(num_epochs=1, output_numpy=True),
                          data3.create_tuple_iterator(num_epochs=1, output_numpy=True),
                          data4.create_tuple_iterator(num_epochs=1, output_numpy=True)):
        num_cols = len(d0)
        offset = 0
        for t1 in d0:
            np.testing.assert_array_equal(t1, d3[offset])
            np.testing.assert_array_equal(t1, d3[offset + num_cols])
            np.testing.assert_array_equal(t1, d4[offset])
            np.testing.assert_array_equal(t1, d4[offset + num_cols])
            offset += 1
        rows += 1
    assert rows == 12

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("zip_dataset_pipeline")


def test_serdes_random_crop():
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipeline with RandomCrop op
    Expectation: Output verified for multiple deserialized pipelines
    """
    logger.info("test_random_crop")
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_dir = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    # First dataset
    data1 = ds.TFRecordDataset(data_dir, schema_dir, columns_list=["image"])
    decode_op = vision.Decode()
    random_crop_op = vision.RandomCrop([512, 512], [200, 200, 200, 200])
    data1 = data1.map(operations=decode_op, input_columns="image")
    data1 = data1.map(operations=random_crop_op, input_columns="image")

    # Serializing into Python dictionary
    ds1_dict = ds.serialize(data1)
    # Serializing into json object
    _ = json.dumps(ds1_dict, indent=2)

    # Reconstruct dataset pipeline from its serialized form
    data1_1 = ds.deserialize(input_dict=ds1_dict)

    # Second dataset
    data2 = ds.TFRecordDataset(data_dir, schema_dir, columns_list=["image"])
    data2 = data2.map(operations=decode_op, input_columns="image")

    for item1, item1_1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                                     data1_1.create_dict_iterator(num_epochs=1, output_numpy=True),
                                     data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item1_1['image'])
        _ = item2["image"]

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)


def test_serdes_to_device(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipeline with to_device op
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"
    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    data1 = data1.to_device()
    util_check_serialize_deserialize_file(data1, "transfer_dataset_pipeline", remove_json_files)


def test_serdes_pyvision(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines with Python implementation selected for vision ops
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    transforms1 = [
        vision.Decode(True),
        vision.CenterCrop([32, 32])
    ]
    transforms2 = [
        vision.RandomColorAdjust(),
        vision.FiveCrop(1),
        vision.Grayscale()
    ]
    data1 = data1.map(operations=transforms.Compose(transforms1), input_columns=["image"])
    data1 = data1.map(operations=transforms.RandomApply(transforms2), input_columns=["image"])
    util_check_serialize_deserialize_file(data1, "pyvision_dataset_pipeline", remove_json_files)

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("pyvision_dataset_pipeline")


def test_serdes_pyfunc(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines with Python functions
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data2 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    data2 = data2.map(operations=(lambda x, y, z: (
        np.array(x).flatten().reshape(10, 39),
        np.array(y).flatten().reshape(10, 39),
        np.array(z).flatten().reshape(10, 1)
    )))
    ds.serialize(data2, "pyfunc_dataset_pipeline.json")
    assert validate_jsonfile("pyfunc_dataset_pipeline.json") is True

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("pyfunc_dataset_pipeline")


def test_serdes_inter_mixed_map(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines in which each map op has the same
        implementation (Python or C++) of ops
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    # The following map op uses Python implementation of ops
    data1 = data1.map(operations=[vision.Decode(True), vision.CenterCrop([24, 24])], input_columns=["image"])
    # The following map op uses C++ implementation of ToTensor op
    data1 = data1.map(operations=[vision.ToTensor()], input_columns=["image"])
    # The following map op uses C++ implementation of ops
    data1 = data1.map(operations=[vision.HorizontalFlip(), vision.VerticalFlip()], input_columns=["image"])
    # The following map op uses Python implementation of ops
    data1 = data1.map(operations=[vision.ToPIL(), vision.FiveCrop((18, 22))], input_columns=["image"])

    util_check_serialize_deserialize_file(data1, "inter_mixed_map_pipeline", remove_json_files)

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("inter_mixed_map_pipeline")


def test_serdes_intra_mixed_py2c_map(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines in which each map op has a mix of Python implementation
        then C++ implementation of ops
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    # The following map op uses mixed implementation of ops:
    # - Decode - Python implementation
    # - CenterCrop - Python Implementation
    # - ToTensor - C++ implementation
    # - RandonHorizontalFlip - C++ implementation
    # - VerticalFlip - C++ implementation
    transforms_list = [vision.Decode(True),
                       vision.CenterCrop([24, 24]),
                       vision.ToTensor(),
                       vision.RandomHorizontalFlip(),
                       vision.VerticalFlip()]
    data1 = data1.map(operations=transforms_list, input_columns=["image"])
    data2 = util_check_serialize_deserialize_file(data1, "intra_mixed_py2c_map_pipeline", False)

    num_itr = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_itr += 1
    assert num_itr == 3

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("intra_mixed_py2c_map_pipeline")


def test_serdes_intra_mixed_c2py_map(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines in which each map op has a mix of C++ implementation
        then Python implementation of ops
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    # The following map op uses mixed implementation of ops:
    # - Decode - C++ implementation
    # - RandomSolarize - C++ implementation
    # - ToPIL - Python Implementation
    # - CenterCrop - Python Implementation
    transforms_list = [vision.Decode(),
                       vision.RandomSolarize((0, 127)),
                       vision.ToPIL(),
                       vision.CenterCrop([64, 64])]
    data1 = data1.map(operations=transforms_list, input_columns=["image"])
    data2 = util_check_serialize_deserialize_file(data1, "intra_mixed_c2py_map_pipeline", False)

    num_itr = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_itr += 1
    assert num_itr == 3

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("intra_mixed_c2py_map_pipeline")


def test_serdes_totensor_normalize(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines in which each map op has common scenario with
        ToTensor and Normalize ops
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    # The following map op uses mixed implementation of ops:
    # - Decode - Python implementation
    # - CenterCrop - Python Implementation
    # - ToTensor - C++ implementation
    # - Normalize - C++ implementation
    transforms_list = [vision.Decode(True),
                       vision.CenterCrop([30, 50]),
                       vision.ToTensor(),
                       vision.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225], is_hwc=False)]
    data1 = data1.map(operations=transforms_list, input_columns=["image"])
    data2 = util_check_serialize_deserialize_file(data1, "totensor_normalize_pipeline", False)

    num_itr = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_itr += 1
    assert num_itr == 3

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("totensor_normalize_pipeline")


def test_serdes_tonumpy(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines with ToNumpy op
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"

    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    # The following map op uses mixed implementation of ops:
    # - Decode - Python implementation
    # - CenterCrop - Python Implementation
    # - ToNumpy - C++ implementation set
    # - Crop - C++ implementation
    transforms_list = [vision.Decode(to_pil=True),
                       vision.CenterCrop((200, 300)),
                       vision.ToNumpy(),
                       vision.Crop([5, 5], [40, 60])]
    data1 = data1.map(operations=transforms_list, input_columns=["image"])
    data2 = util_check_serialize_deserialize_file(data1, "tonumpy_pipeline", False)

    num_itr = 0
    # Iterate and compare the data in the original pipeline (data1) against the deserialized pipeline (data2)
    for item1, item2 in zip(data1.create_dict_iterator(num_epochs=1, output_numpy=True),
                            data2.create_dict_iterator(num_epochs=1, output_numpy=True)):
        np.testing.assert_array_equal(item1['image'], item2['image'])
        num_itr += 1
    assert num_itr == 3

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)

    if remove_json_files:
        delete_json_files("tonumpy_pipeline")


def test_serdes_uniform_augment(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipeline with UniformAugment op
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """
    original_seed = config_get_set_seed(1)
    original_num_parallel_workers = config_get_set_num_parallel_workers(1)

    data_dir = "../data/dataset/testPK/data"
    data = ds.ImageFolderDataset(dataset_dir=data_dir, shuffle=False)

    transforms_ua = [vision.RandomHorizontalFlip(),
                     vision.RandomVerticalFlip(),
                     vision.RandomColor(),
                     vision.RandomSharpness(),
                     vision.Invert(),
                     vision.AutoContrast(),
                     vision.Equalize()]
    transforms_all = [vision.Decode(), vision.Resize(size=[224, 224]),
                      vision.UniformAugment(transforms=transforms_ua, num_ops=5)]
    data = data.map(operations=transforms_all, input_columns="image", num_parallel_workers=1)
    util_check_serialize_deserialize_file(data, "uniform_augment_pipeline", remove_json_files)

    # Restore configuration
    ds.config.set_seed(original_seed)
    ds.config.set_num_parallel_workers(original_num_parallel_workers)


def skip_test_serdes_fill(remove_json_files=True):
    """
    Feature: Serialize and Deserialize Support
    Description: Test serialize and deserialize on pipelines with Fill op
    Expectation: Serialized versus Deserialized+reserialized pipeline output verified
    """

    def gen():
        yield (np.array([4, 5, 6, 7], dtype=np.int32),)

    data = ds.GeneratorDataset(gen, column_names=["col"])
    fill_op = transforms.Fill(3)

    data = data.map(operations=fill_op, input_columns=["col"])
    expected = np.array([3, 3, 3, 3], dtype=np.int32)
    for data_row in data:
        np.testing.assert_array_equal(data_row[0].asnumpy(), expected)

    util_check_serialize_deserialize_file(data, "fill_pipeline", remove_json_files)


def test_serdes_exception():
    """
    Feature: Serialize and Deserialize Support
    Description: Test exception cases
    Expectation: Correct error is verified
    """
    data_dir = ["../data/dataset/test_tf_file_3_images/train-0000-of-0001.data"]
    schema_file = "../data/dataset/test_tf_file_3_images/datasetSchema.json"
    data1 = ds.TFRecordDataset(data_dir, schema_file, columns_list=["image", "label"], shuffle=False)
    data1 = data1.filter(input_columns=["image", "label"], predicate=lambda data: data < 11, num_parallel_workers=4)
    data1_json = ds.serialize(data1)
    with pytest.raises(RuntimeError) as msg:
        data2 = ds.deserialize(input_dict=data1_json)
        ds.serialize(data2, "filter_dataset_fail.json")
    assert "Invalid data, unsupported operation type: Filter" in str(msg)
    delete_json_files("filter_dataset_fail")


def util_check_serialize_deserialize_file(data_orig, filename, remove_json_files):
    """
    Utility function for testing serdes files. It is to check if a json file is indeed created with correct name
    after serializing and if it remains the same after repeatedly saving and loading.
    :param data_orig: original data pipeline to be serialized
    :param filename: filename to be saved as json format
    :param remove_json_files: whether to remove the json file after testing
    :return: The data pipeline after serializing and deserializing using the original pipeline
    """
    file1 = filename + ".json"
    file2 = filename + "_1.json"
    ds.serialize(data_orig, file1)
    assert validate_jsonfile(file1) is True
    assert validate_jsonfile("wrong_name.json") is False

    data_changed = ds.deserialize(json_filepath=file1)
    ds.serialize(data_changed, file2)
    assert validate_jsonfile(file2) is True
    assert filecmp.cmp(file1, file2, shallow=False)

    # Remove the generated json file
    if remove_json_files:
        delete_json_files(filename)
    return data_changed


def validate_jsonfile(filepath):
    try:
        file_exist = os.path.exists(filepath)
        with open(filepath, 'r') as jfile:
            loaded_json = json.load(jfile)
    except IOError:
        return False
    return file_exist and isinstance(loaded_json, dict)


def delete_json_files(filename):
    file_list = glob.glob(filename + '.json') + glob.glob(filename + '_1.json')
    for f in file_list:
        try:
            os.remove(f)
        except IOError:
            logger.info("Error while deleting: {}".format(f))


if __name__ == '__main__':
    test_serdes_imagefolder_dataset()
    test_serdes_mnist_dataset()
    test_serdes_cifar10_dataset()
    test_serdes_celeba_dataset()
    test_serdes_csv_dataset()
    test_serdes_voc_dataset()
    test_serdes_zip_dataset()
    test_serdes_random_crop()
    test_serdes_to_device()
    test_serdes_pyvision()
    test_serdes_pyfunc()
    test_serdes_inter_mixed_map()
    test_serdes_intra_mixed_py2c_map()
    test_serdes_intra_mixed_c2py_map()
    test_serdes_totensor_normalize()
    test_serdes_tonumpy()
    test_serdes_uniform_augment()
    skip_test_serdes_fill()
    test_serdes_exception()
