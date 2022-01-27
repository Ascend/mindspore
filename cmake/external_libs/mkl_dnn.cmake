set(onednn_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2")
set(onednn_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")

if(USE_MS_THREADPOOL_FOR_DNNL)
  set(USE_MS_THREADPOOL "-DDNNL_CPU_RUNTIME=THREADPOOL")
else()
  set(USE_MS_THREADPOOL "")
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
  set(ARGS HEAD_ONLY ./include RELEASE on)

  set(REQ_URL https://github.com/oneapi-src/oneDNN/releases/download/v2.2/dnnl_win_2.2.0_cpu_vcomp.zip)
  set(MD5 fa12c693b2ec07700d174e1e99d60a7e)
else()
  if(ENABLE_GITEE)
    set(REQ_URL "https://gitee.com/mirrors/MKL-DNN/repository/archive/v2.2.tar.gz")
    set(MD5 "49c650e0cc24ef9ae7033d4cb22ebfad")
  else()
    set(REQ_URL "https://github.com/oneapi-src/oneDNN/archive/v2.2.tar.gz")
    set(MD5 "6a062e36ea1bee03ff55bf44ee243e27")
  endif()
  set(ARGS
      PATCHES
      ${CMAKE_SOURCE_DIR}/third_party/patch/onednn/0001-fix-user-threadpool-bug.patch
      PATCHES
      ${CMAKE_SOURCE_DIR}/third_party/patch/onednn/0002-fix-pool-nthr-bug.patch
      CMAKE_OPTION
      -DDNNL_ARCH_OPT_FLAGS=''
      -DDNNL_BUILD_EXAMPLES=OFF
      -DDNNL_BUILD_TESTS=OFF
      ${USE_MS_THREADPOOL}
      -DDNNL_ENABLE_CONCURRENT_EXEC=ON)
endif()

mindspore_add_pkg(
  onednn
  VER 2.2
  LIBS dnnl mkldnn
  URL ${REQ_URL}
  MD5 ${MD5} ${ARGS}
  TARGET_ALIAS mindspore::dnnl onednn::dnnl
  TARGET_ALIAS mindspore::mkldnn onednn::mkldnn)

include_directories(${onednn_INC})
