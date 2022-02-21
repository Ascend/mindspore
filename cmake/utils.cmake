include(FetchContent)
set(FETCHCONTENT_QUIET OFF)

if(CMAKE_SYSTEM_NAME MATCHES "Windows" AND ${CMAKE_VERSION} VERSION_GREATER_EQUAL 3.17.0)
  set(CMAKE_FIND_LIBRARY_SUFFIXES .dll ${CMAKE_FIND_LIBRARY_SUFFIXES})
endif()

function(mindspore_add_submodule_obj des_submodule_objs sub_dir submodule_name_obj)

  add_subdirectory(${sub_dir})

  if(NOT TARGET ${submodule_name_obj})
    message(FATAL_ERROR "Can not find submodule '${submodule_name_obj}'. in ${CMAKE_CURRENT_LIST_FILE}")
  endif()
  if("$<TARGET_OBJECTS:${submodule_name_obj}>" IN_LIST ${des_submodule_objs})
    message(FATAL_ERROR "submodule '${submodule_name_obj}' added more than once. in ${CMAKE_CURRENT_LIST_FILE}")
  endif()

  set(${des_submodule_objs}
      ${${des_submodule_objs}} $<TARGET_OBJECTS:${submodule_name_obj}>
      PARENT_SCOPE)

endfunction()

if(DEFINED ENV{MSLIBS_CACHE_PATH})
  set(_MS_LIB_CACHE $ENV{MSLIBS_CACHE_PATH})
else()
  set(_MS_LIB_CACHE ${CMAKE_BINARY_DIR}/.mslib)
endif()
message(STATUS "MS LIBS CACHE PATH:  ${_MS_LIB_CACHE}")

if(NOT EXISTS ${_MS_LIB_CACHE})
  file(MAKE_DIRECTORY ${_MS_LIB_CACHE})
endif()

if(DEFINED ENV{MSLIBS_SERVER} AND NOT ENABLE_GITEE)
  set(LOCAL_LIBS_SERVER $ENV{MSLIBS_SERVER})
  message(STATUS "LOCAL_LIBS_SERVER:  ${LOCAL_LIBS_SERVER}")
endif()

include(ProcessorCount)
ProcessorCount(N)
if(JOBS)
  set(THNUM ${JOBS})
else()
  set(JOBS 8)
  if(${JOBS} GREATER ${N})
    set(THNUM ${N})
  else()
    set(THNUM ${JOBS})
  endif()
endif()
message(STATUS "set make thread num: ${THNUM}")

if(LOCAL_LIBS_SERVER)
  if(NOT ENV{no_proxy})
    set(ENV{no_proxy} "${LOCAL_LIBS_SERVER}")
  else()
    string(FIND $ENV{no_proxy} ${LOCAL_LIBS_SERVER} IP_POS)
    if(${IP_POS} EQUAL -1)
      set(ENV{no_proxy} "$ENV{no_proxy},${LOCAL_LIBS_SERVER}")
    endif()
  endif()
endif()

function(__download_pkg pkg_name pkg_url pkg_md5)

  if(LOCAL_LIBS_SERVER)
    get_filename_component(_URL_FILE_NAME ${pkg_url} NAME)
    set(pkg_url "http://${LOCAL_LIBS_SERVER}:8081/libs/${pkg_name}/${_URL_FILE_NAME}" ${pkg_url})
  endif()

  FetchContent_Declare(
    ${pkg_name}
    URL ${pkg_url}
    URL_HASH MD5=${pkg_md5})
  FetchContent_GetProperties(${pkg_name})
  message(STATUS "download: ${${pkg_name}_SOURCE_DIR} , ${pkg_name} , ${pkg_url}")
  if(NOT ${pkg_name}_POPULATED)
    FetchContent_Populate(${pkg_name})
    string(TOLOWER ${pkg_name} _pkg_name)
    set(${pkg_name}_SOURCE_DIR
        ${${_pkg_name}_SOURCE_DIR}
        PARENT_SCOPE)
  endif()

endfunction()

function(__download_pkg_with_git pkg_name pkg_url pkg_git_commit pkg_md5)

  if(LOCAL_LIBS_SERVER)
    set(pkg_url "http://${LOCAL_LIBS_SERVER}:8081/libs/${pkg_name}/${pkg_git_commit}")
    FetchContent_Declare(
      ${pkg_name}
      URL ${pkg_url}
      URL_HASH MD5=${pkg_md5})
  else()
    FetchContent_Declare(
      ${pkg_name}
      GIT_REPOSITORY ${pkg_url}
      GIT_TAG ${pkg_git_commit})
  endif()
  FetchContent_GetProperties(${pkg_name})
  message(STATUS "download: ${${pkg_name}_SOURCE_DIR} , ${pkg_name} , ${pkg_url}")
  if(NOT ${pkg_name}_POPULATED)
    FetchContent_Populate(${pkg_name})
    string(TOLOWER ${pkg_name} _pkg_name)
    set(${pkg_name}_SOURCE_DIR
        ${${_pkg_name}_SOURCE_DIR}
        PARENT_SCOPE)
  endif()

endfunction()

