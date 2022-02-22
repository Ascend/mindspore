# ==============================================================================
#
# Copyright 2022 <Huawei Technologies Co., Ltd>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ==============================================================================

if(NOT "${CMAKE_CUDA_COMPILER}" STREQUAL "")
  set(_with_cuda TRUE)
else()
  set(_with_cuda FALSE)
endif()

set(_comps
    alphamat
    aruco
    barcode
    bgsegm
    bioinspired
    calib3d
    ccalib
    core
    correspondence
    cudaarithm
    cudabgsegm
    cudacodec
    cudafeatures2d
    cudafilters
    cudaimgproc
    cudalegacy
    cudaobjdetect
    cudaoptflow
    cudastereo
    cudawarping
    cudev
    cvv
    datasets
    dnn
    dnn_objdetect
    dnn_superres
    dpm
    face
    features2d
    flann
    freetype
    fuzzy
    gapi
    hdf
    hfs
    highgui
    img_hash
    imgcodecs
    imgproc
    intensity_transform
    line_descriptor
    mcc
    ml
    multiview
    numeric
    objdetect
    optflow
    ovis
    phase_unwrapping
    photo
    plot
    quality
    rapid
    reg
    rgbd
    saliency
    sfm
    shape
    simple_pipeline
    stereo
    stitching
    structured_light
    superres
    surface_matching
    text
    tracking
    video
    videoio
    videostab
    viz
    wechat_qrcode
    xfeatures2d
    ximgproc
    xobjdetect
    xphoto)

# Set names of each component of OpenCV 4.3
foreach(comp ${_comps})
  set(${_pkg}_${comp}_NAMES opencv_${comp} opencv_${comp}430)
endforeach()

set(${_pkg}_alphamat_DEPENDENCIES core imgproc)
set(${_pkg}_aruco_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_barcode_DEPENDENCIES core dnn imgproc)
set(${_pkg}_bgsegm_DEPENDENCIES calib3d core features2d flann imgproc video)
set(${_pkg}_bioinspired_DEPENDENCIES core highgui imgcodecs imgproc videoio)
set(${_pkg}_calib3d_DEPENDENCIES core features2d flann imgproc)
set(${_pkg}_ccalib_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    highgui
    imgcodecs
    imgproc
    videoio)
set(${_pkg}_core_DEPENDENCIES)
set(${_pkg}_cudaarithm_DEPENDENCIES core)
set(${_pkg}_cudabgsegm_DEPENDENCIES calib3d core features2d flann imgproc video)
set(${_pkg}_cudacodec_DEPENDENCIES core imgcodecs imgproc videoio)
set(${_pkg}_cudafeatures2d_DEPENDENCIES
    core
    cudaarithm
    cudafilters
    cudawarping
    features2d
    flann
    imgproc)
set(${_pkg}_cudafilters_DEPENDENCIES core cudaarithm imgproc)
set(${_pkg}_cudaimgproc_DEPENDENCIES core cudaarithm cudafilters imgproc)
set(${_pkg}_cudalegacy_DEPENDENCIES
    calib3d
    core
    cudaarithm
    cudafilters
    cudaimgproc
    features2d
    flann
    imgproc
    objdetect
    video)
set(${_pkg}_cudaobjdetect_DEPENDENCIES
    calib3d
    core
    cudaarithm
    cudafilters
    cudaimgproc
    cudalegacy
    cudawarping
    features2d
    flann
    imgproc
    objdetect
    video)
set(${_pkg}_cudaoptflow_DEPENDENCIES
    calib3d
    core
    cudaarithm
    cudafilters
    cudaimgproc
    cudalegacy
    cudawarping
    features2d
    flann
    imgcodecs
    imgproc
    objdetect
    optflow
    video
    ximgproc)
set(${_pkg}_cudastereo_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_cudawarping_DEPENDENCIES core imgproc)
set(${_pkg}_cvv_DEPENDENCIES core features2d flann imgproc)
set(${_pkg}_datasets_DEPENDENCIES
    core
    dnn
    features2d
    flann
    imgcodecs
    imgproc
    ml
    text)
set(${_pkg}_dnn_DEPENDENCIES core imgproc)
set(${_pkg}_dnn_objdetect_DEPENDENCIES core dnn highgui imgcodecs imgproc videoio)
set(${_pkg}_dnn_superres_DEPENDENCIES core dnn imgproc ml quality)
set(${_pkg}_dpm_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    highgui
    imgcodecs
    imgproc
    objdetect
    videoio)
set(${_pkg}_face_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgproc
    objdetect
    photo)
if(_with_cuda)
  list(APPEND ${_pkg}_face_DEPENDENCIES cudaarithm cudafilters cudaimgproc)
