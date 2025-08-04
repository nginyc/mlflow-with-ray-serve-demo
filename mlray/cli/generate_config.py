from argparse import ArgumentParser
import yaml

from mlray.config import read_config, Config
from mlray.mlflow import DeployableModel, InvalidMlflowModelError, MlRayMlFlowClient

def configure_paser(arg_parser: ArgumentParser):
    arg_parser.add_argument(
        "config_path",
        type=str,
        default="config.yml",
        help="Path to the MLRay config.yml file",
    )
    arg_parser.add_argument(
        "--kuberay_config_path",
        type=str,
        nargs='?',
        default=None,
        help="Kubernetes custom resource YAML to update, if deploying on Kubernetes via KubeRay. This or `serve_config_path` must be provided.",
    )
    arg_parser.add_argument(
        "--serve_config_path",
        type=str,
        nargs='?',
        default=None,
        help="File path to generate the Ray Serve config, if deploying directly to a Ray Cluster. This or `kuberay_config_path` must be provided.",
    )
    arg_parser.set_defaults(main=main)


class LiteralString(str):
    pass

def literal_representer(dumper, data):
    """
    Tells the PyYAML dumper to use the literal block style for this string.
    """
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralString, literal_representer)

def main(
    config_path: str,
    kuberay_config_path: str | None = None,
    serve_config_path: str | None = None,
):
    """
    Deploy models to Ray Serve based on the MLflow model registry.
    """
    if not kuberay_config_path and not serve_config_path:
        raise ValueError("Either `kuberay_config_path` or `serve_config_path` must be provided.")

    config = read_config(config_path)
    client = MlRayMlFlowClient()
    try:
        deployable_models = list(client.fetch_deployable_models())
    except InvalidMlflowModelError as e:
        raise ValueError(f"Error fetching deployable models: {e}") from e
    
    ray_serve_config = build_ray_serve_config(config, deployable_models)
    if kuberay_config_path:
        update_kuberay_config(kuberay_config_path, ray_serve_config)
    elif serve_config_path:
        save_ray_serve_config(serve_config_path, ray_serve_config)

def update_kuberay_config(
    kuberay_config_path: str,
    serve_config: dict,
):
    """
    Update the Kubernetes custom resource YAML with the Ray Serve configuration.
    """
    # Load the existing config
    with open(kuberay_config_path, 'r') as f:
        kuberay_config = yaml.safe_load(f)
    
    serve_config_yaml = yaml.safe_dump(serve_config, sort_keys=False)
    
    # Update the spec.serveConfigV2 field
    if 'spec' not in kuberay_config:
        kuberay_config['spec'] = {}
    kuberay_config['spec']['serveConfigV2'] = LiteralString(serve_config_yaml)
    
    # Write the updated config back to the file
    with open(kuberay_config_path, 'w') as f:
        yaml.dump(kuberay_config, f, default_flow_style=False)

    print(f"KubeRay config updated at {kuberay_config_path}")
    print(f"Run `kubectl apply -f {kuberay_config_path}` to deploy the RayService.")

def save_ray_serve_config(
    serve_config_path: str,
    config: dict,
):
    """
    Save the Ray Serve configuration to a YAML file.
    """
    with open(serve_config_path, 'w') as f:
        yaml.safe_dump(config, f)

    print(f"Ray Serve config saved to {serve_config_path}")
    print(f"Run `RAY_DASHBOARD_ADDRESS=... serve deploy {serve_config_path}` to deploy the config.")

def build_ray_serve_config(
    config: Config,
    deployable_models: list[DeployableModel]
):
    print(f"Generating Ray Serve config with {len(deployable_models)} deployable model(s)...")
    applications = []
    for model in deployable_models:
        app = build_ray_serve_config_application(config, model)
        applications.append(app)

    return {
        "applications": applications,
        "grpc_options": {
            "grpc_servicer_functions": [],
            "port": 9000
        },
        "http_options": {
            "host": "0.0.0.0",
            "port": 8000
        },
        "logging_config": {
            "additional_log_standard_attrs": [],
            "enable_access_log": True,
            "encoding": "TEXT",
            "log_level": "INFO",
            "logs_dir": None
        },
        "proxy_location": "EveryNode",
    }

def build_ray_serve_config_application(
    config: Config,
    model: DeployableModel,
) -> dict:
    max_batch_size = model.max_batch_size if model.max_batch_size else 1
    should_batch = max_batch_size > 1

    target_ongoing_requests = max_batch_size if should_batch else 2
    max_ongoing_requests = max(round(target_ongoing_requests * 1.2), target_ongoing_requests + 1)

    min_replicas = 1
    if model.min_replicas is not None:
        if model.min_replicas < 0:
            raise ValueError(f"min_replicas must be at least 0, got {model.min_replicas}")
        min_replicas = model.min_replicas
    
    max_replicas = 100
    if model.max_replicas is not None:
        if model.max_replicas < 1:
            raise ValueError(f"max_replicas must be at least 1, got {model.max_replicas}")
        max_replicas = model.max_replicas

    # This points to `mlray/app.py` or `mlray/batching_app.py.py` 
    import_path = f"mlray.batching_app:app" if should_batch else f"mlray.app:app"

    user_config = {}
    if should_batch:
        user_config['max_batch_size'] = max_batch_size
    
    app = {
        "name": model.name,
        "route_prefix": f"/{model.name}",
        "import_path": import_path,
         "runtime_env": {
            "working_dir": config.working_dir,
            "env_vars": {
                'MLFLOW_TRACKING_URI': config.mlflow_tracking_uri,
                'MODEL_URI': model.model_uri,
                **config.env_vars,
                **model.env_vars,
            },
            "pip": model.pip_requirements,
        },
        "deployments": [
            {
                "name": "App", # This points to `App` class
                "max_ongoing_requests": max_ongoing_requests,
                "autoscaling_config": {
                    "target_ongoing_requests": target_ongoing_requests,
                    "min_replicas": min_replicas,
                    "max_replicas": max_replicas,
                },
                "ray_actor_options": {
                    "num_cpus": model.num_cpus,
                    "memory": model.memory
                },
                "user_config": user_config if user_config else None,
            }
        ]
    }

    return app

