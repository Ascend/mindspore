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

#[=======================================================================[.rst:
Findsentencepiece
---------

Find sentencepiece include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(sentencepiece
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if sentencepiece is not found
    [COMPONENTS <libs>...] # sentencepiece libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "sentencepiece
CMake" build.  For the latter case skip to the :ref:`sentencepiece CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``sentencepiece_FOUND``
  True if headers and requested libraries were found.

``sentencepiece_INCLUDE_DIRS``
  sentencepiece include directories.

``sentencepiece_LIBRARY_DIRS``
  Link directories for sentencepiece libraries.

``sentencepiece_LIBRARIES``
  sentencepiece component libraries to be linked.

``sentencepiece_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``sentencepiece_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``sentencepiece_VERSION``
  sentencepiece version number in ``X.Y`` format.

``sentencepiece_VERSION_MAJOR``
  sentencepiece major version number (``X`` in ``X.Y``).

``sentencepiece_VERSION_MINOR``
  sentencepiece minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``sentencepiece_INCLUDE_DIR``
  Directory containing sentencepiece headers.

``sentencepiece_LIBRARY_DIR_RELEASE``
  Directory containing release sentencepiece libraries.

``sentencepiece_LIBRARY_DIR_DEBUG``
  Directory containing debug sentencepiece libraries.

``sentencepiece_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``sentencepiece_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``sentencepiece_ROOT``, ``sentencepieceROOT``
  Preferred installation prefix.

``sentencepiece_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``sentencepiece_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``sentencepiece_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``sentencepiece``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the sentencepiece header files using the above hint variables (excluding ``sentencepiece_LIBRARYDIR``) and
saves the result in ``sentencepiece_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``sentencepiece_INCLUDEDIR``), "lib" directories near ``sentencepiece_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``sentencepiece_LIBRARY_DIR_DEBUG`` and ``sentencepiece_LIBRARY_DIR_RELEASE`` and
individual library locations in ``sentencepiece_<COMPONENT>_LIBRARY_DEBUG`` and ``sentencepiece_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``sentencepiece::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(sentencepiece)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

sentencepiece libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``sentencepiece_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``sentencepiece_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  sentencepiece_FIND_RELEASE_ONLY is ``ON``).

``sentencepiece_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``sentencepiece_DEBUG``
  Set to ``ON`` to enable debug output from ``Findsentencepiece``.  Please enable this before filing any bug report.

``sentencepiece_LIBRARY_DIR``
  Default value for ``sentencepiece_LIBRARY_DIR_RELEASE`` and ``sentencepiece_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find sentencepiece headers only:

.. code-block:: cmake

  find_package(sentencepiece 2.0.0)
  if(sentencepiece_FOUND)
    include_directories(${sentencepiece_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC sentencepiece::sentencepiece)
  endif()

Find sentencepiece libraries and use imported targets:

.. code-block:: cmake

  find_package(sentencepiece 2.0.0 REQUIRED COMPONENTS sentencepiece)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC sentencepiece::sentencepiece)

Find sentencepiece headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(sentencepiece_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(sentencepiece_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(sentencepiece 2.0.0 COMPONENTS sentencepiece)
  if(sentencepiece_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC sentencepiece::sentencepiece)
  endif()

.. _`sentencepiece CMake`:

sentencepiece CMake
^^^^^^^^^^^

If sentencepiece was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``sentencepieceConfig.cmake`` and stores the result in ``CACHE``
entry ``sentencepiece_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the sentencepiece CMake package configuration for details on what it provides.

Set ``sentencepiece_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`sentencepiece pkg-config`:

sentencepiece CMake
^^^^^^^^^^^

If sentencepiece was installed with its pkg-config files, this module may attempt to look for sentencepiece by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``sentencepiece_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg sentencepiece)
set(${_pkg}_INCLUDE_FILE sentencepiece_processor.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS sentencepiece sentencepiece_train)
set(${_pkg}_sentencepiece_NAMES sentencepiece)
set(${_pkg}_sentencepiece_train_NAMES sentencepiece_train)
set(${_pkg}_sentencepiece_train_PKGCONFIG_NAMES sentencepiece)
set(_${_pkg}_exec_names spm_decode spm_encode spm_export_vocab spm_normalize spm_train)

foreach(_exec _${_pkg}_exec_names)
  set(${_pkg}_${exec}_NAMES ${_exec})
  set(${_pkg}_${exec}_TYPE "EXECUTABLE")
endforeach()

function(sentencepiece_version_function include_dir)
  find_program(
    _spm_exec
    NAMES ${_${_pkg}_exec_names}
    PATHS ${include_dir}/../bin
    NO_DEFAULT_PATH)

  if(_spm_exec)
    # NB: workaround possible issue with library loading issues
    if(APPLE)
      set(ENV{DYLD_LIBRARY_PATH} "${include_dir}/../lib;$ENV{DYLD_LIBRARY_PATH}")
    elseif(UNIX)
      set(ENV{LD_LIBRARY_PATH} "${include_dir}/../lib;$ENV{LD_LIBRARY_PATH}")
    endif()

    execute_process(
      COMMAND ${_spm_exec} --version
      RESULT_VARIABLE _has_sentencepiece_version
      OUTPUT_VARIABLE _sentencepiece_version)

    if(_has_sentencepiece_version EQUAL 0 AND _sentencepiece_version MATCHES
                                              "sentencepiece[ \t]+([0-9]+)\\.([0-9]+)\\.([0-9]+)")
      set(${_pkg}_VERSION_MAJOR ${CMAKE_MATCH_1})
      set(${_pkg}_VERSION_MINOR ${CMAKE_MATCH_2})
      set(${_pkg}_VERSION_PATCH ${CMAKE_MATCH_3})
    endif()
  endif()

  if("${${_pkg}_VERSION_MAJOR}" STREQUAL "" AND "${${_pkg}_VERSION_MINOR}" STREQUAL "")
    message(
      WARNING
        "Unable to determine sentencepiece's version since google/sentencepiece/stubs/common.h file cannot be found!")
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

# Update SENTENCEPIECE library search directories with pre-built paths
function(sentencepiece_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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

include(_find_utils_end)

# ==============================================================================
