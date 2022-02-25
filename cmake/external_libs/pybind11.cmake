set(PYTHON_VERSION ${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR})

if(ENABLE_GITEE)
  if(PYTHON_VERSION VERSION_GREATER_EQUAL 3.8.0)
    set(REQ_URL "https://gitee.com/mirrors/pybind11/repository/archive/v2.6.1.tar.gz")
    set(MD5 "cd04f7bd275fedb97e8b583c115769e6")
  elseif(PYTHON_VERSION VERSION_GREATER_EQUAL 3.7.0)
    set(REQ_URL "https://gitee.com/mirrors/pybind11/repository/archive/v2.4.3.tar.gz")
    set(MD5 "8f69438201bc824c63e5774bf8c1d422")
  else()
    message("Could not find 'Python 3.8' or 'Python 3.7' or 'Python 3.9'")
    return()
  endif()
else()
  if(PYTHON_VERSION VERSION_GREATER_EQUAL 3.8.0)
    set(REQ_URL "https://github.com/pybind/pybind11/archive/v2.6.1.tar.gz")
    set(MD5 "32a7811f3db423df4ebfc731a28e5901")
  elseif(PYTHON_VERSION VERSION_GREATER_EQUAL 3.7.0)
    set(REQ_URL "https://github.com/pybind/pybind11/archive/v2.4.3.tar.gz")
    set(MD5 "62254c40f89925bb894be421fe4cdef2")
  else()
    message("Could not find 'Python 3.8' or 'Python 3.7' or 'Python 3.9'")
    return()
  endif()
endif()
set(pybind11_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2")
set(pybind11_CFLAGS "-D_FORTIFY_SOURCE=2 -O2")

if(PYTHON_VERSION VERSION_GREATER_EQUAL 3.8.0)
  set(VER 2.6.1)
elseif(PYTHON_VERSION VERSION_GREATER_EQUAL 3.7.0)
  set(VER 2.4.3)
else()
  set(VER NOT-FOUND)
endif()

mindspore_add_pkg(
  pybind11
  VER ${VER}
  URL ${REQ_URL}
  MD5 ${MD5}
  CMAKE_OPTION -DPYBIND11_TEST=OFF -DPYBIND11_LTO_CXX_FLAGS=FALSE
  TARGET_ALIAS mindspore::pybind11_module pybind11::module)
