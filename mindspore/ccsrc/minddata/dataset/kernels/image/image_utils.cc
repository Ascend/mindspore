/**
 * Copyright 2019-2022 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "minddata/dataset/kernels/image/image_utils.h"
#include <opencv2/imgproc/types_c.h>
#include <algorithm>
#include <limits>
#include <string>
#include <vector>
#include <stdexcept>
#include <opencv2/imgcodecs.hpp>
#include "utils/ms_utils.h"
#include "minddata/dataset/core/cv_tensor.h"
#include "minddata/dataset/core/tensor.h"
#include "minddata/dataset/core/tensor_shape.h"
#include "minddata/dataset/include/dataset/constants.h"
#include "minddata/dataset/kernels/image/math_utils.h"
#include "minddata/dataset/kernels/image/resize_cubic_op.h"
#include "minddata/dataset/kernels/data/data_utils.h"

const int32_t MAX_INT_PRECISION = 16777216;  // float int precision is 16777216
const int32_t DOUBLING_FACTOR = 2;           // used as multiplier with MAX_INT_PRECISION
const int32_t DEFAULT_NUM_HEIGHT = 1;
const int32_t DEFAULT_NUM_WIDTH = 1;

namespace mindspore {
namespace dataset {
int GetCVInterpolationMode(InterpolationMode mode) {
  switch (mode) {
    case InterpolationMode::kLinear:
      return static_cast<int>(cv::InterpolationFlags::INTER_LINEAR);
    case InterpolationMode::kCubic:
      return static_cast<int>(cv::InterpolationFlags::INTER_CUBIC);
    case InterpolationMode::kArea:
      return static_cast<int>(cv::InterpolationFlags::INTER_AREA);
    case InterpolationMode::kNearestNeighbour:
      return static_cast<int>(cv::InterpolationFlags::INTER_NEAREST);
    default:
      return static_cast<int>(cv::InterpolationFlags::INTER_LINEAR);
  }
}

int GetCVBorderType(BorderType type) {
  switch (type) {
    case BorderType::kConstant:
      return static_cast<int>(cv::BorderTypes::BORDER_CONSTANT);
    case BorderType::kEdge:
      return static_cast<int>(cv::BorderTypes::BORDER_REPLICATE);
    case BorderType::kReflect:
      return static_cast<int>(cv::BorderTypes::BORDER_REFLECT101);
    case BorderType::kSymmetric:
      return static_cast<int>(cv::BorderTypes::BORDER_REFLECT);
    default:
      return static_cast<int>(cv::BorderTypes::BORDER_CONSTANT);
  }
}

Status GetConvertShape(ConvertMode convert_mode, const std::shared_ptr<CVTensor> &input_cv,
                       std::vector<dsize_t> *node) {
  std::vector<ConvertMode> one_channels = {ConvertMode::COLOR_BGR2GRAY, ConvertMode::COLOR_RGB2GRAY,
                                           ConvertMode::COLOR_BGRA2GRAY, ConvertMode::COLOR_RGBA2GRAY};
  std::vector<ConvertMode> three_channels = {
    ConvertMode::COLOR_BGRA2BGR, ConvertMode::COLOR_RGBA2RGB, ConvertMode::COLOR_RGBA2BGR, ConvertMode::COLOR_BGRA2RGB,
    ConvertMode::COLOR_BGR2RGB,  ConvertMode::COLOR_RGB2BGR,  ConvertMode::COLOR_GRAY2BGR, ConvertMode::COLOR_GRAY2RGB};
  std::vector<ConvertMode> four_channels = {ConvertMode::COLOR_BGR2BGRA,  ConvertMode::COLOR_RGB2RGBA,
                                            ConvertMode::COLOR_BGR2RGBA,  ConvertMode::COLOR_RGB2BGRA,
                                            ConvertMode::COLOR_BGRA2RGBA, ConvertMode::COLOR_RGBA2BGRA,
                                            ConvertMode::COLOR_GRAY2BGRA, ConvertMode::COLOR_GRAY2RGBA};
  if (std::find(three_channels.begin(), three_channels.end(), convert_mode) != three_channels.end()) {
    *node = {input_cv->shape()[0], input_cv->shape()[1], 3};
  } else if (std::find(four_channels.begin(), four_channels.end(), convert_mode) != four_channels.end()) {
    *node = {input_cv->shape()[0], input_cv->shape()[1], 4};
  } else if (std::find(one_channels.begin(), one_channels.end(), convert_mode) != one_channels.end()) {
    *node = {input_cv->shape()[0], input_cv->shape()[1]};
  } else {
    RETURN_STATUS_UNEXPECTED(
      "The mode of image channel conversion must be in ConvertMode, which mainly includes "
      "conversion between RGB, BGR, GRAY, RGBA etc.");
  }
  return Status::OK();
}

Status ImageNumChannels(const std::shared_ptr<Tensor> &image, dsize_t *channels) {
  if (image->Rank() < kMinImageRank) {
    RETURN_STATUS_UNEXPECTED(
      "GetImageNumChannels: invalid parameter, image should have at least two dimensions, but got: " +
      std::to_string(image->Rank()));
  } else if (image->Rank() == kMinImageRank) {
    *channels = 1;
  } else {
    *channels = image->shape()[-1];
  }
  return Status::OK();
}

Status ImageSize(const std::shared_ptr<Tensor> &image, std::vector<dsize_t> *size) {
  RETURN_UNEXPECTED_IF_NULL(size);
  *size = std::vector<dsize_t>(kMinImageRank);
  if (image->Rank() < kMinImageRank) {
    RETURN_STATUS_UNEXPECTED("GetImageSize: invalid parameter, image should have at least two dimensions, but got: " +
                             std::to_string(image->Rank()));
  } else if (image->Rank() == kMinImageRank) {
    (*size)[0] = image->shape()[0];
    (*size)[1] = image->shape()[1];
  } else {
    const int32_t kHeightIndex = -3;
    const int32_t kWidthIndex = -2;
    (*size)[0] = image->shape()[kHeightIndex];
    (*size)[1] = image->shape()[kWidthIndex];
  }
  return Status::OK();
}

Status ValidateImage(const std::shared_ptr<Tensor> &image, const std::string &op_name,
                     const std::set<uint8_t> &valid_dtype, const std::set<dsize_t> &valid_rank,
                     const std::set<dsize_t> &valid_channel) {
  // Validate image dtype
  if (!valid_dtype.empty()) {
    auto dtype = image->type();
    if (valid_dtype.find(dtype.value()) == valid_dtype.end()) {
      std::string err_msg = op_name + ": the data type of image tensor does not match the requirement of operator.";
      err_msg += " Expecting tensor in type of " + DataTypeSetToString(valid_dtype);
      err_msg += ". But got type " + dtype.ToString() + ".";
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
  }
  // Validate image rank
  if (!valid_rank.empty()) {
    auto rank = image->Rank();
    if (valid_rank.find(rank) == valid_rank.end()) {
      std::string err_msg = op_name + ": the dimension of image tensor does not match the requirement of operator.";
      err_msg += " Expecting tensor in dimension of " + NumberSetToString(valid_rank);
      err_msg += ". But got dimension " + std::to_string(rank) + ".";
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
  }
  // Validate image channel
  if (!valid_channel.empty()) {
    dsize_t channel = 1;
    RETURN_IF_NOT_OK(ImageNumChannels(image, &channel));
    if (valid_channel.find(channel) == valid_channel.end()) {
      std::string err_msg = op_name + ": the channel of image tensor does not match the requirement of operator.";
      err_msg += " Expecting tensor in channel of " + NumberSetToString(valid_channel);
      err_msg += ". But got channel " + std::to_string(channel) + ".";
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
  }
  return Status::OK();
}

Status ValidateImageDtype(const std::string &op_name, DataType dtype) {
  uint8_t type = dtype.AsCVType();
  if (type == kCVInvalidType) {
    std::string type_name = "unknown";
    if (type < DataType::NUM_OF_TYPES) {
      type_name = std::string(DataType::kTypeInfo[type].name_);
    }
    std::string err_msg = op_name + ": Cannot convert [" + type_name + "] to OpenCV type." +
                          " Currently unsupported data type: [uint32, int64, uint64, string]";
    RETURN_STATUS_UNEXPECTED(err_msg);
  }
  return Status::OK();
}

Status ValidateImageRank(const std::string &op_name, int32_t rank) {
  if (rank != kMinImageRank && rank != kDefaultImageRank) {
    std::string err_msg =
      op_name + ": input tensor is not in shape of <H,W> or <H,W,C>, but got rank: " + std::to_string(rank);
    if (rank == 1) {
      err_msg = err_msg + ". You may need to perform Decode first.";
    }
    RETURN_STATUS_UNEXPECTED(err_msg);
  }
  return Status::OK();
}

bool CheckTensorShape(const std::shared_ptr<Tensor> &tensor, const int &channel) {
  if (tensor == nullptr) {
    return false;
  }
  bool rc = false;
  if (tensor->shape().Size() <= channel) {
    return false;
  }
  if (tensor->Rank() != kDefaultImageRank ||
      (tensor->shape()[channel] != 1 && tensor->shape()[channel] != kDefaultImageChannel)) {
    rc = true;
  }
  return rc;
}

Status Flip(std::shared_ptr<Tensor> input, std::shared_ptr<Tensor> *output, int flip_code) {
  std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(std::move(input));
  if (!input_cv->mat().data) {
    RETURN_STATUS_UNEXPECTED("[Internal ERROR] Flip: load image failed.");
  }

  std::shared_ptr<CVTensor> output_cv;
  RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));

  try {
    cv::flip(input_cv->mat(), output_cv->mat(), flip_code);
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Flip: " + std::string(e.what()));
  }
  return Status::OK();
}

Status HorizontalFlip(std::shared_ptr<Tensor> input, std::shared_ptr<Tensor> *output) {
  return Flip(std::move(input), output, 1);
}

Status VerticalFlip(std::shared_ptr<Tensor> input, std::shared_ptr<Tensor> *output) {
  return Flip(std::move(input), output, 0);
}

Status Resize(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, int32_t output_height,
              int32_t output_width, double fx, double fy, InterpolationMode mode) {
  std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
  if (!input_cv->mat().data) {
    RETURN_STATUS_UNEXPECTED("[Internal ERROR] Resize: load image failed.");
  }
  RETURN_IF_NOT_OK(ValidateImageRank("Resize", input_cv->Rank()));

  cv::Mat in_image = input_cv->mat();
  const uint32_t kResizeShapeLimits = 1000;
  // resize image too large or too small, 1000 is arbitrarily chosen here to prevent open cv from segmentation fault
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int>::max() / kResizeShapeLimits) > in_image.rows,
                               "Resize: in_image rows out of bounds.");
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int>::max() / kResizeShapeLimits) > in_image.cols,
                               "Resize: in_image cols out of bounds.");
  if (output_height > in_image.rows * kResizeShapeLimits || output_width > in_image.cols * kResizeShapeLimits) {
    std::string err_msg =
      "Resize: the resizing width or height is too big, it's 1000 times bigger than the original image, got output "
      "height: " +
      std::to_string(output_height) + ", width: " + std::to_string(output_width) +
      ", and original image size:" + std::to_string(in_image.rows) + ", " + std::to_string(in_image.cols);
    return Status(StatusCode::kMDShapeMisMatch, err_msg);
  }
  if (output_height == 0 || output_width == 0) {
    std::string err_msg = "Resize: the input value of 'resize' is invalid, width or height is zero.";
    return Status(StatusCode::kMDShapeMisMatch, err_msg);
  }

  if (mode == InterpolationMode::kCubicPil) {
    if (input_cv->shape().Size() != kDefaultImageChannel ||
        input_cv->shape()[kChannelIndexHWC] != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("Resize: Interpolation mode PILCUBIC only supports image with 3 channels, but got: " +
                               input_cv->shape().ToString());
    }

    LiteMat imIn, imOut;
    std::shared_ptr<Tensor> output_tensor;
    TensorShape new_shape = TensorShape({output_height, output_width, 3});
    RETURN_IF_NOT_OK(Tensor::CreateEmpty(new_shape, input_cv->type(), &output_tensor));
    uint8_t *buffer = reinterpret_cast<uint8_t *>(&(*output_tensor->begin<uint8_t>()));
    imOut.Init(output_width, output_height, input_cv->shape()[kChannelIndexHWC], reinterpret_cast<void *>(buffer),
               LDataType::UINT8);
    imIn.Init(input_cv->shape()[1], input_cv->shape()[0], input_cv->shape()[kChannelIndexHWC], input_cv->mat().data,
              LDataType::UINT8);
    if (ResizeCubic(imIn, imOut, output_width, output_height) == false) {
      RETURN_STATUS_UNEXPECTED("Resize: failed to do resize, please check the error msg.");
    }
    *output = output_tensor;
    return Status::OK();
  }
  try {
    TensorShape shape{output_height, output_width};
    if (input_cv->Rank() == kDefaultImageRank) {
      int num_channels = input_cv->shape()[kChannelIndexHWC];
      shape = shape.AppendDim(num_channels);
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(shape, input_cv->type(), &output_cv));

    auto cv_mode = GetCVInterpolationMode(mode);
    cv::resize(in_image, output_cv->mat(), cv::Size(output_width, output_height), fx, fy, cv_mode);
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Resize: " + std::string(e.what()));
  }
}

bool IsNonEmptyJPEG(const std::shared_ptr<Tensor> &input) {
  const unsigned char kJpegMagic[] = "\xFF\xD8\xFF";
  constexpr dsize_t kJpegMagicLen = 3;
  return input->SizeInBytes() > kJpegMagicLen && memcmp(input->GetBuffer(), kJpegMagic, kJpegMagicLen) == 0;
}

bool IsNonEmptyPNG(const std::shared_ptr<Tensor> &input) {
  const unsigned char kPngMagic[] = "\x89\x50\x4E\x47";
  constexpr dsize_t kPngMagicLen = 4;
  return input->SizeInBytes() > kPngMagicLen && memcmp(input->GetBuffer(), kPngMagic, kPngMagicLen) == 0;
}

Status Decode(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  if (IsNonEmptyJPEG(input)) {
    return JpegCropAndDecode(input, output);
  } else {
    return DecodeCv(input, output);
  }
}

Status DecodeCv(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
  if (!input_cv->mat().data) {
    RETURN_STATUS_UNEXPECTED("[Internal ERROR] Decode: load image failed.");
  }
  try {
    cv::Mat img_mat = cv::imdecode(input_cv->mat(), cv::IMREAD_COLOR | cv::IMREAD_IGNORE_ORIENTATION);
    if (img_mat.data == nullptr) {
      std::string err = "Decode: image decode failed.";
      RETURN_STATUS_UNEXPECTED(err);
    }
    cv::cvtColor(img_mat, img_mat, static_cast<int>(cv::COLOR_BGR2RGB));
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(img_mat, 3, &output_cv));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Decode: " + std::string(e.what()));
  }
}

static void JpegInitSource(j_decompress_ptr cinfo) {}

static boolean JpegFillInputBuffer(j_decompress_ptr cinfo) {
  if (cinfo->src->bytes_in_buffer == 0) {
    // Under ARM platform raise runtime_error may cause core problem,
    // so we catch runtime_error and just return FALSE.
    try {
      ERREXIT(cinfo, JERR_INPUT_EMPTY);
    } catch (std::runtime_error &e) {
      return FALSE;
    }
    return FALSE;
  }
  return TRUE;
}

static void JpegTermSource(j_decompress_ptr cinfo) {}

static void JpegSkipInputData(j_decompress_ptr cinfo, int64_t jump) {
  if (jump < 0) {
    return;
  }
  if (static_cast<size_t>(jump) > cinfo->src->bytes_in_buffer) {
    cinfo->src->bytes_in_buffer = 0;
    return;
  } else {
    cinfo->src->bytes_in_buffer -= jump;
    cinfo->src->next_input_byte += jump;
  }
}

void JpegSetSource(j_decompress_ptr cinfo, const void *data, int64_t datasize) {
  cinfo->src = static_cast<struct jpeg_source_mgr *>(
    (*cinfo->mem->alloc_small)(reinterpret_cast<j_common_ptr>(cinfo), JPOOL_PERMANENT, sizeof(struct jpeg_source_mgr)));
  cinfo->src->init_source = JpegInitSource;
  cinfo->src->fill_input_buffer = JpegFillInputBuffer;
#if defined(_WIN32) || defined(_WIN64) || defined(ENABLE_ARM32) || defined(__APPLE__)
  cinfo->src->skip_input_data = reinterpret_cast<void (*)(j_decompress_ptr, long)>(JpegSkipInputData);
#else
  cinfo->src->skip_input_data = JpegSkipInputData;
#endif
  cinfo->src->resync_to_restart = jpeg_resync_to_restart;
  cinfo->src->term_source = JpegTermSource;
  cinfo->src->bytes_in_buffer = datasize;
  cinfo->src->next_input_byte = static_cast<const JOCTET *>(data);
}

static Status JpegReadScanlines(jpeg_decompress_struct *const cinfo, int max_scanlines_to_read, JSAMPLE *buffer,
                                int buffer_size, int crop_w, int crop_w_aligned, int offset, int stride) {
  // scanlines will be read to this buffer first, must have the number
  // of components equal to the number of components in the image
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int64_t>::max() / cinfo->output_components) > crop_w_aligned,
                               "JpegReadScanlines: multiplication out of bounds.");
  int64_t scanline_size = crop_w_aligned * cinfo->output_components;
  std::vector<JSAMPLE> scanline(scanline_size);
  JSAMPLE *scanline_ptr = &scanline[0];
  while (cinfo->output_scanline < static_cast<unsigned int>(max_scanlines_to_read)) {
    int num_lines_read = 0;
    try {
      num_lines_read = jpeg_read_scanlines(cinfo, &scanline_ptr, 1);
    } catch (std::runtime_error &e) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] Decode: image decode failed.");
    }
    if (cinfo->out_color_space == JCS_CMYK && num_lines_read > 0) {
      for (int i = 0; i < crop_w; ++i) {
        const int cmyk_pixel = 4 * i + offset;
        const int c = scanline_ptr[cmyk_pixel];
        const int m = scanline_ptr[cmyk_pixel + 1];
        const int y = scanline_ptr[cmyk_pixel + 2];
        const int k = scanline_ptr[cmyk_pixel + 3];
        int r, g, b;
        if (cinfo->saw_Adobe_marker) {
          r = (k * c) / kMaxBitValue;
          g = (k * m) / kMaxBitValue;
          b = (k * y) / kMaxBitValue;
        } else {
          r = (kMaxBitValue - c) * (kMaxBitValue - k) / kMaxBitValue;
          g = (kMaxBitValue - m) * (kMaxBitValue - k) / kMaxBitValue;
          b = (kMaxBitValue - y) * (kMaxBitValue - k) / kMaxBitValue;
        }
        buffer[kDefaultImageChannel * i + kRIndex] = r;
        buffer[kDefaultImageChannel * i + kGIndex] = g;
        buffer[kDefaultImageChannel * i + kBIndex] = b;
      }
    } else if (num_lines_read > 0) {
      int copy_status = memcpy_s(buffer, buffer_size, scanline_ptr + offset, stride);
      if (copy_status != 0) {
        jpeg_destroy_decompress(cinfo);
        RETURN_STATUS_UNEXPECTED("[Internal ERROR] Decode: memcpy failed.");
      }
    } else {
      jpeg_destroy_decompress(cinfo);
      std::string err_msg = "[Internal ERROR] Decode: image decode failed.";
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
    buffer += stride;
    buffer_size = buffer_size - stride;
  }
  return Status::OK();
}

static Status JpegSetColorSpace(jpeg_decompress_struct *cinfo) {
  switch (cinfo->num_components) {
    case 1:
      // we want to output 3 components if it's grayscale
      cinfo->out_color_space = JCS_RGB;
      return Status::OK();
    case 3:
      cinfo->out_color_space = JCS_RGB;
      return Status::OK();
    case 4:
      // Need to manually convert to RGB
      cinfo->out_color_space = JCS_CMYK;
      return Status::OK();
    default:
      jpeg_destroy_decompress(cinfo);
      std::string err_msg = "[Internal ERROR] Decode: image decode failed.";
      RETURN_STATUS_UNEXPECTED(err_msg);
  }
}

void JpegErrorExitCustom(j_common_ptr cinfo) {
  char jpeg_last_error_msg[JMSG_LENGTH_MAX];
  (*(cinfo->err->format_message))(cinfo, jpeg_last_error_msg);
  throw std::runtime_error(jpeg_last_error_msg);
}

Status JpegCropAndDecode(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, int crop_x, int crop_y,
                         int crop_w, int crop_h) {
  struct jpeg_decompress_struct cinfo;
  auto DestroyDecompressAndReturnError = [&cinfo](const std::string &err) {
    jpeg_destroy_decompress(&cinfo);
    RETURN_STATUS_UNEXPECTED(err);
  };
  struct JpegErrorManagerCustom jerr;
  cinfo.err = jpeg_std_error(&jerr.pub);
  jerr.pub.error_exit = JpegErrorExitCustom;
  try {
    jpeg_create_decompress(&cinfo);
    JpegSetSource(&cinfo, input->GetBuffer(), input->SizeInBytes());
    (void)jpeg_read_header(&cinfo, TRUE);
    RETURN_IF_NOT_OK(JpegSetColorSpace(&cinfo));
    jpeg_calc_output_dimensions(&cinfo);
  } catch (std::runtime_error &e) {
    return DestroyDecompressAndReturnError(e.what());
  }
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int32_t>::max() - crop_w) > crop_x,
                               "JpegCropAndDecode: addition(crop x and crop width) out of bounds, got crop x:" +
                                 std::to_string(crop_x) + ", and crop width:" + std::to_string(crop_w));
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int32_t>::max() - crop_h) > crop_y,
                               "JpegCropAndDecode: addition(crop y and crop height) out of bounds, got crop y:" +
                                 std::to_string(crop_y) + ", and crop height:" + std::to_string(crop_h));
  if (crop_x == 0 && crop_y == 0 && crop_w == 0 && crop_h == 0) {
    crop_w = cinfo.output_width;
    crop_h = cinfo.output_height;
  } else if (crop_w == 0 || static_cast<unsigned int>(crop_w + crop_x) > cinfo.output_width || crop_h == 0 ||
             static_cast<unsigned int>(crop_h + crop_y) > cinfo.output_height) {
    return DestroyDecompressAndReturnError(
      "Crop: invalid crop size, corresponding crop value equal to 0 or too big, got crop width: " +
      std::to_string(crop_w) + ", crop height:" + std::to_string(crop_h) +
      ", and crop x coordinate:" + std::to_string(crop_x) + ", crop y coordinate:" + std::to_string(crop_y));
  }
  const int mcu_size = cinfo.min_DCT_scaled_size;
  CHECK_FAIL_RETURN_UNEXPECTED(mcu_size != 0, "JpegCropAndDecode: divisor mcu_size is zero.");
  unsigned int crop_x_aligned = (crop_x / mcu_size) * mcu_size;
  unsigned int crop_w_aligned = crop_w + crop_x - crop_x_aligned;
  try {
    bool status = jpeg_start_decompress(&cinfo);
    CHECK_FAIL_RETURN_UNEXPECTED(status, "JpegCropAndDecode: fail to decode multiscan jpeg image.");
    jpeg_crop_scanline(&cinfo, &crop_x_aligned, &crop_w_aligned);
  } catch (std::runtime_error &e) {
    return DestroyDecompressAndReturnError(e.what());
  }
  JDIMENSION skipped_scanlines = jpeg_skip_scanlines(&cinfo, crop_y);
  // three number of output components, always convert to RGB and output
  constexpr int kOutNumComponents = 3;
  TensorShape ts = TensorShape({crop_h, crop_w, kOutNumComponents});
  std::shared_ptr<Tensor> output_tensor;
  RETURN_IF_NOT_OK(Tensor::CreateEmpty(ts, DataType(DataType::DE_UINT8), &output_tensor));
  const int buffer_size = output_tensor->SizeInBytes();
  JSAMPLE *buffer = reinterpret_cast<JSAMPLE *>(&(*output_tensor->begin<uint8_t>()));
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<float_t>::max() - skipped_scanlines) > crop_h,
                               "JpegCropAndDecode: addition out of bounds.");
  const int max_scanlines_to_read = skipped_scanlines + crop_h;
  // stride refers to output tensor, which has 3 components at most
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int32_t>::max() / crop_w) > kOutNumComponents,
                               "JpegCropAndDecode: multiplication out of bounds.");
  const int stride = crop_w * kOutNumComponents;
  // offset is calculated for scanlines read from the image, therefore
  // has the same number of components as the image
  int minius_value = crop_x - crop_x_aligned;
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<float_t>::max() / minius_value) > cinfo.output_components,
                               "JpegCropAndDecode: multiplication out of bounds.");
  const int offset = minius_value * cinfo.output_components;
  RETURN_IF_NOT_OK(
    JpegReadScanlines(&cinfo, max_scanlines_to_read, buffer, buffer_size, crop_w, crop_w_aligned, offset, stride));
  *output = output_tensor;
  jpeg_destroy_decompress(&cinfo);
  return Status::OK();
}

Status Rescale(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, float rescale, float shift) {
  std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
  if (!input_cv->mat().data) {
    RETURN_STATUS_UNEXPECTED("[Internal ERROR] Rescale: load image failed.");
  }
  cv::Mat input_image = input_cv->mat();
  std::shared_ptr<CVTensor> output_cv;
  RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), DataType(DataType::DE_FLOAT32), &output_cv));
  try {
    input_image.convertTo(output_cv->mat(), CV_32F, rescale, shift);
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Rescale: " + std::string(e.what()));
  }
  return Status::OK();
}

Status Crop(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, int x, int y, int w, int h) {
  std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
  if (!input_cv->mat().data) {
    RETURN_STATUS_UNEXPECTED("[Internal ERROR] Crop: load image failed.");
  }
  RETURN_IF_NOT_OK(ValidateImageRank("Crop", input_cv->Rank()));
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int32_t>::max() - y) > h,
                               "Crop: addition(x and height) out of bounds, got height:" + std::to_string(h) +
                                 ", and coordinate y:" + std::to_string(y));
  // account for integer overflow
  if (y < 0 || (y + h) > input_cv->shape()[0] || (y + h) < 0) {
    RETURN_STATUS_UNEXPECTED(
      "Crop: invalid y coordinate value for crop, y coordinate value exceeds the boundary of the image, got y: " +
      std::to_string(y));
  }
  CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int32_t>::max() - x) > w, "Crop: addition out of bounds.");
  // account for integer overflow
  if (x < 0 || (x + w) > input_cv->shape()[1] || (x + w) < 0) {
    RETURN_STATUS_UNEXPECTED(
      "Crop: invalid x coordinate value for crop, "
      "x coordinate value exceeds the boundary of the image, got x: " +
      std::to_string(x));
  }
  try {
    TensorShape shape{h, w};
    if (input_cv->Rank() == kDefaultImageRank) {
      int num_channels = input_cv->shape()[kChannelIndexHWC];
      shape = shape.AppendDim(num_channels);
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(shape, input_cv->type(), &output_cv));
    cv::Rect roi(x, y, w, h);
    (input_cv->mat())(roi).copyTo(output_cv->mat());
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Crop: " + std::string(e.what()));
  }
}

Status ConvertColor(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, ConvertMode convert_mode) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    RETURN_IF_NOT_OK(ValidateImageRank("ConvertColor", input_cv->Rank()));
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] ConvertColor: load image failed.");
    }
    if (input_cv->Rank() == kDefaultImageRank) {
      int num_channels = input_cv->shape()[kChannelIndexHWC];
      if (num_channels != kMinImageChannel && num_channels != kDefaultImageChannel &&
          num_channels != kMaxImageChannel) {
        RETURN_STATUS_UNEXPECTED("ConvertColor: number of channels of image should be 1, 3, 4, but got:" +
                                 std::to_string(num_channels));
      }
    }
    std::vector<dsize_t> node;
    RETURN_IF_NOT_OK(GetConvertShape(convert_mode, input_cv, &node));
    if (node.empty()) {
      RETURN_STATUS_UNEXPECTED(
        "ConvertColor: convert mode must be in ConvertMode, which mainly includes conversion "
        "between RGB, BGR, GRAY, RGBA etc.");
    }
    TensorShape out_shape = TensorShape(node);
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(out_shape, input_cv->type(), &output_cv));
    cv::cvtColor(input_cv->mat(), output_cv->mat(), static_cast<int>(convert_mode));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("ConvertColor: " + std::string(e.what()));
  }
}

Status HwcToChw(std::shared_ptr<Tensor> input, std::shared_ptr<Tensor> *output) {
  try {
    if (input->Rank() == kMinImageRank) {
      // If input tensor is 2D, we assume we have hw dimensions
      *output = input;
      return Status::OK();
    }
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] HWC2CHW: load image failed.");
    }
    if (input_cv->Rank() != kDefaultImageRank) {
      RETURN_STATUS_UNEXPECTED("HWC2CHW: image shape should be <H,W> or <H,W,C>, but got rank: " +
                               std::to_string(input_cv->Rank()));
    }
    cv::Mat output_img;

    int height = input_cv->shape()[0];
    int width = input_cv->shape()[1];
    int num_channels = input_cv->shape()[kChannelIndexHWC];

    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(TensorShape{num_channels, height, width}, input_cv->type(), &output_cv));

    for (int i = 0; i < num_channels; ++i) {
      cv::Mat mat;
      RETURN_IF_NOT_OK(output_cv->MatAtIndex({i}, &mat));
      cv::extractChannel(input_cv->mat(), mat, i);
    }
    *output = std::move(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("HWC2CHW: " + std::string(e.what()));
  }
}

Status MaskWithTensor(const std::shared_ptr<Tensor> &sub_mat, std::shared_ptr<Tensor> *input, int x, int y,
                      int crop_width, int crop_height, ImageFormat image_format) {
  if (image_format == ImageFormat::HWC) {
    if (CheckTensorShape(*input, 2)) {
      RETURN_STATUS_UNEXPECTED(
        "CutMixBatch: MaskWithTensor failed: "
        "input shape doesn't match <H,W,C> format, got shape:" +
        (*input)->shape().ToString());
    }
    if (CheckTensorShape(sub_mat, 2)) {
      RETURN_STATUS_UNEXPECTED(
        "CutMixBatch: MaskWithTensor failed: "
        "sub_mat shape doesn't match <H,W,C> format, got shape:" +
        (*input)->shape().ToString());
    }
    int number_of_channels = (*input)->shape()[kChannelIndexHWC];
    for (int i = 0; i < crop_width; i++) {
      for (int j = 0; j < crop_height; j++) {
        for (int c = 0; c < number_of_channels; c++) {
          RETURN_IF_NOT_OK(CopyTensorValue(sub_mat, input, {j, i, c}, {y + j, x + i, c}));
        }
      }
    }
  } else if (image_format == ImageFormat::CHW) {
    if (CheckTensorShape(*input, 0)) {
      RETURN_STATUS_UNEXPECTED(
        "CutMixBatch: MaskWithTensor failed: "
        "input shape doesn't match <C,H,W> format, got shape:" +
        (*input)->shape().ToString());
    }
    if (CheckTensorShape(sub_mat, 0)) {
      RETURN_STATUS_UNEXPECTED(
        "CutMixBatch: MaskWithTensor failed: "
        "sub_mat shape doesn't match <C,H,W> format, got shape:" +
        (*input)->shape().ToString());
    }
    int number_of_channels = (*input)->shape()[0];
    for (int i = 0; i < crop_width; i++) {
      for (int j = 0; j < crop_height; j++) {
        for (int c = 0; c < number_of_channels; c++) {
          RETURN_IF_NOT_OK(CopyTensorValue(sub_mat, input, {c, j, i}, {c, y + j, x + i}));
        }
      }
    }
  } else if (image_format == ImageFormat::HW) {
    if ((*input)->Rank() != kMinImageRank) {
      RETURN_STATUS_UNEXPECTED(
        "CutMixBatch: MaskWithTensor failed: "
        "input shape doesn't match <H,W> format, got shape:" +
        (*input)->shape().ToString());
    }
    if (sub_mat->Rank() != kMinImageRank) {
      RETURN_STATUS_UNEXPECTED(
        "CutMixBatch: MaskWithTensor failed: "
        "sub_mat shape doesn't match <H,W> format, got shape:" +
        (*input)->shape().ToString());
    }
    for (int i = 0; i < crop_width; i++) {
      for (int j = 0; j < crop_height; j++) {
        RETURN_IF_NOT_OK(CopyTensorValue(sub_mat, input, {j, i}, {y + j, x + i}));
      }
    }
  } else {
    RETURN_STATUS_UNEXPECTED(
      "CutMixBatch: MaskWithTensor failed: "
      "image format must be <C,H,W>, <H,W,C>, or <H,W>, got shape:" +
      (*input)->shape().ToString());
  }
  return Status::OK();
}

Status CopyTensorValue(const std::shared_ptr<Tensor> &source_tensor, std::shared_ptr<Tensor> *dest_tensor,
                       const std::vector<int64_t> &source_indx, const std::vector<int64_t> &dest_indx) {
  if (source_tensor->type() != (*dest_tensor)->type())
    RETURN_STATUS_UNEXPECTED(
      "CutMixBatch: CopyTensorValue failed: "
      "source and destination tensor must have the same type.");
  if (source_tensor->type() == DataType::DE_UINT8) {
    uint8_t pixel_value = 0;
    RETURN_IF_NOT_OK(source_tensor->GetItemAt(&pixel_value, source_indx));
    RETURN_IF_NOT_OK((*dest_tensor)->SetItemAt(dest_indx, pixel_value));
  } else if (source_tensor->type() == DataType::DE_FLOAT32) {
    float pixel_value = 0;
    RETURN_IF_NOT_OK(source_tensor->GetItemAt(&pixel_value, source_indx));
    RETURN_IF_NOT_OK((*dest_tensor)->SetItemAt(dest_indx, pixel_value));
  } else {
    RETURN_STATUS_UNEXPECTED(
      "CutMixBatch: CopyTensorValue failed: "
      "Tensor type is not supported. Tensor type must be float32 or uint8.");
  }
  return Status::OK();
}

Status SwapRedAndBlue(std::shared_ptr<Tensor> input, std::shared_ptr<Tensor> *output) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "SwapRedBlue", {3, 5, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(std::move(input));
    CHECK_FAIL_RETURN_UNEXPECTED(
      input_cv->shape().Size() > kChannelIndexHWC,
      "SwapRedAndBlue: rank of input data should be greater than:" + std::to_string(kChannelIndexHWC) +
        ", but got:" + std::to_string(input_cv->shape().Size()));
    int num_channels = input_cv->shape()[kChannelIndexHWC];
    if (input_cv->shape().Size() != kDefaultImageRank || num_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("SwapRedBlue: image shape should be in <H,W,C> format, but got:" +
                               input_cv->shape().ToString());
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));

    cv::cvtColor(input_cv->mat(), output_cv->mat(), static_cast<int>(cv::COLOR_BGR2RGB));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("SwapRedBlue: " + std::string(e.what()));
  }
}

Status CropAndResize(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, int x, int y,
                     int crop_height, int crop_width, int target_height, int target_width, InterpolationMode mode) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] CropAndResize: load image failed.");
    }
    RETURN_IF_NOT_OK(ValidateImageRank("CropAndResize", input_cv->Rank()));
    // image too large or too small, 1000 is arbitrary here to prevent opencv from segmentation fault
    const uint32_t kCropShapeLimits = 1000;
    CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int>::max() / kCropShapeLimits) > crop_height,
                                 "CropAndResize: crop_height out of bounds.");
    CHECK_FAIL_RETURN_UNEXPECTED((std::numeric_limits<int>::max() / kCropShapeLimits) > crop_width,
                                 "CropAndResize: crop_width out of bounds.");
    if (crop_height == 0 || crop_width == 0 || target_height == 0 || target_height > crop_height * kCropShapeLimits ||
        target_width == 0 || target_width > crop_width * kCropShapeLimits) {
      std::string err_msg =
        "CropAndResize: the resizing width or height 1) is too big, it's up to " + std::to_string(kCropShapeLimits) +
        " times the original image; 2) can not be 0. Detail info is: crop_height: " + std::to_string(crop_height) +
        ", crop_width: " + std::to_string(crop_width) + ", target_height: " + std::to_string(target_height) +
        ", target_width: " + std::to_string(target_width);
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
    cv::Rect roi(x, y, crop_width, crop_height);
    auto cv_mode = GetCVInterpolationMode(mode);
    cv::Mat cv_in = input_cv->mat();

    if (mode == InterpolationMode::kCubicPil) {
      if (input_cv->shape().Size() != kDefaultImageChannel ||
          input_cv->shape()[kChannelIndexHWC] != kDefaultImageChannel) {
        RETURN_STATUS_UNEXPECTED(
          "CropAndResize: Interpolation mode PILCUBIC only supports image with 3 channels, but got: " +
          input_cv->shape().ToString());
      }

      cv::Mat input_roi = cv_in(roi);
      std::shared_ptr<CVTensor> input_image;
      RETURN_IF_NOT_OK(CVTensor::CreateFromMat(input_roi, input_cv->Rank(), &input_image));
      LiteMat imIn, imOut;
      std::shared_ptr<Tensor> output_tensor;
      TensorShape new_shape = TensorShape({target_height, target_width, 3});
      RETURN_IF_NOT_OK(Tensor::CreateEmpty(new_shape, input_cv->type(), &output_tensor));
      uint8_t *buffer = reinterpret_cast<uint8_t *>(&(*output_tensor->begin<uint8_t>()));
      imOut.Init(target_width, target_height, input_cv->shape()[kChannelIndexHWC], reinterpret_cast<void *>(buffer),
                 LDataType::UINT8);
      imIn.Init(input_image->shape()[1], input_image->shape()[0], input_image->shape()[kChannelIndexHWC],
                input_image->mat().data, LDataType::UINT8);
      if (ResizeCubic(imIn, imOut, target_width, target_height) == false) {
        RETURN_STATUS_UNEXPECTED("Resize: failed to do resize, please check the error msg.");
      }
      *output = output_tensor;
      return Status::OK();
    }

    TensorShape shape{target_height, target_width};
    if (input_cv->Rank() == kDefaultImageRank) {
      int num_channels = input_cv->shape()[kChannelIndexHWC];
      shape = shape.AppendDim(num_channels);
    }
    std::shared_ptr<CVTensor> cvt_out;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(shape, input_cv->type(), &cvt_out));
    cv::resize(cv_in(roi), cvt_out->mat(), cv::Size(target_width, target_height), 0, 0, cv_mode);
    *output = std::static_pointer_cast<Tensor>(cvt_out);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("CropAndResize: " + std::string(e.what()));
  }
}

Status Rotate(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, std::vector<float> center,
              float degree, InterpolationMode interpolation, bool expand, uint8_t fill_r, uint8_t fill_g,
              uint8_t fill_b) {
  try {
    RETURN_IF_NOT_OK(ValidateImageRank("Rotate", input->Rank()));
    dsize_t channel = 1;
    RETURN_IF_NOT_OK(ImageNumChannels(input, &channel));
    CHECK_FAIL_RETURN_UNEXPECTED(channel <= kMaxImageChannel || interpolation != InterpolationMode::kCubic,
                                 "Rotate: interpolation can not be CUBIC when image channel is greater than 4.");
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] Rotate: load image failed.");
    }

    cv::Mat input_img = input_cv->mat();
    if (input_img.cols > (MAX_INT_PRECISION * DOUBLING_FACTOR) ||
        input_img.rows > (MAX_INT_PRECISION * DOUBLING_FACTOR)) {
      RETURN_STATUS_UNEXPECTED("Rotate: image is too large and center is not precise, got image width:" +
                               std::to_string(input_img.cols) + ", and image height:" + std::to_string(input_img.rows) +
                               ", both should be small than:" + std::to_string(MAX_INT_PRECISION * DOUBLING_FACTOR));
    }
    float fx = 0, fy = 0;
    if (center.empty()) {
      // default to center of image
      fx = (input_img.cols - 1) * kHalf;
      fy = (input_img.rows - 1) * kHalf;
    } else {
      fx = center[0];
      fy = center[1];
    }
    cv::Mat output_img;
    cv::Scalar fill_color = cv::Scalar(fill_b, fill_g, fill_r);
    // maybe don't use uint32 for image dimension here
    cv::Point2f pc(fx, fy);
    cv::Mat rot = cv::getRotationMatrix2D(pc, degree, 1.0);
    std::shared_ptr<CVTensor> output_cv;
    if (!expand) {
      // this case means that the shape doesn't change, size stays the same
      // We may not need this memcpy if it is in place.
      RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
      // using inter_nearest to comply with python default
      cv::warpAffine(input_img, output_cv->mat(), rot, input_img.size(), GetCVInterpolationMode(interpolation),
                     cv::BORDER_CONSTANT, fill_color);
    } else {
      // we resize here since the shape changes
      // create a new bounding box with the rotate
      cv::Rect2f bbox = cv::RotatedRect(pc, input_img.size(), degree).boundingRect2f();
      rot.at<double>(0, 2) += bbox.width / 2.0 - input_img.cols / 2.0;
      rot.at<double>(1, 2) += bbox.height / 2.0 - input_img.rows / 2.0;
      // use memcpy and don't compute the new shape since openCV has a rounding problem
      cv::warpAffine(input_img, output_img, rot, bbox.size(), GetCVInterpolationMode(interpolation),
                     cv::BORDER_CONSTANT, fill_color);
      RETURN_IF_NOT_OK(CVTensor::CreateFromMat(output_img, input_cv->Rank(), &output_cv));
      RETURN_UNEXPECTED_IF_NULL(output_cv);
    }
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Rotate: " + std::string(e.what()));
  }
  return Status::OK();
}

template <typename T1, typename T2>
void Normalize(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, std::vector<float> mean,
               std::vector<float> std, bool is_hwc, bool pad = false) {
  // T1 is the type of input tensor, T2 is the type of output tensor
  auto itr_out = (*output)->begin<T2>();
  auto itr = input->begin<T1>();
  auto end = input->end<T1>();
  int64_t num_channels;
  if (is_hwc) {
    num_channels = (*output)->shape()[kChannelIndexHWC];
    while (itr != end) {
      for (int64_t i = 0; i < num_channels - static_cast<int>(pad); i++) {
        *itr_out = static_cast<T2>((static_cast<float>(*itr) - mean[i]) / std[i]);
        ++itr_out;
        ++itr;
      }
    }
  } else {
    num_channels = (*output)->shape()[kChannelIndexCHW];
    int64_t height_index = 1;
    int64_t width_index = 2;
    int64_t channel_len = (*output)->shape()[height_index] * (*output)->shape()[width_index];
    while (itr != end) {
      for (int64_t i = 0; i < num_channels - static_cast<int>(pad); i++) {
        for (int64_t j = 0; j < channel_len; j++) {
          *itr_out = static_cast<T2>((static_cast<float>(*itr) - mean[i]) / std[i]);
          ++itr_out;
          ++itr;
        }
      }
    }
  }
}

template <typename T>
Status Normalize_caller(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output,
                        std::vector<float> mean_v, std::vector<float> std_v, bool is_hwc, bool pad) {
  switch (input->type().value()) {
    case DataType::DE_BOOL:
      Normalize<bool, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_INT8:
      Normalize<int8_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_UINT8:
      Normalize<uint8_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_INT16:
      Normalize<int16_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_UINT16:
      Normalize<uint16_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_INT32:
      Normalize<int32_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_UINT32:
      Normalize<uint32_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_INT64:
      Normalize<int64_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_UINT64:
      Normalize<uint64_t, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_FLOAT16:
      Normalize<float16, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_FLOAT32:
      Normalize<float, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    case DataType::DE_FLOAT64:
      Normalize<double, T>(input, output, mean_v, std_v, is_hwc, pad);
      break;
    default:
      std::string op_name = (pad) ? "NormalizePad" : "Normalize";
      RETURN_STATUS_UNEXPECTED(
        op_name + ": unsupported type, currently supported types include " +
        "[bool,int8_t,uint8_t,int16_t,uint16_t,int32_t,uint32_t,int64_t,uint64_t,float16,float,double].");
  }
  return Status::OK();
}

Status Normalize(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, std::vector<float> mean,
                 std::vector<float> std, bool is_hwc) {
  RETURN_IF_NOT_OK(Tensor::CreateEmpty(input->shape(), DataType(DataType::DE_FLOAT32), output));
  if (input->Rank() == kMinImageRank) {
    RETURN_IF_NOT_OK((*output)->ExpandDim(kMinImageRank));
  }

  CHECK_FAIL_RETURN_UNEXPECTED((*output)->Rank() == kDefaultImageRank,
                               "Normalize: output image rank should be: " + std::to_string(kDefaultImageRank) +
                                 ", but got: " + std::to_string((*output)->Rank()));
  CHECK_FAIL_RETURN_UNEXPECTED(std.size() == mean.size(),
                               "Normalize: mean and std vectors are not of same size, got size of std: " +
                                 std::to_string(std.size()) + ", and mean size: " + std::to_string(mean.size()));
  int64_t channel_index;
  if (is_hwc) {
    channel_index = kChannelIndexHWC;
  } else {
    channel_index = kChannelIndexCHW;
  }
  // caller provided 1 mean/std value and there is more than one channel --> duplicate mean/std value
  if (mean.size() == 1 && (*output)->shape()[channel_index] != 1) {
    for (int64_t i = 0; i < (*output)->shape()[channel_index] - 1; i++) {
      mean.push_back(mean[0]);
      std.push_back(std[0]);
    }
  }
  CHECK_FAIL_RETURN_UNEXPECTED((*output)->shape()[channel_index] == mean.size(),
                               "Normalize: number of channels does not match the size of mean and std vectors, got "
                               "channels: " +
                                 std::to_string((*output)->shape()[channel_index]) +
                                 ", size of mean: " + std::to_string(mean.size()));
  RETURN_IF_NOT_OK(Normalize_caller<float>(input, output, mean, std, is_hwc, false));

  if (input->Rank() == kMinImageRank) {
    (*output)->Squeeze();
  }
  return Status::OK();
}

Status NormalizePad(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, std::vector<float> mean,
                    std::vector<float> std, const std::string &dtype, bool is_hwc) {
  RETURN_IF_NOT_OK(ValidateImageRank("NormalizePad", input->Rank()));
  int64_t channel_index = kChannelIndexCHW;
  if (is_hwc) {
    channel_index = kChannelIndexHWC;
  }
  int32_t channels = 1;
  if (input->Rank() == kDefaultImageRank) {
    channels = input->shape()[channel_index];
  }

  if (is_hwc) {
    TensorShape new_shape = TensorShape({input->shape()[0], input->shape()[1], channels + 1});
    Tensor::CreateEmpty(new_shape, DataType(dtype), output);
    (*output)->Zero();
  } else {
    TensorShape new_shape = TensorShape({channels + 1, input->shape()[1], input->shape()[2]});
    Tensor::CreateEmpty(new_shape, DataType(dtype), output);
    (*output)->Zero();
  }

  // caller provided 1 mean/std value and there are more than one channel --> duplicate mean/std value
  if (mean.size() == 1 && channels > 1) {
    while (mean.size() < channels) {
      mean.push_back(mean[0]);
      std.push_back(std[0]);
    }
  }
  CHECK_FAIL_RETURN_UNEXPECTED((*output)->shape()[channel_index] == mean.size() + 1,
                               "NormalizePad: number of channels does not match the size of mean and std vectors, got "
                               "channels: " +
                                 std::to_string((*output)->shape()[channel_index] - 1) +
                                 ", size of mean: " + std::to_string(mean.size()));
  if (dtype == "float16") {
    RETURN_IF_NOT_OK(Normalize_caller<float16>(input, output, mean, std, is_hwc, true));
  } else {
    RETURN_IF_NOT_OK(Normalize_caller<float>(input, output, mean, std, is_hwc, true));
  }
  if (input->Rank() == kMinImageRank) {
    (*output)->Squeeze();
  }
  return Status::OK();
}

Status AdjustBrightness(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const float &alpha) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    cv::Mat input_img = input_cv->mat();
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] AdjustBrightness: load image failed.");
    }
    CHECK_FAIL_RETURN_UNEXPECTED(
      input_cv->shape().Size() > kChannelIndexHWC,
      "AdjustBrightness: image rank should be greater than: " + std::to_string(kChannelIndexHWC) +
        ", but got: " + std::to_string(input_cv->shape().Size()));
    int num_channels = input_cv->shape()[kChannelIndexHWC];
    // Rank of the image represents how many dimensions, image is expected to be HWC
    if (input_cv->Rank() != kDefaultImageRank || num_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("AdjustBrightness: image shape is not <H,W,C> or channel is not 3, got image rank: " +
                               std::to_string(input_cv->Rank()) + ", and channel:" + std::to_string(num_channels));
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
    output_cv->mat() = input_img * alpha;
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("AdjustBrightness: " + std::string(e.what()));
  }
  return Status::OK();
}

Status AdjustContrast(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const float &alpha) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "AdjustContrast", {3, 5, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    cv::Mat input_img = input_cv->mat();
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] AdjustContrast: load image failed.");
    }
    CHECK_FAIL_RETURN_UNEXPECTED(
      input_cv->shape().Size() > kChannelIndexHWC,
      "AdjustContrast: image rank should be greater than: " + std::to_string(kChannelIndexHWC) +
        ", but got: " + std::to_string(input_cv->shape().Size()));
    int num_channels = input_cv->shape()[kChannelIndexHWC];
    if (input_cv->Rank() != kDefaultImageChannel || num_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("AdjustContrast: image shape is not <H,W,C> or channel is not 3, got image rank: " +
                               std::to_string(input_cv->Rank()) + ", and channel:" + std::to_string(num_channels));
    }
    cv::Mat gray, output_img;
    cv::cvtColor(input_img, gray, CV_RGB2GRAY);
    auto mean_img = cv::mean(gray).val[0];
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
    output_img = cv::Mat::zeros(input_img.rows, input_img.cols, input_img.depth());
    output_img = output_img + mean_img;
    cv::cvtColor(output_img, output_img, CV_GRAY2RGB);
    output_cv->mat() = output_img * (1.0 - alpha) + input_img * alpha;
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("AdjustContrast: " + std::string(e.what()));
  }
  return Status::OK();
}

Status AdjustGamma(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const float &gamma,
                   const float &gain) {
  try {
    int num_channels = 1;
    if (input->Rank() < kMinImageRank) {
      RETURN_STATUS_UNEXPECTED("AdjustGamma: input tensor is not in shape of <...,H,W,C> or <H,W>, got shape:" +
                               input->shape().ToString());
    }
    if (input->Rank() > 2) {
      num_channels = input->shape()[-1];
    }
    if (num_channels != 1 && num_channels != 3) {
      RETURN_STATUS_UNEXPECTED("AdjustGamma: channel of input image should be 1 or 3, but got: " +
                               std::to_string(num_channels));
    }
    if (input->type().IsFloat()) {
      for (auto itr = input->begin<float>(); itr != input->end<float>(); itr++) {
        *itr = pow((*itr) * gain, gamma);
        *itr = std::min(std::max((*itr), 0.0f), 1.0f);
      }
      *output = input;
    } else {
      std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
      if (!input_cv->mat().data) {
        RETURN_STATUS_UNEXPECTED("[Internal ERROR] AdjustGamma: load image failed.");
      }
      cv::Mat input_img = input_cv->mat();
      std::shared_ptr<CVTensor> output_cv;
      RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
      uchar LUT[256] = {};
      auto kMaxPixelValueFloat = static_cast<float>(kMaxBitValue);
      for (int i = 0; i < 256; i++) {
        float f = i / kMaxPixelValueFloat;
        f = pow(f, gamma);
        LUT[i] =
          static_cast<uchar>(floor(std::min(f * (kMaxPixelValueFloat + 1.f - 1e-3f) * gain, kMaxPixelValueFloat)));
      }
      if (input_img.channels() == 1) {
        cv::MatIterator_<uchar> it = input_img.begin<uchar>();
        cv::MatIterator_<uchar> it_end = input_img.end<uchar>();
        for (; it != it_end; ++it) {
          *it = LUT[(*it)];
        }
      } else {
        cv::MatIterator_<cv::Vec3b> it = input_img.begin<cv::Vec3b>();
        cv::MatIterator_<cv::Vec3b> it_end = input_img.end<cv::Vec3b>();
        for (; it != it_end; ++it) {
          (*it)[0] = LUT[(*it)[0]];
          (*it)[1] = LUT[(*it)[1]];
          (*it)[2] = LUT[(*it)[2]];
        }
      }
      output_cv->mat() = input_img * 1;
      *output = std::static_pointer_cast<Tensor>(output_cv);
    }
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("AdjustGamma: " + std::string(e.what()));
  }
  return Status::OK();
}

Status AutoContrast(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const float &cutoff,
                    const std::vector<uint32_t> &ignore) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] AutoContrast: load image failed.");
    }
    if (input_cv->Rank() != kDefaultImageRank && input_cv->Rank() != kMinImageRank) {
      std::string err_msg = "AutoContrast: image rank should be 2 or 3,  but got: " + std::to_string(input_cv->Rank());
      if (input_cv->Rank() == 1) {
        err_msg = err_msg + ", may need to do Decode operation first.";
      }
      RETURN_STATUS_UNEXPECTED("AutoContrast: image rank should be 2 or 3,  but got: " +
                               std::to_string(input_cv->Rank()));
    }
    // Reshape to extend dimension if rank is 2 for algorithm to work. then reshape output to be of rank 2 like input
    if (input_cv->Rank() == kMinImageRank) {
      RETURN_IF_NOT_OK(input_cv->ExpandDim(kMinImageRank));
    }
    // Get number of channels and image matrix
    std::size_t num_of_channels = input_cv->shape()[kChannelIndexHWC];
    if (num_of_channels != kMinImageChannel && num_of_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("AutoContrast: channel of input image should be 1 or 3, but got: " +
                               std::to_string(num_of_channels));
    }
    cv::Mat image = input_cv->mat();
    // Separate the image to channels
    std::vector<cv::Mat> planes(num_of_channels);
    cv::split(image, planes);
    cv::Mat b_hist, g_hist, r_hist;
    // Establish the number of bins and set variables for histogram
    int32_t hist_size = 256;
    int32_t channels = 0;
    float range[] = {0, 256};
    const float *hist_range[] = {range};
    bool uniform = true, accumulate = false;
    // Set up lookup table for LUT(Look up table algorithm)
    std::vector<int32_t> table;
    std::vector<cv::Mat> image_result;
    for (std::size_t layer = 0; layer < planes.size(); layer++) {
      // Reset lookup table
      table = std::vector<int32_t>{};
      // Calculate Histogram for channel
      cv::Mat hist;
      cv::calcHist(&planes[layer], 1, &channels, cv::Mat(), hist, 1, &hist_size, hist_range, uniform, accumulate);
      hist.convertTo(hist, CV_32SC1);
      std::vector<int32_t> hist_vec;
      hist.col(0).copyTo(hist_vec);
      // Ignore values in ignore
      for (const auto &item : ignore) hist_vec[item] = 0;
      int32_t hi = kMaxBitValue;
      int32_t lo = 0;
      RETURN_IF_NOT_OK(ComputeUpperAndLowerPercentiles(&hist_vec, cutoff, cutoff, &hi, &lo));
      if (hi <= lo) {
        for (int32_t i = 0; i < 256; i++) {
          table.push_back(i);
        }
      } else {
        const float scale = static_cast<float>(kMaxBitValue) / (hi - lo);
        const float offset = -1 * lo * scale;
        for (int32_t i = 0; i < 256; i++) {
          int32_t ix = static_cast<int32_t>(i * scale + offset);
          ix = std::max(ix, 0);
          ix = std::min(ix, kMaxBitValue);
          table.push_back(ix);
        }
      }
      cv::Mat result_layer;
      cv::LUT(planes[layer], table, result_layer);
      image_result.push_back(result_layer);
    }
    cv::Mat result;
    cv::merge(image_result, result);
    result.convertTo(result, input_cv->mat().type());
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(result, input_cv->Rank(), &output_cv));
    (*output) = std::static_pointer_cast<Tensor>(output_cv);
    RETURN_IF_NOT_OK((*output)->Reshape(input_cv->shape()));
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("AutoContrast: " + std::string(e.what()));
  }
  return Status::OK();
}

Status AdjustSaturation(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const float &alpha) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "AdjustSaturation", {3, 5, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    cv::Mat input_img = input_cv->mat();
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] AdjustSaturation: load image failed.");
    }
    CHECK_FAIL_RETURN_UNEXPECTED(
      input_cv->shape().Size() > kChannelIndexHWC,
      "AdjustSaturation: image rank should be greater than: " + std::to_string(kChannelIndexHWC) +
        ", but got: " + std::to_string(input_cv->shape().Size()));
    int num_channels = input_cv->shape()[kChannelIndexHWC];
    if (input_cv->Rank() != kDefaultImageRank || num_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("AdjustSaturation: image shape is not <H,W,C> or channel is not 3, but got rank: " +
                               std::to_string(input_cv->Rank()) + ", and channel: " + std::to_string(num_channels));
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
    cv::Mat output_img = output_cv->mat();
    cv::Mat gray;
    cv::cvtColor(input_img, gray, CV_RGB2GRAY);
    cv::cvtColor(gray, output_img, CV_GRAY2RGB);
    output_cv->mat() = output_img * (1.0 - alpha) + input_img * alpha;
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("AdjustSaturation: " + std::string(e.what()));
  }
  return Status::OK();
}

Status AdjustHue(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const float &hue) {
  if (hue > 0.5 || hue < -0.5) {
    RETURN_STATUS_UNEXPECTED("AdjustHue: invalid parameter, hue should within [-0.5, 0.5], but got: " +
                             std::to_string(hue));
  }
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "AdjustHue", {3, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    cv::Mat input_img = input_cv->mat();
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] AdjustHue: load image failed.");
    }
    CHECK_FAIL_RETURN_UNEXPECTED(input_cv->shape().Size() > kMinImageRank,
                                 "AdjustHue: image rank should be greater than: " + std::to_string(kMinImageRank) +
                                   ", but got: " + std::to_string(input_cv->shape().Size()));
    int num_channels = input_cv->shape()[2];
    if (input_cv->Rank() != kDefaultImageRank || num_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("AdjustHue: image shape is not <H,W,C> or channel is not 3, but got rank: " +
                               std::to_string(input_cv->Rank()) + ", and channel: " + std::to_string(num_channels));
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
    cv::Mat output_img;
    cv::cvtColor(input_img, output_img, CV_RGB2HSV_FULL);
    for (int y = 0; y < output_img.cols; y++) {
      for (int x = 0; x < output_img.rows; x++) {
        uint8_t cur1 = output_img.at<cv::Vec3b>(cv::Point(y, x))[0];
        uint8_t h_hue = 0;
        h_hue = static_cast<uint8_t>(hue * kMaxBitValue);
        cur1 += h_hue;
        output_img.at<cv::Vec3b>(cv::Point(y, x))[0] = cur1;
      }
    }
    cv::cvtColor(output_img, output_cv->mat(), CV_HSV2RGB_FULL);
    *output = std::static_pointer_cast<Tensor>(output_cv);
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("AdjustHue: " + std::string(e.what()));
  }
  return Status::OK();
}

Status Equalize(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] Equalize: load image failed.");
    }
    if (input_cv->Rank() != kDefaultImageRank && input_cv->Rank() != kMinImageRank) {
      RETURN_STATUS_UNEXPECTED("Equalize: image rank should be 2 or 3,  but got: " + std::to_string(input_cv->Rank()));
    }
    // For greyscale images, extend dimension if rank is 2 and reshape output to be of rank 2.
    if (input_cv->Rank() == kMinImageRank) {
      RETURN_IF_NOT_OK(input_cv->ExpandDim(kMinImageRank));
    }
    // Get number of channels and image matrix
    std::size_t num_of_channels = input_cv->shape()[kChannelIndexHWC];
    if (num_of_channels != kMinImageChannel && num_of_channels != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("Equalize: channel of input image should be 1 or 3, but got: " +
                               std::to_string(num_of_channels));
    }
    cv::Mat image = input_cv->mat();
    // Separate the image to channels
    std::vector<cv::Mat> planes(num_of_channels);
    cv::split(image, planes);
    // Equalize each channel separately
    std::vector<cv::Mat> image_result;
    for (std::size_t layer = 0; layer < planes.size(); layer++) {
      cv::Mat channel_result;
      cv::equalizeHist(planes[layer], channel_result);
      image_result.push_back(channel_result);
    }
    cv::Mat result;
    cv::merge(image_result, result);
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(result, input_cv->Rank(), &output_cv));
    (*output) = std::static_pointer_cast<Tensor>(output_cv);
    RETURN_IF_NOT_OK((*output)->Reshape(input_cv->shape()));
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Equalize: " + std::string(e.what()));
  }
  return Status::OK();
}

Status ValidateCutOutImage(const std::shared_ptr<Tensor> &input, bool is_hwc, int32_t box_height, int32_t box_width) {
  uint32_t channel_index = is_hwc ? kChannelIndexHWC : kChannelIndexCHW;
  uint32_t height_index = is_hwc ? 0 : 1;
  uint32_t width_index = is_hwc ? 1 : 2;
  std::string right_shape = is_hwc ? "<H,W,C>" : "<C,H,W>";
  int64_t image_h = input->shape()[height_index];
  int64_t image_w = input->shape()[width_index];

  CHECK_FAIL_RETURN_UNEXPECTED(input->shape().Size() > channel_index, "CutOut: shape is invalid.");

  if (input->Rank() != kDefaultImageRank) {
    RETURN_STATUS_UNEXPECTED("CutOut: image shape is not " + right_shape +
                             ", but got rank: " + std::to_string(input->Rank()));
  }

  if (box_height > image_h || box_width > image_w) {
    RETURN_STATUS_UNEXPECTED(
      "CutOut: box size is too large for image erase, got box height: " + std::to_string(box_height) +
      "box weight: " + std::to_string(box_width) + ", and image height: " + std::to_string(image_h) +
      ", image width: " + std::to_string(image_w));
  }
  return Status::OK();
}

Status Erase(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, int32_t box_height,
             int32_t box_width, int32_t num_patches, bool bounded, bool random_color, std::mt19937 *rnd,
             std::vector<uint8_t> fill_colors, bool is_hwc) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    RETURN_IF_NOT_OK(ValidateCutOutImage(input_cv, is_hwc, box_height, box_width));
    uint32_t channel_index = is_hwc ? kChannelIndexHWC : kChannelIndexCHW;
    uint32_t height_index = is_hwc ? 0 : 1;
    uint32_t width_index = is_hwc ? 1 : 2;
    uint64_t num_channels = input_cv->shape()[channel_index];
    int64_t image_h = input_cv->shape()[height_index];
    int64_t image_w = input_cv->shape()[width_index];
    // for random color
    std::normal_distribution<double> normal_distribution(0, 1);
    std::uniform_int_distribution<int> height_distribution_bound(0, image_h - box_height);
    std::uniform_int_distribution<int> width_distribution_bound(0, image_w - box_width);
    std::uniform_int_distribution<int> height_distribution_unbound(0, image_h + box_height);
    std::uniform_int_distribution<int> width_distribution_unbound(0, image_w + box_width);

    if (fill_colors.empty()) {
      fill_colors = std::vector<uint8_t>(num_channels, 0);
    }
    CHECK_FAIL_RETURN_UNEXPECTED(fill_colors.size() == num_channels,
                                 "Number of fill colors (" + std::to_string(fill_colors.size()) +
                                   ") does not match the number of channels (" + std::to_string(num_channels) + ").");
    // core logic
    // update values based on random erasing or cutout
    for (int32_t i = 0; i < num_patches; i++) {
      // rows in cv mat refers to the height of the cropped box
      // we determine h_start and w_start using two different distributions as erasing is used by two different
      // image augmentations. The bounds are also different in each case.
      int32_t h_start = (bounded) ? height_distribution_bound(*rnd) : (height_distribution_unbound(*rnd) - box_height);
      int32_t w_start = (bounded) ? width_distribution_bound(*rnd) : (width_distribution_unbound(*rnd) - box_width);

      int32_t max_width = (w_start + box_width > image_w) ? image_w : w_start + box_width;
      int32_t max_height = (h_start + box_height > image_h) ? image_h : h_start + box_height;
      // check for starting range >= 0, here the start range is checked after for cut out, for random erasing
      // w_start and h_start will never be less than 0.
      h_start = (h_start < 0) ? 0 : h_start;
      w_start = (w_start < 0) ? 0 : w_start;

      for (int x = h_start; x < max_height; x++) {
        for (int y = w_start; y < max_width; y++) {
          for (int c = 0; c < num_channels; c++) {
            uint8_t fill_value = fill_colors[c];
            if (random_color) {
              // fill each box with a random value
              fill_value = static_cast<int32_t>(normal_distribution(*rnd));
            }
            if (num_channels == 1) {
              input_cv->SetItemAt<uint8_t>({x, y}, fill_value);
            } else {
              std::vector<dsize_t> index = is_hwc ? std::vector<dsize_t>{x, y, c} : std::vector<dsize_t>{c, x, y};
              input_cv->SetItemAt<uint8_t>(index, fill_value);
            }
          }
        }
      }
    }

    *output = std::static_pointer_cast<Tensor>(input);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("CutOut: " + std::string(e.what()));
  }

  return Status::OK();
}

Status Pad(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const int32_t &pad_top,
           const int32_t &pad_bottom, const int32_t &pad_left, const int32_t &pad_right, const BorderType &border_types,
           uint8_t fill_r, uint8_t fill_g, uint8_t fill_b) {
  try {
    // input image
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);

    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] Pad: load image failed.");
    }

    // validate rank and number channels
    RETURN_IF_NOT_OK(ValidateImageRank("Pad", input_cv->Rank()));
    if (input_cv->Rank() == kDefaultImageRank) {
      if (input_cv->shape()[kChannelIndexHWC] != kDefaultImageChannel &&
          input_cv->shape()[kChannelIndexHWC] != kMinImageChannel) {
        RETURN_STATUS_UNEXPECTED("Pad: number of channels for input tensor can only be 1 or 3, got channel: " +
                                 std::to_string(input_cv->shape()[kChannelIndexHWC]));
      }
    }

    // get the border type in openCV
    auto b_type = GetCVBorderType(border_types);
    // output image
    cv::Mat out_image;
    if (b_type == cv::BORDER_CONSTANT) {
      cv::Scalar fill_color = cv::Scalar(fill_r, fill_g, fill_b);
      cv::copyMakeBorder(input_cv->mat(), out_image, pad_top, pad_bottom, pad_left, pad_right, b_type, fill_color);
    } else {
      cv::copyMakeBorder(input_cv->mat(), out_image, pad_top, pad_bottom, pad_left, pad_right, b_type);
    }
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(out_image, input_cv->Rank(), &output_cv));
    // pad the dimension if shape information is only 2 dimensional, this is grayscale
    if (input_cv->Rank() == kDefaultImageRank && input_cv->shape()[kChannelIndexHWC] == kMinImageChannel &&
        output_cv->Rank() == kMinImageRank)
      RETURN_IF_NOT_OK(output_cv->ExpandDim(kChannelIndexHWC));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Pad: " + std::string(e.what()));
  }
}

Status RandomLighting(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, float rnd_r, float rnd_g,
                      float rnd_b) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    cv::Mat input_img = input_cv->mat();

    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED(
        "RandomLighting: Cannot convert from OpenCV type, unknown "
        "CV type. Currently supported data type: [int8, uint8, int16, uint16, "
        "int32, float16, float32, float64].");
    }

    if (input_cv->Rank() != kDefaultImageRank || input_cv->shape()[kChannelIndexHWC] != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED(
        "RandomLighting: input tensor is not in shape of <H,W,C> or channel is not 3, got rank: " +
        std::to_string(input_cv->Rank()) + ", and channel: " + std::to_string(input_cv->shape()[kChannelIndexHWC]));
    }
    auto input_type = input->type();
    CHECK_FAIL_RETURN_UNEXPECTED(input_type != DataType::DE_UINT32 && input_type != DataType::DE_UINT64 &&
                                   input_type != DataType::DE_INT64 && input_type != DataType::DE_STRING,
                                 "RandomLighting: invalid tensor type of uint32, int64, uint64 or string.");

    std::vector<std::vector<float>> eig = {{55.46 * -0.5675, 4.794 * 0.7192, 1.148 * 0.4009},
                                           {55.46 * -0.5808, 4.794 * -0.0045, 1.148 * -0.8140},
                                           {55.46 * -0.5836, 4.794 * -0.6948, 1.148 * 0.4203}};

    float pca_r = eig[0][0] * rnd_r + eig[0][1] * rnd_g + eig[0][2] * rnd_b;
    float pca_g = eig[1][0] * rnd_r + eig[1][1] * rnd_g + eig[1][2] * rnd_b;
    float pca_b = eig[2][0] * rnd_r + eig[2][1] * rnd_g + eig[2][2] * rnd_b;
    for (int row = 0; row < input_img.rows; row++) {
      for (int col = 0; col < input_img.cols; col++) {
        float r = static_cast<float>(input_img.at<cv::Vec3b>(row, col)[0]);
        float g = static_cast<float>(input_img.at<cv::Vec3b>(row, col)[1]);
        float b = static_cast<float>(input_img.at<cv::Vec3b>(row, col)[2]);
        input_img.at<cv::Vec3b>(row, col)[0] = cv::saturate_cast<uchar>(r + pca_r);
        input_img.at<cv::Vec3b>(row, col)[1] = cv::saturate_cast<uchar>(g + pca_g);
        input_img.at<cv::Vec3b>(row, col)[2] = cv::saturate_cast<uchar>(b + pca_b);
      }
    }

    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(input_img, input_cv->Rank(), &output_cv));

    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("RandomLighting: " + std::string(e.what()));
  }
}

Status RgbaToRgb(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "RgbaToRgb", {3, 5, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(std::move(input));
    if (input_cv->shape().Size() != kDefaultImageChannel || input_cv->shape()[kChannelIndexHWC] != kMaxImageChannel) {
      std::string err_msg =
        "RgbaToRgb: rank of image is not: " + std::to_string(kDefaultImageChannel) +
        ", but got: " + std::to_string(input_cv->shape().Size()) +
        ", or channels of image should be 4, but got: " + std::to_string(input_cv->shape()[kChannelIndexHWC]);
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
    TensorShape out_shape = TensorShape({input_cv->shape()[0], input_cv->shape()[1], 3});
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(out_shape, input_cv->type(), &output_cv));
    cv::cvtColor(input_cv->mat(), output_cv->mat(), static_cast<int>(cv::COLOR_RGBA2RGB));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("RgbaToRgb: " + std::string(e.what()));
  }
}

Status RgbaToBgr(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "RgbaToBgr", {3, 5, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(std::move(input));
    if (input_cv->shape().Size() != kDefaultImageChannel || input_cv->shape()[kChannelIndexHWC] != kMaxImageChannel) {
      std::string err_msg =
        "RgbaToBgr: rank of image is not: " + std::to_string(kDefaultImageChannel) +
        ", but got: " + std::to_string(input_cv->shape().Size()) +
        ", or channels of image should be 4, but got: " + std::to_string(input_cv->shape()[kChannelIndexHWC]);
      RETURN_STATUS_UNEXPECTED(err_msg);
    }
    TensorShape out_shape = TensorShape({input_cv->shape()[0], input_cv->shape()[1], 3});
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(out_shape, input_cv->type(), &output_cv));
    cv::cvtColor(input_cv->mat(), output_cv->mat(), static_cast<int>(cv::COLOR_RGBA2BGR));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("RgbaToBgr: " + std::string(e.what()));
  }
}

Status RgbToBgr(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "RgbToBgr", {3, 4, 5, 6, 10, 11, 12}));
    auto input_type = input->type();
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] RgbToBgr: load image failed.");
    }
    if (input_cv->Rank() != kDefaultImageRank || input_cv->shape()[kChannelIndexHWC] != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("RgbToBgr: input tensor is not in shape of <H,W,C> or channel is not 3, got rank: " +
                               std::to_string(input_cv->Rank()) +
                               ", and channel: " + std::to_string(input_cv->shape()[2]));
    }

    cv::Mat image = input_cv->mat().clone();
    if (input_type == DataType::DE_FLOAT16 || input_type == DataType::DE_INT16 || input_type == DataType::DE_UINT16) {
      for (int i = 0; i < input_cv->mat().rows; ++i) {
        cv::Vec3s *p1 = input_cv->mat().ptr<cv::Vec3s>(i);
        cv::Vec3s *p2 = image.ptr<cv::Vec3s>(i);
        for (int j = 0; j < input_cv->mat().cols; ++j) {
          p2[j][2] = p1[j][0];
          p2[j][1] = p1[j][1];
          p2[j][0] = p1[j][2];
        }
      }
    } else if (input_type == DataType::DE_FLOAT32 || input_type == DataType::DE_INT32) {
      for (int i = 0; i < input_cv->mat().rows; ++i) {
        cv::Vec3f *p1 = input_cv->mat().ptr<cv::Vec3f>(i);
        cv::Vec3f *p2 = image.ptr<cv::Vec3f>(i);
        for (int j = 0; j < input_cv->mat().cols; ++j) {
          p2[j][2] = p1[j][0];
          p2[j][1] = p1[j][1];
          p2[j][0] = p1[j][2];
        }
      }
    } else if (input_type == DataType::DE_FLOAT64) {
      for (int i = 0; i < input_cv->mat().rows; ++i) {
        cv::Vec3d *p1 = input_cv->mat().ptr<cv::Vec3d>(i);
        cv::Vec3d *p2 = image.ptr<cv::Vec3d>(i);
        for (int j = 0; j < input_cv->mat().cols; ++j) {
          p2[j][2] = p1[j][0];
          p2[j][1] = p1[j][1];
          p2[j][0] = p1[j][2];
        }
      }
    } else {
      cv::cvtColor(input_cv->mat(), image, cv::COLOR_RGB2BGR);
    }

    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(image, input_cv->Rank(), &output_cv));

    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("RgbToBgr: " + std::string(e.what()));
  }
}

Status RgbToGray(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output) {
  try {
    RETURN_IF_NOT_OK(ValidateImage(input, "RgbToGray", {3, 5, 11}));
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(std::move(input));
    if (input_cv->Rank() != kDefaultImageRank || input_cv->shape()[kChannelIndexHWC] != kDefaultImageChannel) {
      RETURN_STATUS_UNEXPECTED("RgbToGray: image shape is not <H,W,C> or channel is not 3, got rank: " +
                               std::to_string(input_cv->Rank()) + ", and shape: " + input_cv->shape().ToString());
    }
    TensorShape out_shape = TensorShape({input_cv->shape()[0], input_cv->shape()[1]});
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(out_shape, input_cv->type(), &output_cv));
    cv::cvtColor(input_cv->mat(), output_cv->mat(), static_cast<int>(cv::COLOR_RGB2GRAY));
    *output = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("RgbToGray: " + std::string(e.what()));
  }
}

Status GetJpegImageInfo(const std::shared_ptr<Tensor> &input, int *img_width, int *img_height) {
  struct jpeg_decompress_struct cinfo {};
  struct JpegErrorManagerCustom jerr {};
  cinfo.err = jpeg_std_error(&jerr.pub);
  jerr.pub.error_exit = JpegErrorExitCustom;
  try {
    jpeg_create_decompress(&cinfo);
    JpegSetSource(&cinfo, input->GetBuffer(), input->SizeInBytes());
    (void)jpeg_read_header(&cinfo, TRUE);
    jpeg_calc_output_dimensions(&cinfo);
  } catch (std::runtime_error &e) {
    jpeg_destroy_decompress(&cinfo);
    RETURN_STATUS_UNEXPECTED(e.what());
  }
  *img_height = cinfo.output_height;
  *img_width = cinfo.output_width;
  jpeg_destroy_decompress(&cinfo);
  return Status::OK();
}

Status Affine(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const std::vector<float_t> &mat,
              InterpolationMode interpolation, uint8_t fill_r, uint8_t fill_g, uint8_t fill_b) {
  try {
    RETURN_IF_NOT_OK(ValidateImageRank("Affine", input->Rank()));
    dsize_t channel = 1;
    RETURN_IF_NOT_OK(ImageNumChannels(input, &channel));
    CHECK_FAIL_RETURN_UNEXPECTED(channel <= kMaxImageChannel || interpolation != InterpolationMode::kCubic,
                                 "Affine: interpolation can not be CUBIC when image channel is greater than 4.");
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] Affine: load image failed.");
    }

    cv::Mat affine_mat(mat);
    affine_mat = affine_mat.reshape(1, {2, 3});

    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateEmpty(input_cv->shape(), input_cv->type(), &output_cv));
    RETURN_UNEXPECTED_IF_NULL(output_cv);
    cv::warpAffine(input_cv->mat(), output_cv->mat(), affine_mat, input_cv->mat().size(),
                   GetCVInterpolationMode(interpolation), cv::BORDER_CONSTANT, cv::Scalar(fill_r, fill_g, fill_b));
    (*output) = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("Affine: " + std::string(e.what()));
  }
}

Status GaussianBlur(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, int32_t kernel_x,
                    int32_t kernel_y, float sigma_x, float sigma_y) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (input_cv->mat().data == nullptr) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] GaussianBlur: load image failed.");
    }
    cv::Mat output_cv_mat;
    cv::GaussianBlur(input_cv->mat(), output_cv_mat, cv::Size(kernel_x, kernel_y), static_cast<double>(sigma_x),
                     static_cast<double>(sigma_y));
    std::shared_ptr<CVTensor> output_cv;
    RETURN_IF_NOT_OK(CVTensor::CreateFromMat(output_cv_mat, input_cv->Rank(), &output_cv));
    (*output) = std::static_pointer_cast<Tensor>(output_cv);
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("GaussianBlur: " + std::string(e.what()));
  }
}

Status ComputePatchSize(const std::shared_ptr<CVTensor> &input_cv,
                        std::shared_ptr<std::pair<int32_t, int32_t>> *patch_size, int32_t num_height, int32_t num_width,
                        SliceMode slice_mode) {
  if (input_cv->mat().data == nullptr) {
    RETURN_STATUS_UNEXPECTED("[Internal ERROR] SlicePatches: Tensor could not convert to CV Tensor.");
  }
  RETURN_IF_NOT_OK(ValidateImageRank("Affine", input_cv->Rank()));

  cv::Mat in_img = input_cv->mat();
  cv::Size s = in_img.size();
  if (num_height == 0 || num_height > s.height) {
    RETURN_STATUS_UNEXPECTED(
      "SlicePatches: The number of patches on height axis equals 0 or is greater than height, got number of patches:" +
      std::to_string(num_height));
  }
  if (num_width == 0 || num_width > s.width) {
    RETURN_STATUS_UNEXPECTED(
      "SlicePatches: The number of patches on width axis equals 0 or is greater than width, got number of patches:" +
      std::to_string(num_width));
  }
  int32_t patch_h = s.height / num_height;
  if (s.height % num_height != 0) {
    if (slice_mode == SliceMode::kPad) {
      patch_h += 1;  // patch_h * num_height - s.height
    }
  }
  int32_t patch_w = s.width / num_width;
  if (s.width % num_width != 0) {
    if (slice_mode == SliceMode::kPad) {
      patch_w += 1;  // patch_w * num_width - s.width
    }
  }
  (*patch_size)->first = patch_h;
  (*patch_size)->second = patch_w;
  return Status::OK();
}

Status SlicePatches(const std::shared_ptr<Tensor> &input, std::vector<std::shared_ptr<Tensor>> *output,
                    int32_t num_height, int32_t num_width, SliceMode slice_mode, uint8_t fill_value) {
  if (num_height == DEFAULT_NUM_HEIGHT && num_width == DEFAULT_NUM_WIDTH) {
    (*output).push_back(input);
    return Status::OK();
  }

  auto patch_size = std::make_shared<std::pair<int32_t, int32_t>>(0, 0);
  int32_t patch_h = 0;
  int32_t patch_w = 0;

  std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
  RETURN_IF_NOT_OK(ComputePatchSize(input_cv, &patch_size, num_height, num_width, slice_mode));
  std::tie(patch_h, patch_w) = *patch_size;

  cv::Mat in_img = input_cv->mat();
  cv::Size s = in_img.size();
  try {
    cv::Mat out_img;
    if (slice_mode == SliceMode::kPad) {  // padding on right and bottom directions
      auto padding_h = patch_h * num_height - s.height;
      auto padding_w = patch_w * num_width - s.width;
      out_img = cv::Mat(s.height + padding_h, s.width + padding_w, in_img.type(), cv::Scalar::all(fill_value));
      in_img.copyTo(out_img(cv::Rect(0, 0, s.width, s.height)));
    } else {
      out_img = in_img;
    }
    for (int i = 0; i < num_height; ++i) {
      for (int j = 0; j < num_width; ++j) {
        std::shared_ptr<CVTensor> patch_cv;
        cv::Rect rect(j * patch_w, i * patch_h, patch_w, patch_h);
        cv::Mat patch(out_img(rect));
        RETURN_IF_NOT_OK(CVTensor::CreateFromMat(patch, input_cv->Rank(), &patch_cv));
        (*output).push_back(std::static_pointer_cast<Tensor>(patch_cv));
      }
    }
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("SlicePatches: " + std::string(e.what()));
  }
}

Status ToTensor(const std::shared_ptr<Tensor> &input, std::shared_ptr<Tensor> *output, const DataType &data_type) {
  try {
    std::shared_ptr<CVTensor> input_cv = CVTensor::AsCVTensor(input);
    if (!input_cv->mat().data) {
      RETURN_STATUS_UNEXPECTED("[Internal ERROR] ToTensor: load image failed.");
    }
    if (input_cv->Rank() == kMinImageRank) {
      // If input tensor is 2D, we assume we have HW dimensions
      RETURN_IF_NOT_OK(input_cv->ExpandDim(kMinImageRank));
    }
    CHECK_FAIL_RETURN_UNEXPECTED(
      input_cv->shape().Size() > kChannelIndexHWC,
      "ToTensor: rank of input data should be greater than: " + std::to_string(kChannelIndexHWC) +
        ", but got:" + std::to_string(input_cv->shape().Size()));
    int num_channels = input_cv->shape()[kChannelIndexHWC];
    if (input_cv->shape().Size() != kDefaultImageRank) {
      RETURN_STATUS_UNEXPECTED("ToTensor: image shape should be <H,W,C>, but got rank: " +
                               std::to_string(input_cv->shape().Size()));
    }

    int height = input_cv->shape()[0];
    int width = input_cv->shape()[1];

    // OpenCv has a bug in extractChannel when the type is float16.
    // To avoid the segfault, we cast to float32 first.
    if (input_cv->type() == DataType(DataType::DE_FLOAT16)) {
      RETURN_IF_NOT_OK(TypeCast(input_cv, output, DataType(DataType::DE_FLOAT32)));
      input_cv = CVTensor::AsCVTensor(*output);
    }

    std::shared_ptr<CVTensor> output_cv;
    // Reshape from HCW to CHW
    RETURN_IF_NOT_OK(
      CVTensor::CreateEmpty(TensorShape{num_channels, height, width}, DataType(DataType::DE_FLOAT32), &output_cv));
    // Rescale tensor by dividing by 255
    const float kMaxBitValueinFloat = static_cast<float>(kMaxBitValue);
    for (int i = 0; i < num_channels; ++i) {
      cv::Mat mat_t;
      cv::extractChannel(input_cv->mat(), mat_t, i);
      cv::Mat mat;
      RETURN_IF_NOT_OK(output_cv->MatAtIndex({i}, &mat));
      mat_t.convertTo(mat, CV_32F, 1 / kMaxBitValueinFloat, 0);
    }

    // Process tensor output according to desired output data type
    if (data_type != DataType(DataType::DE_FLOAT32)) {
      RETURN_IF_NOT_OK(TypeCast(output_cv, output, data_type));
    } else {
      *output = std::move(output_cv);
    }
    return Status::OK();
  } catch (const cv::Exception &e) {
    RETURN_STATUS_UNEXPECTED("ToTensor: " + std::string(e.what()));
  }
}
}  // namespace dataset
}  // namespace mindspore
