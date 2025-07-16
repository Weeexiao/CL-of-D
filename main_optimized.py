"""
文件自动分类工具 - 优化版本
主程序入口
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import Optional

# 导入自定义模块
from config import config_manager
from logger import log_manager
from api_service import api_service
from file_processor import file_processor
from ui_components import (
    ModernButton, APIConfigDialog, ClassificationRulesDialog, 
    ProgressDialog, HelpDialog
)

# 获取日志记录器
logger = log_manager.get_logger()


class FileClassifierApp:
    """文件分类应用程序主类"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化应用程序
        
        Args:
            root: 主窗口对象
        """
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.create_menu()
        self.create_main_ui()
        self.create_status_bar()
        
        # 加载配置
        self.load_configuration()
        
        logger.info("应用程序初始化完成")
    
    def setup_window(self):
        """设置主窗口"""
        self.root.title("文件自动分类工具 V2.0 - 优化版本")
        
        # 获取配置的窗口尺寸
        config = config_manager.load_config()
        self.root.geometry(f"{config.window_width}x{config.window_height}")
        
        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (config.window_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (config.window_height // 2)
        self.root.geometry(f"{config.window_width}x{config.window_height}+{x}+{y}")
        
        # 设置最小尺寸
        self.root.minsize(600, 400)
    
    def setup_variables(self):
        """设置变量"""
        self.source_folder = ""
        self.classification_rules = ""
        self.progress_dialog: Optional[ProgressDialog] = None
        
        # 版本信息
        self.version_info = {
            "V2.0": {
                "title": "V2.0 优化版本（当前版本）",
                "details": [
                    "1. 代码架构重构：采用模块化设计，提高代码可维护性",
                    "2. 性能优化：异步处理和批量操作，提升处理效率",
                    "3. 用户体验改进：现代化UI组件和更好的交互体验",
                    "4. 错误处理完善：更完善的异常处理和日志记录",
                    "5. 配置管理优化：使用Pydantic进行配置验证和管理",
                    "6. 日志系统升级：使用Loguru进行结构化日志记录"
                ]
            },
            "V1.41": {
                "title": "V1.41 更新说明",
                "details": [
                    "1. 新增开发目的菜单",
                    "2. 优化开发目的文档排版"
                ]
            }
        }
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开文件夹", command=self.choose_folder)
        file_menu.add_command(label="开始分类", command=self.start_classification)
        file_menu.add_separator()
        file_menu.add_command(label="导出结果", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="API配置", command=self.show_api_config)
        settings_menu.add_command(label="分类规则", command=self.show_classification_rules)
        menubar.add_cascade(label="设置", menu=settings_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="常见问题", command=self.show_faq)
        help_menu.add_command(label="获取豆包API", command=self.show_get_doubao_api)
        help_menu.add_command(label="获取DeepSeek API", command=self.show_get_deepseek_api)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        # 关于菜单
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="版本信息", command=self.show_version_info)
        about_menu.add_command(label="开发目的", command=self.show_development_purpose)
        about_menu.add_command(label="作者信息", command=self.show_author)
        menubar.add_cascade(label="关于", menu=about_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_ui(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具栏
        self.create_toolbar(main_frame)
        
        # 文件列表区域
        self.create_file_list_area(main_frame)
        
        # 进度条
        self.create_progress_bar(main_frame)
    
    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 打开文件夹按钮
        self.open_button = ModernButton(toolbar, text="📁 打开文件夹", 
                                       command=self.choose_folder)
        self.open_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 开始分类按钮
        self.classify_button = ModernButton(toolbar, text="🚀 开始分类", 
                                           command=self.start_classification)
        self.classify_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 设置按钮
        self.settings_button = ModernButton(toolbar, text="⚙️ 设置", 
                                           command=self.show_settings_menu)
        self.settings_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 帮助按钮
        self.help_button = ModernButton(toolbar, text="❓ 帮助", 
                                       command=self.show_help)
        self.help_button.pack(side=tk.LEFT)
        
        # 右侧状态显示
        self.status_label = ttk.Label(toolbar, text="就绪", font=("微软雅黑", 9))
        self.status_label.pack(side=tk.RIGHT)
    
    def create_file_list_area(self, parent):
        """创建文件列表区域"""
        # 文件列表框架
        list_frame = ttk.LabelFrame(parent, text="文件列表", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文件显示区域
        self.file_display = tk.Text(list_frame, yscrollcommand=scrollbar.set, 
                                   wrap=tk.WORD, font=("微软雅黑", 10))
        self.file_display.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_display.yview)
        
        # 配置文本标签
        self.file_display.tag_configure("success", foreground="green")
        self.file_display.tag_configure("error", foreground="red")
        self.file_display.tag_configure("info", foreground="blue")
    
    def create_progress_bar(self, parent):
        """创建进度条"""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, 
                                   anchor=tk.W, font=("微软雅黑", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_configuration(self):
        """加载配置"""
        try:
            # 加载应用配置
            config = config_manager.load_config()
            
            # 加载分类规则
            self.classification_rules = config_manager.load_classification_rules()
            
            logger.info("配置加载完成")
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            messagebox.showerror("配置错误", f"配置加载失败: {str(e)}")
    
    def choose_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择需要分类的文件夹")
        if folder:
            self.source_folder = folder
            
            # 加载文件
            file_items = file_processor.load_files(folder)
            
            if file_items:
                self.update_file_display()
                self.update_status(f"已加载文件夹：{folder}，共{len(file_items)}个文件/文件夹")
                logger.info(f"文件夹加载成功: {folder}, 文件数量: {len(file_items)}")
            else:
                self.update_status("文件夹加载失败或文件夹为空")
                logger.warning(f"文件夹加载失败: {folder}")
    
    def update_file_display(self):
        """更新文件列表显示"""
        self.file_display.delete(1.0, tk.END)
        
        if not file_processor.file_items:
            self.file_display.insert(tk.END, "未加载文件")
            return
        
        for item in file_processor.file_items:
            self.file_display.insert(tk.END, f"{item.entry_type}: {item.name}\n")
    
    def start_classification(self):
        """开始分类"""
        if not self.source_folder:
            messagebox.showwarning("提示", "请先选择需要分类的文件夹")
            return
        
        if not file_processor.file_items:
            messagebox.showwarning("提示", "没有可分类的文件")
            return
        
        # 检查API配置
        api_config = config_manager.get_api_config()
        if not api_config.doubao_api_key and not api_config.deepseek_api_key:
            messagebox.showerror("配置错误", "请先配置API密钥")
            return
        
        # 在新线程中执行分类
        threading.Thread(target=self._run_classification, daemon=True).start()
    
    def _run_classification(self):
        """执行分类任务"""
        try:
            # 创建进度对话框
            self.progress_dialog = ProgressDialog(self.root, "文件分类中")
            
            def progress_callback(progress: float, status: str):
                """进度回调函数"""
                self.root.after(0, lambda: self._update_progress(progress, status))
            
            # 执行分类
            result = file_processor.process_all_files(
                self.classification_rules, 
                progress_callback
            )
            
            # 完成处理
            self.root.after(0, lambda: self._classification_complete(result))
            
        except Exception as e:
            logger.error(f"分类过程发生错误: {e}")
            self.root.after(0, lambda: self._classification_error(str(e)))
    
    def _update_progress(self, progress: float, status: str):
        """更新进度"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(progress, status)
        
        self.progress_var.set(progress)
        self.update_status(status)
    
    def _classification_complete(self, result: dict):
        """分类完成处理"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.progress_var.set(100)
        
        if result.get("success"):
            success_count = result["success_count"]
            total_count = result["total_files"]
            duration = result["duration"]
            
            message = f"分类完成！成功处理{success_count}个，{total_count-success_count}个失败，耗时{duration:.2f}秒"
            self.update_status(message)
            
            messagebox.showinfo("分类完成", message)
            logger.info(f"分类完成 - 成功: {success_count}/{total_count}, 耗时: {duration:.2f}秒")
        else:
            error_msg = result.get("error", "未知错误")
            self.update_status(f"分类失败: {error_msg}")
            messagebox.showerror("分类失败", f"分类过程中发生错误: {error_msg}")
            logger.error(f"分类失败: {error_msg}")
    
    def _classification_error(self, error: str):
        """分类错误处理"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.update_status(f"分类失败: {error}")
        messagebox.showerror("分类失败", f"分类过程中发生错误: {error}")
    
    def show_api_config(self):
        """显示API配置对话框"""
        dialog = APIConfigDialog(self.root)
        result = dialog.show()
        
        if result:
            logger.info("API配置已更新")
    
    def show_classification_rules(self):
        """显示分类规则设置对话框"""
        dialog = ClassificationRulesDialog(self.root)
        result = dialog.show()
        
        if result:
            self.classification_rules = result
            logger.info("分类规则已更新")
    
    def show_settings_menu(self):
        """显示设置菜单"""
        # 这里可以创建一个设置菜单对话框
        pass
    
    def export_results(self):
        """导出结果"""
        if not file_processor.file_items:
            messagebox.showwarning("提示", "没有可导出的结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="导出结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if file_processor.export_results(file_path):
                messagebox.showinfo("导出成功", f"结果已导出到: {file_path}")
            else:
                messagebox.showerror("导出失败", "结果导出失败")
    
    def show_help(self):
        """显示帮助"""
        help_content = """使用说明：

一、基本操作
1. 打开文件夹：点击「文件→打开文件夹」或工具栏按钮选择需要分类的目录
2. 开始分类：确认文件列表后，点击「文件→开始分类」或工具栏按钮启动分类流程
3. 导出结果：分类完成后可以导出详细的处理结果

二、API配置
1. 点击「设置→API配置」进行API密钥设置
2. 支持豆包API和DeepSeek API，可自由切换
3. 配置会自动保存，下次启动无需重复设置

三、分类规则设置
1. 点击「设置→分类规则」自定义分类规则
2. 规则会自动保存到本地文件
3. 支持重置为默认规则

四、注意事项
1. 确保API密钥有效且有足够的调用额度
2. 分类过程中请勿关闭程序
3. 建议在分类前备份重要文件"""
        
        dialog = HelpDialog(self.root, "使用说明", help_content)
        dialog.show()
    
    def show_faq(self):
        """显示常见问题"""
        faq_content = """常见问题解答：

Q: 为什么文件没被分类？
A: 可能是API识别失败或文件名无法匹配规则，请检查API配置和分类规则

Q: 如何修改API配置？
A: 点击「设置→API配置」进行修改，支持豆包和DeepSeek两种API

Q: 如何修改分类规则？
A: 点击「设置→分类规则」，在弹出窗口中编辑规则后保存即可

Q: 分类规则会保存吗？
A: 会保存，修改的规则会自动保存到本地文件，下次启动自动加载

Q: 支持哪些文件类型？
A: 支持所有文件类型，分类基于文件名和内容关键词

Q: 分类过程中可以中断吗？
A: 可以，但建议等待当前文件处理完成后再中断"""
        
        dialog = HelpDialog(self.root, "常见问题", faq_content)
        dialog.show()
    
    def show_get_doubao_api(self):
        """显示获取豆包API说明"""
        content = """获取豆包API Key步骤：

1. 访问火山引擎官网：https://www.volcengine.com/
2. 注册/登录火山引擎账号
3. 进入「豆包大模型」产品页面，申请API调用权限
4. 权限通过后，在控制台「API Key管理」页面获取API Key
5. 注意：需确保账号已完成企业实名认证（部分功能需要）"""
        
        dialog = HelpDialog(self.root, "获取豆包API", content)
        dialog.show()
    
    def show_get_deepseek_api(self):
        """显示获取DeepSeek API说明"""
        content = """获取DeepSeek API的步骤：

1. 注册/登录DeepSeek开发者平台
   访问官网：https://www.deepseek.com/，点击「开发者平台」注册或登录账号

2. 申请API Key
   在控制台中找到「API管理」或「密钥管理」页面，申请新的API Key（需完成企业/个人实名认证）

3. 查看API文档
   成功申请后，可在「文档中心」查看详细的API调用说明

4. 测试API连接
   在本工具的「设置-API配置」中，选择DeepSeek API类型，输入申请的Key后点击测试"""
        
        dialog = HelpDialog(self.root, "获取DeepSeek API", content)
        dialog.show()
    
    def show_version_info(self):
        """显示版本信息"""
        content = "版本信息：\n\n"
        
        for version, info in self.version_info.items():
            content += f"{info['title']}\n"
            content += "-" * 30 + "\n"
            for detail in info['details']:
                content += f"• {detail}\n"
            content += "\n"
        
        dialog = HelpDialog(self.root, "版本信息", content)
        dialog.show()
    
    def show_development_purpose(self):
        """显示开发目的"""
        content = """开发目的与软件简介：

【开发目的】
本工具旨在解决企业/机构日常文件归档效率低、分类标准不统一的问题。通过自动化识别文件内容关键词，结合预设的部门分类规则和保管期限规则，实现文件的智能分类与归档，减少人工操作失误，提升档案管理的规范化水平。

【软件简介】
「文件自动分类工具」是一款基于AI大语言模型的智能文件管理工具，核心功能包括：
• 多维度分类：支持按「部门归属」和「保管期限」双维度分类
• 规则自定义：提供分类规则设置功能，用户可根据实际业务需求修改规则
• 多API支持：兼容豆包和DeepSeek大语言模型，支持灵活切换API类型
• 可视化操作：提供文件列表可视化展示、实时分类日志输出等交互功能
• 配置持久化：自动保存API Key、分类规则等配置，避免重复设置

【适用场景】
• 企业行政档案管理
• 项目资料归档
• 事业单位文件整理
• 其他需要规范化分类的场景"""
        
        dialog = HelpDialog(self.root, "开发目的", content)
        dialog.show()
    
    def show_author(self):
        """显示作者信息"""
        messagebox.showinfo("作者信息", 
                           "开发者：史智阳\n"
                           "联系邮箱：562052228@qq.com\n"
                           "版本：V2.0 优化版本")
    
    def update_status(self, message: str):
        """更新状态信息"""
        self.status_bar.config(text=message)
        self.status_label.config(text=message)


def main():
    """主函数"""
    try:
        # 创建主窗口
        root = tk.Tk()
        
        # 创建应用程序实例
        app = FileClassifierApp(root)
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        messagebox.showerror("启动错误", f"应用程序启动失败: {str(e)}")


if __name__ == "__main__":
    main() 