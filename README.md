# MLflow x Ray Serve (MLRay) Demo

This is a demo of how [MLflow](https://mlflow.org/) models can be deployed with [Ray Serve](https://docs.ray.io/en/latest/serve/index.html).

Document is split into:
- [Setting Up for Development](#setting-up-for-development)
- [Preparing Models for Deployment](/docs/1_preparing-models-for-deployment.md)
- [Deploying Models on Kubernetes](/docs/2_deploying-models-on-kubernetes.md)
- [Deploying Models on VMs](/docs/3_deploying-models-on-vms.md)
- [Frequently Asked Questions (FAQ)](/docs/4_frequently_asked_questions.md)

## Setting Up for Development

### Setting up Local Environment

1. Install the following:
    - [pyenv](https://github.com/pyenv/pyenv) for switching between Python versions easily
    - [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python package and project management


2. Install [Podman](https://podman.io/docs/installation) for a container runtime e.g.
    ```sh
    podman machine init --memory 8192 --cpus 4 --rootful
    podman machine start
    podman machine inspect
    ```

3. Install this project's Python version with `pyenv`, install Python dependencies with `uv` and activate the virtual environment:

    ```sh
    pyenv install
    uv sync
    source .venv/bin/activate
    ```

### Running Local Ray Cluster

For development purposes, you can run a single-node setup locally (without metrics visualization) with:

```sh
ray start --head --dashboard-host=0.0.0.0 
```

Visit Ray Dashboard at http://localhost:8265.

### Running Local MLflow 

This demo assumes that there is a running instance of MLflow server that would serve as the ML model registry. This MLflow server needs to be network-accessible by the Ray Clusters.

For development, you can run a MLflow server using Podman in the same network as the Ray Clusters:

```sh
podman network create mlray-net
podman run -d --name mlflow-server --network mlray-net -p 8080:8080 ghcr.io/mlflow/mlflow \
mlflow server --host 0.0.0.0 --port 8080
```
...and visit MLflow's web UI at http://localhost:8080.

### Setting Up Config

Copy `.env.template` as `.env` and configure the required environment variables. For example, `MLFLOW_TRACKING_URI` configures which instance of MLflow we connect to.

Copy `config.example.yml` to `config.yml` and update the configuration as necessary. These configure how models are served on Ray Serve.