function(__exec_cmd)
  set(options)
  set(oneValueArgs WORKING_DIRECTORY)
  set(multiValueArgs COMMAND)

  cmake_parse_arguments(EXEC "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

  execute_process(
    COMMAND ${EXEC_COMMAND}
    WORKING_DIRECTORY ${EXEC_WORKING_DIRECTORY}
    RESULT_VARIABLE RESULT)
  if(NOT RESULT EQUAL "0")
    message(FATAL_ERROR "error! when ${EXEC_COMMAND} in ${EXEC_WORKING_DIRECTORY}")
  endif()
endfunction()

function(__check_patches pkg_patches)
  # check patches
  if(PKG_PATCHES)
    file(TOUCH ${_MS_LIB_CACHE}/${pkg_name}_patch.md5)
    file(READ ${_MS_LIB_CACHE}/${pkg_name}_patch.md5 ${pkg_name}_PATCHES_MD5)

    message(STATUS "patches md5:${${pkg_name}_PATCHES_MD5}")

    set(${pkg_name}_PATCHES_NEW_MD5)
    foreach(_PATCH ${PKG_PATCHES})
      file(MD5 ${_PATCH} _PF_MD5)
      set(${pkg_name}_PATCHES_NEW_MD5 "${${pkg_name}_PATCHES_NEW_MD5},${_PF_MD5}")
    endforeach()

    if(NOT ${pkg_name}_PATCHES_MD5 STREQUAL ${pkg_name}_PATCHES_NEW_MD5)
      set(${pkg_name}_PATCHES ${PKG_PATCHES})
      file(REMOVE_RECURSE "${_MS_LIB_CACHE}/${pkg_name}-subbuild")
      file(WRITE ${_MS_LIB_CACHE}/${pkg_name}_patch.md5 ${${pkg_name}_PATCHES_NEW_MD5})
      message(STATUS "patches changed : ${${pkg_name}_PATCHES_NEW_MD5}")
    endif()
  endif()
endfunction()

# ~~~
# (helper function) Convert a path to CMake format
#
# to_cmake_path(<path-var>)
# ~~~
macro(to_cmake_path path_var)
  if(DEFINED ${path_var})
    if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.20)
      cmake_path(CONVERT "${${path_var}}" TO_CMAKE_PATH_LIST ${path_var} NORMALIZE)
    else()
      file(TO_CMAKE_PATH "${${path_var}}" ${path_var})
    endif()
  endif()
endmacro()

# ~~~
# Create target aliases based on a list of key-value pairs where:
#  - key: target alias name
#  - value: target to alias
#
# __create_target_aliases([[<tgt_alias>, <tgt_name>]...])
# ~~~
function(__create_target_aliases)
  list(LENGTH ARGN n_args)
  if(NOT n_args)
    return()
  endif()
  math(EXPR is_error_length "${n_args} % 2")
  if(is_error_length)
    message(FATAL_ERROR "Invalid number of arguments (key-value pairs)")
  endif()

  math(EXPR stop "${n_args} - 1")
  foreach(idx RANGE 0 ${stop} 2)
    math(EXPR idx_1 "${idx} + 1")
    list(GET ARGN ${idx} tgt_alias)
    list(GET ARGN ${idx_1} tgt_name)

    if(NOT TARGET ${tgt_name})
      message(FATAL_ERROR "Target ${tgt_name} cannot be found, not defining ${tgt_alias} alias")
    endif()

    get_target_property(_aliased ${tgt_name} ALIASED_TARGET)
    if(_aliased)
      set(tgt_name ${_aliased})
    endif()

    get_target_property(_imported ${tgt_name} IMPORTED)
    get_target_property(_imported_global ${tgt_name} IMPORTED_GLOBAL)
    if(_imported AND NOT _imported_global)
      set_property(TARGET ${tgt_name} PROPERTY IMPORTED_GLOBAL TRUE)
    endif()

    get_target_property(_aliased ${tgt_name} ALIASED_TARGET)
    if(_aliased)
      set(tgt_name ${_aliased})
    endif()

    get_target_property(_type ${tgt_name} TYPE)
    if("${_type}" STREQUAL "EXECUTABLE")
      add_executable(${tgt_alias} ALIAS ${tgt_name})
    else()
      add_library(${tgt_alias} ALIAS ${tgt_name})
    endif()
    message(STATUS "Creating alias target: ${tgt_alias} -> ${tgt_name}")
  endforeach()
endfunction()

include(FindPackageHandleStandardArgs)
# Find a Python module in the current (potential virtual) environment
#
# __find_python_module(<module> [REQUIRED|EXACT|QUIET] [VERSION <version>])
#
# Usage is similar to the builtin find_package(...)
function(__find_python_module module)
  # cmake-lint: disable=C0103
  cmake_parse_arguments(PARSE_ARGV 1 PYMOD "REQUIRED;EXACT;QUIET" "VERSION" "")

  string(REPLACE "-" "_" module_name ${module})
  string(TOUPPER ${module_name} MODULE)
  if(NOT PYMOD_${MODULE})
    if(PYMOD_REQUIRED)
      set(PYMOD_${module}_FIND_REQUIRED TRUE)
      set(PYMOD_${MODULE}_FIND_REQUIRED TRUE)
    endif()
    if(PYMOD_QUIET)
      set(PYMOD_${module}_FIND_QUIETLY TRUE)
      set(PYMOD_${MODULE}_FIND_QUIETLY TRUE)
    endif()
    if(PYMOD_EXACT)
      set(PYMOD_${module}_FIND_VERSION_EXACT TRUE)
      set(PYMOD_${MODULE}_FIND_VERSION_EXACT TRUE)
    endif()
    if(PYMOD_VERSION)
      set(PYMOD_${module}_FIND_VERSION ${PYMOD_VERSION})
      set(PYMOD_${MODULE}_FIND_VERSION ${PYMOD_VERSION})
    endif()

    execute_process(
      COMMAND "${Python_EXECUTABLE}" "-c" "import os, ${module_name}; print(os.path.dirname(${module_name}.__file__))"
      RESULT_VARIABLE _${MODULE}_status
      OUTPUT_VARIABLE _${MODULE}_location
      ERROR_QUIET OUTPUT_STRIP_TRAILING_WHITESPACE)

    if(NOT _${MODULE}_status)
      set(PYMOD_${MODULE}_PATH
          ${_${MODULE}_location}
          CACHE STRING "Location of Python module ${module}")

      if(PYMOD_VERSION)
        execute_process(
          COMMAND "${Python_EXECUTABLE}" "-c" "import ${module_name}; print(${module_name}.__version__)"
          RESULT_VARIABLE _${MODULE}_status
          OUTPUT_VARIABLE _${MODULE}_version
          ERROR_QUIET OUTPUT_STRIP_TRAILING_WHITESPACE)

        if(NOT _${MODULE}_status)
          set(PYMOD_${MODULE}_VERSION
              ${_${MODULE}_version}
              CACHE STRING "Version of Python module ${module}")
          set(PYMOD_${module}_VERSION
              ${PYMOD_${MODULE}_VERSION}
              CACHE STRING "Version of Python module ${module}")
        endif()
      endif()
    endif()
  endif()

  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.19 AND CMAKE_VERSION VERSION_LESS 3.20)
    set(CMAKE_FIND_PACKAGE_NAME PYMOD_${module})
  endif()

  find_package_handle_standard_args(
    PYMOD_${module_name}
    REQUIRED_VARS PYMOD_${MODULE}_PATH
    VERSION_VAR PYMOD_${MODULE}_VERSION NAME_MISMATCHED)

  set(PYMOD_${MODULE}_FOUND
      ${PYMOD_${MODULE}_FOUND}
      CACHE INTERNAL "")

  mark_as_advanced(PYMOD_${MODULE}_FOUND PYMOD_${MODULE}_PATH PYMOD_${MODULE}_VERSION)
