# docker 方式运行

我们配置好了 HuixiangDou2 运行所需的 cuda 12.4 docker image，最终可以一条命令启动 Swagger Server API 服务。

[百度云盘下载地址](https://pan.baidu.com/s/1H1u5XYxh35xh2G8ZYRf-ZQ?pwd=76gs)

镜像里已经包含：
- Qwen2.5-7B-Instruct 模型、bce embedding/reranker 模型
- vllm 环境
- TuGraph 运行环境
- HuixiangDou2 源码

## 一、环境要求

- 总显存 24G（单卡 24，或者 2 块 16G 都行）
- 检查 GPU 驱动版本，确保支持 cuda12.4
- 安装 nvidia-docker，支持 `docker --gpus all` 命令

## 二、docker 使用
下载镜像，导入到 docker
```text
sudo docker load -i hxd-public.tar
sudo docker images
..
REPOSITORY                        TAG       IMAGE ID       CREATED        SIZE
hxd-public                        latest    ce59f3a3763f   47 hours ago   52.4GB
```

进入 hxd-public 镜像对应容器
```text
# 8888 是将要监听的服务端口；7070、7687、9090 是 TuGraph 端口可以不映射
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -it hxd-public /bin/bash

# 这里有下载好的模型、代码、tugraph
ls /root

..
Qwen2.5-7B-Instruct
bce-embedding-base_v1 
bce-reranker-base_v1
HuixiangDou
run.sh
```

启动 TuGraph 和 vllm（命令就在 run.sh 里）
```bash
/usr/local/bin/lgraph_server -d start -c /root/lgraph.json --log_dir ""
nohup vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1 &
```

## 三、建立知识库
`HuixiangDou/tests/data` 下有两篇文档，把它拷贝到 `repodir`，待 vllm 启动后，建知识库。
```bash
cd HuixiangDou
cp -rf tests/data repodir
python3 -m huixiangdou.pipeline.store
```
打开浏览器 17070 端口，账号 admin，密码 73@TuGraph 登录，能看到对应图谱（镜像代码多写了个 `pdb.set_trace()`，自行删一下qaq）

<img src="https://github.com/user-attachments/assets/873fedfe-c2fe-47f2-bbb1-723c1c21c463" width=400>

## 四、检索

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

### Gradio UI 接入

```bash
python3 -m huixiangdou.gradio_ui --port 8888
```

然后打开浏览器 8888 端口，可以流式响应

<img src="https://github.com/user-attachments/assets/b7b7cb90-4a85-4ffc-9de0-52670dd9159e" width=800>

### Swagger API
同样也支持 [swagger API 文档](../swagger.json)

启动 server

```bash
python3 -m huixiangdou.server --port 8888
```

浏览器打开 8888 号端口查看 SwaggerUI。执行 client 测试

```bash
python3 huixiangdou/client.py
```

## 五、一键启动

提交建好知识库的镜像
```text
sudo docker commit [容器ID] [镜像名，如hxd-public]
```

然后可以一键启动所有服务
```text
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -it seed-service /bin/bash -ic "/root/run.sh"
```
