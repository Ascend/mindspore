if(MSVC)
  set(opencv_CXXFLAGS "${CMAKE_CXX_FLAGS}")
  set(opencv_CFLAGS "${CMAKE_C_FLAGS}")
  set(opencv_LDFLAGS "${CMAKE_SHARED_LINKER_FLAGS}")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(opencv_CXXFLAGS "-fstack-protector-all -Wno-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2")
  set(opencv_CFLAGS "-fstack-protector-all -Wno-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2")
  set(opencv_LDFLAGS "-Wl")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Windows")
  set(opencv_CXXFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2")
  set(opencv_CFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2")
  set(opencv_CXXFLAGS "${opencv_CXXFLAGS} -Wno-attributes -Wno-unknown-pragmas")
  set(opencv_CXXFLAGS "${opencv_CXXFLAGS} -Wno-unused-value -Wno-implicit-fallthrough")
else()
  set(opencv_CXXFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2")
  set(opencv_CXXFLAGS "${opencv_CXXFLAGS} -O2")
  if(NOT ENABLE_GLIBCXX)
    set(opencv_CXXFLAGS "${opencv_CXXFLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
  endif()
  set(opencv_CFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2")
  set(opencv_LDFLAGS "-Wl,-z,relro,-z,now,-z,noexecstack -s")
endif()

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/opencv/repository/archive/4.5.2.tar.gz")
  set(MD5 "d3141f649ab2d76595fdd8991ee15c55")
else()
  set(REQ_URL "https://github.com/opencv/opencv/archive/4.5.2.tar.gz")
  set(MD5 "d3141f649ab2d76595fdd8991ee15c55")
endif()

set(CMAKE_OPTION
    -DCMAKE_BUILD_TYPE=Release
    -DWITH_PROTOBUF=OFF
    -DWITH_WEBP=OFF
    -DWITH_IPP=OFF
    -DWITH_ADE=OFF
    -DBUILD_ZLIB=ON
    -DBUILD_JPEG=ON
    -DBUILD_PNG=ON
    -DBUILD_OPENEXR=OFF
    -DBUILD_TESTS=OFF
    -DBUILD_PERF_TESTS=OFF
    -DBUILD_opencv_apps=OFF
    -DCMAKE_SKIP_RPATH=TRUE
    -DBUILD_opencv_python3=OFF
    -DWITH_FFMPEG=OFF
    -DWITH_TIFF=ON
    -DBUILD_TIFF=OFF
    -DWITH_JASPER=OFF
    -DBUILD_JASPER=OFF
    -DCV_TRACE=OFF # cause memory usage increacing
    -DTIFF_INCLUDE_DIR=${tiff_INC}
    -DTIFF_LIBRARY=${tiff_LIB})

if(MSVC)
  set(LIBS opencv_core452.lib opencv_imgcodecs452.lib opencv_imgproc452.lib)
  set(LIB_PATH LIB_PATH x64/*/lib)
  list(APPEND CMAKE OPTION -DBUILD_opencv_videoio=OFF)
elseif(WIN32)
  set(LIBS libopencv_core452.dll.a libopencv_imgcodecs452.dll.a libopencv_imgproc452.dll.a)
  set(LIB_PATH LIB_PATH x64/mingw/lib)
  list(APPEND CMAKE_OPTION -DBUILD_opencv_videoio=OFF -DWITH_LAPACK=OFF)
else()
  list(APPEND CMAKE_OPTION -DWITH_LAPACK=OFF)
endif()

mindspore_add_pkg(
  OpenCV
  VER 4.5.2
  LIBS opencv_core opencv_imgcodecs opencv_imgproc
  LIBS_CMAKE_NAMES core imgcodecs imgproc ${LIB_PATH}
  URL ${REQ_URL}
  MD5 ${MD5}
  CMAKE_OPTION ${CMAKE_OPTION}
  TARGET_ALIAS mindspore::opencv_core opencv_core
  TARGET_ALIAS mindspore::opencv_imgcodecs opencv_imgcodecs
  TARGET_ALIAS mindspore::opencv_imgproc opencv_imgproc)

if(MSVC)
  include_directories(${opencv_INC})
elseif(WIN32)
  include_directories(${opencv_INC})
else()
  include_directories(${opencv_INC}/opencv4)
endif()
