import os
import mlflow
import ray
import ray.serve
from starlette.requests import Request

@ray.serve.deployment
class App:
    def __init__(self):
        self._model_uri = os.environ["MODEL_URI"]
        self._model = mlflow.pyfunc.load_model(self._model_uri)

    async def __call__(self, http_request: Request) -> str:
        req = await http_request.json()
        return self._model.predict(req["data"]).tolist()

app = App.bind() # type: ignore # 
