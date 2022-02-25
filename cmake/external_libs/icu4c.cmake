set(LIB_ICU_COMMON icuuc)
set(LIB_ICU_DATA icudata)
set(LIB_ICU_I18N icui18n)

if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/icu/repository/archive/release-67-1.tar.gz")
  set(MD5 "0c2662a2b0bc80b0eb56495205247c8f")
else()
  set(REQ_URL "https://github.com/unicode-org/icu/archive/release-67-1.tar.gz")
  set(MD5 "fd525fb47d8827b0b7da78b51dd2d93f")
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
  message("icu4c thirdparty do not support windows currently.")
else()
  set(JSON_FILE
      "{ \n\
  \"strategy\": \"additive\",\n\
  \"featureFilters\": {\n\
    \"normalization\": \"include\"\n\
  }\n\
}\
    ")
  file(WRITE ${CMAKE_BINARY_DIR}/icu4c_filter.json ${JSON_FILE})
  if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set(PATCHES ${CMAKE_SOURCE_DIR}/third_party/patch/icu4c/icu4c.patch01)
    set(CONFIGURE_COMMAND ./icu4c/source/runConfigureICU MacOSX --disable-tests --disable-samples --disable-icuio
                          --disable-extras ICU_DATA_FILTER_FILE=${CMAKE_BINARY_DIR}/icu4c_filter.json)
  else()
    set(PATCHES ${TOP_DIR}/third_party/patch/icu4c/icu4c.patch01)
    set(CONFIGURE_COMMAND ./icu4c/source/runConfigureICU Linux --enable-rpath --disable-tests --disable-samples
                          --disable-icuio --disable-extras ICU_DATA_FILTER_FILE=${CMAKE_BINARY_DIR}/icu4c_filter.json)
  endif()

  mindspore_add_pkg(
    ICU
    VER 67.1
    LIBS ${LIB_ICU_COMMON} ${LIB_ICU_DATA} ${LIB_ICU_I18N}
    LIBS_CMAKE_NAMES uc data i18n
    URL ${REQ_URL}
    MD5 ${MD5}
    PATCHES ${PATCHES}
    CONFIGURE_COMMAND ${CONFIGURE_COMMAND}
    GEN_CMAKE_CONFIG
    TARGET_ALIAS mindspore::icuuc ICU::uc
    TARGET_ALIAS mindspore::icudata ICU::data
    TARGET_ALIAS mindspore::icui18n ICU::i18n)

  if(CMAKE_SYSTEM_NAME MATCHES "Darwin" AND NOT MS_ICU_PREFER_SYSTEM)
    include(${CMAKE_SOURCE_DIR}/cmake/change_rpath.cmake)
    changerpath($<TARGET_FILE:ICU::uc> ${LIB_ICU_COMMON} "libicuuc;libicudata")
    changerpath($<TARGET_FILE:ICU::data> ${LIB_ICU_DATA} "libicudata")
    changerpath($<TARGET_FILE:ICU::i18n> ${LIB_ICU_I18N} "libicuuc;libicudata;libicui18n")
  endif()
  add_definitions(-DENABLE_ICU4C)
endif()
