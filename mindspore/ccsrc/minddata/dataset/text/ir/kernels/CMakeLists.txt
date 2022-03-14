file(GLOB_RECURSE _CURRENT_SRC_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cc")
set_property(SOURCE ${_CURRENT_SRC_FILES} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_MD)

set(DATASET_TEXT_IR_KERNELS_SRC_FILES
        text_ir.cc
        )

add_library(text-ir-kernels OBJECT ${DATASET_TEXT_IR_KERNELS_SRC_FILES})
target_link_libraries(text-ir-kernels PUBLIC core_headers
                                             mindspore::protobuf
                                             mindspore::json
                                             mindspore::pybind11_module
                                             mindspore::icuuc
                                             $<$<BOOL:${ENABLE_MINDDATA}>:mindspore::cppjieba>
                                             $<$<BOOL:${ENABLE_MINDDATA}>:mindspore::sentencepiece>
                                             $<$<BOOL:${USE_GLOG}>:mindspore::glog>)
