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

    async def __call__(self, request: Request):
        request_json = await request.json()
        X = request_json["data"]
        y = self._model.predict(X).tolist()
        return y

app = App.bind()  # type: ignore
