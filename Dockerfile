ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS builder

ARG UV_VERSION=0.7.10
RUN pip install --upgrade pip && pip install uv==${UV_VERSION}

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y \
    blender \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY src .

CMD [".venv/bin/python", "-m", "blender_camera"]