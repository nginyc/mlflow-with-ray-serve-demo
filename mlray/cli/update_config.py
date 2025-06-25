import yaml
import os
from argparse import ArgumentParser

from mlray.mlflow import DeployableModel, InvalidMlflowModelError, MlRayMlFlowClient

def configure_paser(arg_parser: ArgumentParser):
    arg_parser.add_argument(
        "python_version_config_pairs",
        type=str,
        nargs="+",
        help="Pairs of python_version:config_path (e.g. 3.12.11:examples/config-py312.yml)",
    )
    arg_parser.add_argument(
        "--mlflow-tracking-uri",
        type=str,
        default=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:8080"),
        help="MLflow tracking URI (default: env MLFLOW_TRACKING_URI or http://localhost:8080)",
    )
    arg_parser.add_argument(
        "--runtime-mlflow-tracking-uri",
        type=str,
        default=os.environ.get("RUNTIME_MLFLOW_TRACKING_URI", "http://localhost:8080"),
        help="Runtime MLflow tracking URI (default: env RUNTIME_MLFLOW_TRACKING_URI or http://localhost:8080)",
    )
    arg_parser.set_defaults(main=main)


def main(
    python_version_config_pairs: list, mlflow_tracking_uri: str, runtime_mlflow_tracking_uri: str
):
    """
    Update the Ray Serve config.yml files for multiple Python versions based on the ML model registry.
    """
    python_version_to_config_path = {}
    for pair in python_version_config_pairs:
        if ":" not in pair:
            raise ValueError(f"Invalid pair format: {pair}. Expected format is python_version:config_path.")

        python_version, config_path = pair.split(":", 1)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file {config_path} does not exist.")
        
        python_version_to_config_path[python_version] = config_path

    client = MlRayMlFlowClient(mlflow_tracking_uri)
    try:
        deployable_models = list(client.fetch_deployable_models())
    except InvalidMlflowModelError as e:
        raise ValueError(f"Error fetching deployable models: {e}") from e
    
    non_deployable_models = [model for model in deployable_models if model.python_version not in python_version_to_config_path]
    if non_deployable_models:
        raise ValueError(
            f"Some models are not deployable with the provided Python versions: {', '.join(model.name for model in non_deployable_models)}."
        )    
    
    for python_version, config_path in python_version_to_config_path.items():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if config is None:
            raise ValueError(f"Config file {config_path} is empty or invalid.")

        apps = format_applications_for_config(
            deployable_models,
            runtime_mlflow_tracking_uri,
            python_version
        )
        config['applications'] = apps

        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f)

        print(f"Updated config file at {config_path} for Python {python_version}")

def format_applications_for_config(
    deployable_models: list[DeployableModel],
    runtime_mlflow_tracking_uri: str,
    python_version: str,
) -> list[dict]:
    app_deployable_models = [
        model for model in deployable_models if model.python_version == python_version
    ]

    if not app_deployable_models:
        return []
    
    return [
        format_application_for_config(model, runtime_mlflow_tracking_uri)
        for model in app_deployable_models
    ]
    

def format_application_for_config(
    model: DeployableModel,
    runtime_mlflow_tracking_uri: str
) -> dict:
    app = {
        "name": model.name,
        "route_prefix": f"/{model.name}",
        "import_path": "mlray.app:app", # This points to `mlray/app.py`
         "runtime_env": {
            "env_vars": {
                **model.env_vars,
                'MLFLOW_TRACKING_URI': runtime_mlflow_tracking_uri,
                'MODEL_URI': model.model_uri,
            },
            "pip": model.pip_requirements,
        },
        "deployments": [
            {
                "name": "App", # This points to `App` class in `mlray/app.py`
                "num_replicas": model.num_replicas,
                "ray_actor_options": {
                    "num_cpus": model.num_cpus,
                    "memory": model.memory
                }
            }
        ]
    }
    return app
