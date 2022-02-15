if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/abseil-cpp/repository/archive/20200923.3.tar.gz")
  set(MD5 "daba6e99c7a84e2242a0107bbd873669")
else()
  set(REQ_URL "https://github.com/abseil/abseil-cpp/archive/20200923.3.tar.gz")
  set(MD5 "daba6e99c7a84e2242a0107bbd873669")
endif()

if(NOT ENABLE_GLIBCXX)
  set(absl_CXXFLAGS "${absl_CXXFLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
endif()

mindspore_add_pkg(
  absl
  VER 20200923.3
  FORCE_EXACT_VERSION
  LIBS absl_strings absl_throw_delegate absl_raw_logging_internal absl_int128 absl_bad_optional_access
  LIBS_CMAKE_NAMES strings throw_delegate raw_logging_internal int128 bad_optional_access
  URL ${REQ_URL}
  MD5 ${MD5}
  CMAKE_OPTION -DCMAKE_BUILD_TYPE:STRING=Release -DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=TRUE -DCMAKE_CXX_STANDARD=11
  PATCHES ${TOP_DIR}/third_party/patch/absl/absl.patch001
  TARGET_ALIAS mindspore::absl_strings absl::strings
  TARGET_ALIAS mindspore::absl_throw_delegate absl::throw_delegate
  TARGET_ALIAS mindspore::absl_raw_logging_internal absl::raw_logging_internal
  TARGET_ALIAS mindspore::absl_int128 absl::int128
  TARGET_ALIAS mindspore::absl_bad_optional_access absl::bad_optional_access)

include_directories(${absl_INC})
