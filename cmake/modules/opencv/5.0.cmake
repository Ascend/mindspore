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

# Set names of each component of OpenCV 5.0-pre
foreach(
  comp
  3d
  alphamat
  aruco
  barcode
  bgsegm
  bioinspired
  calib
  ccalib
  core
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
  julia
  line_descriptor
  mcc
  ml
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
  xphoto
  xstereo)
  set(${_pkg}_${comp}_NAMES
      opencv_${comp}
      opencv_${comp}509
      opencv_${comp}508
      opencv_${comp}507
      opencv_${comp}506
      opencv_${comp}505
      opencv_${comp}504
      opencv_${comp}503
      opencv_${comp}502
      opencv_${comp}501
      opencv_${comp}500)
endforeach()
