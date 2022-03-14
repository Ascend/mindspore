file(GLOB_RECURSE _EXPORTER_IR_SRC_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cc")
file(STRINGS "${CMAKE_SOURCE_DIR}/version.txt" VERSION)
add_definitions(-DVERSION=\"${VERSION}\")
set_property(SOURCE ${_EXPORTER_IR_SRC_FILES} PROPERTY COMPILE_DEFINITIONS
  SUBMODULE_ID=mindspore::SubModuleId::SM_EXPRESS)
add_library(_mindspore_transform_express_ir_obj OBJECT ${_EXPORTER_IR_SRC_FILES})
target_link_libraries(_mindspore_transform_express_ir_obj PRIVATE mindspore::protobuf)

if(USE_GLOG)
   target_link_libraries(_mindspore_transform_express_ir_obj PUBLIC mindspore::glog)
endif()
