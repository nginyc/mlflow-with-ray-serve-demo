FROM ubuntu:24.04

# Install dependencies for pyenv and Python build
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev \
    libffi-dev liblzma-dev git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install pyenv
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
RUN curl -fsSL https://pyenv.run | bash

# Install Python 3.9 via pyenv
RUN pyenv install 3.9.22 && \
    pyenv global 3.9.22
ENV PATH="/root/.pyenv/shims:$PATH"

# Ensure pip is up to date
RUN pip install --upgrade pip

# Install Ray Serve and MLflow
RUN pip install "ray[serve]"
RUN pip install mlflow boto3

# Copy mlray/ into image
COPY mlray/ mlray/

# Set default shell to bash and pyenv in PATH
SHELL ["/bin/bash", "-c"]
ENV PATH="/root/.pyenv/shims:$PATH"