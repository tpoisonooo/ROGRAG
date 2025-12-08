source ~/.bashrc
echo $PWD
export PATH=/root/miniconda3/bin:$PATH
conda init bash
conda env list
conda run -n py310 python3 -m pip install faiss-cpu  pypinyin oss2
echo "start server.."
conda run -n py310 python3 -m huixiangdou.server

# vllm serving
vllm serve /data/share/Qwen2.5-7B-Instruct  --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 2
vllm serve /home/data/share/Qwen2.5-72B-Instruct  --enable-prefix-caching --served-model-name Qwen2.5-72B-Instruct --port 8001 --max-model-len 131072 --tensor-parallel-size 4
vllm serve /data/share/seedllm-20250110 --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 2
vllm serve /data/Baichuan-M1-14B-Instruct/  --enable-prefix-caching  --served-model-name baichuan --port 8000  --tensor-parallel-size 2  --trust-remote-code

# retrieve content
python3 -m huixiangdou.pipeline.store --config_path config.ini.mwf --repo_dir repodir.mwf/  --work_dir workdir.mwf
python3 evaluation/kag_precision/6_seed_expert.py  --workdir workdir.mwf --config_path config.ini.mwf  --pipeline parallel  --datadir /home/khj/workspace/HuixiangDou/expert_level_questions/mwf

python3 -m huixiangdou.pipeline.store --config_path config.ini.mzn --repo_dir repodir.mzn/  --work_dir workdir.mzn
python3 evaluation/kag_precision/6_seed_expert.py  --workdir workdir.mzn --config_path config.ini.mzn  --pipeline parallel  --datadir /home/khj/workspace/HuixiangDou/expert_level_questions/mzn

python3 -m huixiangdou.pipeline.store --config_path config.ini.gene --repo_dir repodir.gene/  --work_dir workdir.gene
python3 evaluation/kag_precision/6_seed_expert.py  --workdir workdir.gene --config_path config.ini.gene  --pipeline parallel  --datadir /home/khj/workspace/HuixiangDou/expert_level_questions/gene

python3 -m huixiangdou.pipeline.store --config_path config.ini.transcriptome --repo_dir repodir.transcriptome/  --work_dir workdir.transcriptome
python3 evaluation/kag_precision/6_seed_expert.py  --workdir workdir.transcriptome --config_path config.ini.transcriptome  --pipeline parallel  --datadir /home/khj/workspace/HuixiangDou/expert_level_questions/transcriptome

python3 -m huixiangdou.pipeline.store --config_path config.ini.filter --repo_dir filter/  --work_dir workdir.filter
python3 -m huixiangdou.pipeline.store --config_path config.ini.geneid --repo_dir geneid/  --work_dir workdir.geneid


python3 -m huixiangdou.pipeline.store --config_path config.ini --repo_dir repodir/  --work_dir workdir

# k8s
/root/miniconda3/bin/vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1

# centos
# 安装 nvidia-docker 插件
# 安装 docker
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -v /data/khj/workspace/docker-share:/data/share  -it tugraph/tugraph-runtime-centos7:4.5.0  /bin/bash

# 运行 tugraph
 sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -v /data/khj/workspace/docker-share:/data/share  -it  seed-service  /bin/bash 
/usr/local/bin/lgraph_server -d start -c /root/lgraph.json --log_dir "" && nohup vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1 &
&& sleep 120 && cd /root/HuixiangDou && python3 -m huixiangdou.server --port 8888


sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -it  seed-service  /bin/bash -ic "/usr/local/bin/lgraph_server -d start -c /root/lgraph.json --log_dir \"\" && nohup vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1 && sleep 120 && cd /root/HuixiangDou && python3 -m huixiangdou.server --port 8888"
sudo docker run --gpus all -p 17070:7070 -p 17687:7687 -p 19090:9090 -p 18888:8888 -v /data/khj/workspace/docker-share:/data/share  -it  seed-service  /bin/bash -ic "/usr/local/bin/lgraph_server -d start -c /root/lgraph.json --log_dir \"\" && nohup vllm serve /root/Qwen2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen2.5-7B-Instruct --port 8000 --tensor-parallel-size 1 && sleep 120 && cd /root/HuixiangDou && python3 -m huixiangdou.server --port 8888"
