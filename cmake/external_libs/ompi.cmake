if(ENABLE_GITEE)
  set(REQ_URL "https://gitee.com/mirrors/ompi/repository/archive/v4.0.3.tar.gz")
  set(MD5 "70f764c26ab6cd99487d58be0cd8c409")
else()
  set(REQ_URL "https://github.com/open-mpi/ompi/archive/v4.0.3.tar.gz")
  set(MD5 "86cb724e8fe71741ad3be4e7927928a2")
endif()

set(ompi_CXXFLAGS "-D_FORTIFY_SOURCE=2 -O2")
mindspore_add_pkg(
  MPI
  VER 3.0 # NB: in the case of MPI, this is the MPI standard version, not the actual library version
  LIBS mpi
  LIBS_CMAKE_NAMES C
  URL ${REQ_URL}
  MD5 ${MD5}
  PRE_CONFIGURE_COMMAND ./autogen.pl
  CONFIGURE_COMMAND ./configure
  TARGET_ALIAS mindspore::ompi MPI::MPI_C)
include_directories(${ompi_INC})
