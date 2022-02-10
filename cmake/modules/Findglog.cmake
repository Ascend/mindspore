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
Findglog
---------

Find glog include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(glog
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if glog is not found
    [COMPONENTS <libs>...] # glog libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "glog
CMake" build.  For the latter case skip to the :ref:`glog CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``glog_FOUND``
  True if headers and requested libraries were found.

``glog_INCLUDE_DIRS``
  glog include directories.

``glog_LIBRARY_DIRS``
  Link directories for glog libraries.

``glog_LIBRARIES``
  glog component libraries to be linked.

``glog_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``glog_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``glog_VERSION``
  glog version number in ``X.Y`` format.

``glog_VERSION_MAJOR``
  glog major version number (``X`` in ``X.Y``).

``glog_VERSION_MINOR``
  glog minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``glog_INCLUDE_DIR``
  Directory containing glog headers.

``glog_LIBRARY_DIR_RELEASE``
  Directory containing release glog libraries.

``glog_LIBRARY_DIR_DEBUG``
  Directory containing debug glog libraries.

``glog_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``glog_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``glog_ROOT``, ``glogROOT``
  Preferred installation prefix.

``glog_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``glog_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``glog_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``glog``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the glog header files using the above hint variables (excluding ``glog_LIBRARYDIR``) and
saves the result in ``glog_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``glog_INCLUDEDIR``), "lib" directories near ``glog_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``glog_LIBRARY_DIR_DEBUG`` and ``glog_LIBRARY_DIR_RELEASE`` and
individual library locations in ``glog_<COMPONENT>_LIBRARY_DEBUG`` and ``glog_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``glog::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(glog)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

glog libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``glog_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``glog_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  glog_FIND_RELEASE_ONLY is ``ON``).

``glog_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``glog_DEBUG``
  Set to ``ON`` to enable debug output from ``Findglog``.  Please enable this before filing any bug report.

``glog_LIBRARY_DIR``
  Default value for ``glog_LIBRARY_DIR_RELEASE`` and ``glog_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find glog headers only:

.. code-block:: cmake

  find_package(glog 0.5.0)
  if(glog_FOUND)
    include_directories(${glog_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC glog::glog)
  endif()

Find glog libraries and use imported targets:

.. code-block:: cmake

  find_package(glog 0.5.0 REQUIRED COMPONENTS glog)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC glog::glog)

Find glog headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(glog_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(glog_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(glog 0.5.0 COMPONENTS glog)
  if(glog_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC glog::glog)
  endif()

.. _`glog CMake`:

glog CMake
^^^^^^^^^^^

If glog was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``glogConfig.cmake`` and stores the result in ``CACHE``
entry ``glog_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the glog CMake package configuration for details on what it provides.

Set ``glog_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`glog pkg-config`:

glog CMake
^^^^^^^^^^^

If glog was installed with its pkg-config files, this module may attempt to look for glog by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``glog_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

include(_find_utils_begin)

set(_pkg glog)
set(${_pkg}_INCLUDE_FILE stl_logging.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS glog)
set(${_pkg}_glog_NAMES glog)

function(glog_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
  if("x${CMAKE_CXX_COMPILER_ID}" STREQUAL "xMSVC")
    list(APPEND ${componentlibvar} ${basedir}/Relase)
    list(APPEND ${componentlibvar} ${basedir}/MinSizeRel)
    list(APPEND ${componentlibvar} ${basedir}/RelWithDebInfo)
    list(APPEND ${componentlibvar} ${basedir}/Debug)
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
