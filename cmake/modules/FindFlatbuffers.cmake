# ==============================================================================
#
# Copyright 2022 <Huawei Technologies Co., Ltd>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ==============================================================================

include(_find_utils_begin)

set(_pkg Flatbuffers)
string(TOLOWER ${_pkg} _pkg_low)
set(${_pkg}_NAMESPACE flatbuffers)
set(${_pkg}_INCLUDE_FILE flatc.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg_low} ${_pkg_low})
set(${_pkg}_INCLUDE_DIR_UP_INDEX 1)
set(${_pkg}_DEFAULT_COMPONENTS flatbuffers_shared flatc)
set(${_pkg}_flatbuffers_shared_NAMES flatbuffers)
set(${_pkg}_flatc_NAMES flatc)
set(${_pkg}_flatc_TYPE EXECUTABLE)

# Update RE2 library search directories with pre-built paths
function(flatc_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
  if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC")
    list(APPEND ${componentlibvar} ${basedir}/lib)
  elseif(UNIX)
    list(APPEND ${componentlibvar} ${basedir}/lib64)
    list(APPEND ${componentlibvar} ${basedir}/lib)
    list(APPEND ${componentlibvar} ${basedir}/lib/x86_64-linux-gnu)
  endif()

  set(${componentlibvar}
      ${${componentlibvar}}
      PARENT_SCOPE)
endfunction()

function(Flatbuffers_version_function include_dir)
  find_file(
    _flatbuffers_base_h base.h
    PATHS ${include_dir}/flatbuffers
    NO_DEFAULT_PATH)

  if(_flatbuffers_base_h)
    file(READ ${_flatbuffers_base_h} _flatbuffers_base_content)
    string(REGEX MATCHALL "#define[ \t]+[a-zA-Z0-9_]+VERSION[a-zA-Z0-9_ ]+" _flatbuffers_base_content
                 "${_flatbuffers_base_content}")
    list(APPEND _flatbuffers_base_content "")

    if("${_flatbuffers_base_content}" MATCHES "#define[ \t]+FLATBUFFERS_VERSION_MAJOR[ \t]+([0-9]+)[^\\.]")
      set(${_pkg}_VERSION_MAJOR ${CMAKE_MATCH_1})
    endif()
    if("${_flatbuffers_base_content}" MATCHES "#define[ \t]+FLATBUFFERS_VERSION_MINOR[ \t]+([0-9]+)[^\\.]")
      set(${_pkg}_VERSION_MINOR ${CMAKE_MATCH_1})
    endif()
    if("${_flatbuffers_base_content}" MATCHES "#define[ \t]+FLATBUFFERS_VERSION_REVISION[ \t]+([0-9]+)[^\\.]")
      set(${_pkg}_VERSION_PATCH ${CMAKE_MATCH_1})
    endif()
  endif()

  if("${${_pkg}_VERSION_MAJOR}" STREQUAL "" AND "${${_pkg}_VERSION_MINOR}" STREQUAL "")
    message(WARNING "Unable to determine Flatbuffers's version since flatbuffers/base.h file cannot be found!")
    set(${_pkg}_VERSION_MAJOR 99)
    set(${_pkg}_VERSION_MINOR 99)
    set(${_pkg}_VERSION_PATCH 99)
  endif()
  set(${_pkg}_VERSION "${${_pkg}_VERSION_MAJOR}.${${_pkg}_VERSION_MINOR}.${${_pkg}_VERSION_PATCH}")

  set(${_pkg}_VERSION_MAJOR
      ${${_pkg}_VERSION_MAJOR}
      PARENT_SCOPE)
  set(${_pkg}_VERSION_MINOR
      ${${_pkg}_VERSION_MINOR}
      PARENT_SCOPE)
  set(${_pkg}_VERSION_PATCH
      ${${_pkg}_VERSION_PATCH}
      PARENT_SCOPE)
  set(${_pkg}_VERSION
      ${${_pkg}_VERSION}
      PARENT_SCOPE)
endfunction()

include(_find_utils_end)

# ==============================================================================
