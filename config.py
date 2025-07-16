"""
配置管理模块
负责应用程序的配置加载、保存和验证
"""

import os
import json
from typing import Optional
from pydantic import BaseModel, Field
from pathlib import Path


class APIConfig(BaseModel):
    """API配置模型"""
    doubao_api_key: str = Field(default="", description="豆包API密钥")
    deepseek_api_key: str = Field(default="", description="DeepSeek API密钥")
    api_type: str = Field(default="doubao", description="当前使用的API类型")


class AppConfig(BaseModel):
    """应用程序配置模型"""
    api_config: APIConfig = Field(default_factory=APIConfig)
    window_width: int = Field(default=800, description="窗口宽度")
    window_height: int = Field(default=600, description="窗口高度")
    log_level: str = Field(default="INFO", description="日志级别")
    max_retries: int = Field(default=3, description="API调用最大重试次数")
    timeout: int = Field(default=30, description="API调用超时时间(秒)")


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为程序所在目录
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.config_file = self.config_dir / "config.json"
        self.rules_file = self.config_dir / "rules.txt"
        self.logs_dir = self.config_dir / "logs"
        
        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self._default_config = AppConfig()
        self._config = self._default_config.copy()
    
    def load_config(self) -> AppConfig:
        """
        加载配置文件
        
        Returns:
            加载的配置对象
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    self._config = AppConfig(**config_data)
            else:
                # 如果配置文件不存在，使用默认配置并保存
                self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
            self._config = self._default_config.copy()
        
        return self._config
    
    def save_config(self) -> bool:
        """
        保存配置文件
        
        Returns:
            保存是否成功
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config.dict(), f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def update_api_config(self, api_config: APIConfig) -> bool:
        """
        更新API配置
        
        Args:
            api_config: 新的API配置
            
        Returns:
            更新是否成功
        """
        try:
            self._config.api_config = api_config
            return self.save_config()
        except Exception as e:
            print(f"更新API配置失败: {e}")
            return False
    
    def get_api_config(self) -> APIConfig:
        """
        获取当前API配置
        
        Returns:
            当前API配置
        """
        return self._config.api_config
    
    def load_classification_rules(self) -> str:
        """
        加载分类规则
        
        Returns:
            分类规则文本
        """
        default_rules = """部门识别规则：文件内容或标题含公文、机要、保密、档案、印信、信访、综合治理、会议管理、数字化管理、党建、工会、共青团、企业文化宣传、社会责任、扶贫等关键词或相关内容的归办公室（党委办公室、党委工作部）；含劳动用工、人事管理、薪酬绩效、社保福利、教育培训、职业技能鉴定、劳动合同、职工名册、干部任免等关键词或相关内容的归人力资源部（党委组织部）；含财务预算、决算、税务管理、会计核算、财务分析报告、银行对账单、纳税申报表等关键词或相关内容的归财务资金部；含审计通知书、审计报告、纪检监督、aceeption、违纪案件查处、内控报告等关键词或相关内容的归审计监督部(纪委办公室)；含合同管理、工程预算、成本控制、计量支付、变更索赔、法律纠纷、诉讼调解书等关键词或相关内容的归经营管理部（法律合约部）；含项目管理、施工许可、工程验收、生产计划、进度控制、信用评价、项目经理部成立等关键词或相关内容的归生产管理部；含物资采购、机械设备管理、采购合同、资产购置、特种设备维保、量价成本管控等关键词或相关内容的归物资装备部；含安全生产、职业健康、应急救援预案、环保规划、节能减排、事故调查报告等关键词或相关内容的归安全环保管理部；含科技研发、专利管理、工法申报、质量管理、BIM技术、工程试验检测、高新技术企业申报等关键词或相关内容的归技术质量部；含市场开发计划、项目投标、招标文件、中标通知书、区域办事处设立、履约保函等关键词或相关内容的归市场开发部；未命中部门专属关键词或相关内容的归各部门通用归档范围。保管期限分类规则：文件内容或标题满足涉及重要事项的会议文件、上级机关重要文件、公司战略规划、资质管理、重大合同协议、人事档案核心材料、财务决算、税务年报、会计档案保管清册、重大事件记录、重要声像资料、电子文件等条件的永久保管；满足一般会议文件、非核心业务文件、培训资料、对标考察报告、对标检查材料、非重大奖项荣誉、一般合同协议、设备购置计划、非核心财务文件等条件的30年保管；满足未通过的文件、日常事务性材料、短期业务记录、非重要载体材料、基层事务性文件等条件的10年保管，优先匹配永久规则，其次30年，最后10年。"""
        
        try:
            if self.rules_file.exists():
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            else:
                # 如果规则文件不存在，创建默认规则文件
                self.save_classification_rules(default_rules)
                return default_rules
        except Exception as e:
            print(f"加载分类规则失败: {e}，使用默认规则")
            return default_rules
    
    def save_classification_rules(self, rules: str) -> bool:
        """
        保存分类规则
        
        Args:
            rules: 分类规则文本
            
        Returns:
            保存是否成功
        """
        try:
            with open(self.rules_file, "w", encoding="utf-8") as f:
                f.write(rules)
            return True
        except Exception as e:
            print(f"保存分类规则失败: {e}")
            return False
    
    def get_log_file_path(self, filename: str = "classification.log") -> Path:
        """
        获取日志文件路径
        
        Args:
            filename: 日志文件名
            
        Returns:
            日志文件完整路径
        """
        return self.logs_dir / filename
    
    def get_config_dir(self) -> Path:
        """
        获取配置目录
        
        Returns:
            配置目录路径
        """
        return self.config_dir


# 全局配置管理器实例
config_manager = ConfigManager() 