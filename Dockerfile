FROM debian:8
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


# Install the Jupyter notebook
# Based off jupyter/notebook/Dockerfile
RUN curl -sL https://deb.nodesource.com/setup | bash - && \
    apt-get update && apt-get install -y \
  locales \
  libzmq3-dev \
  sqlite3 \
  libsqlite3-dev \
  pandoc \
  libcurl4-openssl-dev \
  nodejs

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
  locale-gen
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN pip3 install --upgrade setuptools pip

RUN mkdir -p /srv/
WORKDIR /srv/
RUN git clone --depth 1 https://github.com/ipython/ipykernel /srv/ipykernel
WORKDIR /srv/ipykernel
RUN pip3 install .

WORKDIR /srv/
RUN git clone --depth 1 https://github.com/jupyter/notebook /srv/notebook
WORKDIR /srv/notebook/
RUN chmod -R +rX /srv/notebook
RUN pip3 install .
RUN python3 -m ipykernel.kernelspec

EXPOSE 8889

CMD ["sh", "-c", "jupyter notebook --port=8889 --no-browser --ip=0.0.0.0"]


# Make the SimpleITK Tutorial Notebooks available
# Tutorial dependencies
# libfreetype6-dev is a matplotlib workaround:
# https://stackoverflow.com/questions/27024731/matplotlib-compilation-error-typeerror-unorderable-types-str-int
RUN apt-get update && apt-get install -y \
  python3-matplotlib \
  python3-numpy

# jupyter is our user
RUN useradd -m -s /bin/bash jupyter
USER jupyter
ENV HOME /home/jupyter
ENV SHELL /bin/bash
ENV USER jupyter
WORKDIR /home/jupyter/

RUN mkdir -p ./Data
ADD Data/* ./Data/
ADD *.ipynb *.py *.png *.svg *.jpg ./
USER root
RUN chown -R jupyter.jupyter *
USER jupyter
