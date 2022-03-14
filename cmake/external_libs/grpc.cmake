set(grpc_USE_STATIC_LIBS OFF)
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(grpc_CXXFLAGS "-fstack-protector-all -Wno-uninitialized -Wno-unused-parameter -fPIC -D_FORTIFY_SOURCE=2 -O2 \
        -Dgrpc=mindspore_grpc -Dgrpc_impl=mindspore_grpc_impl -Dgrpc_core=mindspore_grpc_core")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Windows")
  set(grpc_CXXFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2")
else()
  set(grpc_CXXFLAGS "-fstack-protector-all -Wno-maybe-uninitialized -Wno-unused-parameter -D_FORTIFY_SOURCE=2 -O2 \
        -Dgrpc=mindspore_grpc -Dgrpc_impl=mindspore_grpc_impl -Dgrpc_core=mindspore_grpc_core")
  if(NOT ENABLE_GLIBCXX)
    set(grpc_CXXFLAGS "${grpc_CXXFLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
  endif()
endif()

if(NOT ${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(grpc_LDFLAGS "-Wl,-z,relro,-z,now,-z,noexecstack")
endif()

file(GLOB _dirs "${_MS_LIB_CACHE}/*")
list(PREPEND CMAKE_PREFIX_PATH ${_dirs})

if(NOT MS_PREFER_SYSTEM_PKGS AND NOT MS_PROTOBUF_PREFER_SYSTEM)
  if(NOT protobuf_DIR)
    find_package(protobuf CONFIG QUIET)
  endif()
  set(_FINDPACKAGE_PROTOBUF_CONFIG_DIR "-DProtobuf_DIR:PATH=${protobuf_DIR}")
  message("grpc using Protobuf_DIR : " ${_FINDPACKAGE_PROTOBUF_CONFIG_DIR})
else()
  # We rely on system discovery anyway so should work when building grpc
endif()

if(NOT absl_DIR)
  find_package(absl CONFIG QUIET)
endif()
set(_FINDPACKAGE_ABSL_CONFIG_DIR "-Dabsl_DIR:PATH=${absl_DIR}")
message("grpc using absl_DIR : " ${_FINDPACKAGE_ABSL_CONFIG_DIR})

if(NOT MS_PREFER_SYSTEM_PKGS AND NOT MS_RE2_PREFER_SYSTEM)
  if(NOT re2_DIR)
    find_package(re2 CONFIG QUIET)
  endif()
  set(_FINDPACKAGE_RE2_CONFIG_DIR "-Dre2_DIR:PATH=${re2_DIR}")
  message("grpc using re2_DIR : " ${_FINDPACKAGE_RE2_CONFIG_DIR})
else()
  # We rely on system discovery anyway so should work when building grpc
endif()

list(POP_FRONT CMAKE_PREFIX_PATH)

if(NOT MS_PREFER_SYSTEM_PKGS AND NOT MS_OPENSSL_PREFER_SYSTEM)
  foreach(_dir ${_dirs})
    if(_dir MATCHES ".*OpenSSL.*")
      set(OpenSSL_ROOT ${_dir})
      break()
    endif()
  endforeach()
  message(STATUS "OpenSSL_ROOT = ${OpenSSL_ROOT}")
  if(EXISTS ${OpenSSL_ROOT})
    set(_CMAKE_ARGS_OPENSSL_ROOT_DIR "-DOPENSSL_ROOT_DIR:PATH=${OpenSSL_ROOT}")
  endif()
else()
  # We rely on system discovery anyway so should work when building grpc
endif()

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/grpc/repository/archive/v1.36.1.tar.gz")
  set(MD5 "71252ebcd8e9e32a818a907dfd4b63cc")
else()
  set(REQ_URL "https://github.com/grpc/grpc/archive/v1.36.1.tar.gz")
  set(MD5 "90c93203e95e89af5f46738588217057")
endif()

mindspore_add_pkg(
  gRPC
  VER 1.36.1
  LIBS mindspore_grpc++ mindspore_grpc mindspore_gpr mindspore_upb mindspore_address_sorting
  LIBS_CMAKE_NAMES grpc++ grpc gpr upb address_sorting
  EXE grpc_cpp_plugin
  URL ${REQ_URL}
  MD5 ${MD5}
  PATCHES ${TOP_DIR}/third_party/patch/grpc/grpc.patch001
  CMAKE_OPTION
    -DCMAKE_BUILD_TYPE:STRING=Release
    -DBUILD_SHARED_LIBS=ON
    -DgRPC_INSTALL:BOOL=ON
    -DgRPC_BUILD_TESTS:BOOL=OFF
    -DgRPC_PROTOBUF_PROVIDER:STRING=package
    -DgRPC_PROTOBUF_PACKAGE_TYPE:STRING=CONFIG
    ${_FINDPACKAGE_PROTOBUF_CONFIG_DIR}
    -DgRPC_ZLIB_PROVIDER:STRING=package
    -DZLIB_ROOT:PATH=${zlib_ROOT}
    -DgRPC_ABSL_PROVIDER:STRING=package
    ${_FINDPACKAGE_ABSL_CONFIG_DIR}
    -DgRPC_CARES_PROVIDER:STRING=package
    -Dc-ares_DIR:PATH=${c-ares_ROOT}/lib/cmake/c-ares
    -DgRPC_SSL_PROVIDER:STRING=package
    ${_CMAKE_ARGS_OPENSSL_ROOT_DIR}
    -DgRPC_RE2_PROVIDER:STRING=package
    ${_FINDPACKAGE_RE2_CONFIG_DIR}
  TARGET_ALIAS mindspore::grpc++ gRPC::grpc++)

# modify mindspore macro define

# add_compile_definitions(grpc=mindspore_grpc)

# add_compile_definitions(grpc_impl=mindspore_grpc_impl)

# add_compile_definitions(grpc_core=mindspore_grpc_core)

function(ms_grpc_generate c_var h_var)
  if(NOT ARGN)
    message(SEND_ERROR "Error: ms_grpc_generate() called without any proto files")
    return()
  endif()

  set(${c_var})
  set(${h_var})

  foreach(file ${ARGN})
    get_filename_component(abs_file ${file} ABSOLUTE)
    get_filename_component(file_name ${file} NAME_WE)
    get_filename_component(file_dir ${abs_file} PATH)
    file(RELATIVE_PATH rel_path ${CMAKE_CURRENT_SOURCE_DIR} ${file_dir})

    list(APPEND ${c_var} "${CMAKE_BINARY_DIR}/proto/${file_name}.pb.cc")
    list(APPEND ${h_var} "${CMAKE_BINARY_DIR}/proto/${file_name}.pb.h")
    list(APPEND ${c_var} "${CMAKE_BINARY_DIR}/proto/${file_name}.grpc.pb.cc")
    list(APPEND ${h_var} "${CMAKE_BINARY_DIR}/proto/${file_name}.grpc.pb.h")

    add_custom_command(
      OUTPUT "${CMAKE_BINARY_DIR}/proto/${file_name}.pb.cc" "${CMAKE_BINARY_DIR}/proto/${file_name}.pb.h"
             "${CMAKE_BINARY_DIR}/proto/${file_name}.grpc.pb.cc" "${CMAKE_BINARY_DIR}/proto/${file_name}.grpc.pb.h"
      WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
      COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/proto"
      COMMAND protobuf::protoc --version
      COMMAND protobuf::protoc -I${file_dir} --cpp_out=${CMAKE_BINARY_DIR}/proto --grpc_out=${CMAKE_BINARY_DIR}/proto
              --plugin=protoc-gen-grpc=$<TARGET_FILE:gRPC::grpc_cpp_plugin> ${abs_file}
      DEPENDS protobuf::protoc gRPC::grpc_cpp_plugin ${abs_file}
      COMMENT "Running C++ gRPC compiler on ${file}"
      VERBATIM)
  endforeach()

  set_source_files_properties(${${c_var}} ${${h_var}} PROPERTIES GENERATED TRUE)
  set(${c_var}
      ${${c_var}}
      PARENT_SCOPE)
  set(${h_var}
      ${${h_var}}
      PARENT_SCOPE)
endfunction()