endfunction()

function(__largest_common_prefix a b prefix)
  string(LENGTH "${a}" _len_a)
  string(LENGTH "${b}" _len_b)

  if(${_len_a} LESS ${_len_b})
    set(_len ${_len_a})
  else()
    set(_len ${_len_b})
  endif()

  # iterate over the length
  foreach(end RANGE 1 ${_len})
    # get substrings
    string(SUBSTRING "${a}" 0 ${end} sub_a)
    string(SUBSTRING "${b}" 0 ${end} sub_b)

    if("${sub_a}" STREQUAL "${sub_b}")
      set(${prefix}
          ${sub_a}
          PARENT_SCOPE)
    else()
      break()
    endif()
  endforeach()
endfunction()

macro(__calculate_root_dir pkg_name)
  if(NOT ${pkg_name}_ROOT)
    if(${pkg_name}_DIR)
      set(_root_dir ${${pkg_name}_DIR})
      foreach(_ RANGE 2)
        if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.20)
          cmake_path(GET _root_dir PARENT_PATH _root_dir)
        else()
          get_filename_component(_root_dir ${_root_dir} DIRECTORY)
        endif()
      endforeach()
    else()
      set(_targets ${PKG_LIBS_CMAKE_NAMES})
      list(GET ${_inc_location_var} 0 _inc_path)
      if(NOT _inc_path)
        unset(_inc_path)
      endif()
      list(GET _targets 0 _comp)
      if(TARGET ${PKG_NS_NAME}::${_comp})
        set(_target_name ${PKG_NS_NAME}::${_comp})
      elseif(TARGET ${PKG_NS_NAME}::${PKG_NS_NAME}_${_comp})
        set(_target_name ${PKG_NS_NAME}::${PKG_NS_NAME}_${_comp})
      endif()

      foreach(_prop IMPORTED_LOCATION IMPORETD_LOCATION_DEBUG IMPORTED_LOCATION_RELEASE IMPORTED_LOCATION_NONE
                    IMPORTED_LOCATION_NOCONFIG INTERFACE_LINK_LIBRARIES)
        get_target_property(_imported_location ${_target_name} ${_prop})
        if(_imported_location)
          file(TO_CMAKE_PATH "${_imported_location}" _imported_location)
          break()
        endif()
      endforeach()
      if(_imported_location)
        list(GET _imported_location 0 _lib_path)
      endif()

      if((NOT "${_inc_path}" STREQUAL "") AND (NOT "${_lib_path}" STREQUAL ""))
        __largest_common_prefix("${_inc_path}" "${_lib_path}" _root_dir)
      elseif(NOT "${_lib_path}" STREQUAL "")
        set(_root_dir ${_lib_path})
        foreach(_ RANGE 1)
          if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.20)
            cmake_path(GET _root_dir PARENT_PATH _root_dir)
          else()
            get_filename_component(_root_dir ${_root_dir} DIRECTORY)
          endif()
        endforeach()
      endif()
    endif()
    set(${pkg_name}_ROOT
        ${_root_dir}
        PARENT_SCOPE)
  endif()
endmacro()

function(__get_imported_location_from_interface_library tgt)
  set(_basename ${tgt})
  if(_tgt MATCHES "([a-zA-Z0-9_]+)::([a-zA-Z0-9_]+)")
    set(_basename ${CMAKE_MATCH_2})
    string(TOLOWER ${CMAKE_MATCH_2} _basename_lower)
  endif()

  set(_imported_location)
  get_target_property(_libs ${_tgt} INTERFACE_LINK_LIBRARIES)
  if(_libs)
    foreach(_lib ${_libs})
      if(_lib MATCHES ".*${_basename}.*" OR _lib MATCHES ".*${_basename_lower}.*")
        set(_imported_location "${_lib}")
        break()
      endif()
    endforeach()
  endif()
  set(_imported_location
      "${_imported_location}"
      PARENT_SCOPE)
endfunction()

