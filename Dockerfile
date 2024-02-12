FROM ghcr.io/bento-platform/bento_base_image:python-debian-2024.02.01

# Use uvicorn (instead of hypercorn) in production since I've found
# multiple benchmarks showing it to be faster - David L
RUN pip install --no-cache-dir poetry==1.7.1 "uvicorn[standard]==0.27.1"

# Backwards-compatible with old BentoV2 container layout
WORKDIR /drop-box

COPY pyproject.toml .
COPY poetry.lock .

# Install production dependencies
# Without --no-root, we get errors related to the code not being copied in yet.
# But we don't want the code here, otherwise Docker cache doesn't work well.
RUN poetry config virtualenvs.create false && poetry install --without dev --no-root

# Manually copy only what's relevant
# (Don't use .dockerignore, which allows us to have development containers too)
COPY bento_drop_box_service bento_drop_box_service
COPY entrypoint.bash .
COPY run.bash .
COPY LICENSE .
COPY README.md .

# Install the module itself, locally (similar to `pip install -e .`)
RUN poetry install --without dev

ENTRYPOINT [ "bash", "./entrypoint.bash" ]
CMD [ "bash", "./run.bash" ]
