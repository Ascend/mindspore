file(GLOB_RECURSE _CURRENT_SRC_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cc")
set_property(SOURCE ${_CURRENT_SRC_FILES} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_MD)
if(NOT ${CMAKE_SYSTEM_NAME} MATCHES "Linux")
  LIST(REMOVE_ITEM _CURRENT_SRC_FILES numa_interface.cc)
endif()
add_library(utils OBJECT ${_CURRENT_SRC_FILES})
target_link_libraries(utils PUBLIC core_headers mindspore::protobuf mindspore::json mindspore::pybind11_module
                                   $<$<BOOL:${ENABLE_GPU}>:CUDA::cudart> $<$<BOOL:${USE_GLOG}>:mindspore::glog>)
