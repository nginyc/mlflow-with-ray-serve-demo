from argparse import ArgumentParser
import os
import subprocess
import yaml

from mlray.utils import get_python_major_version
from mlray.config import MlRayConfig, read_config, RayClusterConfig
from mlray.mlflow import DeployableModel, InvalidMlflowModelError, MlRayMlFlowClient

def configure_paser(arg_parser: ArgumentParser):
    arg_parser.add_argument(
        "config_path",
        type=str,
        default="config.yml",
        help="Path to the MLRay config.yml file",
    )
    arg_parser.add_argument(
        "cluster_name",
        type=str,
        help="Cluster name in the config.yml to deploy for",
    )
    arg_parser.set_defaults(main=main)


def main(
    config_path: str,
    cluster_name: str,
):
    """
    Deploy models to Ray Serve based on the MLflow model registry.
    """
    config = read_config(config_path)
    mlray_config = config.mlray
    cluster_config = next((c for c in config.ray_clusters if c.name == cluster_name), None)
    if not cluster_config:
        raise ValueError(f"No cluster config with name found: {cluster_name}.")

    client = MlRayMlFlowClient()
    try:
        deployable_models = list(client.fetch_deployable_models())
    except InvalidMlflowModelError as e:
        raise ValueError(f"Error fetching deployable models: {e}") from e
    
    cluster_deployable_models = [
        model for model in deployable_models 
        if get_python_major_version(model.python_version) == cluster_config.python_version
    ]
    ray_serve_config = build_ray_serve_config(cluster_config, cluster_deployable_models)
    ray_serve_config_path = save_ray_serve_config(mlray_config, cluster_config, ray_serve_config)
    deploy_ray_serve_config(cluster_config, ray_serve_config_path)


def deploy_ray_serve_config(
    cluster_config: RayClusterConfig,
    config_path: str
):
    dashboard_address = cluster_config.dashboard_address
    print(f"Deploying Ray Serve config to cluster at {dashboard_address}...")

    result = subprocess.run(
        ['serve', 'deploy', config_path],
        env={**os.environ, 'RAY_DASHBOARD_ADDRESS': dashboard_address},
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to deploy Ray Serve config")
    else:
        print(f"Ray Serve config deployed successfully")   

def save_ray_serve_config(
    mlray_config: MlRayConfig,
    cluster_config: RayClusterConfig,
    config: dict,
) -> str:
    """
    Save the Ray Serve configuration to a YAML file.
    """
    cluster_name = cluster_config.name
    config_file_name = f"{cluster_name}.ray_serve.config.yml"
    
    os.makedirs(mlray_config.working_dir, exist_ok=True)
    config_path = os.path.join(mlray_config.working_dir, config_file_name)
    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f)

    print(f"Ray Serve config saved to {config_path}")

    return config_path

def build_ray_serve_config(
    cluster_config: RayClusterConfig,
    deployable_models: list[DeployableModel]
):
    print(f"Building Ray Serve config with {len(deployable_models)} deployable model(s)...")
    applications = []
    for model in deployable_models:
        app = build_ray_serve_config_application(cluster_config, model)
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
    cluster_config: RayClusterConfig,
    model: DeployableModel,
) -> dict:
    max_batch_size = model.max_batch_size if model.max_batch_size else 1
    should_batch = max_batch_size > 1

    target_ongoing_requests = max_batch_size if should_batch else 2
    max_ongoing_requests = max(round(target_ongoing_requests * 1.2), target_ongoing_requests + 1)
    min_replicas = model.min_replicas if model.min_replicas else 1
    max_replicas = model.max_replicas if model.max_replicas else 100

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
            "env_vars": {
                'MLFLOW_TRACKING_URI': cluster_config.mlflow_tracking_uri,
                'MODEL_URI': model.model_uri,
                **model.env_vars,
                **cluster_config.env_vars,
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
