import os
import mlflow
import dotenv
import ray
import ray.serve
from starlette.requests import Request

dotenv.load_dotenv()

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:8080")
MODEL_URI = os.getenv("MODEL_URI", "")

@ray.serve.deployment
class App:
    def __init__(self):
        self.model = mlflow.pyfunc.load_model(MODEL_URI)

    async def __call__(self, http_request: Request) -> str:
        req = await http_request.json()
        return self.model.predict(req["data"]).tolist()

app = App.bind() # pylint: disable=E1101
