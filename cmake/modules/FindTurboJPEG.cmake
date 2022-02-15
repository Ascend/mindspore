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
FindTurboJPEG
---------

Find TurboJPEG include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(TurboJPEG
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if TurboJPEG is not found
    [COMPONENTS <libs>...] # TurboJPEG libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "TurboJPEG
CMake" build.  For the latter case skip to the :ref:`TurboJPEG CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``TurboJPEG_FOUND``
  True if headers and requested libraries were found.

``TurboJPEG_INCLUDE_DIRS``
  TurboJPEG include directories.

``TurboJPEG_LIBRARY_DIRS``
  Link directories for TurboJPEG libraries.

``TurboJPEG_LIBRARIES``
  TurboJPEG component libraries to be linked.

``TurboJPEG_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``TurboJPEG_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``TurboJPEG_VERSION``
  TurboJPEG version number in ``X.Y`` format.

``TurboJPEG_VERSION_MAJOR``
  TurboJPEG major version number (``X`` in ``X.Y``).

``TurboJPEG_VERSION_MINOR``
  TurboJPEG minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``TurboJPEG_INCLUDE_DIR``
  Directory containing TurboJPEG headers.

``TurboJPEG_LIBRARY_DIR_RELEASE``
  Directory containing release TurboJPEG libraries.

``TurboJPEG_LIBRARY_DIR_DEBUG``
  Directory containing debug TurboJPEG libraries.

``TurboJPEG_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``TurboJPEG_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``TurboJPEG_ROOT``, ``TurboJPEGROOT``
  Preferred installation prefix.

``TurboJPEG_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``TurboJPEG_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``TurboJPEG_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``TurboJPEG``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the TurboJPEG header files using the above hint variables (excluding ``TurboJPEG_LIBRARYDIR``) and
saves the result in ``TurboJPEG_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``TurboJPEG_INCLUDEDIR``), "lib" directories near ``TurboJPEG_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``TurboJPEG_LIBRARY_DIR_DEBUG`` and ``TurboJPEG_LIBRARY_DIR_RELEASE`` and
individual library locations in ``TurboJPEG_<COMPONENT>_LIBRARY_DEBUG`` and ``TurboJPEG_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``TurboJPEG::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(TurboJPEG)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

TurboJPEG libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``TurboJPEG_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``TurboJPEG_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  TurboJPEG_FIND_RELEASE_ONLY is ``ON``).

``TurboJPEG_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``TurboJPEG_DEBUG``
  Set to ``ON`` to enable debug output from ``FindTurboJPEG``.  Please enable this before filing any bug report.

``TurboJPEG_LIBRARY_DIR``
  Default value for ``TurboJPEG_LIBRARY_DIR_RELEASE`` and ``TurboJPEG_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find TurboJPEG headers only:

.. code-block:: cmake

  find_package(TurboJPEG 2.0.0)
  if(TurboJPEG_FOUND)
    include_directories(${TurboJPEG_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC TurboJPEG::TurboJPEG)
  endif()

Find TurboJPEG libraries and use imported targets:

.. code-block:: cmake

  find_package(TurboJPEG 2.0.0 REQUIRED COMPONENTS TurboJPEG)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC TurboJPEG::TurboJPEG)

