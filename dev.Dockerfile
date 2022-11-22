FROM ghcr.io/bento-platform/bento_base_image:python-debian-latest

RUN pip install --no-cache-dir poetry==1.2.2 "hypercorn[uvloop]==0.14.3"

# Backwards-compatible with old BentoV2 container layout
WORKDIR /drop-box

COPY pyproject.toml pyproject.toml
COPY poetry.toml poetry.toml
COPY poetry.lock poetry.lock

# Install production + development dependencies
# Without --no-root, we get errors related to the code not being copied in yet.
# But we don't want the code here, otherwise Docker cache doesn't work well.
RUN poetry install --no-root

# Don't include actual code in the development image - will be mounted in using a volume.

CMD [ "sh", "./entrypoint.dev.sh" ]
