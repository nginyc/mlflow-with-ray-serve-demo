from typing import Annotated
from pydantic import BaseModel, AfterValidator
import yaml

from mlray.utils import validate_python_major_version

class RayClusterConfig(BaseModel):
    name: str
    # This must be a major version of Python e.g. "3.9", "3.12"
    python_version: Annotated[str, AfterValidator(validate_python_major_version)]
    dashboard_address: str
    mlflow_tracking_uri: str

class MlRayConfig(BaseModel):
    working_dir: str

class Config(BaseModel):
    mlray: MlRayConfig
    ray_clusters: list[RayClusterConfig]

def read_config(config_path: str) -> Config:
    '''
    Reads the configuration file and returns a Config object.
    '''
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)
