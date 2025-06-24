import os
import mlflow
import ray
import ray.serve
from starlette.requests import Request

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:8080")
MODEL_URI = os.environ["MODEL_URI"]

@ray.serve.deployment
class App:
    def __init__(self):
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        self.model = mlflow.pyfunc.load_model(MODEL_URI)

    async def __call__(self, http_request: Request) -> str:
        req = await http_request.json()
        return self.model.predict(req["data"]).tolist()

app = App.bind() # type: ignore # 
