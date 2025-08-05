# Preparing Models for Deployment

This document describes how models trained on MLflow should be prepared on MLflow for deployment.

## Training and Logging Models

First, we need to train ML models and log them to MLflow.

For demonstration purposes, we train and log 2 XGBoost models with conflicting library versions. We run `train_xgboost_model.ipynb` after installing their required dependencies:

1. Set up a virtual environment with `pyenv`

    For example, set it up for `3.12.11`:
    ```sh
    pyenv install 3.12.11
    pyenv shell 3.12.11
    python -m venv .venv.py312/
    ```

    > Note that these versions need to match the Ray Cluster, down to the patch number

2. The 1st model uses Xgboost 1.X on Python 3.12, with its PIP requirements in `examples/requirements.iris_classifier-py312-xgboost1.txt`

    ```sh
    source .venv.py312/bin/activate
    pip install -r examples/requirements.iris_classifier-py312-xgboost1.txt
    # Now run `train_xgboost_model.ipynb` with this Python kernel
    ```

3. The 2nd model uses Xgboost 2.X on Python 3.12, with its PIP requirements in `examples/requirements.iris_classifier-py312-xgboost2.txt`

    ```sh
    source .venv.py312/bin/activate
    pip install -r examples/requirements.iris_classifier-py312-xgboost2.txt
    # Now run `train_xgboost_model.ipynb` with this Python kernel
    ```

> MLflow automatically [infers the required dependencies](https://mlflow.org/docs/latest/ml/model/dependencies) of the trained model when the `log_model(model)` method is called. 

![](/examples/mlflow_experiments.png)

## Registering and Tagging Models

**Registering Models**

Subsequently, on MLflow, for each model that is to be deployed, [register each model](https://mlflow.org/docs/latest/ml/model-registry) with a `.staging` suffix in their name, and *promote* a trained model version under the registered model.

For example, register a model each for `iris_classifier-py312-xgboost1.staging` and `iris_classifier-py312-xgboost2.staging` based on the trained models in the previous step.

![](/examples/mlflow_registered_models.png)

**Tagging Models**

For each registered model to be deployed, add the following tags on MLflow:

| **Tag** | **Required** | **Example** | **Description** |
|:--------|:------------:|:------------|:----------------|
| `ray.name` | Yes | `iris_classifier-py312-xgboost1` | Name of the deployment |
| `ray.ray_actor_options.num_cpus` | Yes | `0.5` | Number of CPUs per replica |
| `ray.ray_actor_options.memory` | Yes | `1` | Memory in GB per replica |
| `ray.ray_actor_options.runtime_env.env_vars` | No | `{"ENV_VAR": "value"}` | Environment variables for deployment |
| `ray.autoscaling_config.min_replicas` | No | `1` | Min. no. of replicas for the deployment.<br/>Default value: 1 |
| `ray.autoscaling_config.max_replicas` | No | `100` | Max. no. of replicas for the deployment.<br/>Default value: 100 |
| `ray.user_config.max_batch_size` | No | `8` | Max batch size for [Ray Serve dynamic request batching](https://docs.ray.io/en/latest/serve/advanced-guides/dyn-req-batch.html).<br/>Request batching is disabled unless this is specified. |
| `ray.autoscaling_config.target_ongoing_requests` | No | `2` | Average no. of ongoing requests per replica that the [Ray Serve autoscaler](https://docs.ray.io/en/latest/serve/autoscaling-guide.html) tries to ensure.<br/>Default value: 2 if batching is disabled, otherwise max batch size |

These tags configure their corresponding [model deployments when deployed on Ray Serve](https://docs.ray.io/en/latest/serve/configure-serve-deployment.html).

## Deploying Models

Next, depending on whether where Ray Serve is deployed:
- [Deploying models on Kubernetes](/docs/2_deploying-models-on-kubernetes.md)
- [Deploying models on VMs](/docs/3_deploying-models-on-vms.md)
