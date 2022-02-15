if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/c-ares/repository/archive/cares-1_17_2.tar.gz")
  set(MD5 "59cd1207df8f9522797535245e12b871")
else()
  set(REQ_URL "https://github.com/c-ares/c-ares/releases/download/cares-1_17_2/c-ares-1.17.2.tar.gz")
  set(MD5 "3802264830c6886411dac606c66fdbf8")
endif()

mindspore_add_pkg(
  c-ares
  VER 1.17.2
  LIBS cares
  URL ${REQ_URL}
  MD5 ${MD5}
  PATCHES ${TOP_DIR}/third_party/patch/c-ares/c-ares.patch001
  CMAKE_OPTION -DCMAKE_BUILD_TYPE:STRING=Release -DCARES_SHARED:BOOL=OFF -DCARES_STATIC:BOOL=ON
               -DCARES_STATIC_PIC:BOOL=ON -DHAVE_LIBNSL:BOOL=OFF
  TARGET_ALIAS mindspore::cares c-ares::cares)

include_directories(${c-ares_INC})
