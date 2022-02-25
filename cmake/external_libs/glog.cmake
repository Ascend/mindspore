if(BUILD_LITE)
  if(MSVC)
    set(flatbuffers_CXXFLAGS "${CMAKE_CXX_FLAGS}")
    set(flatbuffers_CFLAGS "${CMAKE_C_FLAGS}")
    set(flatbuffers_LDFLAGS "${CMAKE_SHARED_LINKER_FLAGS}")
  else()
    set(glog_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2 ${SECURE_CXX_FLAGS} -Dgoogle=mindspore_private")
    set(glog_CFLAGS "-D_FORTIFY_SOURCE=2 -O2 ${SECURE_C_FLAGS}")
    set(glog_LDFLAGS "${SECURE_SHARED_LINKER_FLAGS}")
  endif()
  set(glog_patch "")
else()
  set(glog_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2 ${SECURE_CXX_FLAGS} -Dgoogle=mindspore_private")
  set(glog_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")
  set(glog_patch ${CMAKE_SOURCE_DIR}/third_party/patch/glog/glog.patch001)
endif()

if(NOT ENABLE_GLIBCXX)
  set(glog_CXXFLAGS "${glog_CXXFLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
endif()

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/glog/repository/archive/v0.4.0.tar.gz")
  set(MD5 "9a7598a00c569a11ff1a419076de4ed7")
else()
  set(REQ_URL "https://github.com/google/glog/archive/v0.4.0.tar.gz")
  set(MD5 "0daea8785e6df922d7887755c3d100d0")
endif()

set(glog_option -DBUILD_TESTING=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=ON -DWITH_GFLAGS=OFF
                -DCMAKE_BUILD_TYPE=Release)

if(WIN32 AND NOT MSVC)
  execute_process(COMMAND "${CMAKE_C_COMPILER}" -dumpmachine OUTPUT_VARIABLE i686_or_x86_64)
  if(i686_or_x86_64 MATCHES "^i686-")
    set(glog_option ${glog_option} -DHAVE_DBGHELP=ON)
  endif()
endif()

mindspore_add_pkg(
  glog
  VER 0.4.0
  LIBS glog
  URL ${REQ_URL}
  MD5 ${MD5}
  PATCHES ${glog_patch}
  CMAKE_OPTION ${glog_option}
  TARGET_ALIAS mindspore::glog glog::glog)

if(NOT MS_PREFER_SYSTEM_PKGS AND NOT MS_GLOG_PREFER_SYSTEM)
  set(MS_PATCHED_GLOG_NAME
      TRUE
      CACHE INTERNAL "")
  target_compile_definitions(glog::glog INTERFACE MS_PATCHED_GLOG_NAME)
else()
  set(MS_PATCHED_GLOG_NAME
      FALSE
      CACHE INTERNAL "")
endif()
