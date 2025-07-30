from pydantic import BaseModel
import yaml

class Config(BaseModel):
    working_dir: str
    mlflow_tracking_uri: str
    env_vars: dict[str, str] = {}

def read_config(config_path: str) -> Config:
    '''
    Reads the configuration file and returns a Config object.
    '''
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)
