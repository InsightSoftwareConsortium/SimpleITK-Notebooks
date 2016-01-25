#!/bin/sh

which docker &> /dev/null
if [ $? -ne 0 ]; then
	echo "Error: the 'docker' command was not found.  Please install docker."
	exit 1
fi

_OS=$(uname)
if [ "${_OS}" != "Linux" ]; then
	_VM=$(docker-machine active 2> /dev/null || echo "default")
	if ! docker-machine inspect "${_VM}" &> /dev/null; then
		echo "Creating machine ${_VM}..."
		docker-machine -D create -d virtualbox --virtualbox-memory 2048 ${_VM}
	fi
	docker-machine start ${_VM} > /dev/null
    eval $(docker-machine env $_VM --shell=sh)
fi

_IP=$(docker-machine ip ${_VM} 2> /dev/null || echo "localhost" )
_URL="http://${_IP}:8888"

_RUNNING=$(docker ps -q --filter "name=simpleitk-notebooks")
if [ -n "$_RUNNING" ]; then
	docker stop simpleitk-notebooks
fi

echo ""
echo "Setting up the Docker Jupyter Notebook"
echo ""
echo "Point your web browser to ${_URL}"
echo ""
echo ""
echo "Enter Control-C to stop the server."

_REPO_DIR="$(cd "$(dirname "$0")" && pwd )"
_MOUNT_LOCAL=""
if [ "${_OS}" = "Linux" ] || [ "${_OS}" = "Darwin" ]; then
	_MOUNT_LOCAL=" -v ${_REPO_DIR}:/home/jovyan/notebooks/ "
fi
docker run \
  --rm \
  --name 2015-miccai \
  ${_MOUNT_LOCAL} \
  -p 8888:8888 \
  insighttoolkit/simpleitk-notebooks &> /dev/null

# vim: noexpandtab shiftwidth=4 tabstop=4 softtabstop=0
