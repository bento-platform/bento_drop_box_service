FROM ghcr.io/bento-platform/bento_base_image:python-debian-2023.11.10

RUN pip install --no-cache-dir poetry==1.6.1 "uvicorn[standard]==0.24.0"

# Backwards-compatible with old BentoV2 container layout
WORKDIR /drop-box

COPY pyproject.toml .
COPY poetry.lock .

# Install production + development dependencies
# Without --no-root, we get errors related to the code not being copied in yet.
# But we don't want the code here, otherwise Docker cache doesn't work well.
RUN poetry config virtualenvs.create false && poetry install --no-root

# Don't include actual code in the development image - will be mounted in using a volume.
# Include an entrypoint + runner just so we have somewhere to start.
COPY entrypoint.bash .
COPY run.dev.bash .

# Tell the service that we're running a local development container
ENV BENTO_CONTAINER_LOCAL=true

ENTRYPOINT [ "bash", "./entrypoint.bash" ]
CMD [ "bash", "./run.dev.bash" ]
