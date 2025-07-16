#!/usr/bin/env python3
"""
文件自动分类工具启动脚本
提供多种运行选项和错误处理
"""

import sys
import os
import traceback
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'openai',
        'pydantic', 
        'loguru',
        'tkinter'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True

def setup_environment():
    """设置运行环境"""
    # 添加当前目录到Python路径
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # 设置工作目录
    os.chdir(current_dir)

def run_original_version():
    """运行原始版本"""
    try:
        from main import FileClassifierApp
        import tkinter as tk
        
        root = tk.Tk()
        app = FileClassifierApp(root)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 运行原始版本失败: {e}")
        traceback.print_exc()

def run_optimized_version():
    """运行优化版本"""
    try:
        from main_optimized import FileClassifierApp
        import tkinter as tk
        
        root = tk.Tk()
        app = FileClassifierApp(root)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 运行优化版本失败: {e}")
        traceback.print_exc()

def run_tests():
    """运行测试"""
    try:
        from test_app import run_tests
        
        print("🧪 开始运行测试...")
        success = run_tests()
        
        if success:
            print("✅ 所有测试通过！")
        else:
            print("❌ 部分测试失败！")
            
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        traceback.print_exc()

def show_help():
    """显示帮助信息"""
    help_text = """
文件自动分类工具启动脚本

用法:
    python run.py [选项]

选项:
    -o, --original     运行原始版本 (V1.41)
    -n, --new          运行优化版本 (V2.0) [默认]
    -t, --test         运行测试
    -h, --help         显示此帮助信息

示例:
    python run.py              # 运行优化版本
    python run.py -o           # 运行原始版本
    python run.py -t           # 运行测试
    python run.py --help       # 显示帮助

注意事项:
    1. 首次运行前请确保已安装所有依赖包
    2. 运行前请配置好API密钥
    3. 建议使用优化版本以获得更好的体验
    """
    print(help_text)

def main():
    """主函数"""
    print("🚀 文件自动分类工具启动器")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查依赖包
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 解析命令行参数
    args = sys.argv[1:]
    
    if not args or '-h' in args or '--help' in args:
        show_help()
        return
    
    if '-t' in args or '--test' in args:
        run_tests()
        return
    
    if '-o' in args or '--original' in args:
        print("📁 启动原始版本 (V1.41)...")
        run_original_version()
    else:
        print("🚀 启动优化版本 (V2.0)...")
        run_optimized_version()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        traceback.print_exc()
        sys.exit(1) 