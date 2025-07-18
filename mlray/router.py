import random
from ray.serve.request_router import PendingRequest, RequestRouter, RunningReplica # type: ignore
from typing import List, Optional

class UniformRequestRouter(RequestRouter):
    '''
    A request router that chooses a random replica from the available replicas.
    Adapted from https://docs.ray.io/en/master/serve/advanced-guides/custom-request-router.html.
    '''

    async def choose_replicas(
        self,
        candidate_replicas: List[RunningReplica],
        pending_request: Optional[PendingRequest] = None,
    ) -> List[List[RunningReplica]]:
        available_replicas = self.select_available_replicas(candidate_replicas)
        index = random.randint(0, len(available_replicas) - 1)
        return [[candidate_replicas[index]]]
