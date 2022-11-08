#!/bin/sh

if [ -z "${INTERNAL_PORT}" ]; then
  # Set default internal port to 5000
  INTERNAL_PORT=5000
fi

uvicorn bento_drop_box_service.app:application \
  --workers 1 \
  --worker_class uvloop \
  --bind "0.0.0.0:${INTERNAL_PORT}"
