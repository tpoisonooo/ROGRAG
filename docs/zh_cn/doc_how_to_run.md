# 运行

建图期间，我们会把 raw 文档整理成有结构的图谱形式。如图所示：

<img src="https://github.com/user-attachments/assets/b9872a7b-4b15-4f51-b361-7a5b0001134b" width=400>

检索期间，我们先基于 Query 从图谱获取子图和对应的 Chunks，再用 LLM 获取答案。

<img src="https://github.com/user-attachments/assets/71241689-472b-4f1c-a821-32a12ade1409" width=800>

本文档使用的工具如下：
- **样例 raw 文档**：周树人《朝花夕拾》片段，可换为任意其他文档
- **图谱存储**：[TuGraph](https://github.com/TuGraph-family/tugraph-db)，开源图数据库（看作 mysql-server 即可）
- **LLM**：本文档以 [SiliconCloud](https://cloud.siliconflow.cn) 提供的 Qwen2.5-7B-Instruct 为例，用户可切换为任何 [PyPI `openai`](https://pypi.org/project/openai/) 接口，无论模型来自 SFT 还是 remote API

## 一、安装依赖

1. **部署 TuGraph 服务**。[TuGraph 官方](https://tugraph-db.readthedocs.io/zh-cn/latest/5.installation%26running/index.html)支持 docker/在线服务/二进制文件部署，这里用 docker 部署 TuGraph（和 HuixiangDou2 环境无关，二者可以不在同一台机器上）
   
   我使用的 Server 版本是 **4.5.0**

   ```bash
   # 拉取镜像
   docker pull tugraph/tugraph-runtime-centos
   # 运行
   docker run -d -p 7070:7070  -p 7687:7687 -p 9090:9090 -v /root/tugraph/data:/var/lib/lgraph/data  -v /root/tugraph/log:/var/log/lgraph_log --name tugraph_demo ${REPOSITORY}:${VERSION}
   # ${REPOSITORY}是镜像地址，${VERSION}是版本号。
   # 7070是默认的http端口，访问tugraph-db-browser使用。   
   # 7687是bolt端口，bolt client访问使用。
   # 9090是默认的rpc端口，rpc client访问使用。
   # /var/lib/lgraph/data是容器内的默认数据目录，/var/log/lgraph_log是容器内的默认日志目录
   # 命令将数据目录和日志目录挂载到了宿主机的/root/tugraph/上进行持久化，您可以根据实际情况修改。
   ```

   TuGraph 是 C++ 开发，如果不方便使用 docker，也可以从[官网下载](https://github.com/TuGraph-family/tugraph-db/releases)编译好的 deb/rpm 安装运行。

   成功后，在浏览器打开 7070 端口，会看到 TuGraph UI 界面，默认账号 admin，默认密码 73@TuGraph

   <img src="https://github.com/user-attachments/assets/010224cc-76ee-4c1c-9198-9cf4f01e248d" width=400>

3. **HuixiangDou2 依赖**。直接使用 `pip install` 即可。

   ```bash
   # 需 GPU
   python3 -m pip install -r requirements.txt
   ```

   我们同样支持 cpu-only 运行，但 config.ini 配置需要[参照 config.ini.cpu-only-example](../../config.ini.cpu-only-example) 配置 SiliconCloud api_token
   ```bash
   # CPU only
   python3 -m pip install -r requirements/cpu.txt
   ```

4. **下载 embedding 模型。** HuixiangDou2 支持 bce/bge 文本+图文模型。以 bce [embedding](https://huggingface.co/InfiniFlow/bce-embedding-base_v1) 和 [reranker](https://huggingface.co/InfiniFlow/bce-reranker-base_v1) 为例，假设模型下载到本机以下两个位置：
   * `/home/data/share/bce-embedding-base_v1`
   * `/home/data/share/bce-reranker-base_v1`

5. **LLM Key**。我们用 [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud) **免费** LLM API。
   * 点击[API密钥](https://cloud.siliconflow.cn/account/ak) 获取 sk
   * 本教程使用的模型均为 `Qwen/Qwen2.5-7B-Instruct`
   
   > Tips1: 新用户用这个链接注册，可在免费额度基础上，加送 token：https://cloud.siliconflow.cn/s/tpoisonooo

   > Tips2: 也可以用 `vllm` 部署自己的模型。参考命令 `vllm serve /path/to/Qwen2.5-7B-Instruct  --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1`

6. **配置`config.ini`**。把`config.ini.example`拷贝为`config.ini`，填写 SiliconCloud SK 即可。[这里是完整的配置说明](./doc_config.md) 

   ```bash
   cp config.ini.example config.ini
   ```

## 二、创建

`tests/data` 下有两篇文档，把它拷贝到 `repodir`，建知识库。
```bash
cp -rf tests/data repodir
python3 -m huixiangdou.pipeline.store
```

成功后，`workdir` 会出现多个特征目录；同时 TuGraph 图项目会看到名为 `HuixiangDou2` 的图谱。

<img src="https://github.com/user-attachments/assets/873fedfe-c2fe-47f2-bbb1-723c1c21c463" width=400>

## 三、查询

### 命令行方式

执行 `main.py` 可在命令行运行查询样例：
```bash
python3 -m huixiangdou.main

+------------------+---------+---------------------------------+---------------+
|      Query       |  State  |            Response             |  References   |
+==================+=========+=================================+===============+
| 百草园里有什么？ | success | 百草园里有多种植物和昆虫，包括碧绿的菜畦、高大的皂荚树、紫红的 | baicaoyuan.md |
|                  |         | 桑椹、像小珊瑚珠攒成的小球的覆盆子等植物，以及鸣蝉、黄蜂、叫天 |               |
|                  |         | 子（云雀）、油蛉、蟋蟀、蜈蚣、斑蝥等昆虫。此外，还有何首乌藤和 |               |
|                  |         | 木莲藤缠绕，石井栏和断砖作为自然特征存在。 |               |
+------------------+---------+---------------------------------+---------------+
```

### Gradio UI 方式

俺也实现了 Gradio 接入方法

```bash
python3 -m huixiangdou.gradio_ui
```

然后打开浏览器 7860 端口，可以流式响应

<img src="https://github.com/user-attachments/assets/b7b7cb90-4a85-4ffc-9de0-52670dd9159e" width=800>

### Swagger API
同样也支持 [swagger API 文档](../swagger.json)

启动 server

```bash
python3 -m huixiangdou.server --port 23334
```

执行 client 测试

```bash
python3 huixiangdou/client.py
```


## 四、删除已有知识库

删掉 `workdir` 和 `TuGraph` 里的实体关系即可。
```bash
# 删除特征
rm -rf workdir
# 图名称配置在 `config.ini` 中，默认是 `HuixiangDou2`
# 执行后输入 Y 确认删除实体关系
python3 -m huixiangdou.service.graph_store drop
```
