#!/bin/bash

# Set .gitconfig for development
/set_gitconfig.bash

# Source the development virtual environment
source /env/bin/activate

# Update dependencies and install module locally (similar to pip install -e: "editable mode")
poetry install

export QUART_ENV='development'
export QUART_APP='bento_drop_box_service.app:application'

if [[ -z "${INTERNAL_PORT}" ]]; then
  # Set default internal port to 5000
  INTERNAL_PORT=5000
fi

# Module was installed locally in entrypoint before dropping into root
python -m debugpy --listen 0.0.0.0:5678 -m quart run \
  --host 0.0.0.0 \
  --port "${INTERNAL_PORT}"
