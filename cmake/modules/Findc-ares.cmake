#.rst:
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
Findc-ares
---------

Find c-ares include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(c-ares
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if c-ares is not found
    [COMPONENTS <libs>...] # c-ares libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "c-ares
CMake" build.  For the latter case skip to the :ref:`c-ares CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``c-ares_FOUND``
  True if headers and requested libraries were found.

``c-ares_INCLUDE_DIRS``
  c-ares include directories.

``c-ares_LIBRARY_DIRS``
  Link directories for c-ares libraries.

``c-ares_LIBRARIES``
  c-ares component libraries to be linked.

``c-ares_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``c-ares_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``c-ares_VERSION``
  c-ares version number in ``X.Y`` format.

``c-ares_VERSION_MAJOR``
  c-ares major version number (``X`` in ``X.Y``).

``c-ares_VERSION_MINOR``
  c-ares minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``c-ares_INCLUDE_DIR``
  Directory containing c-ares headers.

``c-ares_LIBRARY_DIR_RELEASE``
  Directory containing release c-ares libraries.

``c-ares_LIBRARY_DIR_DEBUG``
  Directory containing debug c-ares libraries.

``c-ares_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``c-ares_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``c-ares_ROOT``, ``c-aresROOT``
  Preferred installation prefix.

``c-ares_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``c-ares_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``c-ares_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``c-ares``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the c-ares header files using the above hint variables (excluding ``c-ares_LIBRARYDIR``) and
saves the result in ``c-ares_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``c-ares_INCLUDEDIR``), "lib" directories near ``c-ares_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``c-ares_LIBRARY_DIR_DEBUG`` and ``c-ares_LIBRARY_DIR_RELEASE`` and
individual library locations in ``c-ares_<COMPONENT>_LIBRARY_DEBUG`` and ``c-ares_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``c-ares::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(c-ares)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

c-ares libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``c-ares_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``c-ares_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  c-ares_FIND_RELEASE_ONLY is ``ON``).

``c-ares_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``c-ares_DEBUG``
  Set to ``ON`` to enable debug output from ``Findc-ares``.  Please enable this before filing any bug report.

``c-ares_LIBRARY_DIR``
  Default value for ``c-ares_LIBRARY_DIR_RELEASE`` and ``c-ares_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find c-ares headers only:

.. code-block:: cmake

  find_package(c-ares 2.0.0)
  if(c-ares_FOUND)
    include_directories(${c-ares_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC c-ares::c-ares)
  endif()

Find c-ares libraries and use imported targets:

.. code-block:: cmake

  find_package(c-ares 2.0.0 REQUIRED COMPONENTS c-ares)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC c-ares::c-ares)

Find c-ares headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(c-ares_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(c-ares_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(c-ares 2.0.0 COMPONENTS c-ares)
  if(c-ares_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC c-ares::c-ares)
  endif()

.. _`c-ares CMake`:

c-ares CMake
^^^^^^^^^^^

If c-ares was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``c-aresConfig.cmake`` and stores the result in ``CACHE``
entry ``c-ares_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the c-ares CMake package configuration for details on what it provides.

Set ``c-ares_NO_CMAKE`` to ``ON``, to disable the search for tbb-cmake.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg c-ares)
set(${_pkg}_INCLUDE_FILE ares.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS cares)
set(${_pkg}_DEFINE_PREFIX ARES)
set(${_pkg}_cares_NAMES cares)

# Update C-ARES library search directories with pre-built paths
function(c-ares_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
