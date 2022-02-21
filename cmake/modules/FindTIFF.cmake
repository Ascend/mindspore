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
FindTIFF
---------

Find TIFF include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(TIFF
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if TIFF is not found
    [COMPONENTS <libs>...] # TIFF libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "TIFF
CMake" build.  For the latter case skip to the :ref:`TIFF CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``TIFF_FOUND``
  True if headers and requested libraries were found.

``TIFF_INCLUDE_DIRS``
  TIFF include directories.

``TIFF_LIBRARY_DIRS``
  Link directories for TIFF libraries.

``TIFF_LIBRARIES``
  TIFF component libraries to be linked.

``TIFF_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``TIFF_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``TIFF_VERSION``
  TIFF version number in ``X.Y`` format.

``TIFF_VERSION_MAJOR``
  TIFF major version number (``X`` in ``X.Y``).

``TIFF_VERSION_MINOR``
  TIFF minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``TIFF_INCLUDE_DIR``
  Directory containing TIFF headers.

``TIFF_LIBRARY_DIR_RELEASE``
  Directory containing release TIFF libraries.

``TIFF_LIBRARY_DIR_DEBUG``
  Directory containing debug TIFF libraries.

``TIFF_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``TIFF_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``TIFF_ROOT``, ``TIFFROOT``
  Preferred installation prefix.

``TIFF_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``TIFF_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``TIFF_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``TIFF``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the TIFF header files using the above hint variables (excluding ``TIFF_LIBRARYDIR``) and
saves the result in ``TIFF_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``TIFF_INCLUDEDIR``), "lib" directories near ``TIFF_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``TIFF_LIBRARY_DIR_DEBUG`` and ``TIFF_LIBRARY_DIR_RELEASE`` and
individual library locations in ``TIFF_<COMPONENT>_LIBRARY_DEBUG`` and ``TIFF_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``TIFF::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(TIFF)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

TIFF libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``TIFF_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``TIFF_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  TIFF_FIND_RELEASE_ONLY is ``ON``).

``TIFF_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``TIFF_DEBUG``
  Set to ``ON`` to enable debug output from ``FindTIFF``.  Please enable this before filing any bug report.

``TIFF_LIBRARY_DIR``
  Default value for ``TIFF_LIBRARY_DIR_RELEASE`` and ``TIFF_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find TIFF headers only:

.. code-block:: cmake

  find_package(TIFF 2.0.0)
  if(TIFF_FOUND)
    include_directories(${TIFF_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC TIFF::TIFF)
  endif()

Find TIFF libraries and use imported targets:

.. code-block:: cmake

  find_package(TIFF 2.0.0 REQUIRED COMPONENTS TIFF)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC TIFF::TIFF)

Find TIFF headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(TIFF_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(TIFF_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(TIFF 2.0.0 COMPONENTS TIFF)
  if(TIFF_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC TIFF::TIFF)
  endif()

.. _`TIFF CMake`:

TIFF CMake
^^^^^^^^^^^

If TIFF was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``TIFFConfig.cmake`` and stores the result in ``CACHE``
entry ``TIFF_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the TIFF CMake package configuration for details on what it provides.

Set ``TIFF_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`TIFF pkg-config`:

TIFF CMake
^^^^^^^^^^^

If TIFF was installed with its pkg-config files, this module may attempt to look for TIFF by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``TIFF_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg TIFF)
set(${_pkg}_INCLUDE_FILE tiff.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS TIFF)
set(${_pkg}_TIFF_NAMES tiff libtiff tiff3 libtiff3)
if(MSVC)
  # C++ bindings are built into the main tiff library.
  set(${_pkg}_CXX_NAMES ${${_pkg}_TIFF_NAMES})
else()
  set(${_pkg}_CXX_NAMES tiffxx libtiffxx tiff3xx libtiff3xx)
endif()

function(TIFF_version_function include_dir)
  message(STATUS "${include_dir}")
  find_file(
    _tiffvers_h tiffvers.h
    PATHS ${include_dir}
    NO_DEFAULT_PATH)

  if(_tiffvers_h)
    file(STRINGS "${_tiffvers_h}" tiff_version_str REGEX "^#define[\t ]+TIFFLIB_VERSION_STR[\t ]+\"LIBTIFF, Version .*")
    string(REGEX REPLACE "^#define[\t ]+TIFFLIB_VERSION_STR[\t ]+\"LIBTIFF, Version +([^ \\n]*).*" "\\1"
                         ${_pkg}_VERSION "${tiff_version_str}")
  endif()

  if(${_pkg}_VERSION MATCHES "([0-9]+)\.([0-9]+)\.([0-9]+)")
    set(${_pkg}_VERSION_MAJOR ${CMAKE_MATCH_1})
    set(${_pkg}_VERSION_MINOR ${CMAKE_MATCH_2})
    set(${_pkg}_VERSION_PATCH ${CMAKE_MATCH_3})
  else()
    message(WARNING "Unable to determine TIFF's version since tiffvers.h file cannot be found!")
    set(${_pkg}_VERSION_MAJOR 99999999)
    set(${_pkg}_VERSION_MINOR 99)
    set(${_pkg}_VERSION_PATCH 0)
  endif()

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

function(TIFF_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
