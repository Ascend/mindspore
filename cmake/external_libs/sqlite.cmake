if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/sqlite/repository/archive/version-3.36.0.tar.gz")
  set(MD5 "715df9c2d2ccf6207158d6c087f711cf")
else()
  set(REQ_URL "https://github.com/sqlite/sqlite/archive/version-3.36.0.tar.gz")
  set(MD5 "715df9c2d2ccf6207158d6c087f711cf")
endif()

if(WIN32)
  set(REQ_URL https://sqlite.org/2021/sqlite-amalgamation-3360000.zip)
  set(MD5 c5d360c74111bafae1b704721ff18fe6)
  set(PATCHES ${CMAKE_SOURCE_DIR}/third_party/patch/sqlite/sqlite.windows.patch002)
else()
  set(sqlite_USE_STATIC_LIBS ON)
  set(sqlite_CXXFLAGS)
  if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    set(sqlite_CFLAGS "-fstack-protector-all -Wno-uninitialized -Wno-unused-parameter -fPIC -D_FORTIFY_SOURCE=2 \
          -O2")
  else()
    set(sqlite_CFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -fPIC \
          -D_FORTIFY_SOURCE=2 -O2")
    set(sqlite_LDFLAGS "-Wl,-z,relro,-z,now,-z,noexecstack")
  endif()
  set(CONFIGURE_COMMAND CONFIGURE_COMMAND ./configure --enable-shared=no --disable-tcl --disable-editline
                        --enable-json1)
endif()
mindspore_add_pkg(
  sqlite
  VER 3.36.0
  LIBS sqlite3
  URL ${REQ_URL}
  MD5 ${MD5} ${PATCHES} ${CONFIGURE_COMMAND}
  CMAKE_OPTION " "
  TARGET_ALIAS mindspore::sqlite sqlite::sqlite3)

include_directories(${sqlite_INC})
