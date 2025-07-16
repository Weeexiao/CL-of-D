"""
测试文件
用于验证优化后的应用程序功能
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 导入要测试的模块
from config import config_manager, APIConfig, AppConfig
from file_processor import FileProcessor, FileItem
from api_service import APIService


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = config_manager.__class__(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_config(self):
        """测试配置加载"""
        config = self.config_manager.load_config()
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.window_width, 800)
        self.assertEqual(config.window_height, 600)
    
    def test_save_config(self):
        """测试配置保存"""
        config = AppConfig()
        config.window_width = 1000
        config.window_height = 700
        
        result = self.config_manager.save_config()
        self.assertTrue(result)
        
        # 验证文件是否创建
        config_file = Path(self.temp_dir) / "config.json"
        self.assertTrue(config_file.exists())
    
    def test_update_api_config(self):
        """测试API配置更新"""
        api_config = APIConfig(
            doubao_api_key="test_doubao_key",
            deepseek_api_key="test_deepseek_key",
            api_type="doubao"
        )
        
        result = self.config_manager.update_api_config(api_config)
        self.assertTrue(result)
        
        # 验证配置是否正确保存
        saved_config = self.config_manager.get_api_config()
        self.assertEqual(saved_config.doubao_api_key, "test_doubao_key")
        self.assertEqual(saved_config.deepseek_api_key, "test_deepseek_key")
        self.assertEqual(saved_config.api_type, "doubao")


class TestFileProcessor(unittest.TestCase):
    """文件处理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = FileProcessor()
        
        # 创建测试文件
        self.test_files = [
            "test1.txt",
            "test2.docx",
            "test_folder"
        ]
        
        for file_name in self.test_files:
            file_path = os.path.join(self.temp_dir, file_name)
            if file_name.endswith(('.txt', '.docx')):
                with open(file_path, 'w') as f:
                    f.write(f"Test content for {file_name}")
            else:
                os.makedirs(file_path)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_files(self):
        """测试文件加载"""
        file_items = self.processor.load_files(self.temp_dir)
        
        self.assertEqual(len(file_items), 3)
        
        # 验证文件项
        file_names = [item.name for item in file_items]
        self.assertIn("test1.txt", file_names)
        self.assertIn("test2.docx", file_names)
        self.assertIn("test_folder", file_names)
        
        # 验证文件类型
        for item in file_items:
            if item.name.endswith(('.txt', '.docx')):
                self.assertEqual(item.entry_type, "文件")
            else:
                self.assertEqual(item.entry_type, "文件夹")
    
    def test_create_classification_directories(self):
        """测试分类目录创建"""
        # 设置源文件夹
        self.processor.source_folder = self.temp_dir
        result = self.processor.create_classification_directories()
        self.assertTrue(result)
        
        # 验证目录是否创建
        for period in ["永久", "长期", "短期"]:
            period_path = os.path.join(self.temp_dir, period)
            self.assertTrue(os.path.exists(period_path))
    
    def test_get_file_list_display(self):
        """测试文件列表显示"""
        self.processor.load_files(self.temp_dir)
        display_text = self.processor.get_file_list_display()
        
        self.assertIn("test1.txt", display_text)
        self.assertIn("test2.docx", display_text)
        self.assertIn("test_folder", display_text)


class TestFileItem(unittest.TestCase):
    """文件项测试"""
    
    def test_file_item_creation(self):
        """测试文件项创建"""
        item = FileItem("test.txt", "/path/to/test.txt", "文件")
        
        self.assertEqual(item.name, "test.txt")
        self.assertEqual(item.path, "/path/to/test.txt")
        self.assertEqual(item.entry_type, "文件")
        self.assertIsNone(item.classification_result)
        self.assertIsNone(item.target_path)
        self.assertIsNone(item.error)
        self.assertEqual(item.processing_time, 0.0)
    
    def test_file_item_string_representation(self):
        """测试文件项字符串表示"""
        item = FileItem("test.txt", "/path/to/test.txt", "文件")
        self.assertEqual(str(item), "文件: test.txt")


class TestAPIService(unittest.TestCase):
    """API服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.api_service = APIService()
    
    def test_get_model_name(self):
        """测试模型名称获取"""
        doubao_model = self.api_service._get_model_name("doubao")
        deepseek_model = self.api_service._get_model_name("deepseek")
        
        self.assertEqual(doubao_model, "doubao-pro-32k-241215")
        self.assertEqual(deepseek_model, "deepseek-chat")
    
    @patch.object(APIService, '_get_client')
    def test_test_connection_success(self, mock_get_client):
        """测试连接成功"""
        # 模拟成功的API调用
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试成功"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # 设置测试用的API配置
        self.api_service.config.doubao_api_key = "test_key"
        self.api_service.config.api_type = "doubao"
        success, message = self.api_service.test_connection("doubao")
        self.assertTrue(success)
        self.assertEqual(message, "连接成功")
    
    @patch.object(APIService, '_get_client')
    def test_test_connection_failure(self, mock_get_client):
        """测试连接失败"""
        # 模拟失败的API调用
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        mock_get_client.return_value = mock_client
        
        # 设置测试用的API配置
        self.api_service.config.doubao_api_key = "test_key"
        self.api_service.config.api_type = "doubao"
        success, message = self.api_service.test_connection("doubao")
        self.assertFalse(success)
        self.assertIn("API错误", message)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = FileProcessor()
        self.api_service = APIService()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # 2. 加载文件
        file_items = self.processor.load_files(self.temp_dir)
        self.assertEqual(len(file_items), 1)
        
        # 3. 创建分类目录
        result = self.processor.create_classification_directories()
        self.assertTrue(result)
        
        # 4. 验证目录结构
        for period in ["永久", "长期", "短期"]:
            period_path = os.path.join(self.temp_dir, period)
            self.assertTrue(os.path.exists(period_path))


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestConfigManager,
        TestFileProcessor,
        TestFileItem,
        TestAPIService,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("开始运行测试...")
    success = run_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败！")
    
    print("\n测试完成。") 