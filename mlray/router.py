import random
from typing import List, Optional
from ray.serve.request_router import PendingRequest, RequestRouter, RunningReplica # type: ignore

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
        
        if not available_replicas:
            return []

        chosen_replicas = random.sample(
            list(available_replicas),
            k=min(2, len(available_replicas)),
        )

        return [chosen_replicas]

