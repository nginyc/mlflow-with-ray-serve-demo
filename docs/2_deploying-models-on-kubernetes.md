# Deploying Models on Kubernetes

With a Kubernetes cluster, Ray Serve has enhanced high availability, such as [worker/head node recovery](https://docs.ray.io/en/latest/serve/production-guide/fault-tolerance.html).

To deploy models on Kubernetes, you would need to:
1. Get access to or set up a Kubernetes cluster
2. Install the [KubeRay operator](https://docs.ray.io/en/latest/cluster/kubernetes/getting-started.html) (to get the `RayService` custom resource definition on Kubernetes)
3. Simply deploy a `RayService` custom resource on the Kubernetes cluster with the right Ray Serve config. This custom resource would in turn creates the right Kubernetes pods and services for the Ray Cluster head, workers, Ray Serve, etc

You can also refer to Ray's documentation [*Deploy on Kubernetes*](https://docs.ray.io/en/latest/serve/production-guide/kubernetes.html).

## Setting up a Kubernetes cluster

If you don't have a ready Kuberneters cluster, you can consider using [kind](https://kind.sigs.k8s.io/) or [k3s](https://docs.k3s.io/).

## Installing the KubeRay operator

Install the [KubeRay operator](https://github.com/ray-project/kuberay), which offers 3 custom resource definitions (CRDs) for Kubernetes: `RayCluster`, `RayJob` and `RayService`. For serving models, we would rely on the `RayService` CRD. 

To install KubeRay, you can follow [the official documentation](https://docs.ray.io/en/latest/cluster/kubernetes/getting-started/kuberay-operator-installation.html) or follow these instructions:

1. Install [helm](https://helm.sh/docs/intro/install/) for the Kubernetes cluster

2. Run the following:
    ```sh
    helm repo add kuberay https://ray-project.github.io/kuberay-helm/
    helm repo update
    # Install both CRDs and KubeRay operator v1.4.0.
    helm install kuberay-operator kuberay/kuberay-operator --version 1.4.0
    ```

3. Verify that operator is running in the namespace `default`:
    ```sh
    kubectl get pods
    ```
    ```sh
    NAME                                READY   STATUS    RESTARTS   AGE
    kuberay-operator-6bc45dd644-gwtqv   1/1     Running   0          24s
    ```

## Deploying Models on Kubernetes with RayService 

First, run the `mlray generate-config` command to update a given Kubernetes YAML with the Ray Serve config based on the tagged models on MLflow. An example Kubernetes YAML is provided at `examples/rayservice-py312.kuberay.yml` - be sure to tweak it first based on your requirements:

```sh
mlray generate-config config.yml --kuberay_config_path=examples/rayservice-py312.kuberay.yml
```

> For each model, this command reads from `python_env.yml` and `requirements.txt` in the [MLflow model artifact](https://mlflow.org/docs/latest/ml/model/dependencies) to determine its required Python version and PIP dependencies for Ray Serve. It also reads from each model's tags to configure the Ray Serve deployment.

Then, simply apply this Kubernetes YAML to the Kubernetes cluster:

```sh
kubectl apply -f examples/rayservice-py312.kuberay.yml
```

Check the Ray dashboard to check on the status of the deployments. 

![](/examples/ray_serve_deployments.png)

You can verify that the model serving endpoints are working with e.g. REST requests like those in `examples/xxx.request.http`

![](/examples/model_http_request.png)

To access the Ray Dashboard and Ray Serve endpoints from localhost, you may need to `kubectl port-forward` first:
```sh
kubectl port-forward service/rayservice-py312-head-svc 8265 &
kubectl port-forward service/rayservice-py312-serve-svc 8000 &
```

If [MLflow Authentication](https://mlflow.org/docs/latest/ml/auth/) is enabled, you need to uncomment the lines that provide `MLFLOW_TRACKING_USERNAME` and `MLFLOW_TRACKING_PASSWORD` to the Ray worker pods, and [create a `generic` Kubernetes secret](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#define-container-environment-variables-using-secret-data) like:

```sh
kubectl create secret generic mlflow-credentials --from-literal=username='XXXXX' --from-literal=password='XXXXX'
```

> To understand how to further customize the YAML, refer to [KubeRay's config samples](https://github.com/ray-project/kuberay/tree/master/ray-operator/config/samples) and [KubeRay's API reference](https://ray-project.github.io/kuberay/reference/api/).