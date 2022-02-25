set(libevent_CFLAGS "-fstack-protector-all -D_FORTIFY_SOURCE=2 -O2")
if(NOT CMAKE_SYSTEM_NAME MATCHES "Darwin")
  set(libevent_LDFLAGS "-Wl,-z,now")
endif()

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/libevent/repository/archive/release-2.1.12-stable.tar.gz")
  set(MD5 "0d5a27436bf7ff8253420c8cf09f47ca")
else()
  set(REQ_URL
      "https://github.com/libevent/libevent/releases/download/release-2.1.12-stable/libevent-2.1.12-stable.tar.gz")
  set(MD5 "b5333f021f880fe76490d8a799cd79f4")
endif()

message("libevent using openssl stub dir: " ${openssl_ROOT})

mindspore_add_pkg(
  Libevent
  NS_NAME libevent
  VER 2.1.12
  LIBS event_pthreads event_core event_extra event_openssl
  LIBS_CMAKE_NAMES pthreads core extra openssl
  URL ${REQ_URL}
  MD5 ${MD5}
  PATCHES ${CMAKE_SOURCE_DIR}/third_party/patch/libevent/libevent.patch001
  CMAKE_OPTION -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_TESTING=OFF -DOPENSSL_ROOT_DIR:PATH=${openssl_ROOT}
  TARGET_ALIAS mindspore::event_extra libevent::extra
  TARGET_ALIAS mindspore::event_pthreads libevent::pthreads
  TARGET_ALIAS mindspore::event_core libevent::core
  TARGET_ALIAS mindspore::event_openssl libevent::openssl)
