import asyncio
import os
from typing import Any
import mlflow
import ray
import ray.serve
from starlette.requests import Request

@ray.serve.deployment
class App:
    def __init__(self):
        self._model_uri = os.environ["MODEL_URI"]
        self._model = mlflow.pyfunc.load_model(self._model_uri)

    def reconfigure(self, config: dict[str, Any]):
        self.__call__.set_max_batch_size(config['max_batch_size']) # type: ignore

    @ray.serve.batch
    async def __call__(self, requests: list[Request]):
        # Gather JSON data from all requests
        request_jsons = await asyncio.gather(*(request.json() for request in requests))
        data_list = [req["data"] for req in request_jsons]

        # Flatten data across all requests for prediction
        X = [x for data in data_list for x in data]

        # Predict using the model for all requests at once
        y = self._model.predict(X).tolist()

        # Return predictions in the same order as requests
        resps = []
        start_idx = 0
        for i in range(len(data_list)):
            end_idx = start_idx + len(data_list[i])
            resps.append(y[start_idx:end_idx])
            start_idx = end_idx

        return resps


app = App.bind() # type: ignore # 
