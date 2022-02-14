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
Findre2
---------

Find re2 include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(re2
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if re2 is not found
    [COMPONENTS <libs>...] # re2 libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "re2
CMake" build.  For the latter case skip to the :ref:`re2 CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``re2_FOUND``
  True if headers and requested libraries were found.

``re2_INCLUDE_DIRS``
  re2 include directories.

``re2_LIBRARY_DIRS``
  Link directories for re2 libraries.

``re2_LIBRARIES``
  re2 component libraries to be linked.

``re2_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``re2_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``re2_VERSION``
  re2 version number in ``X.Y`` format.

``re2_VERSION_MAJOR``
  re2 major version number (``X`` in ``X.Y``).

``re2_VERSION_MINOR``
  re2 minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``re2_INCLUDE_DIR``
  Directory containing re2 headers.

``re2_LIBRARY_DIR_RELEASE``
  Directory containing release re2 libraries.

``re2_LIBRARY_DIR_DEBUG``
  Directory containing debug re2 libraries.

``re2_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``re2_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``re2_ROOT``, ``re2ROOT``
  Preferred installation prefix.

``re2_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``re2_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``re2_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``re2``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the re2 header files using the above hint variables (excluding ``re2_LIBRARYDIR``) and
saves the result in ``re2_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``re2_INCLUDEDIR``), "lib" directories near ``re2_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``re2_LIBRARY_DIR_DEBUG`` and ``re2_LIBRARY_DIR_RELEASE`` and
individual library locations in ``re2_<COMPONENT>_LIBRARY_DEBUG`` and ``re2_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``re2::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(re2)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

re2 libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``re2_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``re2_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  re2_FIND_RELEASE_ONLY is ``ON``).

``re2_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``re2_DEBUG``
  Set to ``ON`` to enable debug output from ``Findre2``.  Please enable this before filing any bug report.

``re2_LIBRARY_DIR``
  Default value for ``re2_LIBRARY_DIR_RELEASE`` and ``re2_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find re2 headers only:

.. code-block:: cmake

  find_package(re2 2.0.0)
  if(re2_FOUND)
    include_directories(${re2_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC re2::re2)
  endif()

Find re2 libraries and use imported targets:

.. code-block:: cmake

  find_package(re2 2.0.0 REQUIRED COMPONENTS re2)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC re2::re2)

Find re2 headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(re2_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(re2_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(re2 2.0.0 COMPONENTS re2)
  if(re2_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC re2::re2)
  endif()

.. _`re2 CMake`:

re2 CMake
^^^^^^^^^^^

If re2 was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``re2Config.cmake`` and stores the result in ``CACHE``
entry ``re2_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the re2 CMake package configuration for details on what it provides.

Set ``re2_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`re2 pkg-config`:

re2 CMake
^^^^^^^^^^^

If re2 was installed with its pkg-config files, this module may attempt to look for re2 by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``re2_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg re2)
set(${_pkg}_INCLUDE_FILE re2.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS re2)
set(${_pkg}_re2_NAMES re2) # names for the library

# Update RE2 library search directories with pre-built paths
function(re2_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
