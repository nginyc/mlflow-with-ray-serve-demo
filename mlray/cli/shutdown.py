from argparse import ArgumentParser
import os
import subprocess

from mlray.config import read_config, RayClusterConfig

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
    Shutdown Ray Serve on the specified cluster.
    """
    config = read_config(config_path)
    mlray_config = config.mlray
    cluster_config = next((c for c in config.ray_clusters if c.name == cluster_name), None)
    if not cluster_config:
        raise ValueError(f"No cluster config with name found: {cluster_name}.")

    shutdown(cluster_config)


def shutdown(
    cluster_config: RayClusterConfig
):
    dashboard_address = cluster_config.dashboard_address
    print(f"Shutting down Ray Serve on cluster at {dashboard_address}...")

    result = subprocess.run(
        ['serve', 'shutdown', '-y'],
        env={**os.environ, 'RAY_DASHBOARD_ADDRESS': dashboard_address},
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to shut down Ray Serve")
    else:
        print(f"Ray Serve shut down successfully")   
