# ---- Stage 1: Install dependencies ----
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS installer

WORKDIR /pulsarity

COPY pyproject.toml uv.lock ./

# Install production deps + uv itself into the venv
# uv is included to mainly assist with downloading plugins
RUN uv sync --frozen --no-dev --no-install-project --extra uv

# ---- Stage 2: Runtime ----
FROM python:3.14-slim AS runtime

WORKDIR /pulsarity

COPY --from=installer /pulsarity/.venv /pulsarity/.venv

# Set for the application to read
ENV DOCKER=1

# Makes uv an accessible command line tool
ENV PATH="/pulsarity/.venv/bin:$PATH"

COPY . .

# Install the application source code with uv
RUN uv pip install --no-deps .[uv]

# Non-root user
RUN useradd --create-home pulsarity && \
    chown -R pulsarity:pulsarity /pulsarity
USER pulsarity

EXPOSE 5000

# Run with uv
CMD ["uv", "run", "pulsarity"]   