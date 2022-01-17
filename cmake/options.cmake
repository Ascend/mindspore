option(ENABLE_D "Enable d" OFF)
option(ENABLE_GPU "Enable gpu" OFF)
option(ENABLE_CPU "Enable cpu" OFF)
option(ENABLE_MINDDATA "Enable minddata compile" OFF)
option(ENABLE_TESTCASES "Run testcases switch, default off" OFF)
option(ENABLE_CPP_ST "Run cpp st testcases switch, default off" OFF)
option(DEBUG_MODE "Debug mode, default off" OFF)
option(ENABLE_ASAN "Enable Google Sanitizer to find memory bugs")
option(ENABLE_LOAD_ANF_IR "Enable load ANF-IR as input of 'infer' stage of pipeline" OFF)
option(ENABLE_COVERAGE "Enable code coverage report" OFF)
option(USE_GLOG "Use glog to output log" OFF)
option(ENABLE_SECURITY "Enable security, maintenance function will be disabled, default off" OFF)
option(ENABLE_PROFILE "Enable pipeline profile, default off" OFF)
option(ENABLE_TIMELINE "Enable time line record" OFF)
option(ENABLE_DUMP_PROTO "Enable dump anf graph to file in ProtoBuffer format, default on" ON)
option(ENABLE_DUMP_IR "Enable dump function graph ir, default on" ON)
option(ENABLE_MPI "enable mpi" OFF)
option(ENABLE_AKG "enable akg" OFF)
option(ENABLE_DEBUGGER "enable debugger" OFF)
option(ENABLE_IBVERBS "enable IBVERBS for parameter server" OFF)
option(ENABLE_PYTHON "Enable python" ON)
option(ENABLE_ACL "enable acl" OFF)
option(ENABLE_GLIBCXX "enable_glibcxx" OFF)
option(MODE_ASCEND_ALL "supports all ascend platform" OFF)
option(MODE_ASCEND_ACL "supports ascend acl mode only" OFF)
option(ENABLE_SYM_FILE "enable sym file" OFF)
option(BUILD_DEV_MODE "MindSpore build nightly dev mode" OFF)
option(ENABLE_FAST_HASH_TABLE "Enable use fast hash table instead of std ones" ON)
option(USE_LLVM "use llvm" OFF)
option(USE_MS_THREADPOOL_FOR_DNNL "use ms threadpool for onednn ops" ON)

if(NOT CMAKE_SYSTEM_NAME MATCHES "Linux")
    set(USE_MS_THREADPOOL_FOR_DNNL OFF)
endif()

if(NOT ENABLE_D AND NOT ENABLE_TESTCASES AND NOT ENABLE_ACL)
    set(ENABLE_GLIBCXX ON)
endif()

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    if(WIN32)
        set(OPTION_CXX_FLAGS "${OPTION_CXX_FLAGS} -fstack-protector-all")
    else()
        set(OPTION_CXX_FLAGS "${OPTION_CXX_FLAGS} -fstack-protector-all -Wl,-z,relro,-z,now,-z,noexecstack")
    endif()
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set(OPTION_CXX_FLAGS "${OPTION_CXX_FLAGS} -Wsign-compare")
endif()

if(ENABLE_COVERAGE)
    set(COVERAGE_COMPILER_FLAGS "-g --coverage -fprofile-arcs -ftest-coverage")
    set(OPTION_CXX_FLAGS "${OPTION_CXX_FLAGS} ${COVERAGE_COMPILER_FLAGS}")
endif()

if(ENABLE_ASAN)
    set(OPTION_CXX_FLAGS "${OPTION_CXX_FLAGS} -fsanitize=address -fsanitize-recover=address -fno-omit-frame-pointer")
    if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        set(OPTION_CXX_FLAGS "${OPTION_CXX_FLAGS} -static-libsan")
    endif()
endif()

if(DEBUG_MODE)
    set(CMAKE_BUILD_TYPE "Debug")
    add_compile_definitions(MEM_REUSE_DEBUG)
else()
    set(CMAKE_BUILD_TYPE "Release")
endif()

if((CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64") OR (CMAKE_BUILD_TYPE STREQUAL Release))
    set(PYBIND11_LTO_CXX_FLAGS FALSE)
endif()

if(NOT BUILD_PATH)
    set(BUILD_PATH "${CMAKE_SOURCE_DIR}/build")
endif()

if(ENABLE_D)
    set(ENABLE_TDTQUE ON)
endif()

if(ENABLE_GPU)
    set(ENABLE_GPUQUE ON)
    add_compile_definitions(ENABLE_GPU_COLLECTIVE)
endif()

if(ENABLE_CPU)
    add_compile_definitions(ENABLE_CPU)
endif()

if(ENABLE_D)
    add_compile_definitions(ENABLE_D)
    add_compile_definitions(CUSTOM_OP)
endif()

if(USE_GLOG)
    add_compile_definitions(USE_GLOG)
endif()

if(ENABLE_PROFILE)
    add_compile_definitions(ENABLE_PROFILE)
endif()

if(ENABLE_SECURITY)
    add_compile_definitions(ENABLE_SECURITY)
endif()

if(ENABLE_TIMELINE)
    add_compile_definitions(ENABLE_TIMELINE)
endif()

if(ENABLE_LOAD_ANF_IR)
    add_compile_definitions(ENABLE_LOAD_ANF_IR)
endif()

if(ENABLE_TESTCASES OR (NOT ENABLE_D))
    add_compile_definitions(NO_DLIB=1)
endif()

if(ENABLE_DUMP_IR)
    add_compile_definitions(ENABLE_DUMP_IR)
endif()

if(ENABLE_MINDDATA)
    add_compile_definitions(ENABLE_MINDDATA)
    if(ENABLE_TDTQUE)
        add_compile_definitions(ENABLE_TDTQUE)
    endif()
endif()

if(ENABLE_DEBUGGER)
    add_compile_definitions(ENABLE_DEBUGGER)
endif()

if(ENABLE_DEBUGGER OR ENABLE_TESTCASES)
    set(MS_BUILD_GRPC ON)
endif()
if(ENABLE_MINDDATA AND NOT CMAKE_SYSTEM_NAME MATCHES "Windows")
    set(MS_BUILD_GRPC ON)
endif()

if(ENABLE_D AND ENABLE_ACL)
    set(MODE_ASCEND_ALL ON)
endif()

if(ENABLE_ACL AND NOT ENABLE_D)
    set(MODE_ASCEND_ACL ON)
endif()

if(ENABLE_CPU AND NOT WIN32)
    add_compile_definitions(ENABLE_ARMOUR)
endif()

if(ENABLE_AKG AND CMAKE_SYSTEM_NAME MATCHES "Linux")
    add_compile_definitions(ENABLE_AKG)
endif()

if(USE_LLVM)
    add_compile_definitions(USE_LLVM)
endif()

if(USE_MS_THREADPOOL_FOR_DNNL)
    add_compile_definitions(USE_MS_THREADPOOL_FOR_DNNL)
endif()
