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
FindGTest
---------

Find GTest include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(GTest
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if GTest is not found
    [COMPONENTS <libs>...] # GTest libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "GTest
CMake" build.  For the latter case skip to the :ref:`GTest CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``GTest_FOUND``
  True if headers and requested libraries were found.

``GTest_INCLUDE_DIRS``
  GTest include directories.

``GTest_LIBRARY_DIRS``
  Link directories for GTest libraries.

``GTest_LIBRARIES``
  GTest component libraries to be linked.

``GTest_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``GTest_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``GTest_VERSION``
  GTest version number in ``X.Y`` format.

``GTest_VERSION_MAJOR``
  GTest major version number (``X`` in ``X.Y``).

``GTest_VERSION_MINOR``
  GTest minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``GTest_INCLUDE_DIR``
  Directory containing GTest headers.

``GTest_LIBRARY_DIR_RELEASE``
  Directory containing release GTest libraries.

``GTest_LIBRARY_DIR_DEBUG``
  Directory containing debug GTest libraries.

``GTest_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``GTest_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``GTest_ROOT``, ``GTestROOT``
  Preferred installation prefix.

``GTest_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``GTest_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``GTest_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``GTest``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the GTest header files using the above hint variables (excluding ``GTest_LIBRARYDIR``) and
saves the result in ``GTest_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``GTest_INCLUDEDIR``), "lib" directories near ``GTest_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``GTest_LIBRARY_DIR_DEBUG`` and ``GTest_LIBRARY_DIR_RELEASE`` and
individual library locations in ``GTest_<COMPONENT>_LIBRARY_DEBUG`` and ``GTest_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``GTest::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(GTest)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

GTest libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``GTest_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``GTest_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  GTest_FIND_RELEASE_ONLY is ``ON``).

``GTest_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``GTest_DEBUG``
  Set to ``ON`` to enable debug output from ``FindGTest``.  Please enable this before filing any bug report.

``GTest_LIBRARY_DIR``
  Default value for ``GTest_LIBRARY_DIR_RELEASE`` and ``GTest_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find GTest headers only:

.. code-block:: cmake

  find_package(GTest 2.0.0)
  if(GTest_FOUND)
    include_directories(${GTest_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC GTest::GTest)
  endif()

Find GTest libraries and use imported targets:

.. code-block:: cmake

  find_package(GTest 2.0.0 REQUIRED COMPONENTS GTest)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC GTest::GTest)

Find GTest headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(GTest_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(GTest_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(GTest 2.0.0 COMPONENTS GTest)
  if(GTest_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC GTest::GTest)
  endif()

.. _`GTest CMake`:

GTest CMake
^^^^^^^^^^^

If GTest was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``GTestConfig.cmake`` and stores the result in ``CACHE``
entry ``GTest_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the GTest CMake package configuration for details on what it provides.

Set ``GTest_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`GTest pkg-config`:

GTest CMake
^^^^^^^^^^^

If GTest was installed with its pkg-config files, this module may attempt to look for GTest by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``GTest_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg GTest)
string(TOLOWER ${_pkg} _pkg_lower)
set(${_pkg}_INCLUDE_FILE gtest.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg_lower} ${_pkg_lower})
set(${_pkg}_DEFAULT_COMPONENTS gtest gmock)
set(${_pkg}_gtest_NAMES gtest)
set(${_pkg}_gmock_NAMES gmock)
set(${_pkg}_gtest_main_NAMES gtest_main)
set(${_pkg}_gmock_main_NAMES gmock_main)

# Update GTEST library search directories with pre-built paths
function(GTest_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
