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
FindOpenCV
---------

Find OpenCV include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(OpenCV
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if OpenCV is not found
    [COMPONENTS <libs>...] # OpenCV libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "OpenCV
CMake" build.  For the latter case skip to the :ref:`OpenCV CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``OpenCV_FOUND``
  True if headers and requested libraries were found.

``OpenCV_INCLUDE_DIRS``
  OpenCV include directories.

``OpenCV_LIBRARY_DIRS``
  Link directories for OpenCV libraries.

``OpenCV_LIBRARIES``
  OpenCV component libraries to be linked.

``OpenCV_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``OpenCV_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``OpenCV_VERSION``
  OpenCV version number in ``X.Y`` format.

``OpenCV_VERSION_MAJOR``
  OpenCV major version number (``X`` in ``X.Y``).

``OpenCV_VERSION_MINOR``
  OpenCV minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``OpenCV_INCLUDE_DIR``
  Directory containing OpenCV headers.

``OpenCV_LIBRARY_DIR_RELEASE``
  Directory containing release OpenCV libraries.

``OpenCV_LIBRARY_DIR_DEBUG``
  Directory containing debug OpenCV libraries.

``OpenCV_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``OpenCV_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``OpenCV_ROOT``, ``OpenCVROOT``
  Preferred installation prefix.

``OpenCV_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``OpenCV_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``OpenCV_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``OpenCV``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the OpenCV header files using the above hint variables (excluding ``OpenCV_LIBRARYDIR``) and
saves the result in ``OpenCV_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``OpenCV_INCLUDEDIR``), "lib" directories near ``OpenCV_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``OpenCV_LIBRARY_DIR_DEBUG`` and ``OpenCV_LIBRARY_DIR_RELEASE`` and
individual library locations in ``OpenCV_<COMPONENT>_LIBRARY_DEBUG`` and ``OpenCV_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``OpenCV::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(OpenCV)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

OpenCV libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``OpenCV_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``OpenCV_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  OpenCV_FIND_RELEASE_ONLY is ``ON``).

``OpenCV_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``OpenCV_DEBUG``
  Set to ``ON`` to enable debug output from ``FindOpenCV``.  Please enable this before filing any bug report.

``OpenCV_LIBRARY_DIR``
  Default value for ``OpenCV_LIBRARY_DIR_RELEASE`` and ``OpenCV_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find OpenCV headers only:

.. code-block:: cmake

  find_package(OpenCV 2.0.0)
  if(OpenCV_FOUND)
    include_directories(${OpenCV_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC OpenCV::OpenCV)
  endif()

Find OpenCV libraries and use imported targets:

.. code-block:: cmake

  find_package(OpenCV 2.0.0 REQUIRED COMPONENTS OpenCV)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC OpenCV::OpenCV)

Find OpenCV headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(OpenCV_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(OpenCV_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(OpenCV 2.0.0 COMPONENTS OpenCV)
  if(OpenCV_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC OpenCV::OpenCV)
  endif()

.. _`OpenCV CMake`:

OpenCV CMake
^^^^^^^^^^^

If OpenCV was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``OpenCVConfig.cmake`` and stores the result in ``CACHE``
entry ``OpenCV_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the OpenCV CMake package configuration for details on what it provides.

Set ``OpenCV_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`OpenCV pkg-config`:

OpenCV CMake
^^^^^^^^^^^

If OpenCV was installed with its pkg-config files, this module may attempt to look for OpenCV by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``OpenCV_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg OpenCV)
set(${_pkg}_INCLUDE_FILE version.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include/opencv2/core opencv2/core)
set(${_pkg}_DEFINE_PREFIX CV)
set(${_pkg}_INCLUDE_DIR_UP_INDEX 2)
set(${_pkg}_DEFAULT_COMPONENTS core)

if(WIN32)
  # Extensions:
  #
  # * .ddl.a: shared libraries, MinGW flavor
  # * .lib: shared libraries, MSVC flavor (static are *-static.a)
  if(MSVC)
    set(${_pkg}_FIND_LIBRARY_SUFFIXES .lib .a)
  else()
    set(${_pkg}_FIND_LIBRARY_SUFFIXES .dll .ddl.a .lib .a)
  endif()
endif()

if(NOT OpenCV_FIND_VERSION_MAJOR)
  set(OpenCV_FIND_VERSION_MAJOR 4)
endif()
if(NOT OpenCV_FIND_VERSION_MINOR)
  set(OpenCV_FIND_VERSION_MINOR 5)
endif()
include(${CMAKE_CURRENT_LIST_DIR}/opencv/${OpenCV_FIND_VERSION_MAJOR}.${OpenCV_FIND_VERSION_MINOR}.cmake)

# Update OPENCV library search directories with pre-built paths
function(OpenCV_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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

function(OpenCV_post_process pkg)
  foreach(_comp ${OpenCV_FIND_COMPONENTS})
    if(NOT TARGET ${pkg}::${_comp} AND TARGET opencv_${_comp})
      add_library(${pkg}::${_comp} ALIAS opencv_${_comp})
    endif()
  endforeach()
endfunction()

include(_find_utils_end)

# ==============================================================================
