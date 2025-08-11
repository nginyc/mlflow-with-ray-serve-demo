from mlflow import MlflowException
import yaml
from typing import Iterator, Optional, cast
import mlflow.artifacts
from pydantic import BaseModel, Field, PositiveFloat, PositiveInt, ValidationError, NonNegativeInt
from mlflow.entities.model_registry import ModelVersion

MLFLOW_MODEL_NAME_SUFFIX = ".staging"

class _MlflowModelRequirements(BaseModel):
    python_version: str = Field(...)
    pip_requirements: list[str] = Field(...)

class _MlflowModelTags(BaseModel):
    name: str = Field(..., validation_alias="ray.name", description="Name of Ray Serve application")
    num_cpus: PositiveFloat = Field(..., validation_alias="ray.ray_actor_options.num_cpus", description="Number of CPUs per replica")
    memory: PositiveFloat = Field(..., validation_alias="ray.ray_actor_options.memory", description="Memory in GB per replica")
    env_vars: dict = Field({}, validation_alias="ray.ray_actor_options.runtime_env.env_vars", description="Environment variables for the model")
    min_replicas: Optional[NonNegativeInt] = Field(default=None, validation_alias="ray.autoscaling_config.min_replicas", description="Min. no. of replicas for the deployment")
    max_replicas: Optional[NonNegativeInt] = Field(default=None, validation_alias="ray.autoscaling_config.max_replicas", description="Max. no. of replicas for the deployment")
    target_ongoing_requests: Optional[PositiveInt] = Field(default=None, validation_alias="ray.autoscaling_config.target_ongoing_requests", description="Average no. of ongoing requests per replica that the Ray Serve autoscaler tries to ensure")
    max_batch_size: Optional[PositiveInt] = Field(default=None, validation_alias="ray.user_config.max_batch_size", description="Max batch size for Ray Serve dynamic request batching")

class DeployableModel(_MlflowModelRequirements):
    model_uri: str
    name: str 
    num_cpus: PositiveFloat
    memory: PositiveFloat 
    env_vars: dict 
    min_replicas: Optional[NonNegativeInt]
    max_replicas: Optional[NonNegativeInt]
    target_ongoing_requests: Optional[PositiveInt]
    max_batch_size: Optional[PositiveInt]

class InvalidMlflowModelError(Exception):
    pass

class MlRayMlFlowClient:
    def fetch_deployable_models(self) -> Iterator[DeployableModel]:
        print(f"Fetching deployable models from MLflow registry at {mlflow.get_tracking_uri()}...")

        mlflow_models = mlflow.search_registered_models(filter_string=f"name LIKE '%{MLFLOW_MODEL_NAME_SUFFIX}'")

        for mlflow_model in mlflow_models:
            name = mlflow_model.name
            tags = mlflow_model.tags

            try:
                versions = mlflow_model.latest_versions
                if not versions:
                    raise ValueError(f"No versions available.")
                
                if len(versions) > 1:
                    raise ValueError(f"Multiple versions available. Only one version should be available.")
                
                version = cast(ModelVersion, versions[0])
                model_uri = version.source

                if not model_uri:
                    raise ValueError(f"No model URI available.")

                tags = self._parse_tags(tags)
                reqs = self._get_model_requirements(model_uri)
                
                yield DeployableModel(
                    model_uri=model_uri, **tags.model_dump(), **reqs.model_dump()
                )

            except ValueError as e:
                raise InvalidMlflowModelError(f'MLflow model "{name}" is invalid for deployment: {e}')
            
    def _parse_tags(self, tags: dict) -> _MlflowModelTags:
        try:
            return _MlflowModelTags(**tags)
        except ValidationError as e:
            raise ValueError(f"One or more tags are invalid: {e}")

    def _get_model_requirements(self, model_uri: str) -> _MlflowModelRequirements:
        try:
            python_env_yaml = mlflow.artifacts.load_text(model_uri + '/python_env.yaml')
        except MlflowException as e:
            raise ValueError(f"Failed to load python_env.yaml: {e}")
        
        requirements = cast(dict, yaml.safe_load(python_env_yaml))
        python_version = requirements.get('python')

        if not python_version:
            raise ValueError("Python version not found in python_env.yaml")
        
        try:
            requirements_txt = mlflow.artifacts.load_text(model_uri + '/requirements.txt')
        except MlflowException as e:
            raise ValueError(f"Failed to load requirements.txt: {e}")
        
        pip_requirements = requirements_txt.splitlines() if requirements_txt else []

        '''
        As a safeguard against the error "numpy.core.multiarray failed to import", 
            we force install pyarrow == 19.0.1 if pyarrow is not already in the requirements.
        Refer to the related open issue at https://github.com/ray-project/ray/issues/48559
        '''
        has_pyarrow = any(req.startswith('pyarrow') for req in pip_requirements)
        if not has_pyarrow:
            pip_requirements.append('pyarrow==19.0.1')

        return _MlflowModelRequirements(
            python_version=python_version, 
            pip_requirements=pip_requirements
        )
