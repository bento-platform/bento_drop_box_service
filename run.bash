#!/bin/bash

export ASGI_APP='bento_drop_box_service.app:application'

# Set default internal port to 5000
: "${INTERNAL_PORT:=5000}"

uvicorn "${ASGI_APP}" \
  --workers 1 \
  --loop uvloop \
  --host 0.0.0.0 \
  --port "${INTERNAL_PORT}"
