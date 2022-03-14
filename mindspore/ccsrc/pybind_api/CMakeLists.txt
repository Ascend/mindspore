file(GLOB_RECURSE _PYBIND_API_SRC_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cc")
set_property(SOURCE ${_PYBIND_API_SRC_LIST} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_COMMON)
add_library(_mindspore_pybind_api_obj OBJECT ${_PYBIND_API_SRC_LIST})
target_link_libraries(_mindspore_pybind_api_obj PUBLIC core_headers mindspore::protobuf mindspore::pybind11_module
                                                       $<$<BOOL:${USE_GLOG}>:mindspore::glog>)

if("${ENABLE_HIDDEN}" STREQUAL "OFF")
    string(REPLACE " -Werror " " " CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    string(REPLACE " -fvisibility=hidden" " -fvisibility=default" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
endif()
