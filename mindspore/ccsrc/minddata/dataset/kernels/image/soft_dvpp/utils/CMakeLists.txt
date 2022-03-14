file(GLOB_RECURSE _CURRENT_SRC_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cc")
set_property(SOURCE ${_CURRENT_SRC_FILES} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_MD)
if(MS_PATCHED_GLOG_NAME)
  set_property(SOURCE ${_CURRENT_SRC_FILES} PROPERTY COMPILE_DEFINITIONS google=mindspore_private)
endif()
add_library(soft-dvpp-utils OBJECT
            soft_dp.cc
            soft_dp_tools.cc
            soft_jpegd.cc
            soft_vpc.cc
            yuv_scaler_para_set.cc)
target_link_libraries(soft-dvpp-utils PUBLIC mindspore::jpeg_turbo)
if(USE_GLOG)
    message("Soft dvpp use glog to print message.")
    target_link_libraries(soft-dvpp-utils PUBLIC mindspore::glog)
else()
    add_compile_definitions(DVPP_UTST)
endif()