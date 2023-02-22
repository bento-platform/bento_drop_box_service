#!/bin/bash

cd /drop-box || exit

# Create bento_user + home
source /create_service_user.bash

# Fix permissions on /drop-box (including virtualenv)
chown -R bento_user:bento_user /drop-box

# Fix permissions on the data directory
if [[ -n "${SERVICE_DATA}" ]]; then
  chown -R bento_user:bento_user "${SERVICE_DATA}"
  chmod -R o-rwx "${SERVICE_DATA}"  # Remove all access from others
fi

# Drop into bento_user from root and execute the CMD specified for the image
exec gosu bento_user "$@"
