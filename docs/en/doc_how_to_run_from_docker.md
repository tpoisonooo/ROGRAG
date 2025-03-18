# Running with Docker

We have configured the CUDA 12.4 Docker image required for running HuixiangDou2, and ultimately, the Swagger Server API service can be launched with a single command.

[Download link from Baidu Cloud](https://pan.baidu.com/s/1H1u5XYxh35xh2G8ZYRf-ZQ?pwd=76gs)

The image already includes:
- Qwen2.5-7B-Instruct model, BCE embedding/reranker models
- VLLM environment
- TuGraph runtime environment
- HuixiangDou2 source code

## I. Environment Requirements

- Total GPU memory of 24GB (either a single 24GB card or two 16GB cards)
- Check the GPU driver version to ensure it supports CUDA 12.4
- Install NVIDIA Docker to support the `docker --gpus all` command

## II. Using Docker
Download the image and import it into Docker:
```text
sudo docker load -i hxd-public.tar
sudo docker images
..
REPOSITORY                        TAG       IMAGE ID       CREATED        SIZE
hxd-public                        latest    ce59f3a3763f   47 hours ago   52.4GB
```

Enter the container corresponding to the hxd-public image:
```text
# 8888 is the port to be listened to by the service; 7070, 7687, and 9090 are TuGraph ports, which can be omitted.
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -it hxd-public /bin/bash

# Here are the downloaded models, code, and TuGraph.
ls /root

..
Qwen2.5-7B-Instruct
bce-embedding-base_v1 
bce-reranker-base_v1
HuixiangDou
run.sh
```

Start TuGraph and VLLM (the commands are in run.sh):
```bash
/usr/local/bin/lgraph_server -d start -c /root/lgraph.json --log_dir ""
nohup vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1 &
```

## III. Building the Knowledge Base
There are two documents under `HuixiangDou/tests/data`. Copy them to `repodir` and build the knowledge base after VLLM is started.
```bash
cd HuixiangDou
cp -rf tests/data repodir
python3 -m huixiangdou.pipeline.store
```
Open the browser on port 17070, log in with the account `admin` and password `73@TuGraph`, and you will see the corresponding graph (the image code has an extra `pdb.set_trace()`, which you can remove yourself).

![Graph](https://github.com/user-attachments/assets/873fedfe-c2fe-47f2-bbb1-723c1c21c463 "Graph")

## IV. Retrieval

### Command Line Method
Running `main.py` allows you to execute query examples in the command line:
```bash
python3 -m huixiangdou.main

+------------------+---------+---------------------------------+---------------+
|      Query       |  State  |            Response             |  References   |
+==================+=========+=================================+===============+
| What is in the Hundred-Grass Garden? | success | The Hundred-Grass Garden contains various plants and insects, including lush vegetable patches, tall soapberry trees, purple mulberries, raspberry plants that look like coral beads, cicadas, hornets, skylarks, crickets, centipedes, and blister beetles. Additionally, there are entwined Polygonum multiflorum vines and lotus vines, as well as stone wells and broken bricks as natural features. | baicaoyuan.md |
+------------------+---------+---------------------------------+---------------+
```

### Gradio UI Integration
```bash
python3 -m huixiangdou.gradio_ui --port 8888
```
Then open the browser on port 8888 for a streaming response.

![Gradio UI](https://github.com/user-attachments/assets/b7b7cb90-4a85-4ffc-9de0-52670dd9159e "Gradio UI")

### Swagger API
It also supports [Swagger API documentation](../swagger.json).

Start the server:
```bash
python3 -m huixiangdou.server --port 8888
```

Open the browser on port 8888 to view SwaggerUI. Execute the client test:
```bash
python3 huixiangdou/client.py
```

## V. One-Click Startup

Commit the image with the built knowledge base:
```text
sudo docker commit [Container ID] [Image Name, such as hxd-public]
```

Then you can start all services with one command:
```text
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -it seed-service /bin/bash -ic "/root/run.sh"
```
