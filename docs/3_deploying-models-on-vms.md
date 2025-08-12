# Deploying Models on VMs 

To deploy models on VMs without Kubernetes, we need to first set up a *Ray Cluster*, then deploy models from MLflow with Ray Serve onto the Ray Cluster.

> However, note that without Kubernetes, this Ray Cluster has limited [fault tolerance features](https://docs.ray.io/en/latest/serve/production-guide/fault-tolerance.html).

Depending on whether you have a single machine or multiple VMs, you can follow either:
1. [Setting up Ray Cluster on a single machine with Podman](#setting-up-ray-cluster-on-a-single-machine-using-podman)
2. [Setting up Ray Cluster on multiple VMs](#setting-up-ray-cluster-on-multiple-vms)

Then, following [Deploying Models on Ray Cluster with Ray Serve](#deploying-models-on-ray-cluster-with-ray-serve)

## Setting up Ray Cluster on a single machine using Podman

For development & testing, you can emulate multiple Linux VM(s) on a single machine with [Podman](https://podman.io/) instead.

1. Build a Docker image for the Python version e.g.:
    ```sh
    podman build -f docker/ray-serve-py312.Dockerfile -t ray-serve-py312 .
    ```

2. Run a Ray head node for the Python version e.g.: 

    ```sh
    podman network create mlray-net
    podman run --name ray-head-py312 --network mlray-net --cpus=2 --memory=4g -p 8265:8265 -p 6379:6379 -p 10001:10001 -p 8000:8000 -d ray-serve-py312 \
        bash -c "ray start --head --num-cpus=2 --memory=4096 --port=6379 --dashboard-host=0.0.0.0 && tail -f /dev/null"
    ```

    With the above example, you can visit the respective Ray dashboards on your browser with http://localhost:8265 and http://localhost:8266.

3. If desired, run a Ray worker node for the Python version as well e.g.:

    ```sh
    podman run --name ray-worker-py312 --network mlray-net --cpus=2 --memory=4g -d ray-serve-py312 bash -c "ray start --address=ray-head-py312:6379 --num-cpus=2 --memory=4096 && tail -f /dev/null"
    ```

The MLflow instance needs to be network-accessible by the Ray Cluster nodes. You run a MLflow server using Podman in the same network like:

```sh
podman run -d --name mlflow-server --network mlray-net -p 8080:8080 ghcr.io/mlflow/mlflow \
mlflow server --host 0.0.0.0 --port 8080
```

## Setting up Ray Cluster on multiple VMs

> This was tested on Ubuntu 24.04 (LTS) VMs

1. On each VM, install [pyenv](https://github.com/pyenv/pyenv), and ensure shims are set up and shell function is installed such that `pyenv shell` works:

    ```sh
    curl -fsSL https://pyenv.run | bash
    eval "$(pyenv init -)"
    ```

2. Clone this project's code on each VM


3. On each VM, install the same Python version and activate it:

    ```sh
    pyenv shell 3.12.11
    ```
    
4. On each VM, install Ray Serve and MLflow using PIP, and ensure the version of Ray is the same across all VMs:
    
    ```sh
    pip install -U "ray[serve]"
    pip install -U mlflow boto3
    ray --version
    ```

5. On a single VM designated to be the Ray head node for the Ray Cluster, [start a Ray head node](https://docs.ray.io/en/latest/cluster/vms/user-guides/launching-clusters/on-premises.html#start-the-head-node) via the [Ray Cluster Management CLI](https://docs.ray.io/en/latest/cluster/cli.html#ray-start)

    ```sh
    ray start --head --port=6379 --dashboard-host=0.0.0.0 
    ```

6. For every other extra VM designated to Ray worker nodes for the Ray Cluster, [start a Ray worker node](https://docs.ray.io/en/latest/cluster/vms/user-guides/launching-clusters/on-premises.html#start-worker-nodes) via the [Ray Cluster Management CLI](https://docs.ray.io/en/latest/cluster/cli.html#ray-start)

    ```sh
    ray start --address=<head-node-address>:6379
    ```

## Deploying Models on Ray Cluster with Ray Serve

First, run the `mlray generate-config` command to generate the [Ray Serve config](https://docs.ray.io/en/latest/serve/production-guide/config.html) file based on the tagged models on MLflow:

```sh
mlray generate-config config.yml --serve_config_path py312.serve_config.yml
```

> For each model, this command reads from `python_env.yml` and `requirements.txt` in the [MLflow model artifact](https://mlflow.org/docs/latest/ml/model/dependencies) to determine its required Python version and PIP dependencies for Ray Serve. It also reads from each model's tags to configure the Ray Serve deployment.

You can preview the generated Ray Service config at `py312.serve_config.yml`

Then, use Ray Serve's `serve deploy` command to deploy directly to the Ray Cluster that was set up:

```sh
RAY_DASHBOARD_ADDRESS=http://localhost:8265 serve deploy py312.serve_config.yml
```

Check the Ray dashboard to check on the status of the deployments.

![](/examples/ray_serve_deployments.png)

You can verify that the model serving endpoints are working with e.g. REST requests like those in `examples/xxx.request.http`

![](/examples/model_http_request.png)

## Setting up Prometheus and Grafana

To enable metrics visualization, you can follow ([Ray Serve's instructions](https://docs.ray.io/en/latest/cluster/metrics.html)) to run Prometheus and Grafana. Here are some example steps on how to get that working.

1. Run Prometheus:

    ```sh
    ray metrics launch-prometheus &
    rm -rf prometheus-* # Remove temporary files
    ```

2. Download [Grafana and set it up](https://grafana.com/docs/grafana/latest/setup-grafana/):

    ```sh
    GF_SERVER_HTTP_ADDR=localhost GF_SERVER_HTTP_PORT=3000 ./bin/grafana server --homepath ./grafana --config /tmp/ray/session_latest/metrics/grafana/grafana.ini web
    ```

    or alternatively, using podman:

    ```sh
    podman run -d --name grafana --network host \
        -e GF_SERVER_HTTP_PORT=3000 \ 
        -v /tmp/ray:/tmp/ray:ro \
        -v /tmp/ray/session_latest/metrics/grafana/grafana.ini:/etc/grafana/grafana.ini:ro \
        -v /tmp/ray/session_latest/metrics/grafana/provisioning:/etc/grafana/provisioning:ro \
        docker.io/grafana/grafana
    ```


3. Lastly, start Ray with metrics visualization:

    ```sh
    RAY_GRAFANA_HOST=http://localhost:3000 RAY_GRAFANA_IFRAME_HOST=http://localhost:3000 RAY_PROMETHEUS_HOST=http://localhost:9090 ray start --head --dashboard-host=0.0.0.0 
    ```

...and visit the Grafana at http://localhost:3000