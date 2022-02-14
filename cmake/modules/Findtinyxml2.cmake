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
Findtinyxml2
---------

Find tinyxml2 include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(tinyxml2
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if tinyxml2 is not found
    [COMPONENTS <libs>...] # tinyxml2 libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "tinyxml2
CMake" build.  For the latter case skip to the :ref:`tinyxml2 CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``tinyxml2_FOUND``
  True if headers and requested libraries were found.

``tinyxml2_INCLUDE_DIRS``
  tinyxml2 include directories.

``tinyxml2_LIBRARY_DIRS``
  Link directories for tinyxml2 libraries.

``tinyxml2_LIBRARIES``
  tinyxml2 component libraries to be linked.

``tinyxml2_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``tinyxml2_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``tinyxml2_VERSION``
  tinyxml2 version number in ``X.Y`` format.

``tinyxml2_VERSION_MAJOR``
  tinyxml2 major version number (``X`` in ``X.Y``).

``tinyxml2_VERSION_MINOR``
  tinyxml2 minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``tinyxml2_INCLUDE_DIR``
  Directory containing tinyxml2 headers.

``tinyxml2_LIBRARY_DIR_RELEASE``
  Directory containing release tinyxml2 libraries.

``tinyxml2_LIBRARY_DIR_DEBUG``
  Directory containing debug tinyxml2 libraries.

``tinyxml2_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``tinyxml2_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``tinyxml2_ROOT``, ``tinyxml2ROOT``
  Preferred installation prefix.

``tinyxml2_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``tinyxml2_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``tinyxml2_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``tinyxml2``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the tinyxml2 header files using the above hint variables (excluding ``tinyxml2_LIBRARYDIR``) and
saves the result in ``tinyxml2_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``tinyxml2_INCLUDEDIR``), "lib" directories near ``tinyxml2_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``tinyxml2_LIBRARY_DIR_DEBUG`` and ``tinyxml2_LIBRARY_DIR_RELEASE`` and
individual library locations in ``tinyxml2_<COMPONENT>_LIBRARY_DEBUG`` and ``tinyxml2_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``tinyxml2::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(tinyxml2)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

tinyxml2 libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``tinyxml2_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``tinyxml2_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  tinyxml2_FIND_RELEASE_ONLY is ``ON``).

``tinyxml2_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``tinyxml2_DEBUG``
  Set to ``ON`` to enable debug output from ``Findtinyxml2``.  Please enable this before filing any bug report.

``tinyxml2_LIBRARY_DIR``
  Default value for ``tinyxml2_LIBRARY_DIR_RELEASE`` and ``tinyxml2_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find tinyxml2 headers only:

.. code-block:: cmake

  find_package(tinyxml2 0.5.0)
  if(tinyxml2_FOUND)
    include_directories(${tinyxml2_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC tinyxml2::tinyxml2)
  endif()

Find tinyxml2 libraries and use imported targets:

.. code-block:: cmake

  find_package(tinyxml2 0.5.0 REQUIRED COMPONENTS tinyxml2)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC tinyxml2::tinyxml2)

Find tinyxml2 headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(tinyxml2_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(tinyxml2_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(tinyxml2 0.5.0 COMPONENTS tinyxml2)
  if(tinyxml2_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC tinyxml2::tinyxml2)
  endif()

.. _`tinyxml2 CMake`:

tinyxml2 CMake
^^^^^^^^^^^

If tinyxml2 was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``tinyxml2Config.cmake`` and stores the result in ``CACHE``
entry ``tinyxml2_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the tinyxml2 CMake package configuration for details on what it provides.

Set ``tinyxml2_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`tinyxml2 pkg-config`:

tinyxml2 CMake
^^^^^^^^^^^

If tinyxml2 was installed with its pkg-config files, this module may attempt to look for tinyxml2 by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``tinyxml2_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

include(_find_utils_begin)

set(_pkg tinyxml2)
set(${_pkg}_INCLUDE_FILE tinyxml2.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS tinyxml2)
set(${_pkg}_tinyxml2_NAMES tinyxml2)

function(tinyxml2_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
