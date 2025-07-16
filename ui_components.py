"""
UI组件模块
封装常用的UI组件和对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable, Dict, Any
from config import config_manager, APIConfig
from api_service import api_service
import threading


class ModernButton(tk.Button):
    """现代化按钮组件"""
    
    def __init__(self, parent, **kwargs):
        """初始化现代化按钮"""
        # 设置默认样式
        default_style = {
            "font": ("微软雅黑", 10),
            "relief": "flat",
            "bd": 0,
            "padx": 15,
            "pady": 8,
            "cursor": "hand2"
        }
        default_style.update(kwargs)
        super().__init__(parent, **default_style)
        
        # 绑定鼠标事件
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """鼠标进入事件"""
        self.config(bg="#e0e0e0")
    
    def _on_leave(self, event):
        """鼠标离开事件"""
        self.config(bg="SystemButtonFace")


class APIConfigDialog:
    """API配置对话框"""
    
    def __init__(self, parent):
        """初始化API配置对话框"""
        self.parent = parent
        self.result = None
        self._create_dialog()
    
    def _create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("API配置设置")
        self.dialog.geometry("600x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        self._create_widgets()
        self._load_current_config()
    
    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="API配置设置", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # API类型选择
        api_frame = ttk.LabelFrame(main_frame, text="API类型", padding="10")
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.api_type_var = tk.StringVar(value="doubao")
        ttk.Radiobutton(api_frame, text="豆包API", variable=self.api_type_var, 
                       value="doubao", command=self._on_api_type_change).pack(anchor=tk.W)
        ttk.Radiobutton(api_frame, text="DeepSeek API", variable=self.api_type_var, 
                       value="deepseek", command=self._on_api_type_change).pack(anchor=tk.W)
        
        # API Key输入
        key_frame = ttk.LabelFrame(main_frame, text="API密钥", padding="10")
        key_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 豆包API Key
        ttk.Label(key_frame, text="豆包API Key:").pack(anchor=tk.W)
        self.doubao_entry = ttk.Entry(key_frame, width=60, show="*")
        self.doubao_entry.pack(fill=tk.X, pady=(5, 10))
        
        # DeepSeek API Key
        ttk.Label(key_frame, text="DeepSeek API Key:").pack(anchor=tk.W)
        self.deepseek_entry = ttk.Entry(key_frame, width=60, show="*")
        self.deepseek_entry.pack(fill=tk.X, pady=(5, 10))
        
        # 显示/隐藏密码按钮
        self.show_password_var = tk.BooleanVar()
        ttk.Checkbutton(key_frame, text="显示密码", variable=self.show_password_var, 
                       command=self._toggle_password_visibility).pack(anchor=tk.W)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 测试按钮
        self.test_button = ModernButton(button_frame, text="测试连接", 
                                       command=self._test_connection)
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存按钮
        self.save_button = ModernButton(button_frame, text="保存配置", 
                                       command=self._save_config)
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        self.cancel_button = ModernButton(button_frame, text="取消", 
                                         command=self._cancel)
        self.cancel_button.pack(side=tk.RIGHT)
    
    def _load_current_config(self):
        """加载当前配置"""
        current_config = config_manager.get_api_config()
        self.api_type_var.set(current_config.api_type)
        self.doubao_entry.insert(0, current_config.doubao_api_key)
        self.deepseek_entry.insert(0, current_config.deepseek_api_key)
    
    def _on_api_type_change(self):
        """API类型改变事件"""
        # 可以在这里添加类型切换时的逻辑
        pass
    
    def _toggle_password_visibility(self):
        """切换密码显示/隐藏"""
        show = self.show_password_var.get()
        char = "" if show else "*"
        self.doubao_entry.config(show=char)
        self.deepseek_entry.config(show=char)
    
    def _test_connection(self):
        """测试API连接"""
        def run_test():
            self.status_var.set("正在测试连接...")
            self.test_button.config(state=tk.DISABLED)
            
            api_type = self.api_type_var.get()
            success, message = api_service.test_connection(api_type)
            
            self.dialog.after(0, lambda: self._test_complete(success, message))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def _test_complete(self, success: bool, message: str):
        """测试完成回调"""
        self.test_button.config(state=tk.NORMAL)
        if success:
            self.status_var.set("✓ 连接测试成功")
            messagebox.showinfo("测试结果", f"连接测试成功！\n{message}")
        else:
            self.status_var.set("✗ 连接测试失败")
            messagebox.showerror("测试结果", f"连接测试失败！\n{message}")
    
    def _save_config(self):
        """保存配置"""
        try:
            api_config = APIConfig(
                doubao_api_key=self.doubao_entry.get().strip(),
                deepseek_api_key=self.deepseek_entry.get().strip(),
                api_type=self.api_type_var.get()
            )
            
            # 更新配置
            if config_manager.update_api_config(api_config):
                api_service.update_config(api_config)
                self.result = api_config
                messagebox.showinfo("保存成功", "API配置已保存")
                self.dialog.destroy()
            else:
                messagebox.showerror("保存失败", "配置保存失败，请检查文件权限")
                
        except Exception as e:
            messagebox.showerror("保存失败", f"保存配置时发生错误：{str(e)}")
    
    def _cancel(self):
        """取消操作"""
        self.dialog.destroy()
    
    def show(self) -> Optional[APIConfig]:
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


class ClassificationRulesDialog:
    """分类规则设置对话框"""
    
    def __init__(self, parent):
        """初始化分类规则设置对话框"""
        self.parent = parent
        self.result = None
        self._create_dialog()
    
    def _create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("分类规则设置")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"900x700+{x}+{y}")
        
        self._create_widgets()
        self._load_current_rules()
    
    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="分类规则设置", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 说明文本
        info_label = ttk.Label(main_frame, 
                              text="请输入自定义分类规则（支持换行，当前内容为预设规则）：",
                              font=("微软雅黑", 10))
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 文本编辑区域
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文本编辑器
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10),
                                  yscrollcommand=scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 重置按钮
        self.reset_button = ModernButton(button_frame, text="重置为默认规则", 
                                        command=self._reset_rules)
        self.reset_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存按钮
        self.save_button = ModernButton(button_frame, text="保存规则", 
                                       command=self._save_rules)
        self.save_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 取消按钮
        self.cancel_button = ModernButton(button_frame, text="取消", 
                                         command=self._cancel)
        self.cancel_button.pack(side=tk.RIGHT)
    
    def _load_current_rules(self):
        """加载当前规则"""
        current_rules = config_manager.load_classification_rules()
        self.text_widget.insert(tk.END, current_rules)
    
    def _reset_rules(self):
        """重置为默认规则"""
        if messagebox.askyesno("确认重置", "确定要重置为默认分类规则吗？"):
            self.text_widget.delete(1.0, tk.END)
            default_rules = config_manager.load_classification_rules()
            self.text_widget.insert(tk.END, default_rules)
    
    def _save_rules(self):
        """保存规则"""
        try:
            new_rules = self.text_widget.get(1.0, tk.END).strip()
            
            if config_manager.save_classification_rules(new_rules):
                self.result = new_rules
                messagebox.showinfo("保存成功", "分类规则已保存")
                self.dialog.destroy()
            else:
                messagebox.showerror("保存失败", "规则保存失败，请检查文件权限")
                
        except Exception as e:
            messagebox.showerror("保存失败", f"保存规则时发生错误：{str(e)}")
    
    def _cancel(self):
        """取消操作"""
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


class ProgressDialog:
    """进度对话框"""
    
    def __init__(self, parent, title="处理中"):
        """初始化进度对话框"""
        self.parent = parent
        self.title = title
        self._create_dialog()
    
    def _create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态标签
        self.status_var = tk.StringVar(value="准备中...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                font=("微软雅黑", 10))
        status_label.pack(pady=(0, 15))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=300)
        self.progress_bar.pack(pady=(0, 15))
        
        # 百分比标签
        self.percent_var = tk.StringVar(value="0%")
        percent_label = ttk.Label(main_frame, textvariable=self.percent_var, 
                                 font=("微软雅黑", 9))
        percent_label.pack()
    
    def update_progress(self, progress: float, status: str = None):
        """更新进度"""
        self.progress_var.set(progress)
        self.percent_var.set(f"{progress:.1f}%")
        if status:
            self.status_var.set(status)
        self.dialog.update()
    
    def close(self):
        """关闭对话框"""
        self.dialog.destroy()


class HelpDialog:
    """帮助对话框"""
    
    def __init__(self, parent, title: str, content: str):
        """初始化帮助对话框"""
        self.parent = parent
        self.title = title
        self.content = content
        self._create_dialog()
    
    def _create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text=self.title, font=("微软雅黑", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(content_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文本显示
        text_widget = tk.Text(content_frame, wrap=tk.WORD, font=("微软雅黑", 10),
                             yscrollcommand=scrollbar.set, state=tk.DISABLED)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # 插入内容
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, self.content)
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        close_button = ModernButton(main_frame, text="关闭", command=self.dialog.destroy)
        close_button.pack()
    
    def show(self):
        """显示对话框"""
        self.dialog.wait_window() 