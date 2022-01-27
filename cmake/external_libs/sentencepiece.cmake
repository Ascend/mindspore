if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/sentencepiece/repository/archive/v0.1.92.tar.gz")
  set(MD5 "0fc99de9f09b9184398f49647791799f")
else()
  set(REQ_URL "https://github.com/google/sentencepiece/archive/v0.1.92.tar.gz")
  set(MD5 "5dfd2241914b5598a68b2a8542ed8e91")
endif()

set(CMAKE_OPTION -DCMAKE_BUILD_TYPE=Release -DSPM_ENABLE_SHARED=OFF)

if(WIN32)
  set(sentencepiece_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2 -Wno-unused-result -Wno-stringop-overflow \
        -Wno-format-extra-args -Wno-format")
  set(sentencepiece_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")
  list(APPEND CMAKE_OPTION -DSPM_USE_BUILTIN_PROTOBUF=ON)
else()
  set(sentencepiece_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2 -Wno-unused-result -Wno-sign-compare")
  set(sentencepiece_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")
  list(APPEND CMAKE_OPTION -DSPM_USE_BUILTIN_PROTOBUF=OFF)
  if(ENABLE_GLIBCXX)
    set(PATCHES PATCHES ${CMAKE_SOURCE_DIR}/third_party/patch/sentencepiece/sentencepiece.patch001_cpu)
    list(APPEND CMAKE_OPTION -DPROTOBUF_INC=${protobuf_INC} -DCMAKE_CXX_STANDARD=11)
  else()
    set(PATCHES PATCHES ${TOP_DIR}/third_party/patch/sentencepiece/sentencepiece.patch001)
    list(APPEND CMAKE_OPTION -DPROTOBUF_INC=${protobuf_INC})
  endif()
endif()

mindspore_add_pkg(
  sentencepiece
  VER 0.1.92
  LIBS sentencepiece sentencepiece_train
  URL ${REQ_URL}
  CMAKE_OPTION ${CMAKE_OPTION}
  MD5 ${MD5} ${PATCHES}
  TARGET_ALIAS mindspore::sentencepiece sentencepiece::sentencepiece
  TARGET_ALIAS mindspore::sentencepiece_train sentencepiece::sentencepiece_train)

include_directories(${sentencepiece_INC})
