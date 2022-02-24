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
FindgRPC
---------

Find gRPC include dirs and libraries

Use this module by invoking :command:`find_package` with the form:

.. code-block:: cmake

  find_package(gRPC
    [version] [EXACT]      # Minimum or EXACT version e.g. 2020.03
    [REQUIRED]             # Fail with error if gRPC is not found
    [COMPONENTS <libs>...] # gRPC libraries by their canonical name
    )

This module finds headers and requested component libraries OR a CMake package configuration file provided by a "gRPC
CMake" build.  For the latter case skip to the :ref:`gRPC CMake` section below.

Result Variables
^^^^^^^^^^^^^^^^

This module defines the following variables:

``gRPC_FOUND``
  True if headers and requested libraries were found.

``gRPC_INCLUDE_DIRS``
  gRPC include directories.

``gRPC_LIBRARY_DIRS``
  Link directories for gRPC libraries.

``gRPC_LIBRARIES``
  gRPC component libraries to be linked.

``gRPC_<COMPONENT>_FOUND``
  True if component ``<COMPONENT>`` was found (``<COMPONENT>`` name is upper-case).

``gRPC_<COMPONENT>_LIBRARY``
  Libraries to link for component ``<COMPONENT>`` (may include :command:`target_link_libraries` debug/optimized
  keywords).

``gRPC_VERSION``
  gRPC version number in ``X.Y`` format.

``gRPC_VERSION_MAJOR``
  gRPC major version number (``X`` in ``X.Y``).

``gRPC_VERSION_MINOR``
  gRPC minor version number (``Y`` in ``X.Y``).

Cache variables
^^^^^^^^^^^^^^^

Search results are saved persistently in CMake cache entries:

``gRPC_INCLUDE_DIR``
  Directory containing gRPC headers.

``gRPC_LIBRARY_DIR_RELEASE``
  Directory containing release gRPC libraries.

``gRPC_LIBRARY_DIR_DEBUG``
  Directory containing debug gRPC libraries.

``gRPC_<COMPONENT>_LIBRARY_DEBUG``
  Component ``<COMPONENT>`` library debug variant.

``gRPC_<COMPONENT>_LIBRARY_RELEASE``
  Component ``<COMPONENT>`` library release variant.

Hints
^^^^^

This module reads hints about search locations from variables:

``gRPC_ROOT``, ``gRPCROOT``
  Preferred installation prefix.

``gRPC_INCLUDEDIR``
  Preferred include directory e.g. ``<prefix>/include``.

``gRPC_LIBRARYDIR``
  Preferred library directory e.g. ``<prefix>/lib``.

``gRPC_NO_SYSTEM_PATHS``
  Set to ``ON`` to disable searching in locations not specified by these hint variables. Default is ``OFF``.

Users may set these hints or results as ``CACHE`` entries.  Projects should not read these entries directly but
instead use the above result variables.  Note that some hint names start in upper-case ``gRPC``.  One may specify these
as environment variables if they are not specified as CMake variables or cache entries.

This module first searches for the gRPC header files using the above hint variables (excluding ``gRPC_LIBRARYDIR``) and
saves the result in ``gRPC_INCLUDE_DIR``.  Then it searches for requested component libraries using the above hints
(excluding ``gRPC_INCLUDEDIR``), "lib" directories near ``gRPC_INCLUDE_DIR``, and the library name configuration
settings below.  It saves the library directories in ``gRPC_LIBRARY_DIR_DEBUG`` and ``gRPC_LIBRARY_DIR_RELEASE`` and
individual library locations in ``gRPC_<COMPONENT>_LIBRARY_DEBUG`` and ``gRPC_<COMPONENT>_LIBRARY_RELEASE``.  When one
changes settings used by previous searches in the same build tree (excluding environment variables) this module
discards previous search results affected by the changes and searches again.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``gRPC::<component>``
  Target for specific component dependency (shared or static library); ``<component>`` name is lower-case.

It is important to note that the imported targets behave differently than variables created by this module: multiple
calls to :command:`find_package(gRPC)` in the same directory or sub-directories with different options (e.g. static or
shared) will not override the values of the targets created by the first call.

Other Variables
^^^^^^^^^^^^^^^

gRPC libraries come in many variants encoded in their file name.  Users or projects may tell this module which variant
to find by setting variables:

``gRPC_FIND_RELEASE_ONLY``
  Set to ``ON`` or ``OFF`` to specify whether to restrict the search to release libraries only.  Default is ``OFF``.

``gRPC_USE_DEBUG_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the debug libraries.  Default is ``ON`` (except when
  gRPC_FIND_RELEASE_ONLY is ``ON``).

