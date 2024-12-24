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
