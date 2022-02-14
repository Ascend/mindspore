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
FindLibevent
---------

Find Libevent include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(Libevent
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if Libevent is not found
    [COMPONENTS <libs>...] # Libevent libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "Libevent
CMake" build.  For the latter case skip to the :ref:`Libevent CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``Libevent_FOUND``
  True if headers and requested libraries were found.

``Libevent_INCLUDE_DIRS``
  Libevent include directories.

``Libevent_LIBRARY_DIRS``
  Link directories for Libevent libraries.

``Libevent_LIBRARIES``
  Libevent component libraries to be linked.

``Libevent_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``Libevent_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``Libevent_VERSION``
  Libevent version number in ``X.Y`` format.

``Libevent_VERSION_MAJOR``
  Libevent major version number (``X`` in ``X.Y``).

``Libevent_VERSION_MINOR``
  Libevent minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``Libevent_INCLUDE_DIR``
  Directory containing Libevent headers.

``Libevent_LIBRARY_DIR_RELEASE``
  Directory containing release Libevent libraries.

``Libevent_LIBRARY_DIR_DEBUG``
  Directory containing debug Libevent libraries.

``Libevent_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``Libevent_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``Libevent_ROOT``, ``LibeventROOT``
  Preferred installation prefix.

``Libevent_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``Libevent_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``Libevent_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``Libevent``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the Libevent header files using the above hint variables (excluding ``Libevent_LIBRARYDIR``) and
saves the result in ``Libevent_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``Libevent_INCLUDEDIR``), "lib" directories near ``Libevent_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``Libevent_LIBRARY_DIR_DEBUG`` and ``Libevent_LIBRARY_DIR_RELEASE`` and
individual library locations in ``Libevent_<COMPONENT>_LIBRARY_DEBUG`` and ``Libevent_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``Libevent::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(Libevent)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

Libevent libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``Libevent_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``Libevent_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  Libevent_FIND_RELEASE_ONLY is ``ON``).

``Libevent_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``Libevent_DEBUG``
  Set to ``ON`` to enable debug output from ``FindLibevent``.  Please enable this before filing any bug report.

``Libevent_LIBRARY_DIR``
  Default value for ``Libevent_LIBRARY_DIR_RELEASE`` and ``Libevent_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find Libevent headers only:

.. code-block:: cmake

  find_package(Libevent 2.0.0)
  if(Libevent_FOUND)
    include_directories(${Libevent_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC Libevent::Libevent)
  endif()

Find Libevent libraries and use imported targets:

.. code-block:: cmake

  find_package(Libevent 2.0.0 REQUIRED COMPONENTS Libevent)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC Libevent::Libevent)

Find Libevent headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(Libevent_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(Libevent_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(Libevent 2.0.0 COMPONENTS Libevent)
  if(Libevent_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC Libevent::Libevent)
  endif()

.. _`Libevent CMake`:

Libevent CMake
^^^^^^^^^^^

If Libevent was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``LibeventConfig.cmake`` and stores the result in ``CACHE``
entry ``Libevent_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the Libevent CMake package configuration for details on what it provides.

Set ``Libevent_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`Libevent pkg-config`:

Libevent CMake
^^^^^^^^^^^

If Libevent was installed with its pkg-config files, this module may attempt to look for Libevent by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``Libevent_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg Libevent)
set(${_pkg}_NAMESPACE libevent)
set(${_pkg}_INCLUDE_FILE event.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include include/${_pkg} ${_pkg})
set(${_pkg}_DEFAULT_COMPONENTS core extra pthreads openssl)
set(${_pkg}_core_NAMES event_core)
set(${_pkg}_extra_NAMES event_extra)
set(${_pkg}_pthreads_NAMES event_pthreads)
set(${_pkg}_openssl_NAMES event_openssl)

# Extract LIBEVENT version from include directory
function(Libevent_version_function include_dir)
  set(_paths ${include_dir}/event2 ${include_dir}/event)

  _debug_print_var("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "_paths")

  find_file(
    _event_config_h event-config.h
    PATHS ${_paths}
    NO_DEFAULT_PATH)

  if(_event_config_h)
    file(READ ${_event_config_h} _event_config_file)
    set(_ver_type MAJOR MINOR PATCH)
    foreach(_type ${_ver_type})
      set(_var EVENT__VERSION_${_type})
      if("${_event_config_file}" MATCHES ".*#define[ \t]+${_var}[ \t]+([0-9]+).*")
        _debug_print("${CMAKE_CURRENT_LIST_FILE}" "${CMAKE_CURRENT_LIST_LINE}" "  ${_type} version read from ${_var}")
        set(${_pkg}_VERSION_${_type} ${CMAKE_MATCH_1})
      endif()
    endforeach()
  else()
    message(WARNING "Unable to determine Libevent's version since event-config.h file cannot be found!")
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

# Update LIBEVENT library search directories with pre-built paths
function(Libevent_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
