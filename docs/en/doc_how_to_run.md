# Running

During the knowledge graph construction phase, we organize raw documents into a structured graph form. As shown in the figure:

<img src="https://github.com/user-attachments/assets/b9872a7b-4b15-4f51-b361-7a5b0001134b" width=400>

During the retrieval phase, we first obtain subgraphs and corresponding chunks from the graph based on the Query, and then use the LLM to get the answer.

<img src="https://github.com/user-attachments/assets/71241689-472b-4f1c-a821-32a12ade1409" width=800>

The tools used in this document are as follows:
- **Sample raw document**: A segment from Zhou Shuren's "Dawn Blossoms Plucked at Dusk" which can be replaced with any other document.
- **Graph storage**: [TuGraph](https://github.com/TuGraph-family/tugraph-db), an open-source graph database (think of it as a mysql-server).
- **LLM**: This document uses the Qwen2.5-7B-Instruct provided by [SiliconCloud](https://cloud.siliconflow.cn) as an example. Users can switch to any [PyPI `openai`](https://pypi.org/project/openai/) interface, regardless of whether the model comes from SFT or a remote API.

## I. Install Dependencies

1. **Install TuGraph**. [TuGraph Official](https://tugraph-db.readthedocs.io/zh-cn/latest/5.installation%26running/index.html) supports deployment via docker/online service/binary files, and here we use the docker method.

   My server version is **4.5.0**

   ```bash
   # Pull the image
   docker pull tugraph/tugraph-runtime-centos7
   # Run
   docker run -d -p 7070:7070  -p 7687:7687 -p 9090:9090 -v /root/tugraph/data:/var/lib/lgraph/data  -v /root/tugraph/log:/var/log/lgraph_log --name tugraph_demo ${REPOSITORY}:${VERSION}
   # ${REPOSITORY} is the image address, ${VERSION} is the version number.
   # 7070 is the default http port, used for accessing tugraph-db-browser.
   # 7687 is the bolt port, used for bolt client access.
   # 9090 is the default rpc port, used for rpc client access.
   # /var/lib/lgraph/data is the default data directory inside the container, /var/log/lgraph_log is the default log directory inside the container.
   # The command mounts the data and log directories to the host machine's /root/tugraph/ for persistence, which you can modify according to your actual situation.
   ```

   After successful installation, open port 7070 in the browser to see the TuGraph UI interface. The default account is admin, and the default password is 73@TuGraph.

   <img src="https://github.com/user-attachments/assets/010224cc-76ee-4c1c-9198-9cf4f01e248d" width=400>

3. **HuixiangDou2 Dependencies**. Simply use `pip install`.

   ```bash
   python3 -m pip install -r requirements.txt
   ```

   We also support cpu-only
   ```bash
   # CPU only
   python3 -m pip install -r requirements/cpu.txt
   ```

4. **Download the embedding model**. HuixiangDou2 supports bce/bge text and image-text models. For example, using bce [embedding](https://huggingface.co/InfiniFlow/bce-embedding-base_v1) and [reranker](https://huggingface.co/InfiniFlow/bce-reranker-base_v1), assume the models are downloaded to the following two locations on your machine:
   * `/home/data/share/bce-embedding-base_v1`
   * `/home/data/share/bce-reranker-base_v1`

5. **LLM Key**. We use the [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud) **free** LLM API.
   * Click [API Key](https://cloud.siliconflow.cn/account/ak) to obtain the sk.
   * The models used in this tutorial are all `Qwen/Qwen2.5-7B-Instruct`.

   > Tip 1: New users can register with this link to receive additional tokens on top of the free quota: https://cloud.siliconflow.cn/s/tpoisonooo

   > Tip 2: You can also deploy your own model using `vllm`. Refer to the command `vllm serve /path/to/Qwen2.5-7B-Instruct  --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1`

6. **Configure `config.ini`**. Copy `config.ini.example` to `config.ini` and fill in the SiliconCloud SK. [Here is the complete configuration guide](./doc_config.md).

   ```bash
   cp config.ini.example config.ini
   ```

## II. Create

There are two documents under `tests/data`, copy them to `repodir` to build the knowledge base.
```bash
cp -rf tests/data repodir
python3 -m huixiangdou.pipeline.store
```

After successful creation, multiple feature directories will appear in `workdir`; at the same time, the TuGraph graph project will show a graph named `HuixiangDou2`.

<img src="https://github.com/user-attachments/assets/873fedfe-c2fe-47f2-bbb1-723c1c21c463" width=400>

## III. Query

### CMD mode
Running `main.py` will execute a query example:
```bash
python3 -m huixiangdou.main

+------------------+---------+---------------------------------+---------------+
|      Query       |  State  |            Response             |  References   |
+==================+=========+=================================+===============+
| What is in the Hundred Grass Garden? | success | The Hundred Grass Garden has various plants and insects, including green vegetable plots, tall soapberry trees, purple mulberries, raspberries that look like small coral beads, and insects such as cicadas, hornets, skylarks, crickets, centipedes, and blister beetles. In addition, there are twining vines of Polygonum multiflorum and climbing fig, as well as natural features like stone wells and broken bricks. | baicaoyuan.md |
+------------------+---------+---------------------------------+---------------+
```

### Gradio UI mode

We also implement Gradio inside it

```bash
python3 -m huixiangdou.gradio_ui
```

Open port 7860 in web browser:

<img src="https://github.com/user-attachments/assets/b7b7cb90-4a85-4ffc-9de0-52670dd9159e" width=800>

### Swagger API
Also support [Swagger API](../swagger.json)

Start server

```bash
python3 -m huixiangdou.server --port 23334
```

Test with client

```bash
python3 huixiangdou/client.py
```

## IV. Drop Existing Knowledge Base

Simply delete the entities and relationships in `workdir` and TuGraph.
```bash
# Delete features
rm -rf workdir
# After execution, enter Y to confirm the deletion of entity relationships
# The graph name is configured in `config.ini`, default is `HuixiangDou2`
python3 -m huixiangdou.service.graph_store drop
```
