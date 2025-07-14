# MLflow x Ray Serve (MLRay) Demo

This is a demo of how [MLflow](https://mlflow.org/) models can be deployed with [Ray Serve](https://docs.ray.io/en/latest/serve/index.html) running on Ray Clusters deployed on your own VMs. Multiple major Python versions are supported by running multiple Ray Clusters.

## Running Ray Clusters on VMs

### Overview

Each Ray Cluster assumes the same major Python version and Ray version across all its tasks/deployments (see [Ray's documentation on Environment Dependencies](https://docs.ray.io/en/latest/ray-core/handling-dependencies.html)). The Ray team recommends multiple Ray Clusters for each major Python version to be supported (see [Ray's discussion forum](https://discuss.ray.io/t/how-to-use-different-python-versions-in-the-same-cluster/15825)).

**Pre-requisites**
- A list of Python versions to be supported (e.g. `3.9.22` and `3.12.11`)
- Multiple Linux VM(s) with network connectivity with the internet and with one another. There should also be at least as many Linux VM(s) as Python versions

For development & testing, you can emulate multiple Linux VM(s) on a single machine with [Podman](https://podman.io/) instead.

### Steps (on a single machine using Podman)

1. Install [Podman](https://podman.io/docs/installation) for a container runtime. For non-Linux runtimes, ensure that you init and start the Podman machine as rootful with at least 8 GB memory and 4 CPUs:
    ```sh
    podman machine init --memory 8192 --cpus 4 --rootful
    podman machine start
    podman machine inspect
    ```

2. Build a Docker image for each Python version e.g.:
    ```sh
    podman build -f docker/ray-serve-py39.Dockerfile -t ray-serve-py39 .
    podman build -f docker/ray-serve-py312.Dockerfile -t ray-serve-py312 .
    ```

3. Run a Ray head node for each Python version e.g.: 

    ```sh
    podman network create mlray-net
    podman run --name ray-head-py39 --network mlray-net --cpus=2 --memory=4g -p 8265:8265 -p 6379:6379 -p 10001:10001 -p 8000:8000 -d ray-serve-py39 \
        bash -c "ray start --head --num-cpus=2 --memory=4096 --port=6379 --dashboard-host=0.0.0.0 && tail -f /dev/null"

    podman run --name ray-head-py312 --network mlray-net --cpus=2 --memory=4g -p 8266:8265 -p 6380:6379 -p 10002:10001 -p 8001:8000 -d ray-serve-py312 \
        bash -c "ray start --head --num-cpus=2 --memory=4096 --port=6379 --dashboard-host=0.0.0.0 && tail -f /dev/null"
    ```

    With the above example, you can visit the respective Ray dashboards on your browser with http://localhost:8265 and http://localhost:8266.

4. If desired, run a Ray worker node for each Python version as well e.g.:

    ```sh
    podman run --name ray-worker-py39 --network mlray-net --cpus=2 --memory=4g -d ray-serve-py39 bash -c "ray start --address=ray-head-py39:6379 --num-cpus=2 --memory=4096 && tail -f /dev/null"
    podman run --name ray-worker-py312 --network mlray-net --cpus=2 --memory=4g -d ray-serve-py312 bash -c "ray start --address=ray-head-py312:6379 --num-cpus=2 --memory=4096 && tail -f /dev/null"
    ```

### Steps (on actual VMs)

> This demo was tested on Ubuntu 24.04 (LTS) VMs

1. On each VM, install [pyenv](https://github.com/pyenv/pyenv), and ensure shims are set up and shell function is installed such that `pyenv shell` works:

    ```sh
    curl -fsSL https://pyenv.run | bash
    eval "$(pyenv init -)"
    ```

2. Clone this project's code on each VM

3. For each Python version to be supported, at the root of the project's code:

    1. On each VM, install the same Python version and activate it:

        ```sh
        pyenv install 3.9.22
        pyenv shell 3.9.22
        ```
    
    2. On each VM, install Ray Serve and MLflow using PIP, and ensure the version of Ray is the same across all VMs:
        
        ```sh
        pip install -U "ray[serve]"
        pip install -U mlflow boto3
        ray --version
        ```

    3. On a single VM designated to be the Ray head node for the Ray Cluster uniquely associated with this Python version, [start a Ray head node](https://docs.ray.io/en/latest/cluster/vms/user-guides/launching-clusters/on-premises.html#start-the-head-node) via the [Ray Cluster Management CLI](https://docs.ray.io/en/latest/cluster/cli.html#ray-start)

        ```sh
        ray start --head --port=6379 --dashboard-host=0.0.0.0 
        ```

    4. For every other extra VM designated to Ray worker nodes for the Ray Cluster associated with this Python version, [start a Ray worker node](https://docs.ray.io/en/latest/cluster/vms/user-guides/launching-clusters/on-premises.html#start-worker-nodes) via the [Ray Cluster Management CLI](https://docs.ray.io/en/latest/cluster/cli.html#ray-start)
    
        ```sh
        ray start --address=<head-node-address>:6379
        ```

## Running MLflow 

This demo assumes that there is a running instance of MLflow server that would serve as the ML model registry. This MLflow server needs to be network-accessible by the Ray Clusters.

For development, you can run a MLflow server using Podman in the same network as the Ray Clusters:
```sh
podman run -d --name mlflow-server --network mlray-net -p 8080:8080 ghcr.io/mlflow/mlflow \
  mlflow server --host 0.0.0.0 --port 8080
```
...and visit MLflow's web UI at http://localhost:8080.

## Setting up Local Environment

This sets up the local environment where model can be trained and deployed.

1. Install the following:
    - [pyenv](https://github.com/pyenv/pyenv) for switching between Python versions easily
    - [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python package and project management

2. Install this project's Python version with `pyenv`, install Python dependencies with `uv` and activate the virtual environment:

    ```sh
    pyenv install
    uv sync
    source .venv/bin/activate
    ```

## Deploying Trained Models

We demonstrate training and deploying ML models with conflicting library versions and Python versions.

1. Set up a virtual environment for each Python version to test with `pyenv`

    For example, set it up for `3.12.11`:
    ```sh
    pyenv install 3.12.11
    pyenv shell 3.12.11
    python -m venv .venv.py312/
    ```

    ...and set it up for `3.9.22`:
    ```sh
    pyenv install 3.9.22
    pyenv shell 3.9.22
    python -m venv .venv.py39/
    ```

    These versions need to match the respective Ray Clusters', down to the patch number.

2. Copy `.env.template` as `.env` and configure the required environment variables

3. Train different ML models with different library versions and Python versions, and log them all to MLflow:

    For example, we train and log 3 models by running `train_catboost_model.ipynb` in the respective virtual environments after installing their required dependencies:

    1. The 1st model uses CatBoost 1.2 on Python 3.12, with its PIP requirements in `examples/requirements.iris_classifier-py312-catboost12.txt`

        ```sh
        source .venv.py312/bin/activate
        pip install -r examples/requirements.iris_classifier-py312-catboost12.txt
        # Now run `train_catboost_model.ipynb` with this Python kernel
        ```

    2. The 2nd model uses CatBoost 1.2 on Python 3.9, with its PIP requirements in `examples/requirements.iris_classifier-py39-catboost12.txt`

        ```sh
        source .venv.py39/bin/activate
        pip install -r examples/requirements.iris_classifier-py39-catboost12.txt
        # Now run `train_catboost_model.ipynb` with this Python kernel
        ```

    3. The 3rd model uses CatBoost 1.1 on Python 3.9, with its PIP requirements in `examples/requirements.iris_classifier-py39-catboost11.txt`

        ```sh
        source .venv.py39/bin/activate
        pip install -r examples/requirements.iris_classifier-py39-catboost11.txt
        # Now run `train_catboost_model.ipynb` with this Python kernel
        ```

    > MLflow automatically [infers the required dependencies](https://mlflow.org/docs/latest/ml/model/dependencies) of the trained model when the `log_model(model)` method is called. 

    ![](examples/mlflow_experiments.png)

4. On MLflow, for each model that is to be deployed, [register each model](https://mlflow.org/docs/latest/ml/model-registry) with a `.staging` suffix in their name, and promote a trained model version under the registered model

    For example, register a model each for `iris_classifier-py312-catboost12.staging`, `iris_classifier-py39-catboost12.staging`, `iris_classifier-py39-catboost11.staging` based on the trained models in the previous step

    ![](examples/mlflow_registered_models.png)

    4. For each registered model to be deployed, add the following tags to configure their corresponding [Ray Serve deployments](https://docs.ray.io/en/latest/serve/configure-serve-deployment.html):

    | **Tag**                                   | **Required** | **Example**                        | **Description**                        |
    |:------------------------------------------|:------------:|:-----------------------------------|:---------------------------------------|
    | `ray.name`                               | Yes          | `iris_classifier-py39-catboost11`  | Name of the deployment                 |
    | `ray.num_replicas`                       | Yes          | `1`                                | Number of replicas                     |
    | `ray.ray_actor_options.num_cpus`         | Yes          | `0.5`                              | Number of CPUs per replica             |
    | `ray.ray_actor_options.memory`           | Yes          | `1`                                | Memory in GB per replica               |
    | `ray.ray_actor_options.runtime_env.env_vars` | No       | `{"ENV_VAR": "value"}`             | Environment variables for deployment   |

5. Copy `config.example.yml` to `config.yml` and update the configuration as necessary

6. Run the `mlray deploy` command to deploy the registered models in the MLflow model registry for each Ray Cluster e.g.:

    ```sh
    mlray deploy config.yml ray-cluster-py39
    mlray deploy config.yml ray-cluster-py312
    ```

    Check the respective Ray dashboards to check on the status of the deployments.

    ![](examples/ray_serve_deployments.png)

    > For each model, this command reads from `python_env.yml` and `requirements.txt` in the [MLflow model artifact](https://mlflow.org/docs/latest/ml/model/dependencies) to determine its required Python version and PIP dependencies for Ray Serve. It also reads from each model's tags to configure the Ray Serve deployment.
    
    > Note: If you are running this demo fully locally on Apple Silicon (ARM64) on Podman, you would encounter the error that `catboost==1.1` cannot be installed on the Python 3.9 Ray Cluster. This is because your Ray Cluster would be running on ARM64 version of Ubuntu (to match the host machine's architecture) and CatBoost 1.1 does not have the Linux wheels for the ARM64 architecture :(


7. Verify that the model serving endpoints are working with e.g. REST requests like those in `examples/xxx.request.http`

    ![](examples/model_http_request.png)


