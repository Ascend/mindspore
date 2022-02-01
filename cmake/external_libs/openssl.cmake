set(VER 1.1.1m)

# patch 'm' -> 0d -> 13 ('a' -> 01 -> 1, 'f' -> 06 -> 6, 'p' -> 10 -> 16, etc.)
set(VER_FOR_COMP 1.1.1.13)

string(REPLACE "." "_" _url_ver ${VER})

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/openssl/repository/archive/OpenSSL_${_url_ver}.tar.gz")
  set(MD5 "710c2368d28f1a25ab92e25b5b9b11ec")
else()
  set(REQ_URL "https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_${_url_ver}.tar.gz")
  set(MD5 "710c2368d28f1a25ab92e25b5b9b11ec")
endif()

if(${CMAKE_SYSTEM_NAME} MATCHES "Linux" OR APPLE)
  mindspore_add_pkg(
    OpenSSL
    VER ${VER_FOR_COMP}
    LIBS SSL Crypto
    URL ${REQ_URL}
    MD5 ${MD5}
    CONFIGURE_COMMAND ./config no-zlib no-shared
    GEN_CMAKE_CONFIG
    TARGET_ALIAS mindspore::ssl OpenSSL::SSL
    TARGET_ALIAS mindspore::crypto OpenSSL::Crypto)
  include_directories(${openssl_INC})
endif()
