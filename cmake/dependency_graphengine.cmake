message(STATUS "Compiling GraphEngine")
if(NOT(BUILD_LITE))
    set(GE_SOURCE_DIR ${CMAKE_SOURCE_DIR}/graphengine)
else()
    set(GE_SOURCE_DIR ${CMAKE_SOURCE_DIR}/../../graphengine)
endif()

message(STATUS "[ME] build_path: ${BUILD_PATH}")

function(find_submodule_lib module name path)
    find_library(${module}_LIBRARY_DIR NAMES ${name} NAMES_PER_DIR PATHS ${path}
            PATH_SUFFIXES lib
            )
    if("${${module}_LIBRARY_DIR}" STREQUAL "${module}_LIBRARY_DIR-NOTFOUND")
        message(FATAL_ERROR "${name} not found in any of following paths: ${path}")
    endif()
    add_library(${module} SHARED IMPORTED)
    set_target_properties(${module} PROPERTIES
            IMPORTED_LOCATION ${${module}_LIBRARY_DIR}
            )
endfunction()

function(ge_protobuf_generate c_var h_var)
    common_protobuf_generate(${CMAKE_BINARY_DIR}/proto/ge/proto ${c_var} ${h_var} ${ARGN})
    set(${c_var} ${${c_var}} PARENT_SCOPE)
    set(${h_var} ${${h_var}} PARENT_SCOPE)
endfunction()

if(ENABLE_TESTCASES OR MODE_ASCEND_ALL OR MODE_ASCEND_ACL)
    if(NOT(BUILD_LITE))
        file(GLOB_RECURSE GE_PROTO_FILE RELATIVE ${CMAKE_SOURCE_DIR} "graphengine/metadef/proto/*.proto")
    else()
        file(GLOB_RECURSE GE_PROTO_FILE ${TOP_DIR}/graphengine/metadef/proto/*.proto)
    endif()
    set(TMP_FILE_NAME_LIST)
    foreach(file ${GE_PROTO_FILE})
        get_filename_component(file_name ${file} NAME_WE)
        list(FIND TMP_FILE_NAME_LIST ${file_name} OUT_VAR)
        if(NOT ${OUT_VAR} EQUAL "-1")
            list(REMOVE_ITEM GE_PROTO_FILE ${file})
        endif()
        list(APPEND TMP_FILE_NAME_LIST ${file_name})
    endforeach()
    ge_protobuf_generate(GE_PROTO_SRCS GE_PROTO_HDRS ${GE_PROTO_FILE})
    add_library(graph SHARED ${GE_PROTO_SRCS})
else()
    message(FATAL_ERROR "No compile option defined for GraphEngine, exiting")
endif()
