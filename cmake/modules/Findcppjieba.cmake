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
Findcppjieba
---------

Find cppjieba include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(cppjieba
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if cppjieba is not found
    [COMPONENTS <libs>...] # cppjieba libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "cppjieba
CMake" build.  For the latter case skip to the :ref:`cppjieba CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``cppjieba_FOUND``
  True if headers and requested libraries were found.

``cppjieba_INCLUDE_DIRS``
  cppjieba include directories.

``cppjieba_LIBRARY_DIRS``
  Link directories for cppjieba libraries.

``cppjieba_LIBRARIES``
  cppjieba component libraries to be linked.

``cppjieba_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``cppjieba_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``cppjieba_VERSION``
  cppjieba version number in ``X.Y`` format.

``cppjieba_VERSION_MAJOR``
  cppjieba major version number (``X`` in ``X.Y``).

``cppjieba_VERSION_MINOR``
  cppjieba minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``cppjieba_INCLUDE_DIR``
  Directory containing cppjieba headers.

``cppjieba_LIBRARY_DIR_RELEASE``
  Directory containing release cppjieba libraries.

``cppjieba_LIBRARY_DIR_DEBUG``
  Directory containing debug cppjieba libraries.

``cppjieba_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``cppjieba_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``cppjieba_ROOT``, ``cppjiebaROOT``
  Preferred installation prefix.

``cppjieba_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``cppjieba_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``cppjieba_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``cppjieba``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the cppjieba header files using the above hint variables (excluding ``cppjieba_LIBRARYDIR``) and
saves the result in ``cppjieba_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``cppjieba_INCLUDEDIR``), "lib" directories near ``cppjieba_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``cppjieba_LIBRARY_DIR_DEBUG`` and ``cppjieba_LIBRARY_DIR_RELEASE`` and
individual library locations in ``cppjieba_<COMPONENT>_LIBRARY_DEBUG`` and ``cppjieba_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``cppjieba::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(cppjieba)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

cppjieba libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``cppjieba_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``cppjieba_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  cppjieba_FIND_RELEASE_ONLY is ``ON``).

``cppjieba_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``cppjieba_DEBUG``
  Set to ``ON`` to enable debug output from ``Findcppjieba``.  Please enable this before filing any bug report.

``cppjieba_LIBRARY_DIR``
  Default value for ``cppjieba_LIBRARY_DIR_RELEASE`` and ``cppjieba_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find cppjieba headers only:

.. code-block:: cmake

  find_package(cppjieba 2.0.0)
  if(cppjieba_FOUND)
    include_directories(${cppjieba_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC cppjieba::cppjieba)
  endif()

Find cppjieba libraries and use imported targets:

.. code-block:: cmake

  find_package(cppjieba 2.0.0 REQUIRED COMPONENTS cppjieba)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC cppjieba::cppjieba)

Find cppjieba headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(cppjieba_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(cppjieba_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(cppjieba 2.0.0 COMPONENTS cppjieba)
  if(cppjieba_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC cppjieba::cppjieba)
  endif()

.. _`cppjieba CMake`:

cppjieba CMake
^^^^^^^^^^^^^^

If cppjieba was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``cppjiebaConfig.cmake`` and stores the result in
``CACHE`` entry ``cppjieba_DIR``.  If found, the package configuration file is loaded and this module returns with no
further action.  See documentation of the cppjieba CMake package configuration for details on what it provides.

Set ``cppjieba_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`cppjieba pkg-config`:

cppjieba CMake
^^^^^^^^^^^^^^

If cppjieba was installed with its pkg-config files, this module may attempt to look for cppjieba by relying on
pkg-config. If the components are found using this method, this module returns with no further action.

Set ``cppjieba_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg cppjieba)
set(${_pkg}_INCLUDE_FILE Jieba.hpp)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_INCLUDE_DIR_UP_INDEX 1)
set(${_pkg}_DEFAULT_COMPONENTS cppjieba)
set(${_pkg}_cppjieba_HEADER_ONLY TRUE)

include(_find_utils_end)

# ==============================================================================
