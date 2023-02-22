#!/bin/bash

cd /drop-box || exit

# Create bento_user + home
source /create_service_user.bash

# Update dependencies before we drop down from root, if we're in dev mode
if [[ -n "${BENTO_DROP_BOX_ABOUT_TO_RUN_DEV}" ]]; then
  # Install module locally (similar to pip install -e: "editable mode")
  poetry install
fi

# Fix permissions on /drop-box
chown -R bento_user:bento_user /drop-box

# Fix permissions on the data directory
if [[ -n "${SERVICE_DATA}" ]]; then
  chown -R bento_user:bento_user "${SERVICE_DATA}"
  chmod -R o-rwx "${SERVICE_DATA}"  # Remove all access from others
fi

# Drop into bento_user from root and execute the CMD specified for the image
exec gosu bento_user "$@"
