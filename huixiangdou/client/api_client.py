"""
HuixiangDou API Client
提供与server.py的HTTP API交互的异步客户端
"""

import aiohttp
import asyncio
import json
from typing import AsyncGenerator, Dict, List, Optional, Any
from loguru import logger


class HuixiangDouAPIClient:
    """HuixiangDou API异步客户端"""
    
    def __init__(self, base_url: str = "http://localhost:23333"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """通用的HTTP请求方法"""
        if not self.session:
            raise RuntimeError("Client must be used within async context")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    if response.content_type == 'application/json':
                        return await response.json()
                    else:
                        return await response.text()
                else:
                    error_text = await response.text()
                    logger.error(f"API请求失败: {response.status} - {error_text}")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
        except Exception as e:
            logger.error(f"请求异常: {e}")
            raise
    
    async def chat(self, 
                   text: str, 
                   language: str = "zh_cn",
                   enable_web_search: bool = False,
                   db_name: str = "HuixiangDou",
                   history: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        """
        流式聊天接口
        
        Args:
            text: 用户输入的问题
            language: 语言设置 ("zh_cn" 或 "en")
            enable_web_search: 是否启用网络搜索
            db_name: 数据库名称
            history: 历史对话记录
            
        Yields:
            流式回复内容
        """
        if history is None:
            history = []
            
        request_data = {
            "language": language,
            "enable_web_search": enable_web_search,
            "user": text,
            "history": history,
            "db_name": db_name
        }
        
        url = f"{self.base_url}/v2/chat"
        
        try:
            async with self.session.post(url, json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
                
                full_response = ""
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:])  # 移除 "data:" 前缀
                            if 'data' in data and 'delta' in data['data']:
                                delta = data['data']['delta']
                                if delta:
                                    full_response += delta
                                    yield full_response
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析JSON: {line}")
                            continue
                            
        except Exception as e:
            logger.error(f"聊天请求失败: {e}")
            yield f"抱歉，聊天服务暂时不可用: {str(e)}"
    
    async def add_files(self, 
                       file_list: List[str], 
                       db_name: str = "HuixiangDou") -> AsyncGenerator[Dict[str, Any], None]:
        """
        添加文件到知识库（流式）
        
        Args:
            file_list: 文件路径列表
            db_name: 目标数据库名称
            
        Yields:
            进度信息字典
        """
        request_data = {
            "file_list": file_list,
            "db_name": db_name
        }
        
        url = f"{self.base_url}/v2/add_files"
        
        try:
            async with self.session.post(url, json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:])  # 移除 "data:" 前缀
                            yield data
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析JSON: {line}")
                            continue
                            
        except Exception as e:
            logger.error(f"添加文件失败: {e}")
            yield {
                "status": {"code": 1, "error": str(e)},
                "data": {"progress": 0, "message": f"添加文件失败: {str(e)}"}
            }
    
    async def list_files(self, db_name: str = "HuixiangDou") -> List[str]:
        """
        列出数据库中的文件
        
        Args:
            db_name: 数据库名称
            
        Returns:
            文件名称列表
        """
        params = {"db_name": db_name}
        
        try:
            result = await self._make_request("GET", "/v2/list_file", params=params)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    async def list_databases(self) -> List[str]:
        """
        列出所有可用的数据库
        
        Returns:
            数据库名称列表
        """
        try:
            result = await self._make_request("POST", "/v2/list_db")
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"列出数据库失败: {e}")
            return []
    
    async def drop_db(self, db_name: str = "HuixiangDou") -> str:
        """
        清空指定数据库
        
        Args:
            db_name: 要清空的数据库名称
            
        Returns:
            操作结果消息
        """
        request_data = {"db_name": db_name}
        
        try:
            result = await self._make_request("POST", "/v2/drop_db", json=request_data)
            return str(result) if result else "清空数据库成功"
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            return f"清空数据库失败: {str(e)}"
    
    async def export_graph(self, db_name: str = "HuixiangDou") -> Dict[str, Any]:
        """
        导出图谱数据
        
        Args:
            db_name: 数据库名称
            
        Returns:
            导出结果信息，包含下载令牌等
        """
        params = {"db_name": db_name}
        
        try:
            result = await self._make_request("POST", "/v2/export_graph", params=params)
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"导出图谱失败: {e}")
            return {"status": {"code": 1, "error": str(e)}, "data": {}}
    
    async def download_export(self, download_token: str, save_path: str) -> bool:
        """
        下载导出的文件
        
        Args:
            download_token: 下载令牌
            save_path: 保存路径
            
        Returns:
            是否下载成功
        """
        url = f"{self.base_url}/v2/download_export/{download_token}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    return True
                else:
                    logger.error(f"下载失败: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False
    
    async def exemplify(self, 
                       query: str, 
                       language: str = "zh_cn",
                       enable_web_search: bool = False,
                       db_name: str = "HuixiangDou") -> Dict[str, Any]:
        """
        生成示例问题
        
        Args:
            query: 输入问题
            language: 语言设置
            enable_web_search: 是否启用网络搜索
            db_name: 数据库名称
            
        Returns:
            示例问题列表和相关数据
        """
        request_data = {
            "language": language,
            "enable_web_search": enable_web_search,
            "user": query,
            "history": [],
            "db_name": db_name
        }
        
        try:
            result = await self._make_request("POST", "/v2/exemplify", json=request_data)
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"生成示例失败: {e}")
            return {"status": {"code": 1, "error": str(e)}, "data": {"_id": "", "cases": []}}