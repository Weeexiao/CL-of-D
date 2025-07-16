"""
文件处理模块
负责文件分类和移动的核心逻辑
"""

import os
import shutil
import time
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from loguru import logger
from api_service import api_service
from config import config_manager


class FileItem:
    """文件项类"""
    
    def __init__(self, name: str, path: str, entry_type: str):
        """
        初始化文件项
        
        Args:
            name: 文件名
            path: 文件路径
            entry_type: 条目类型（文件/文件夹）
        """
        self.name = name
        self.path = path
        self.entry_type = entry_type
        self.classification_result: Optional[str] = None
        self.target_path: Optional[str] = None
        self.error: Optional[str] = None
        self.processing_time: float = 0.0
    
    def __str__(self) -> str:
        return f"{self.entry_type}: {self.name}"


class FileProcessor:
    """文件处理器"""
    
    def __init__(self):
        """初始化文件处理器"""
        self.source_folder = ""
        self.classification_rules = ""
        self.file_items: List[FileItem] = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = 0.0
    
    def load_files(self, source_folder: str) -> List[FileItem]:
        """
        加载源文件夹中的文件
        
        Args:
            source_folder: 源文件夹路径
            
        Returns:
            文件项列表
        """
        self.source_folder = source_folder
        self.file_items = []
        
        try:
            # 获取所有文件和子文件夹（排除分类目标文件夹）
            entries = [f for f in os.listdir(source_folder) 
                      if f not in ["永久", "长期", "短期"]]
            
            for entry in entries:
                entry_path = os.path.join(source_folder, entry)
                entry_type = "文件" if os.path.isfile(entry_path) else "文件夹"
                
                file_item = FileItem(entry, entry_path, entry_type)
                self.file_items.append(file_item)
            
            logger.info(f"加载文件完成 - 源文件夹: {source_folder}, 文件数量: {len(self.file_items)}")
            return self.file_items
            
        except Exception as e:
            logger.error(f"加载文件失败 - 源文件夹: {source_folder}, 错误: {e}")
            return []
    
    def create_classification_directories(self) -> bool:
        """
        创建分类目录结构
        
        Returns:
            是否成功
        """
        try:
            # 创建保管期限根目录
            for period in ["永久", "长期", "短期"]:
                period_path = os.path.join(self.source_folder, period)
                if not os.path.exists(period_path):
                    os.makedirs(period_path)
                    logger.debug(f"创建目录: {period_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"创建分类目录失败: {e}")
            return False
    
    def classify_file(self, file_item: FileItem) -> bool:
        """
        分类单个文件
        
        Args:
            file_item: 文件项
            
        Returns:
            是否成功
        """
        start_time = time.time()
        
        try:
            # 调用API进行分类
            success, result, details = api_service.classify_file(
                file_item.name, 
                file_item.entry_type, 
                self.classification_rules
            )
            
            file_item.processing_time = time.time() - start_time
            
            if success:
                file_item.classification_result = result
                
                # 解析分类结果
                if "-" in result:
                    period, dept = result.split("-", 1)
                    
                    # 创建目标目录
                    target_dir = os.path.join(self.source_folder, period, dept)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    
                    # 设置目标路径
                    file_item.target_path = os.path.join(target_dir, file_item.name)
                    
                    logger.info(f"分类成功: {file_item.name} → {period}/{dept}")
                    return True
                else:
                    file_item.error = "分类结果格式错误"
                    logger.error(f"分类结果格式错误: {file_item.name}, 结果: {result}")
                    return False
            else:
                file_item.error = details.get("error", "API调用失败")
                logger.error(f"分类失败: {file_item.name}, 错误: {file_item.error}")
                return False
                
        except Exception as e:
            file_item.processing_time = time.time() - start_time
            file_item.error = str(e)
            logger.error(f"分类异常: {file_item.name}, 错误: {e}")
            return False
    
    def move_file(self, file_item: FileItem) -> bool:
        """
        移动文件到目标位置
        
        Args:
            file_item: 文件项
            
        Returns:
            是否成功
        """
        if not file_item.target_path:
            file_item.error = "目标路径未设置"
            return False
        
        try:
            # 移动文件/文件夹
            shutil.move(file_item.path, file_item.target_path)
            logger.info(f"移动成功: {file_item.name} → {file_item.target_path}")
            return True
            
        except Exception as e:
            file_item.error = f"移动失败: {str(e)}"
            logger.error(f"移动失败: {file_item.name}, 错误: {e}")
            return False
    
    def process_all_files(self, classification_rules: str, progress_callback=None) -> Dict[str, Any]:
        """
        处理所有文件
        
        Args:
            classification_rules: 分类规则
            progress_callback: 进度回调函数
            
        Returns:
            处理结果统计
        """
        self.classification_rules = classification_rules
        self.start_time = time.time()
        self.success_count = 0
        self.error_count = 0
        
        # 创建分类目录
        if not self.create_classification_directories():
            return {"success": False, "error": "创建分类目录失败"}
        
        total_files = len(self.file_items)
        logger.info(f"开始处理 {total_files} 个文件")
        
        for i, file_item in enumerate(self.file_items):
            # 更新进度
            if progress_callback:
                progress = (i + 1) / total_files * 100
                progress_callback(progress, f"处理中: {file_item.name}")
            
            # 分类文件
            if self.classify_file(file_item):
                # 移动文件
                if self.move_file(file_item):
                    self.success_count += 1
                else:
                    self.error_count += 1
            else:
                self.error_count += 1
        
        # 完成处理
        duration = time.time() - self.start_time
        result = {
            "success": True,
            "total_files": total_files,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "duration": duration,
            "file_items": self.file_items
        }
        
        logger.info(f"处理完成 - 成功: {self.success_count}, 失败: {self.error_count}, 耗时: {duration:.2f}秒")
        return result
    
    def get_file_list_display(self) -> str:
        """
        获取文件列表显示文本
        
        Returns:
            文件列表文本
        """
        if not self.file_items:
            return "未加载文件"
        
        lines = []
        for item in self.file_items:
            lines.append(f"{item.entry_type}: {item.name}")
        
        return "\n".join(lines)
    
    def get_processing_summary(self) -> str:
        """
        获取处理摘要
        
        Returns:
            处理摘要文本
        """
        if not self.file_items:
            return "未处理文件"
        
        total_time = sum(item.processing_time for item in self.file_items)
        avg_time = total_time / len(self.file_items) if self.file_items else 0
        
        summary = f"""
处理摘要:
- 总文件数: {len(self.file_items)}
- 成功处理: {self.success_count}
- 处理失败: {self.error_count}
- 总耗时: {total_time:.2f}秒
- 平均耗时: {avg_time:.2f}秒/文件
        """
        
        return summary.strip()
    
    def export_results(self, output_file: str) -> bool:
        """
        导出处理结果
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("文件分类处理结果\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"源文件夹: {self.source_folder}\n")
                f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总文件数: {len(self.file_items)}\n")
                f.write(f"成功处理: {self.success_count}\n")
                f.write(f"处理失败: {self.error_count}\n\n")
                
                f.write("详细结果:\n")
                f.write("-" * 30 + "\n")
                
                for item in self.file_items:
                    f.write(f"文件名: {item.name}\n")
                    f.write(f"类型: {item.entry_type}\n")
                    f.write(f"分类结果: {item.classification_result or '未分类'}\n")
                    f.write(f"目标路径: {item.target_path or '无'}\n")
                    f.write(f"处理时间: {item.processing_time:.2f}秒\n")
                    if item.error:
                        f.write(f"错误信息: {item.error}\n")
                    f.write("\n")
            
            logger.info(f"结果导出成功: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"结果导出失败: {e}")
            return False


# 全局文件处理器实例
file_processor = FileProcessor() 