``gRPC_USE_RELEASE_LIBS``
  Set to ``ON`` or ``OFF`` to specify whether to search and use the release libraries.  Default is ``ON``.

Other variables one may set to control this module are:

``gRPC_DEBUG``
  Set to ``ON`` to enable debug output from ``FindgRPC``.  Please enable this before filing any bug report.

``gRPC_LIBRARY_DIR``
  Default value for ``gRPC_LIBRARY_DIR_RELEASE`` and ``gRPC_LIBRARY_DIR_DEBUG``.


Examples
^^^^^^^^

Find gRPC headers only:

.. code-block:: cmake

  find_package(gRPC 2.0.0)
  if(gRPC_FOUND)
    include_directories(${gRPC_INCLUDE_DIRS})
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC gRPC::gRPC)
  endif()

Find gRPC libraries and use imported targets:

.. code-block:: cmake

  find_package(gRPC 2.0.0 REQUIRED COMPONENTS gRPC)
  add_executable(foo foo.cc)
  target_link_libraries(foo PUBLIC gRPC::gRPC)

Find gRPC headers and some *static* (release only) libraries:

.. code-block:: cmake

  set(gRPC_USE_DEBUG_LIBS        OFF)  # ignore debug libs and
  set(gRPC_USE_RELEASE_LIBS       ON)  # only find release libs
  find_package(gRPC 2.0.0 COMPONENTS gRPC)
  if(gRPC_FOUND)
    add_executable(foo foo.cc)
    target_link_libraries(foo PUBLIC gRPC::gRPC)
  endif()

.. _`gRPC CMake`:

gRPC CMake
^^^^^^^^^^^

If gRPC was built using CMake, it provides a package configuration file for use with find_package's config mode.
This module looks for the package configuration file called ``gRPCConfig.cmake`` and stores the result in ``CACHE``
entry ``gRPC_DIR``.  If found, the package configuration file is loaded and this module returns with no further action.
See documentation of the gRPC CMake package configuration for details on what it provides.

Set ``gRPC_NO_CMAKE`` to ``ON``, to disable the search for the package using the CONFIG method.

.. _`gRPC pkg-config`:

gRPC CMake
^^^^^^^^^^^

If gRPC was installed with its pkg-config files, this module may attempt to look for gRPC by relying on pkg-config.
If the components are found using this method, this module returns with no further action.

Set ``gRPC_NO_PKGCONFIG`` to ``ON``, to disable the search for the package using the pkg-config method.

#]=======================================================================]

# cmake-lint: disable=C0103

include(_find_utils_begin)

set(_pkg gRPC)
string(TOLOWER ${_pkg} _pkg_lower)
set(${_pkg}_INCLUDE_FILE grpc.h)
set(${_pkg}_INCLUDE_PATH_SUFFIXES include/${_pkg_lower} ${_pkg_lower})
set(${_pkg}_INCLUDE_DIR_UP_INDEX 1)
set(${_pkg}_DEFAULT_COMPONENTS
    address_sorting
    gpr
    grpc
    grpc_unsecure
    grpc++
    grpc++_alts
    grpc++_error_details
    grpc++_reflection
    grpc++_unsecure
    grpc_plugin_support
    grpcpp_channelz
    upb
    grpc_cpp_plugin
    grpc_csharp_plugin
    grpc_node_plugin
    grpc_objective_c_plugin
    grpc_php_plugin
    grpc_python_plugin
    grpc_ruby_plugin)

set(_${_pkg}_exec_list
    grpc_cpp_plugin
    grpc_csharp_plugin
    grpc_node_plugin
    grpc_objective_c_plugin
    grpc_php_plugin
    grpc_python_plugin
    grpc_ruby_plugin)

foreach(_exec ${_${_pkg}_exec_list})
  set(${_pkg}_${_exec}_NAMES ${_exec})
  set(${_pkg}_${_exec}_TYPE "EXECUTABLE")
endforeach()

# ==============================================================================
# Depend packages

set(${_pkg}_EXTERNAL_DEPENDENCIES ZLIB Protobuf OpenSSL c-ares absl re2)

set(${_pkg}_EXTERNAL_DEPENDENCY_ZLIB_COMPONENTS ZLIB)
set(${_pkg}_EXTERNAL_DEPENDENCY_ZLIB_FOUND_VARS ZLIB_FOUND)
set(${_pkg}_EXTERNAL_DEPENDENCY_ZLIB_FIND_ARGS)

set(${_pkg}_EXTERNAL_DEPENDENCY_Protobuf_FOUND_VARS Protobuf_FOUND PROTOBUF_FOUND)