endif()
set(${_pkg}_features2d_DEPENDENCIES core flann imgproc)
set(${_pkg}_flann_DEPENDENCIES core)
set(${_pkg}_freetype_DEPENDENCIES core imgproc)
set(${_pkg}_fuzzy_DEPENDENCIES core imgproc)
set(${_pkg}_gapi_DEPENDENCIES core imgproc)
set(${_pkg}_hdf_DEPENDENCIES core)
set(${_pkg}_hfs_DEPENDENCIES core imgproc)
set(${_pkg}_highgui_DEPENDENCIES core imgcodecs imgproc videoio)
set(${_pkg}_img_hash_DEPENDENCIES core imgproc)
set(${_pkg}_imgcodecs_DEPENDENCIES core imgproc)
set(${_pkg}_imgproc_DEPENDENCIES core)
set(${_pkg}_intensity_transform_DEPENDENCIES core imgproc)
set(${_pkg}_line_descriptor_DEPENDENCIES core features2d flann imgproc)
set(${_pkg}_mcc_DEPENDENCIES calib3d core dnn features2d flann imgproc)
set(${_pkg}_ml_DEPENDENCIES core)
set(${_pkg}_objdetect_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_optflow_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgcodecs
    imgproc
    video
    ximgproc)
set(${_pkg}_ovis_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_phase_unwrapping_DEPENDENCIES core imgproc)
set(${_pkg}_photo_DEPENDENCIES core imgproc)
if(_with_cuda)
  list(APPEND ${_pkg}_photo_DEPENDENCIES cudaarithm cudafilters cudaimgproc)
endif()
set(${_pkg}_plot_DEPENDENCIES core imgproc)
set(${_pkg}_quality_DEPENDENCIES core imgproc ml)
set(${_pkg}_rapid_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_reg_DEPENDENCIES core imgproc)
set(${_pkg}_rgbd_DEPENDENCIES calib3d core features2d flann imgproc viz)
set(${_pkg}_saliency_DEPENDENCIES core features2d flann imgproc)
set(${_pkg}_sfm_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgcodecs
    imgproc
    ml
    shape
    xfeatures2d)
if(_with_cuda)
  list(APPEND ${_pkg}_sfm_DEPENDENCIES cudaarithm)
endif()
set(${_pkg}_shape_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_stereo_DEPENDENCIES
    calib3d
    core
    datasets
    dnn
    features2d
    flann
    highgui
    imgcodecs
    imgproc
    ml
    plot
    text
    tracking
    video
    videoio)
set(${_pkg}_stitching_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgproc
    ml
    objdetect
    shape
    video
    xfeatures2d)
if(_with_cuda)
  list(
    APPEND
    ${_pkg}_stitching_DEPENDENCIES
    cudaarithm
    cudafeatures2d
    cudafilters
    cudaimgproc
    cudalegacy
    cudawarping)
endif()
set(${_pkg}_structured_light_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgproc
    phase_unwrapping
    viz)
set(${_pkg}_superres_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgcodecs
    imgproc
    objdetect
    optflow
    video
    videoio
    ximgproc)
if(_with_cuda)
  list(
    APPEND
    ${_pkg}_superres_DEPENDENCIES
    cudaarithm
    cudacodec
    cudafilters
    cudaimgproc
    cudalegacy
    cudaoptflow
    cudawarping)
endif()
set(${_pkg}_surface_matching_DEPENDENCIES core flann)
set(${_pkg}_text_DEPENDENCIES core dnn features2d flann imgproc ml)
set(${_pkg}_tracking_DEPENDENCIES
    calib3d
    core
    datasets
    dnn
    features2d
    flann
    highgui
    imgcodecs
    imgproc
    ml
    plot
    text
    video
    videoio)
set(${_pkg}_video_DEPENDENCIES calib3d core features2d flann imgproc)
set(${_pkg}_videoio_DEPENDENCIES core imgcodecs imgproc)
set(${_pkg}_videostab_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgcodecs
    imgproc
    objdetect
    optflow
    photo
    video
    videoio
    ximgproc)
if(_with_cuda)
  list(
    APPEND
    ${_pkg}_videostab_DEPENDENCIES
    cudaarithm
    cudafilters
    cudaimgproc
    cudalegacy
    cudaoptflow
    cudawarping)
endif()
set(${_pkg}_viz_DEPENDENCIES core)
set(${_pkg}_wechat_qrcode_DEPENDENCIES core dnn imgproc)
set(${_pkg}_xfeatures2d_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgproc
    ml
    shape)
if(_with_cuda)
  list(APPEND ${_pkg}_xfeatures2d_DEPENDENCIES cudaarithm)
endif()
set(${_pkg}_ximgproc_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgcodecs
    imgproc
    video)
set(${_pkg}_xobjdetect_DEPENDENCIES
    calib3d
    core
    features2d
    flann
    imgcodecs
    imgproc
    objdetect)
set(${_pkg}_xphoto_DEPENDENCIES core imgproc photo)
if(_with_cuda)
  list(APPEND ${_pkg}_xphoto_DEPENDENCIES cudaarithm cudafilters cudaimgproc)
endif()

if(_with_cuda)
  foreach(comp ${_comps})
    list(PREPEND ${_pkg}_${comp}_NAMES cudev)
  endforeach()
endif()
