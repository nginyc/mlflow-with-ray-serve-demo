# Ray Serve Demo

This is a demo of how [MLflow](https://mlflow.org/) models can be deployed with [Ray Serve](https://docs.ray.io/en/latest/serve/index.html).

## Setup

1. Install the following:
    - [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python package and project management
    - [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl) for running commands against Kubernetes clusters
    - [Helm](https://helm.sh/docs/intro/install/) for installing and managing Kubernetes applications
    - [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) for running local Kubernetes clusters using Docker container “nodes”
    - [Colima](https://github.com/abiosoft/colima) for Docker container runtimes as a replacement for Docker Desktop on MacOS (which requires subscription for commercial use in larger organizations)

2. Install Python dependencies and activate the virtual environment:

    ```sh
    uv sync
    source .venv/bin/activate
    ```

## Train Models

1. First, start a MLflow tracking server locally:

    ```sh
    mlflow server --host 127.0.0.1 --port 8080
    ```

2. Then, you can train models and log them to MLflow. 

    For our example, you can run the notebook `train_catboost_model.ipynb` to train a CatBoost model for iris classification twice:

    For the 1st time, you simply run it with the default dependency versions.
    For the 2nd time, you run it after downgrading to an older catboost version:
    ```sh
    uv pip install catboost==1.1 numpy==1.26.4 pandas==1.5.3
    ```

## Deploy Models

1. Start a Ray Cluster locally with:

    ```sh
    ray start --head
    ```

    You can subsequently view the Ray dashboard at http://localhost:8265.

    You can check the status of the Ray Cluster with:

    ```sh
    ray status
    ```

2. Modify `config.yml`(refer to [Configure Ray Serve deployments](https://docs.ray.io/en/latest/serve/configure-serve-deployment.html)) approriately based on the models you want deployed, and run:
    ```sh
    serve start
    serve deploy config.yml
    ```

    For our example, the default `config.yml` requires you to first register 2 models on MLflow:
    - `catboost-iris-classifier` (version 1), which uses the previously trained model with default dependency versions
    - `old-catboost-iris-classifier` (version 1), which uses older library versions associated with an older version of catboost

    You can check the status of the Ray Serve with:
    ```sh
    ray status
    ```

3. Verify that the model serving endpoints are working with e.g. REST requests like those in `examples/request-xxx.http`


<!-- 1. Start a Ray Cluster on Kubernetes locally by following the instructions at [Ray Cluster Quickstart](https://docs.ray.io/en/latest/cluster/kubernetes/getting-started/raycluster-quick-start.html) -->