set(${_pkg}_EXTERNAL_DEPENDENCY_OpenSSL_FOUND_VARS OPENSSL_FOUND)

set(${_pkg}_EXTERNAL_DEPENDENCY_c-ares_FOUND_VARS c-ares_FOUND)

set(${_pkg}_EXTERNAL_DEPENDENCY_absl_FOUND_VARS absl_FOUND)
set(${_pkg}_EXTERNAL_DEPENDENCY_absl_COMPONENTS
    optional
    time
    synchronization
    strings
    str_format
    status
    memory
    base
    statusor
    status
    bind_front
    inlined_vector
    flat_hash_set
    flat_hash_map)

set(${_pkg}_EXTERNAL_DEPENDENCY_re2_COMPONENTS re2)
set(${_pkg}_EXTERNAL_DEPENDENCY_re2_FOUND_VARS re2_FOUND)

# ==============================================================================

set(${_pkg}_address_sorting_NAMES address_sorting)
set(${_pkg}_gpr_NAMES gpr)
set(${_pkg}_gpr_EXTERNAL_DEPENDENCIES
    absl::optional
    absl::time
    absl::synchronization
    absl::strings
    absl::str_format
    absl::status
    absl::memory
    absl::base)
set(${_pkg}_grpc_NAMES grpc)
set(${_pkg}_grpc_DEPENDENCIES address_sorting upb gpr address_sorting upb)
set(${_pkg}_grpc_EXTERNAL_DEPENDENCIES
    OpenSSL::SSL
    OpenSSL::Crypto
    ZLIB::ZLIB
    c-ares::cares
    re2::re2
    dl
    rt
    m
    pthread
    absl::optional
    absl::strings
    absl::statusor
    absl::status
    absl::bind_front
    absl::inlined_vector
    absl::flat_hash_set
    absl::flat_hash_map)
set(${_pkg}_grpc_unsecure_NAMES grpc_unsecure)
set(${_pkg}_grpc_unsecure_DEPENDENCIES address_sorting upb gpr address_sorting upb)
set(${_pkg}_grpc_unsecure_EXTERNAL_DEPENDENCIES
    ZLIB::ZLIB
    c-ares::cares
    re2::re2
    absl::optional
    absl::strings
    absl::statusor
    absl::status
    absl::inlined_vector
    absl::flat_hash_map)
set(${_pkg}_grpc++_NAMES grpc++)
set(${_pkg}_grpc++_DEPENDENCIES grpc gpr address_sorting upb)
set(${_pkg}_grpc++_EXTERNAL_DEPENDENCIES protobuf::libprotobuf)
set(${_pkg}_grpc++_alts_NAMES grpc++_alts)
set(${_pkg}_grpc++_alts_DEPENDENCIES grpc++ grpc gpr address_sorting upb)
set(${_pkg}_grpc++_alts_EXTERNAL_DEPENDENCIES protobuf::libprotobuf)
set(${_pkg}_grpc++_error_details_NAMES grpc++_error_details)
set(${_pkg}_grpc++_error_details_DEPENDENCIES grpc++ grpc gpr address_sorting upb)
set(${_pkg}_grpc++_error_details_EXTERNAL_DEPENDENCIES protobuf::libprotobuf)
set(${_pkg}_grpc++_reflection_NAMES grpc++_reflection)
set(${_pkg}_grpc++_reflection_DEPENDENCIES grpc++ grpc gpr address_sorting upb)
set(${_pkg}_grpc++_reflection_EXTERNAL_DEPENDENCIES protobuf::libprotobuf)
set(${_pkg}_grpc++_unsecure_NAMES grpc++_unsecure)
set(${_pkg}_grpc++_unsecure_DEPENDENCIES grpc_unsecure gpr address_sorting upb)
set(${_pkg}_grpc++_unsecure_EXTERNAL_DEPENDENCIES protobuf::libprotobuf)
set(${_pkg}_grpc_plugin_support_NAMES grpc_plugin_support)
set(${_pkg}_grpc_plugin_support_EXTERNAL_DEPENDENCIES protobuf::libprotoc protobuf::libprotobuf)
set(${_pkg}_grpcpp_channelz_NAMES grpcpp_channelz)
set(${_pkg}_grpcpp_channelz_DEPENDENCIES grpc++ grpc gpr address_sorting upb)
set(${_pkg}_grpcpp_channelz_EXTERNAL_DEPENDENCIES protobuf::libprotobuf)
set(${_pkg}_upb_NAMES upb)

# Update GRPC library search directories with pre-built paths
function(gRPC_update_library_search_dirs_with_prebuilt_paths componentlibvar basedir)
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
