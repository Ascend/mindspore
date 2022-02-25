set(onednn_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2")
set(onednn_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")

if(USE_MS_THREADPOOL_FOR_DNNL)
  set(USE_MS_THREADPOOL "-DDNNL_CPU_RUNTIME=THREADPOOL")
else()
  set(USE_MS_THREADPOOL "")
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
  set(ARGS HEAD_ONLY ./include RELEASE on)
  set(VERSION 2.2)
  set(REQ_URL https://github.com/oneapi-src/oneDNN/releases/download/v2.2/dnnl_win_2.2.0_cpu_vcomp.zip)
  set(MD5 fa12c693b2ec07700d174e1e99d60a7e)
else()
  set(VERSION 2.5.0)
  if(ENABLE_GITEE)
    set(REQ_URL "https://gitee.com/mirrors/MKL-DNN/repository/archive/v2.5.2.tar.gz")
    set(MD5 "fe4819264dcac225596bd30a1756ce8c")
  else()
    set(REQ_URL "https://github.com/oneapi-src/oneDNN/archive/v2.5.2.tar.gz")
    set(MD5 "fff1c259d9f0bc87f2b3ca257acd472e")
  endif()
  set(ARGS
      CMAKE_OPTION
      -DDNNL_ARCH_OPT_FLAGS=''
      -DDNNL_BUILD_EXAMPLES=OFF
      -DDNNL_BUILD_TESTS=OFF
      ${USE_MS_THREADPOOL}
      -DDNNL_ENABLE_CONCURRENT_EXEC=ON)
endif()

mindspore_add_pkg(
  DNNL
  VER ${VERSION}
  LIBS dnnl
  URL ${REQ_URL}
  MD5 ${MD5} ${ARGS}
  TARGET_ALIAS mindspore::dnnl DNNL::dnnl
  TARGET_ALIAS mindspore::mkldnn DNNL::dnnl)
