#!/bin/bash

# Update dependencies and install module locally
/poetry_user_install_dev.bash

export QUART_ENV='development'
export QUART_APP='bento_drop_box_service.app:application'

# Set default internal port to 5000
: "${INTERNAL_PORT:=5000}"

# Set default debugger port to debugpy default
: "${DEBUGGER_PORT:=5678}"

# Module was installed locally in entrypoint before dropping into root
python -m debugpy --listen "0.0.0.0:${DEBUGGER_PORT}" -m quart run \
  --host 0.0.0.0 \
  --port "${INTERNAL_PORT}"