function(__generate_pseudo_cmake_package_config dest_dir pkg_name pkg_namespace pkg_libs pkg_exe)

  set(_comps ${pkg_libs})
  if(pkg_exe)
    list(APPEND _comps ${pkg_exe})
  endif()

  find_package(
    ${pkg_name} QUIET
    COMPONENTS ${_comps}
    REQUIRED)

  # ----------------------------------------------------------------------------

  set(tgt_list)
  foreach(_comp ${_comps})
    if(TARGET ${pkg_namespace}::${_comp})
      list(APPEND tgt_list ${pkg_namespace}::${_comp})
    endif()
    if(TARGET ${pkg_namespace}::${PKG_NS_NAME}_${_comp})
      list(APPEND tgt_list ${pkg_namespace}::${PKG_NS_NAME}_${_comp})
    endif()
  endforeach()

  # ----------------------------------------------------------------------------

  file(MAKE_DIRECTORY ${dest_dir})
  string(REPLACE ";" "\;" tgt_list_escaped "${tgt_list}")

  # ----------------------------------------------------------------------------

  set(_config_version_content
      "
set(PACKAGE_VERSION \"${PKG_VER}\")

if (PACKAGE_FIND_VERSION_RANGE)
  # Package version must be in the requested version range
  if ((PACKAGE_FIND_VERSION_RANGE_MIN STREQUAL \"INCLUDE\" AND PACKAGE_VERSION VERSION_LESS PACKAGE_FIND_VERSION_MIN)
      OR ((PACKAGE_FIND_VERSION_RANGE_MAX STREQUAL \"INCLUDE\" AND PACKAGE_VERSION VERSION_GREATER PACKAGE_FIND_VERSION_MAX)
        OR (PACKAGE_FIND_VERSION_RANGE_MAX STREQUAL \"EXCLUDE\" AND PACKAGE_VERSION VERSION_GREATER_EQUAL PACKAGE_FIND_VERSION_MAX)))
    set(PACKAGE_VERSION_COMPATIBLE FALSE)
  else()
    set(PACKAGE_VERSION_COMPATIBLE TRUE)
  endif()
else()
  if(PACKAGE_VERSION VERSION_LESS PACKAGE_FIND_VERSION)
    set(PACKAGE_VERSION_COMPATIBLE FALSE)
  else()
    set(PACKAGE_VERSION_COMPATIBLE TRUE)
    if(PACKAGE_FIND_VERSION STREQUAL PACKAGE_VERSION)
      set(PACKAGE_VERSION_EXACT TRUE)
    endif()
  endif()
endif()
")
  file(WRITE ${dest_dir}/${pkg_name}ConfigVersion.cmake ${_config_version_content})

  # ----------------------------------------------------------------------------

  set(_config_content "include (\"\${CMAKE_CURRENT_LIST_DIR}/${pkg_name}Targets.cmake\")\n")
  file(WRITE ${dest_dir}/${pkg_name}Config.cmake ${_config_content})

  # ----------------------------------------------------------------------------

  set(_targets_prefix_content
      "
cmake_policy(PUSH)
cmake_policy(VERSION 2.6...3.20)

set(CMAKE_IMPORT_FILE_VERSION 1)

")

  set(_targets_suffix_content
      "

if(CMAKE_VERSION VERSION_LESS 3.0.0)
  message(FATAL_ERROR \"This file relies on consumers using CMake 3.0.0 or greater.\")
endif()

set(CMAKE_IMPORT_FILE_VERSION)
cmake_policy(POP)
")

  foreach(_tgt ${tgt_list})
    if(NOT TARGET ${_tgt})
      continue()
    endif()

    get_target_property(_libs ${_tgt} INTERFACE_LINK_LIBRARIES)
    if(_libs)
      foreach(_lib ${_libs})
        if(_lib MATCHES "([a-zA-Z0-9_]+)::([a-zA-Z0-9_]+)")
          set(_ns ${CMAKE_MATCH_1})
          set(_tgt ${CMAKE_MATCH_2})

          if("${_ns}" STREQUAL "${ns}" AND TARGET ${_lib})
            list(PREPEND tgt_list ${_lib})
          endif()
        endif()
      endforeach()
    endif()
  endforeach()

  set(_tgt_props
      COMPILE_DEFINITIONS
      COMPILE_FEATURES
      COMPILE_OPTIONS
      INCLUDE_DIRECTORIES
      LINK_OPTIONS
      LINK_LIBRARIES
      INTERFACE_COMPILE_DEFINITIONS
      INTERFACE_COMPILE_FEATURES
      INTERFACE_COMPILE_OPTIONS
      INTERFACE_INCLUDE_DIRECTORIES
      INTERFACE_LINK_OPTIONS
      INTERFACE_LINK_LIBRARIES
      IMPORTED_CONFIGURATIONS
      IMPORTED_SONAME
      IMPORTED_SONAME_DEBUG
      IMPORTED_SONAME_RELEASE
      IMPORTED_LOCATION
      IMPORTED_LOCATION_DEBUG
      IMPORTED_LOCATION_RELEASE
      IMPORTED_LOCATION_NONE
      IMPORTED_LOCATION_NOCONFIG)

  set(_library_content)
  foreach(_tgt ${tgt_list})
    if(NOT TARGET ${_tgt})
      continue()
    endif()

    list(APPEND _library_content "if(NOT TARGET ${_tgt})\n")

    get_target_property(_type ${_tgt} TYPE)
    if("${_type}" STREQUAL "EXECUTABLE")
      list(APPEND _library_content "  add_executable(${_tgt} IMPORTED)\n")
    elseif("${_type}" STREQUAL "UNKNOWN_LIBRARY")
      list(APPEND _library_content "  add_library(${_tgt} UNKNOWN IMPORTED)\n")
    elseif("${_type}" STREQUAL "INTERFACE_LIBRARY")
      list(APPEND _library_content "  add_library(${_tgt} UNKNOWN IMPORTED)\n")
      __get_imported_location_from_interface_library(${_tgt})
      if(_imported_location)
        list(APPEND _library_content "\n  set_target_properties(${_tgt} PROPERTIES\n")
        list(APPEND _library_content "      IMPORTED_LOCATION \"${_imported_location}\"")
        list(APPEND _library_content "  )\n")
      endif()
    elseif("${_type}" STREQUAL "STATIC_LIBRARY")
      list(APPEND _library_content "  add_library(${_tgt} STATIC IMPORTED)\n")
    elseif("${_type}" STREQUAL "SHARED_LIBRARY")
      list(APPEND _library_content "  add_library(${_tgt} SHARED IMPORTED)\n")
    endif()

    list(APPEND _library_content "\n  set_target_properties(${_tgt} PROPERTIES\n")
    foreach(_prop ${_tgt_props})
      get_target_property(_val ${_tgt} ${_prop})
      if(_val)
        if(_imported_location)
          list(REMOVE_ITEM _val "${_imported_location}")
        endif()
        string(REPLACE ";" "\;" _val "${_val}")
        list(APPEND _library_content "       ${_prop} \"${_val}\"\n")
      endif()
    endforeach()
    list(APPEND _library_content "  )\n\n\n")

    list(APPEND _library_content "endif()\n")
  endforeach()

  if(_${pkg}_COMPONENTS_SEARCHED)
    string(REPLACE ";" "\;" _val "${_${pkg}_COMPONENTS_SEARCHED}")
    list(APPEND _library_content "set(_${pkg}_COMPONENTS_SEARCHED ${_val})\n\n\n")
  endif()

  file(WRITE ${dest_dir}/${pkg_name}Targets.cmake ${_targets_prefix_content} ${_library_content}
                                                  ${_targets_suffix_content})
endfunction()

if(MS_PREFER_SYSTEM_PKGS)
  string(TOLOWER ${MS_PREFER_SYSTEM_PKGS} _val)
  if("${_val}" STREQUAL "all")
    set(MS_PREFER_SYSTEM_PKGS ON)
  elseif(
    NOT
    ("${_val}" STREQUAL "on"
     OR "${_val}" STREQUAL "true"
     OR "${_val}" STREQUAL "1"
     OR "${_val}" STREQUAL "off"
     OR "${_val}" STREQUAL "false"
     OR "${_val}" STREQUAL "0"))
    string(REPLACE "," ";" MS_PREFER_SYSTEM_PKGS ${MS_PREFER_SYSTEM_PKGS})
    foreach(_name ${MS_PREFER_SYSTEM_PKGS})
      string(TOUPPER ${_name} _name)
      set(MS_${_name}_PREFER_SYSTEM ON)
      message(STATUS "MS_${_name}_PREFER_SYSTEM = ${MS_${_name}_PREFER_SYSTEM}")
    endforeach()
    set(MS_PREFER_SYSTEM_PKGS "")
  endif()
endif()

macro(
  __find_package
  pkg_name
  PKG_VER
  PKG_LIBS
  PKG_LIBS_CMAKE_NAMES
  PKG_EXE
  PKG_CMAKE_PKG_NO_COMPONENTS
  PKG_NS_NAME
  PKG_TARGET_ALIAS
  search_name)
  message(CHECK_START "Looking ${pkg_name} using CMake find_package(): ${search_name}")
  list(APPEND CMAKE_MESSAGE_INDENT "  ")

  set(pkg_name ${pkg_name})
  string(TOUPPER ${pkg_name} PKG_NAME)

  set(_find_package_args)
  if(PKG_FORCE_EXACT_VERSION)
    list(APPEND _find_package_args EXACT)
  endif()

  if(NOT PKG_CMAKE_PKG_NO_COMPONENTS AND (PKG_LIBS OR PKG_EXE))
    list(APPEND _find_package_args COMPONENTS)
    if(PKG_LIBS)
      list(APPEND _find_package_args ${PKG_LIBS_CMAKE_NAMES})
    endif()
    if(PKG_EXE)
      list(APPEND _find_package_args ${PKG_EXE})
    endif()
  endif()
  # Prefer system installed libraries instead of compiling everything from source
  if(${pkg_name}_DEBUG)
    message(STATUS "find_package(${pkg_name} ${PKG_VER} ${_find_package_args} ${ARGN})")
  endif()
  find_package(${pkg_name} ${PKG_VER} ${_find_package_args} ${ARGN})
  if(${pkg_name}_FOUND)
    set(_inc_location_var)
    if(NOT "${${pkg_name}_INCLUDE_DIRS}" STREQUAL "")
      set(_inc_location_var ${pkg_name}_INCLUDE_DIRS)
    elseif(NOT "${${pkg_name}_INCLUDE_DIR}" STREQUAL "")
      set(_inc_location_var ${pkg_name}_INCLUDE_DIR)
    else()
      set(_targets ${PKG_LIBS_CMAKE_NAMES})
      if(PKG_EXE)
        list(APPEND _targets ${PKG_EXE})
      endif()

      set(_inc_location_var _inc_dirs)
      set(_inc_dirs)
      foreach(_comp ${_targets})
        if(TARGET ${PKG_NS_NAME}::${_comp})
          set(_target_name ${PKG_NS_NAME}::${_comp})
        elseif(TARGET ${PKG_NS_NAME}::${PKG_NS_NAME}_${_comp})
          set(_target_name ${PKG_NS_NAME}::${PKG_NS_NAME}_${_comp})
        endif()
        if(_target_name)
          foreach(_prop INCLUDE_DIRECTORIES INTERFACE_INCLUDE_DIRECTORIES)
            get_target_property(_dir ${_target_name} ${_prop})
            if(_dir)
              break()
            endif()
          endforeach()
          if(_dir)
            list(APPEND _inc_dirs "${_dir}")
          endif()
        endif()
      endforeach()
      list(REMOVE_DUPLICATES _inc_dirs)
    endif()
    set(${pkg_name}_INC
        ${${_inc_location_var}}
        PARENT_SCOPE)

    __calculate_root_dir(${pkg_name})

    list(POP_BACK CMAKE_MESSAGE_INDENT)
    message(CHECK_PASS "Done")
  else()
    list(POP_BACK CMAKE_MESSAGE_INDENT)
    message(CHECK_FAIL "Failed")
  endif()
endmacro()

function(__check_package_location pkg_name pkg_namespace)
  file(TO_CMAKE_PATH "${${pkg_name}_BASE_DIR}" _base_dir)
  set(_tgt_list)
  foreach(_comp ${ARGN})
    set(_tgt ${pkg_namespace}::${_comp})
    if(TARGET ${_tgt})
      foreach(_prop IMPORTED_LOCATION IMPORETD_LOCATION_DEBUG IMPORTED_LOCATION_RELEASE IMPORTED_LOCATION_NONE
                    IMPORTED_LOCATION_NOCONFIG)
        get_target_property(_imported_location ${_tgt} ${_prop})
        if(_imported_location)
          file(TO_CMAKE_PATH "${_imported_location}" _imported_location)
          break()
        endif()
      endforeach()
      if(_imported_location)
        string(FIND "${_imported_location}" "${_base_dir}" _idx)
        if(_idx LESS 0)
          message(
            FATAL_ERROR
              "Imported location of ${_tgt} not found in ${_base_dir}!
- ${_imported_location}
Please clear up CMake cache (${CMAKE_CURRENT_BINARY_DIR}/CMakeCache.txt and re-run CMake.")
        endif()
      endif()
    endif()
  endforeach()
endfunction()

set(MS_FIND_NO_DEFAULT_PATH
    NO_CMAKE_PATH
    NO_CMAKE_ENVIRONMENT_PATH
    NO_SYSTEM_ENVIRONMENT_PATH
    NO_CMAKE_BUILDS_PATH
    NO_CMAKE_PACKAGE_REGISTRY
    NO_CMAKE_SYSTEM_PATH
    NO_CMAKE_SYSTEM_PACKAGE_REGISTRY)
set(MS_FIND_NO_DEFAULT_PATH
    ${MS_FIND_NO_DEFAULT_PATH}
    PARENT_SCOPE)
function(mindspore_add_pkg pkg_name)
  set(options FORCE_EXACT_VERSION CMAKE_PKG_NO_COMPONENTS GEN_CMAKE_CONFIG BUILD_OPTION_PASS_PREFIX)
  set(oneValueArgs
      URL
      MD5
      GIT_REPOSITORY
      GIT_TAG
      VER
      EXE
      DIR
      HEAD_ONLY
      CMAKE_PATH
      RELEASE
      LIB_PATH
      CUSTOM_CMAKE)
  set(multiValueArgs
      CMAKE_OPTION
      LIBS
      LIBS_CMAKE_NAMES
      FORCE_CONFIG_SEARCH
      PRE_CONFIGURE_COMMAND
      CONFIGURE_COMMAND
      BUILD_OPTION
      INSTALL_INCS
      INSTALL_LIBS
      PATCHES
      SUBMODULES
      SOURCEMODULES
      ONLY_MAKE
      ONLY_MAKE_INCS
      ONLY_MAKE_LIBS
      TARGET_ALIAS
      PREFIX_VARS)
  cmake_parse_arguments(PKG "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

  if(NOT PKG_LIB_PATH)
    set(PKG_LIB_PATH lib)
  endif()

  if(NOT PKG_EXE)
    set(PKG_EXE 0)
  endif()

  if(NOT PKG_NS_NAME)
    set(PKG_NS_NAME ${pkg_name})
  endif()

  if(PKG_HEAD_ONLY)
    set(PKG_LIBS ${PKG_HEAD_ONLY})
  endif()

  if(NOT PKG_LIBS_CMAKE_NAMES)
    set(PKG_LIBS_CMAKE_NAMES ${PKG_LIBS})
  else()
    list(LENGTH PKG_LIBS _N_libs)
    list(LENGTH PKG_LIBS_CMAKE_NAMES _N_libs_cmake_names)
    if(NOT _N_libs EQUAL _N_libs_cmake_names)
      message(FATAL_ERROR "Number of values for LIBS and LIBS_CMAKE_NAMES should be identical!")
    endif()
  endif()

  string(TOUPPER ${pkg_name} PKG_NAME)

  message(CHECK_START "Adding external dependency: ${pkg_name}")
  list(APPEND CMAKE_MESSAGE_INDENT "  ")

  if(MS_PREFER_SYSTEM_PKGS OR MS_${PKG_NAME}_PREFER_SYSTEM)
    set(_args)
    if(PKG_FORCE_CONFIG_SEARCH)
      list(APPEND _args CONFIG)
    endif()
    __find_package(
      "${pkg_name}"
      "${PKG_VER}"
      "${PKG_LIBS}"
      "${PKG_LIBS_CMAKE_NAMES}"
      "${PKG_EXE}"
      "${PKG_CMAKE_PKG_NO_COMPONENTS}"
      "${PKG_NS_NAME}"
      "${PKG_TARGET_ALIAS}"
      "system packages"
      ${_args})

    if(${pkg_name}_FOUND)
      if(${pkg_name}_DIR)
        message(STATUS "Package CMake config dir: ${${pkg_name}_DIR}")
      endif()
      __create_target_aliases(${PKG_TARGET_ALIAS})

      list(POP_BACK CMAKE_MESSAGE_INDENT)
      message(CHECK_PASS "Done")
      return()
    else()
      # Cleanup potential variables
      foreach(_var_suffix INCLUDE_DIR INCLUDE_DIRS LIBRARIES)
        set(var ${pkg_name}_${_var_suffix})
      endforeach()
    endif()

    # Otherwise we try to compile from source
  endif()

  # ==============================================================================
  # Ignore system installed libraries and compile a local version instead

  set(${pkg_name}_PATCHES_HASH)
  foreach(_PATCH ${PKG_PATCHES})
    file(MD5 ${_PATCH} _PF_MD5)
    set(${pkg_name}_PATCHES_HASH "${${pkg_name}_PATCHES_HASH},${_PF_MD5}")
  endforeach()

  # check options
  set(${pkg_name}_CONFIG_TXT
      "${CMAKE_CXX_COMPILER_VERSION}-${CMAKE_C_COMPILER_VERSION}
            ${ARGN} - ${${pkg_name}_USE_STATIC_LIBS}- ${${pkg_name}_PATCHES_HASH}
            ${${pkg_name}_CXXFLAGS}--${${pkg_name}_CFLAGS}--${${pkg_name}_LDFLAGS}")
  string(REPLACE ";" "-" ${pkg_name}_CONFIG_TXT ${${pkg_name}_CONFIG_TXT})
  string(MD5 ${pkg_name}_CONFIG_HASH ${${pkg_name}_CONFIG_TXT})

  message(STATUS "${pkg_name} config hash: ${${pkg_name}_CONFIG_HASH}")

  set(${pkg_name}_BASE_DIR ${_MS_LIB_CACHE}/${pkg_name}_${PKG_VER}_${${pkg_name}_CONFIG_HASH})
  set(${pkg_name}_DIRPATH
      ${${pkg_name}_BASE_DIR}
      CACHE STRING INTERNAL)

  if(EXISTS "${${pkg_name}_BASE_DIR}")
    __find_package(
      "${pkg_name}"
      "${PKG_VER}"
      "${PKG_LIBS}"
      "${PKG_LIBS_CMAKE_NAMES}"
      "${PKG_EXE}"
      "${PKG_CMAKE_PKG_NO_COMPONENTS}"
      "${PKG_NS_NAME}"
      "${PKG_TARGET_ALIAS}"
      "MindSpore build dir"
      CONFIG
      ${MS_FIND_NO_DEFAULT_PATH}
      PATHS
      "${${pkg_name}_BASE_DIR}")
    if(${pkg_name}_FOUND)
      if(${pkg_name}_DIR)
        message(STATUS "Package CMake config dir: ${${pkg_name}_DIR}")
      endif()
      __check_package_location(${pkg_name} ${PKG_NS_NAME} ${PKG_LIBS_CMAKE_NAMES} ${PKG_EXE})
      __create_target_aliases(${PKG_TARGET_ALIAS})

      list(POP_BACK CMAKE_MESSAGE_INDENT)
      message(CHECK_PASS "Done")
      return()
    endif()
  endif()

  if(NOT PKG_DIR)
    if(PKG_GIT_REPOSITORY)
      __download_pkg_with_git(${pkg_name} ${PKG_GIT_REPOSITORY} ${PKG_GIT_TAG} ${PKG_MD5})
    else()
      __download_pkg(${pkg_name} ${PKG_URL} ${PKG_MD5})
    endif()
    foreach(_SUBMODULE_FILE ${PKG_SUBMODULES})
      string(REGEX REPLACE "(.+)_(.+)" "\\1" _SUBMODEPATH ${_SUBMODULE_FILE})
      string(REGEX REPLACE "(.+)/(.+)" "\\2" _SUBMODENAME ${_SUBMODEPATH})
      file(GLOB ${pkg_name}_INSTALL_SUBMODULE ${_SUBMODULE_FILE}/*)
      file(COPY ${${pkg_name}_INSTALL_SUBMODULE} DESTINATION ${${pkg_name}_SOURCE_DIR}/3rdparty/${_SUBMODENAME})
    endforeach()
  else()
    set(${pkg_name}_SOURCE_DIR ${PKG_DIR})
  endif()
  file(WRITE ${${pkg_name}_BASE_DIR}/options.txt ${${pkg_name}_CONFIG_TXT})
  message(STATUS "${pkg_name}_SOURCE_DIR : ${${pkg_name}_SOURCE_DIR}")

  foreach(_PATCH_FILE ${PKG_PATCHES})
    get_filename_component(_PATCH_FILE_NAME ${_PATCH_FILE} NAME)
    set(_LF_PATCH_FILE ${CMAKE_BINARY_DIR}/_ms_patch/${_PATCH_FILE_NAME})
    configure_file(
      ${_PATCH_FILE} ${_LF_PATCH_FILE}
      NEWLINE_STYLE LF
      @ONLY)

    message(STATUS "patching ${${pkg_name}_SOURCE_DIR} -p1 < ${_LF_PATCH_FILE}")
    execute_process(
      COMMAND ${Patch_EXECUTABLE} -p1
      INPUT_FILE ${_LF_PATCH_FILE}
      WORKING_DIRECTORY ${${pkg_name}_SOURCE_DIR}
      RESULT_VARIABLE Result)
    if(NOT Result EQUAL "0")
      message(FATAL_ERROR "Failed patch: ${_LF_PATCH_FILE}")
    endif()
  endforeach()
  foreach(_SOURCE_DIR ${PKG_SOURCEMODULES})
    file(GLOB ${pkg_name}_INSTALL_SOURCE ${${pkg_name}_SOURCE_DIR}/${_SOURCE_DIR}/*)
    file(COPY ${${pkg_name}_INSTALL_SOURCE} DESTINATION ${${pkg_name}_BASE_DIR}/${_SOURCE_DIR}/)
  endforeach()
  file(
    LOCK ${${pkg_name}_BASE_DIR} DIRECTORY
    GUARD FUNCTION
    RESULT_VARIABLE ${pkg_name}_LOCK_RET
    TIMEOUT 600)
  if(NOT ${pkg_name}_LOCK_RET EQUAL "0")
    message(FATAL_ERROR "error! when try lock ${${pkg_name}_BASE_DIR} : ${${pkg_name}_LOCK_RET}")
  endif()

  if(PKG_CUSTOM_CMAKE)
    file(GLOB ${pkg_name}_cmake ${PKG_CUSTOM_CMAKE}/CMakeLists.txt)
    file(COPY ${${pkg_name}_cmake} DESTINATION ${${pkg_name}_SOURCE_DIR})
  endif()

  if(${pkg_name}_SOURCE_DIR)
    if(PKG_ONLY_MAKE)
      __exec_cmd(COMMAND ${CMAKE_MAKE_PROGRAM} ${${pkg_name}_CXXFLAGS} -j${THNUM} WORKING_DIRECTORY
                 ${${pkg_name}_SOURCE_DIR})
      set(PKG_INSTALL_INCS ${PKG_ONLY_MAKE_INCS})
      set(PKG_INSTALL_LIBS ${PKG_ONLY_MAKE_LIBS})
      file(GLOB ${pkg_name}_INSTALL_INCS ${${pkg_name}_SOURCE_DIR}/${PKG_INSTALL_INCS})
      file(GLOB ${pkg_name}_INSTALL_LIBS ${${pkg_name}_SOURCE_DIR}/${PKG_INSTALL_LIBS})
      file(COPY ${${pkg_name}_INSTALL_INCS} DESTINATION ${${pkg_name}_BASE_DIR}/include)
      file(COPY ${${pkg_name}_INSTALL_LIBS} DESTINATION ${${pkg_name}_BASE_DIR}/lib)

    elseif(PKG_CMAKE_OPTION)
      # in cmake
      file(MAKE_DIRECTORY ${${pkg_name}_SOURCE_DIR}/_build)
      if(${pkg_name}_CFLAGS)
        set(${pkg_name}_CMAKE_CFLAGS "-DCMAKE_C_FLAGS=${${pkg_name}_CFLAGS}")
      endif()
      if(${pkg_name}_CXXFLAGS)
        set(${pkg_name}_CMAKE_CXXFLAGS "-DCMAKE_CXX_FLAGS=${${pkg_name}_CXXFLAGS}")
      endif()

      if(${pkg_name}_LDFLAGS)
        if(${pkg_name}_USE_STATIC_LIBS)
          # set(${pkg_name}_CMAKE_LDFLAGS "-DCMAKE_STATIC_LINKER_FLAGS=${${pkg_name}_LDFLAGS}")
        else()
          set(${pkg_name}_CMAKE_LDFLAGS "-DCMAKE_SHARED_LINKER_FLAGS=${${pkg_name}_LDFLAGS}")
        endif()
      endif()
      if(APPLE)
        __exec_cmd(
          COMMAND
          ${CMAKE_COMMAND}
          ${PKG_CMAKE_OPTION}
          ${${pkg_name}_CMAKE_CFLAGS}
          ${${pkg_name}_CMAKE_CXXFLAGS}
          ${${pkg_name}_CMAKE_LDFLAGS}
          -DCMAKE_INSTALL_PREFIX=${${pkg_name}_BASE_DIR}
          ${${pkg_name}_SOURCE_DIR}/${PKG_CMAKE_PATH}
          WORKING_DIRECTORY
          ${${pkg_name}_SOURCE_DIR}/_build)
        __exec_cmd(
          COMMAND
          ${CMAKE_COMMAND}
          --build
          .
          --target
          install
          --
          WORKING_DIRECTORY
          ${${pkg_name}_SOURCE_DIR}/_build)
      else()
        __exec_cmd(
          COMMAND
          ${CMAKE_COMMAND}
          ${PKG_CMAKE_OPTION}
          -G
          ${CMAKE_GENERATOR}
          ${${pkg_name}_CMAKE_CFLAGS}
          ${${pkg_name}_CMAKE_CXXFLAGS}
          ${${pkg_name}_CMAKE_LDFLAGS}
          -DCMAKE_INSTALL_PREFIX=${${pkg_name}_BASE_DIR}
          ${${pkg_name}_SOURCE_DIR}/${PKG_CMAKE_PATH}
          WORKING_DIRECTORY
          ${${pkg_name}_SOURCE_DIR}/_build)
        __exec_cmd(
          COMMAND
          ${CMAKE_COMMAND}
          --build
          .
          --target
          install
          --
          -j${THNUM}
          WORKING_DIRECTORY
          ${${pkg_name}_SOURCE_DIR}/_build)
      endif()
    else()
      if(${pkg_name}_CFLAGS)
        set(${pkg_name}_MAKE_CFLAGS "CFLAGS=${${pkg_name}_CFLAGS}")
      endif()
      if(${pkg_name}_CXXFLAGS)
        set(${pkg_name}_MAKE_CXXFLAGS "CXXFLAGS=${${pkg_name}_CXXFLAGS}")
      endif()
      if(${pkg_name}_LDFLAGS)
        set(${pkg_name}_MAKE_LDFLAGS "LDFLAGS=${${pkg_name}_LDFLAGS}")
      endif()
      # in configure && make
      if(PKG_PRE_CONFIGURE_COMMAND)
        __exec_cmd(COMMAND ${PKG_PRE_CONFIGURE_COMMAND} WORKING_DIRECTORY ${${pkg_name}_SOURCE_DIR})
      endif()

      if(PKG_CONFIGURE_COMMAND)
        __exec_cmd(
          COMMAND
          ${PKG_CONFIGURE_COMMAND}
          ${${pkg_name}_MAKE_CFLAGS}
          ${${pkg_name}_MAKE_CXXFLAGS}
          ${${pkg_name}_MAKE_LDFLAGS}
          --prefix=${${pkg_name}_BASE_DIR}
          WORKING_DIRECTORY
          ${${pkg_name}_SOURCE_DIR})
      endif()
      set(${pkg_name}_BUILD_OPTION ${PKG_BUILD_OPTION})
      if(PKG_BUILD_OPTION_PASS_PREFIX)
        set(${pkg_name}_BUILD_OPTION ${${pkg_name}_BUILD_OPTION} PREFIX="${${pkg_name}_BASE_DIR}")
      endif()
      if(NOT PKG_CONFIGURE_COMMAND)
        set(${pkg_name}_BUILD_OPTION ${${pkg_name}_BUILD_OPTION} ${${pkg_name}_MAKE_CFLAGS}
                                     ${${pkg_name}_MAKE_CXXFLAGS} ${${pkg_name}_MAKE_LDFLAGS})
      endif()
      # build
      if(APPLE)
        __exec_cmd(COMMAND ${CMAKE_MAKE_PROGRAM} ${${pkg_name}_BUILD_OPTION} WORKING_DIRECTORY
                   ${${pkg_name}_SOURCE_DIR})
      else()
        __exec_cmd(COMMAND ${CMAKE_MAKE_PROGRAM} ${${pkg_name}_BUILD_OPTION} -j${THNUM} WORKING_DIRECTORY
                   ${${pkg_name}_SOURCE_DIR})
      endif()

      if(PKG_INSTALL_INCS OR PKG_INSTALL_LIBS)
        file(GLOB ${pkg_name}_INSTALL_INCS ${${pkg_name}_SOURCE_DIR}/${PKG_INSTALL_INCS})
        file(GLOB ${pkg_name}_INSTALL_LIBS ${${pkg_name}_SOURCE_DIR}/${PKG_INSTALL_LIBS})
        file(COPY ${${pkg_name}_INSTALL_INCS} DESTINATION ${${pkg_name}_BASE_DIR}/include)
        file(COPY ${${pkg_name}_INSTALL_LIBS} DESTINATION ${${pkg_name}_BASE_DIR}/lib)
      else()
        __exec_cmd(COMMAND ${CMAKE_MAKE_PROGRAM} install WORKING_DIRECTORY ${${pkg_name}_SOURCE_DIR})
      endif()
    endif()
  endif()

  if(PKG_GEN_CMAKE_CONFIG)
    set(_cmake_data_dir ${${pkg_name}_BASE_DIR}/${pkg_name}/share/${pkg_name})

    message(STATUS "Generating fake CMake config file...")

    list(PREPEND CMAKE_PREFIX_PATH "${${pkg_name}_BASE_DIR}")
    set(${PKG_NAME}_ROOT "${${pkg_name}_BASE_DIR}")
    set(${pkg_name}_ROOT "${${pkg_name}_BASE_DIR}")
    __generate_pseudo_cmake_package_config("${_cmake_data_dir}" ${pkg_name} ${PKG_NS_NAME} "${PKG_LIBS_CMAKE_NAMES}"
                                           "${PKG_EXE}")
    list(POP_FRONT CMAKE_PREFIX_PATH)
  endif()

  __find_package(
    "${pkg_name}"
    "${PKG_VER}"
    "${PKG_LIBS}"
    "${PKG_LIBS_CMAKE_NAMES}"
    "${PKG_EXE}"
    "${PKG_CMAKE_PKG_NO_COMPONENTS}"
    "${PKG_NS_NAME}"
    "${PKG_TARGET_ALIAS}"
    "MindSpore build dir"
    REQUIRED
    CONFIG
    ${MS_FIND_NO_DEFAULT_PATH}
    HINTS
    "${${pkg_name}_BASE_DIR}")
  if(${pkg_name}_DIR)
    message(STATUS "Package CMake config dir: ${${pkg_name}_DIR}")
  endif()
  __check_package_location(${pkg_name} ${PKG_NS_NAME} ${PKG_LIBS_CMAKE_NAMES} ${PKG_EXE})
  __create_target_aliases(${PKG_TARGET_ALIAS})

  list(POP_BACK CMAKE_MESSAGE_INDENT)
  message(CHECK_PASS "Done")
endfunction()
