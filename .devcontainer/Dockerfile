ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ARG UV_VERSION=0.7.10
RUN pip install --upgrade pip && pip install uv==${UV_VERSION}

RUN apt-get update && apt-get install -y \
    git \
    blender \
    && rm -rf /var/lib/apt/lists/*
    