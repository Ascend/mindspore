set(gtest_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2")
set(gtest_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")

set(CMAKE_OPTION -DBUILD_TESTING=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=ON
                 -DCMAKE_MACOSX_RPATH=TRUE -Dgtest_disable_pthreads=ON  -Dgtest_build_samples=OFF
                 -Dgtest_build_tests=OFF)
if(BUILD_LITE)
  if(PLATFORM_ARM64)
    set(CMAKE_OPTION
        -DCMAKE_TOOLCHAIN_FILE=$ENV{ANDROID_NDK}/build/cmake/android.toolchain.cmake
        -DANDROID_NATIVE_API_LEVEL=19
        -DANDROID_NDK=$ENV{ANDROID_NDK}
        -DANDROID_ABI=arm64-v8a
        -DANDROID_TOOLCHAIN_NAME=aarch64-linux-android-clang
        -DANDROID_STL=${ANDROID_STL}
        ${CMAKE_OPTION})
  endif()
  if(PLATFORM_ARM32)
    set(CMAKE_OPTION
        -DCMAKE_TOOLCHAIN_FILE=$ENV{ANDROID_NDK}/build/cmake/android.toolchain.cmake
        -DANDROID_NATIVE_API_LEVEL=19
        -DANDROID_NDK=$ENV{ANDROID_NDK}
        -DANDROID_ABI=armeabi-v7a
        -DANDROID_TOOLCHAIN_NAME=aarch64-linux-android-clang
        -DANDROID_STL=${ANDROID_STL}
        ${CMAKE_OPTION})
  endif()
endif()

if(NOT ENABLE_GLIBCXX)
  set(gtest_CXXFLAGS "${gtest_CXXFLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
endif()

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/googletest/repository/archive/release-1.11.0.tar.gz")
  set(MD5 "e8a8df240b6938bb6384155d4c37d937")
else()
  set(REQ_URL "https://github.com/google/googletest/archive/release-1.11.0.tar.gz")
  set(MD5 "e8a8df240b6938bb6384155d4c37d937")
endif()

mindspore_add_pkg(
  GTest
  VER 1.8.1
  LIBS gtest gmock gtest_main gmock_main
  URL ${REQ_URL}
  MD5 ${MD5}
  CMAKE_OPTION ${CMAKE_OPTION}
  TARGET_ALIAS mindspore::gtest GTest::gtest
  TARGET_ALIAS mindspore::gmock GTest::gmock)

foreach(_tgt GTest::gtest GTest::gtest_main GTest::gmock GTest::gmock_main)
  foreach(_prop IMPORTED_LOCATION_RELEASE IMPORTED_LOCATION IMPORTED_LOCATION_DEBUG IMPORTED_LOCATION_NOCONFIG)
    get_target_property(_lib ${_tgt} ${_prop})
    if(_lib)
      file(COPY ${_lib} DESTINATION ${CMAKE_BINARY_DIR}/googletest/googlemock/gtest)
    endif()
  endforeach()
endforeach()
