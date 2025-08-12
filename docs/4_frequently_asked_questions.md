# Frequently Asked Questions (FAQ)

## How does auto-scaling work?

On Ray Serve, there are two forms of auto-scaling:
- **Replica-based**: When the current traffic for a model exceeds the no. of target ongoing requests per replica, the *Ray Serve Controller* would increase the no. of replicas for that model if Ray worker nodes have enough capacity. This is known as [Ray Serve Autoscaling](https://docs.ray.io/en/latest/serve/autoscaling-guide.html)

- **Worker-based**: When the current traffic across all models causes replica-based auto-scaling requirements to exceed Ray worker nodes' resource capacity, the *Ray Autoscaler* would increase the no. of Ray worker nodes. This is known as [Ray Cluster Autoscaling](https://docs.ray.io/en/latest/cluster/key-concepts.html#id6)

### Replica-based Autoscaling 

Replica-based auto-scaling can be configured at a model-level with the tags `ray.autoscaling_config.*`. Refer to Ray's documentation on [Advanced Ray Serve Autoscaling](https://docs.ray.io/en/latest/serve/advanced-guides/advanced-autoscaling.html#serve-advanced-autoscaling) for more details.

Ray Serve supports **scale-from-zero** models. These models have a minimum replica count of *zero*. They tend to be sparsely invoked and cold-start latencies are tolerable. When traffic arrives, the system would spin up the replicas to serve requests.

### Worker-based Autoscaling 

On the other hand, on Kubernetes, worker-based auto-scaling is configured with [KubeRay AutoScaling](https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/configuring-autoscaling.html) by setting the `enableInTreeAutoscaling: true`, as well as `minReplicas` and `maxReplicas` of the `workerGroupSpecs` in the Kubernetes YAML config.

## How to support multiple Python versions?

Each Ray Cluster assumes the same major Python version and Ray version across all its tasks/deployments (see [Ray's documentation on Environment Dependencies](https://docs.ray.io/en/latest/ray-core/handling-dependencies.html)). The Ray team recommends multiple Ray Clusters for each major Python version to be supported (see [Ray's discussion forum](https://discuss.ray.io/t/how-to-use-different-python-versions-in-the-same-cluster/15825)).