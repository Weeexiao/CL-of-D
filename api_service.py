"""
API服务模块
负责与AI大语言模型的API交互
"""

import asyncio
import time
from typing import Optional, Tuple, Dict, Any
from openai import OpenAI, AsyncOpenAI
from loguru import logger
from config import config_manager, APIConfig
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam


class APIService:
    """API服务类"""
    
    def __init__(self):
        """初始化API服务"""
        self.config = config_manager.get_api_config()
        self._clients: Dict[str, OpenAI] = {}
        self._async_clients: Dict[str, AsyncOpenAI] = {}
    
    def _get_client(self, api_type: str) -> OpenAI:
        """
        获取API客户端
        
        Args:
            api_type: API类型 ('doubao' 或 'deepseek')
            
        Returns:
            OpenAI客户端实例
        """
        if api_type not in self._clients:
            if api_type == "doubao":
                self._clients[api_type] = OpenAI(
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                    api_key=self.config.doubao_api_key
                )
            else:  # deepseek
                self._clients[api_type] = OpenAI(
                    base_url="https://api.deepseek.com",
                    api_key=self.config.deepseek_api_key
                )
        
        return self._clients[api_type]
    
    def _get_async_client(self, api_type: str) -> AsyncOpenAI:
        """
        获取异步API客户端
        
        Args:
            api_type: API类型 ('doubao' 或 'deepseek')
            
        Returns:
            异步OpenAI客户端实例
        """
        if api_type not in self._async_clients:
            if api_type == "doubao":
                self._async_clients[api_type] = AsyncOpenAI(
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                    api_key=self.config.doubao_api_key
                )
            else:  # deepseek
                self._async_clients[api_type] = AsyncOpenAI(
                    base_url="https://api.deepseek.com",
                    api_key=self.config.deepseek_api_key
                )
        
        return self._async_clients[api_type]
    
    def _get_model_name(self, api_type: str) -> str:
        """
        获取模型名称
        
        Args:
            api_type: API类型
            
        Returns:
            模型名称
        """
        return "doubao-pro-32k-241215" if api_type == "doubao" else "deepseek-chat"
    
    def test_connection(self, api_type: str) -> Tuple[bool, str]:
        """
        测试API连接
        
        Args:
            api_type: API类型
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            client = self._get_client(api_type)
            model_name = self._get_model_name(api_type)
            
            messages: list[ChatCompletionSystemMessageParam] = [
                ChatCompletionSystemMessageParam(role="system", content="测试连接")
            ]
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=10
            )
            
            return True, "连接成功"
        except Exception as e:
            return False, f"API错误: {str(e)}"
    
    def classify_file(self, filename: str, entry_type: str, classification_rules: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        分类文件
        
        Args:
            filename: 文件名
            entry_type: 条目类型（文件/文件夹）
            classification_rules: 分类规则
            
        Returns:
            (是否成功, 分类结果, 详细信息)
        """
        start_time = time.time()
        api_type = self.config.api_type
        
        try:
            # 构造请求消息
            request_messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
                ChatCompletionSystemMessageParam(role="system", content=f"你是文件分类助手，需严格根据以下规则判断{entry_type}的保管期限和所属部门：\n"
                              f"----- 分类规则 -----\n"
                              f"{classification_rules}\n"
                              f"请分析{entry_type}名称'{filename}'的保管期限（仅返回'永久'、'长期'或'短期'，30年→长期，10年→短期）和所属部门（按规则中的部门名称），格式为'保管期限-部门'（例如'永久-办公室（党委办公室、党委工作部）'）。\n"
                              f"注意：输出必须为纯文本，禁止使用任何格式符号，仅返回'保管期限-部门'格式的结果。"),
                ChatCompletionUserMessageParam(role="user", content="请严格按规则分类，输出'保管期限-部门'格式的结果")
            ]
            
            # 记录API请求
            logger.debug(f"API请求 - 文件: {filename}, API类型: {api_type}")
            
            # 调用API
            client = self._get_client(api_type)
            model_name = self._get_model_name(api_type)
            
            completion = client.chat.completions.create(
                model=model_name,
                messages=request_messages,
                timeout=config_manager.load_config().timeout
            )
            # 解析响应
            content = completion.choices[0].message.content
            result = content.strip() if content else ""
            
            # 记录API响应
            logger.debug(f"API响应 - 文件: {filename}, 结果: {result}")
            
            # 验证结果格式
            if "-" in result and any(period in result for period in ["永久", "长期", "短期"]):
                period, dept = result.split("-", 1)
                duration = time.time() - start_time
                
                details = {
                    "api_type": api_type,
                    "model": model_name,
                    "duration": duration,
                    "raw_response": result,
                    "period": period,
                    "department": dept
                }
                
                return True, result, details
            else:
                duration = time.time() - start_time
                details = {
                    "api_type": api_type,
                    "model": model_name,
                    "duration": duration,
                    "raw_response": result,
                    "error": "格式错误"
                }
                
                return False, "未分类-未分类", details
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"API调用失败 - 文件: {filename}, 错误: {e}")
            
            details = {
                "api_type": api_type,
                "duration": duration,
                "error": str(e)
            }
            
            return False, "未分类-未分类", details
    
    async def classify_file_async(self, filename: str, entry_type: str, classification_rules: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        异步分类文件
        
        Args:
            filename: 文件名
            entry_type: 条目类型（文件/文件夹）
            classification_rules: 分类规则
            
        Returns:
            (是否成功, 分类结果, 详细信息)
        """
        start_time = time.time()
        api_type = self.config.api_type
        
        try:
            # 构造请求消息
            request_messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
                ChatCompletionSystemMessageParam(role="system", content=f"你是文件分类助手，需严格根据以下规则判断{entry_type}的保管期限和所属部门：\n"
                              f"----- 分类规则 -----\n"
                              f"{classification_rules}\n"
                              f"请分析{entry_type}名称'{filename}'的保管期限（仅返回'永久'、'长期'或'短期'，30年→长期，10年→短期）和所属部门（按规则中的部门名称），格式为'保管期限-部门'（例如'永久-办公室（党委办公室、党委工作部）'）。\n"
                              f"注意：输出必须为纯文本，禁止使用任何格式符号，仅返回'保管期限-部门'格式的结果。"),
                ChatCompletionUserMessageParam(role="user", content="请严格按规则分类，输出'保管期限-部门'格式的结果")
            ]
            
            # 记录API请求
            logger.debug(f"异步API请求 - 文件: {filename}, API类型: {api_type}")
            
            # 调用异步API
            client = self._get_async_client(api_type)
            model_name = self._get_model_name(api_type)
            
            completion = await client.chat.completions.create(
                model=model_name,
                messages=request_messages,
                timeout=config_manager.load_config().timeout
            )
            
            # 解析响应
            content = completion.choices[0].message.content
            result = content.strip() if content else ""
            
            # 记录API响应
            logger.debug(f"异步API响应 - 文件: {filename}, 结果: {result}")
            
            # 验证结果格式
            if "-" in result and any(period in result for period in ["永久", "长期", "短期"]):
                period, dept = result.split("-", 1)
                duration = time.time() - start_time
                
                details = {
                    "api_type": api_type,
                    "model": model_name,
                    "duration": duration,
                    "raw_response": result,
                    "period": period,
                    "department": dept
                }
                
                return True, result, details
            else:
                duration = time.time() - start_time
                details = {
                    "api_type": api_type,
                    "model": model_name,
                    "duration": duration,
                    "raw_response": result,
                    "error": "格式错误"
                }
                
                return False, "未分类-未分类", details
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"异步API调用失败 - 文件: {filename}, 错误: {e}")
            
            details = {
                "api_type": api_type,
                "duration": duration,
                "error": str(e)
            }
            
            return False, "未分类-未分类", details
    
    def update_config(self, api_config: APIConfig):
        """
        更新API配置
        
        Args:
            api_config: 新的API配置
        """
        old_config = self.config
        self.config = api_config
        
        # 清除缓存的客户端
        self._clients.clear()
        self._async_clients.clear()
        
        # 记录配置变更
        logger.info(f"API配置已更新 - 类型: {old_config.api_type} → {api_config.api_type}")
    
    def get_current_config(self) -> APIConfig:
        """
        获取当前API配置
        
        Returns:
            当前API配置
        """
        return self.config


# 全局API服务实例
api_service = APIService() 