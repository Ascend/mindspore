file(GLOB_RECURSE CUDA_OPS_SRC_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cu")

if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-delete-non-abstract-non-virtual-dtor -Wno-overloaded-virtual")
endif()

set_property(SOURCE ${CUDA_OPS_SRC_LIST} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_KERNEL)
if(ENABLE_GPU)
    add_library(cuda_common_obj OBJECT cuda_common.cc)
    target_compile_features(cuda_common_obj PRIVATE cxx_std_17)
    target_link_libraries(cuda_common_obj PUBLIC $<$<BOOL:${USE_GLOG}>:mindspore::glog> CUDA::cudart)
    add_library(cuda_ops SHARED ${CUDA_OPS_SRC_LIST} $<TARGET_OBJECTS:cuda_common_obj>)
    target_link_libraries(cuda_ops PUBLIC CUDA::cudart)
    message("add gpu lib to cuda_ops")
    target_link_libraries(cuda_ops PUBLIC mindspore_core CUDA::cublas
            CUDA::curand
            ${CUDNN_LIBRARY_PATH}
            CUDA::cudart
            CUDA::cuda_driver
            CUDA::cusolver
            CUDA::cufft)
endif()