Find TurboJPEG headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(TurboJPEG_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(TurboJPEG_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(TurboJPEG 2.0.0 COMPONENTS TurboJPEG)
  if(TurboJPEG_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC TurboJPEG::TurboJPEG)
  endif()

.. _`TurboJPEG CMake`:

TurboJPEG CMake
^^^^^^^^^^^^^^^

If TurboJPEG was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``TurboJPEGConfig.cmake`` and stores the result in ``CACHE``
entry ``TurboJPEG_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the TurboJPEG CMake package configuration for details on what it provides.

Set ``TurboJPEG_NO_CMAKE`` to ``ON``, to disable the search for $the package using the CONFIG method.

.. _`TurboJPEG pkg-config`:

TurboJPEG PkgConfig
^^^^^^^^^^^^^^^^^^^

If TurboJPEG was installed with its pkg-config files, this module may attempt to look for TurboJPEG by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``TurboJPEG_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

.. _`TurboJpeg pkg-config`:

TurboJpeg CMake
^^^^^^^^^^^

If TurboJpeg was installed with its pkg-config files, this module may attempt to look for TurboJpeg by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``TurboJpeg_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg TurboJPEG)
set(${_pkg}_INCLUDE_FILE turbojpeg.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS JPEG TurboJPEG)
set(${_pkg}_TurboJPEG_NAMES turbojpeg) # names for the library
set(${_pkg}_JPEG_NAMES jpeg) # names for the library

if(WIN32)
  # Extensions:
  #
  # * .ddl.a: shared libraries, MinGW flavor
  # * .lib: shared libraries, MSVC flavor (static are *-static.a)
  set(${_pkg}_FIND_LIBRARY_SUFFIXES .dll .ddl.a .lib .a)

  set(win32_paths)
  if(MSVC)
    list(APPEND ${_pkg}_TurboJPEG_NAMES turbojpeg-static)
    list(APPEND ${_pkg}_JPEG_NAMES jpeg-static)

    list(APPEND win32_paths "$ENV{LOCALAPPDATA}/libjpeg-turbo64")
    list(APPEND win32_paths "$ENV{LOCALAPPDATA}/libjpeg-turbo")
    list(APPEND win32_paths "$ENV{ALLUSERSPROFILE}/libjpeg-turbo64")
    list(APPEND win32_paths "$ENV{ALLUSERSPROFILE}/libjpeg-turbo")
    list(APPEND win32_paths "C:/libjpeg-turbo64")
    list(APPEND win32_paths "C:/libjpeg-turbo")
  elseif(MINGW)
    list(APPEND ${_pkg}_TurboJPEG_NAMES libturbojpeg)
    list(APPEND ${_pkg}_JPEG_NAMES libjpeg)

    list(APPEND win32_paths "$ENV{LOCALAPPDATA}/libjpeg-turbo-gcc64")
    list(APPEND win32_paths "$ENV{LOCALAPPDATA}/libjpeg-turbo-gcc")
    list(APPEND win32_paths "$ENV{ALLUSERSPROFILE}/libjpeg-turbo-gcc64")
    list(APPEND win32_paths "$ENV{ALLUSERSPROFILE}/libjpeg-turbo-gcc")
    list(APPEND win32_paths "C:/libjpeg-turbo-gcc64")
    list(APPEND win32_paths "C:/libjpeg-turbo-gcc")
  endif()

  set(${_pkg}_INC_SYSTEM_PATHS)
  set(${_pkg}_LIB_SYSTEM_PATHS)
  foreach(_path ${win32_paths})
    to_cmake_path(_path)
    list(APPEND ${_pkg}_INC_SYSTEM_PATHS "${_path}")
    list(APPEND ${_pkg}_LIB_SYSTEM_PATHS "${_path}")
  endforeach()
endif()

# Extract TURBOJPEG version from include directory
function(TurboJPEG_version_function include_dir)
  set(_paths ${include_dir}/)

  _debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_paths")

  find_file(
    _jconfig_h jconfig.h
    PATHS ${_paths}
    NO_DEFAULT_PATH)

  if(_jconfig_h)
    file(READ ${_jconfig_h} _jconfig_h_file)
  endif()

  if("${_jconfig_h_file}" MATCHES ".*#define LIBJPEG_TURBO_VERSION +([0-9]+)\\.([0-9]+)\\.*([0-9]+).*")
    set(${_pkg}_VERSION_MAJOR ${CMAKE_MATCH_1})
    set(${_pkg}_VERSION_MINOR ${CMAKE_MATCH_2})
    set(${_pkg}_VERSION_PATCH ${CMAKE_MATCH_3})
  else()
    message(WARNING "Unable to determine TurboJPEG's version since jconfig.h file cannot be found!")
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

# Update TURBOJPEG library search directories with pre-built paths
function(TurboJPEG_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
