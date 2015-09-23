FROM thewtex/jupyter-notebook-debian:latest
MAINTAINER Insight Software Consortium <community@itk.org>


# Install SimpleITK Python wrapping
RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  cmake \
  git \
  libexpat1-dev \
  libhdf5-dev \
  libjpeg-dev \
  libpng12-dev \
  libpython3-dev \
  libtiff5-dev \
  python3 \
  python3-pip \
  ninja-build \
  wget \
  vim \
  zlib1g-dev

WORKDIR /usr/src

RUN git clone git://itk.org/ITK.git && \
  cd ITK && \
  git checkout v4.8.0 && \
  cd ../ && \
  mkdir ITK-build && \
  cd ITK-build && \
  cmake \
    -G Ninja \
    -DCMAKE_INSTALL_PREFIX:PATH=/usr \
    -DBUILD_EXAMPLES:BOOL=OFF \
    -DBUILD_TESTING:BOOL=OFF \
    -DBUILD_SHARED_LIBS:BOOL=ON \
    -DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=ON \
    -DCMAKE_SKIP_RPATH:BOOL=ON \
    -DITK_LEGACY_REMOVE:BOOL=ON \
    -DITK_BUILD_DEFAULT_MODULES:BOOL=ON \
    -DITK_USE_SYSTEM_LIBRARIES:BOOL=ON \
    -DModule_ITKReview:BOOL=ON \
    ../ITK && \
  ninja install && \
  cd .. && \
  rm -rf ITK ITK-build

RUN git clone git://itk.org/SimpleITK.git && \
  cd SimpleITK && \
  git checkout v0.9.0 && \
  cd .. && \
  mkdir SimpleITK-build && \
  cd SimpleITK-build && \
  cmake \
    -G Ninja \
    -DCMAKE_INSTALL_PREFIX:PATH=/usr \
    -DSimpleITK_BUILD_DISTRIBUTE:BOOL=ON \
    -DSimpleITK_BUILD_STRIP:BOOL=ON \
    -DCMAKE_BUILD_TYPE:STRING=MinSizeRel \
    -DUSE_SYSTEM_ITK:BOOL=ON \
    -DBUILD_TESTING:BOOL=OFF \
    -DBUILD_SHARED_LIBS:BOOL=OFF \
    -DWRAP_CSHARP:BOOL=OFF \
    -DWRAP_LUA:BOOL=OFF \
    -DWRAP_PYTHON:BOOL=ON \
    -DWRAP_JAVA:BOOL=OFF \
    -DWRAP_TCL:BOOL=OFF \
    -DWRAP_R:BOOL=OFF \
    -DWRAP_RUBY:BOOL=OFF \
    -DPYTHON_EXECUTABLE:FILEPATH=/usr/bin/python3 \
    -DPYTHON_INCLUDE_DIR:PATH=/usr/include/python3.4 \
    -DPYTHON_LIBRARY:FILEPATH=/usr/lib/python3.4/config-3.4m-x86_64-linux-gnu/libpython3.4.so \
    ../SimpleITK/SuperBuild && \
  ninja && \
  cd SimpleITK-build && \
  ninja install && \
  cd Wrapping && \
  /usr/bin/python3 ./PythonPackage/setup.py install && \
  cd ../../.. && \
  rm -rf SimpleITK SimpleITK-build

USER root
RUN pip3 install ipywidgets
RUN apt-get install -y python3-matplotlib

ADD . ./
