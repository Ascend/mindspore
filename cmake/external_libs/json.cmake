if(MSVC)
  set(flatbuffers_CXXFLAGS "${CMAKE_CXX_FLAGS}")
  set(flatbuffers_CFLAGS "${CMAKE_CXX_FLAGS}")
  set(flatbuffers_LDFLAGS "${CMAKE_SHARED_LINKER_FLAGS}")
else()
  set(nlohmann_json373_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2")
  set(nlohmann_json373_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")
endif()

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/JSON-for-Modern-CPP/repository/archive/v3.7.3.tar.gz")
  set(MD5 "b758acca4f3e133bacf919e31ca302e3")
  set(INCLUDE "./include")
else()
  set(REQ_URL "https://github.com/nlohmann/json/archive/v3.7.3.tar.gz")
  set(MD5 "846bbc611ce9ecd7d45d6554679245e1")
  set(INCLUDE "./include")
endif()

mindspore_add_pkg(
  nlohmann_json
  VER 3.7.3
  CMAKE_PKG_NO_COMPONENTS
  URL ${REQ_URL}
  MD5 ${MD5}
  CMAKE_OPTION -DBUILD_TESTING=OFF -DJSON_MultipleHeaders=ON
  TARGET_ALIAS mindspore::json nlohmann_json::nlohmann_json)
include_directories(${nlohmann_json_INC})
