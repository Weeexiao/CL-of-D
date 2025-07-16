import os
import shutil
import threading
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from openai import OpenAI
import json  # 新增：导入json模块
import datetime  # 新增：导入datetime模块用于日志

class FileClassifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件自动分类工具V1.41-有问题联系作者：史智阳 QQ：562052228")
        self.root.geometry("800x600")
        
        # 全局变量（新增分类规则存储）
        self.source_folder = ""
        # 原 api_key 改为豆包专用 Key（初始值从配置加载）
        self.doubao_api_key = ""
        self.deepseek_api_key = ""
        self.api_type = "doubao"  # 默认豆包API
        
        # 加载API配置（新增）
        self.load_config()
        
        self.file_list = []
        # 初始化分类规则（优先读取本地文件，无则使用预设）
        self.rules_file = os.path.join(os.path.dirname(__file__), "rules.txt")  # 规则文件路径
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    self.classification_rules = f.read().strip()
            except Exception as e:
                messagebox.showerror("规则加载失败", f"读取本地规则文件失败：{str(e)}，将使用预设规则")
                # 保持完整预设内容（与读取失败时一致）
                self.classification_rules = """部门识别规则：文件内容或标题含公文、机要、保密、档案、印信、信访、综合治理、会议管理、数字化管理、党建、工会、共青团、企业文化宣传、社会责任、扶贫等关键词或相关内容的归办公室（党委办公室、党委工作部）；含劳动用工、人事管理、薪酬绩效、社保福利、教育培训、职业技能鉴定、劳动合同、职工名册、干部任免等关键词或相关内容的归人力资源部（党委组织部）；含财务预算、决算、税务管理、会计核算、财务分析报告、银行对账单、纳税申报表等关键词或相关内容的归财务资金部；含审计通知书、审计报告、纪检监督、aceeption、违纪案件查处、内控报告等关键词或相关内容的归审计监督部(纪委办公室)；含合同管理、工程预算、成本控制、计量支付、变更索赔、法律纠纷、诉讼调解书等关键词或相关内容的归经营管理部（法律合约部）；含项目管理、施工许可、工程验收、生产计划、进度控制、信用评价、项目经理部成立等关键词或相关内容的归生产管理部；含物资采购、机械设备管理、采购合同、资产购置、特种设备维保、量价成本管控等关键词或相关内容的归物资装备部；含安全生产、职业健康、应急救援预案、环保规划、节能减排、事故调查报告等关键词或相关内容的归安全环保管理部；含科技研发、专利管理、工法申报、质量管理、BIM技术、工程试验检测、高新技术企业申报等关键词或相关内容的归技术质量部；含市场开发计划、项目投标、招标文件、中标通知书、区域办事处设立、履约保函等关键词或相关内容的归市场开发部；未命中部门专属关键词或相关内容的归各部门通用归档范围。保管期限分类规则：文件内容或标题满足涉及重要事项的会议文件、上级机关重要文件、公司战略规划、资质管理、重大合同协议、人事档案核心材料、财务决算、税务年报、会计档案保管清册、重大事件记录、重要声像资料、电子文件等条件的永久保管；满足一般会议文件、非核心业务文件、培训资料、对标考察报告、对标检查材料、非重大奖项荣誉、一般合同协议、设备购置计划、非核心财务文件等条件的30年保管；满足未通过的文件、日常事务性材料、短期业务记录、非重要载体材料、基层事务性文件等条件的10年保管，优先匹配永久规则，其次30年，最后10年。"""
        else:
            # 无本地文件时使用完整预设内容（与读取失败时一致）
            self.classification_rules = """部门识别规则：文件内容或标题含公文、机要、保密、档案、印信、信访、综合治理、会议管理、数字化管理、党建、工会、共青团、企业文化宣传、社会责任、扶贫等关键词或相关内容的归办公室（党委办公室、党委工作部）；含劳动用工、人事管理、薪酬绩效、社保福利、教育培训、职业技能鉴定、劳动合同、职工名册、干部任免等关键词或相关内容的归人力资源部（党委组织部）；含财务预算、决算、税务管理、会计核算、财务分析报告、银行对账单、纳税申报表等关键词或相关内容的归财务资金部；含审计通知书、审计报告、纪检监督、aceeption、违纪案件查处、内控报告等关键词或相关内容的归审计监督部(纪委办公室)；含合同管理、工程预算、成本控制、计量支付、变更索赔、法律纠纷、诉讼调解书等关键词或相关内容的归经营管理部（法律合约部）；含项目管理、施工许可、工程验收、生产计划、进度控制、信用评价、项目经理部成立等关键词或相关内容的归生产管理部；含物资采购、机械设备管理、采购合同、资产购置、特种设备维保、量价成本管控等关键词或相关内容的归物资装备部；含安全生产、职业健康、应急救援预案、环保规划、节能减排、事故调查报告等关键词或相关内容的归安全环保管理部；含科技研发、专利管理、工法申报、质量管理、BIM技术、工程试验检测、高新技术企业申报等关键词或相关内容的归技术质量部；含市场开发计划、项目投标、招标文件、中标通知书、区域办事处设立、履约保函等关键词或相关内容的归市场开发部；未命中部门专属关键词或相关内容的归各部门通用归档范围。保管期限分类规则：文件内容或标题满足涉及重要事项的会议文件、上级机关重要文件、公司战略规划、资质管理、重大合同协议、人事档案核心材料、财务决算、税务年报、会计档案保管清册、重大事件记录、重要声像资料、电子文件等条件的永久保管；满足一般会议文件、非核心业务文件、培训资料、对标考察报告、对标检查材料、非重大奖项荣誉、一般合同协议、设备购置计划、非核心财务文件等条件的30年保管；满足未通过的文件、日常事务性材料、短期业务记录、非重要载体材料、基层事务性文件等条件的10年保管，优先匹配永久规则，其次30年，最后10年。"""

        # 新增：版本信息字典（保留所有历史版本）
        self.version_info = {
            "V1.41": {
                "title": "V1.41 更新说明（当前版本，20250610）",
                "details": [
                    "1. 新增开发目的菜单：在顶部菜单栏-关于选项中添加「开发目的」二级菜单，提供工具开发背景和功能简介",
                    "2. 优化开发目的文档排版：通过标题层级、项目符号和空行提升内容可读性，增强用户对工具定位的理解"
                ]
            },
            "V1.4": {
                "title": "V1.4 更新说明（20250610）",
                "details": [
                    "1. 修复API配置保存问题：新增`json`模块导入，解决`name 'json' is not defined`错误",
                    "2. 完善配置持久化逻辑：初次运行保存API时自动生成`config.json`文件（与工具同目录）",
                    "3. 优化配置读写稳定性：新增异常处理，保存/加载配置失败时提示具体错误信息"
                ]
            },
            "V1.3": {
                "title": "V1.3 更新说明（20250610）",
                "details": [
                    "1. 新增DeepSeek API支持：支持通过选择框切换使用豆包API或DeepSeek API",
                    "2. 优化API设置界面：新增DeepSeek API Key输入框，支持双API Key管理",
                    "3. 增强API测试功能：测试按钮支持对当前选择的API类型进行连接测试",
                    "4. 模型适配调整：根据API类型自动选择对应模型（豆包-pro-32k-241215/DeepSeek-chat）"
                ]
            },
            "V1.2": {
                "title": "V1.2 更新说明（20250609）",
                "details": [
                    "1. 新增实时日志显示：分类过程中文件列表区域会滚动输出API交互关键信息（请求内容/返回结果）",
                    "2. 优化分类规则设置界面，支持更友好的长文本编辑",
                    "3. 修复部门子目录创建时的权限错误",
                    "4. 新增分类规则持久化功能：修改的规则会保存到本地rules.txt文件（与工具同目录），下次启动自动加载最新规则"
                ]
            },
            "V1.1": {
                "title": "V1.1 更新说明（20250609）",
                "details": [
                    "1. 新增分类规则自定义功能（设置-分类规则设置）",
                    "2. 支持文件/文件夹类型显示（文件列表区域）",
                    "3. 增强API调试日志（显示请求内容、原始响应、提取结果）",
                    "4. 优化分类逻辑（支持部门子目录自动创建）"
                ]
            },
            "V1.0": {
                "title": "V1.0 初始版本（20250609）",
                "details": ["实现基本分类功能"]
            }
        }
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建主界面组件
        self.create_main_ui()
        
        # 创建进度条
        self.progress_frame = Frame(root)
        self.progress_frame.pack(side=BOTTOM, fill=X, padx=10, pady=5)
        self.progress_var = DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=X)

        # 创建状态栏
        self.status_bar = Label(root, text="就绪", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

    def create_menu(self):
        """创建顶部菜单栏"""
        menubar = Menu(self.root)
        
        # 开始菜单
        start_menu = Menu(menubar, tearoff=0)
        start_menu.add_command(label="打开文件夹", command=self.choose_folder)
        start_menu.add_command(label="开始分类", command=self.start_classification_thread)
        start_menu.add_separator()
        start_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="开始", menu=start_menu)
        
        # 设置菜单
        setting_menu = Menu(menubar, tearoff=0)
        setting_menu.add_command(label="API Key设置", command=self.set_api_key)
        # 新增分类规则设置菜单项
        setting_menu.add_command(label="分类规则设置", command=self.set_classification_rules)
        menubar.add_cascade(label="设置", menu=setting_menu)
        
        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="常见问题", command=self.show_faq)
        help_menu.add_command(label="如何获取豆包API", command=self.show_get_api)
        # 新增：DeepSeek API获取说明菜单项
        help_menu.add_command(label="如何获取DeepSeek API", command=self.show_get_deepseek_api)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        # 关于菜单
        about_menu = Menu(menubar, tearoff=0)
        about_menu.add_command(label="作者信息", command=self.show_author)
        about_menu.add_command(label="版权声明", command=self.show_copyright)
        about_menu.add_command(label="更新说明", command=self.show_update)
        # 新增：开发目的菜单项
        about_menu.add_command(label="开发目的", command=self.show_development_purpose)
        menubar.add_cascade(label="关于", menu=about_menu)
        
        self.root.config(menu=menubar)

    def create_main_ui(self):
        """创建主界面文件列表区域"""
        frame = Frame(self.root)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 滚动条
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 文件列表显示（使用Text组件支持换行）
        self.file_display = Text(frame, yscrollcommand=scrollbar.set, wrap=WORD)
        self.file_display.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.file_display.yview)
        
        # 新增：配置绿色字体标签（用于提取结果）
        self.file_display.tag_configure("green", foreground="green")

    def choose_folder(self):
        """选择需要分类的文件夹（修改：同时获取文件和子文件夹）"""
        folder = filedialog.askdirectory(title="选择需要分类的文件夹")
        if folder:
            self.source_folder = folder
            # 获取所有文件和子文件夹（排除分类目标文件夹）
            entries = [f for f in os.listdir(folder) 
                      if f not in ["永久", "长期", "短期"]]  # 排除已存在的分类文件夹
            self.file_list = []
            for entry in entries:
                entry_path = os.path.join(folder, entry)
                entry_type = "文件" if os.path.isfile(entry_path) else "文件夹"
                self.file_list.append({
                    "name": entry,
                    "type": entry_type,
                    "path": entry_path
                })
            self.update_file_display()
            self.status_bar.config(text=f"已加载文件夹：{folder}，共{len(self.file_list)}个文件/文件夹")

    def update_file_display(self):
        """更新文件列表显示（修改：显示文件/文件夹类型）"""
        self.file_display.delete(1.0, END)
        for item in self.file_list:
            self.file_display.insert(END, f"{item['type']}: {item['name']}\n")

    def start_classification(self):
        """执行文件分类核心逻辑（支持双API）"""
        self.status_bar.config(text="正在初始化API连接...")
        self.root.after(0, self.file_display.delete, 1.0, END)
        
        try:
            if self.api_type == "doubao":
                # 使用豆包API
                client = OpenAI(
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                    api_key=self.doubao_api_key
                )
            else:
                # 使用DeepSeek API（根据官方文档）
                client = OpenAI(
                    base_url="https://api.deepseek.com",  # 或https://api.deepseek.com/v1
                    api_key=self.deepseek_api_key
                )
        except Exception as e:
            self.status_bar.config(text=f"API连接失败：{str(e)}")
            return

        self.status_bar.config(text="正在创建分类文件夹...")
        # 先创建保管期限根目录，再创建部门子目录
        for period in ["永久", "长期", "短期"]:
            period_path = os.path.join(self.source_folder, period)
            if not os.path.exists(period_path):
                os.makedirs(period_path)

        self.status_bar.config(text="开始分类文件/文件夹...")
        # 初始化日志文件
        log_path = os.path.join(self.source_folder, "classification_log.txt")
        log_file = None
        try:
            log_file = open(log_path, "a", encoding="utf-8")
            log_file.write(f"=== {datetime.datetime.now()} 分类开始 ===\n")
        except Exception as e:
            self.status_bar.config(text=f"日志文件创建失败: {str(e)}，将继续分类但不记录日志")

        success_count = 0
        total = len(self.file_list)
        for idx, item in enumerate(self.file_list):
            # 更新进度条
            progress = (idx + 1) / total * 100
            self.root.after(0, self.progress_var.set, progress)
            self.root.after(0, self.progress_bar.update)
            entry_name = item["name"]
            entry_type = item["type"]
            entry_path = item["path"]
            
            self.status_bar.config(text=f"分类中({idx+1}/{len(self.file_list)})：{entry_type} '{entry_name}'...")
            
            # 获取"保管期限-部门"结果
            period_dept = self.get_storage_period(client, entry_name, entry_type)
            if "-" not in period_dept:
                 self.status_bar.config(text=f"分类失败：{entry_name} 格式错误")
            if log_file:
                log_file.write(f"[{datetime.datetime.now()}] 错误: {entry_type} '{entry_name}' 分类格式错误\n")
                continue
                
            period, dept = period_dept.split("-", 1)  # 分割为保管期限和部门
            
            # 创建部门子目录
            target_dir = os.path.join(self.source_folder, period, dept)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # 移动文件/文件夹到目标路径
            target_path = os.path.join(target_dir, entry_name)
            try:
                if entry_type == "文件":
                    shutil.move(entry_path, target_path)
                else:
                    shutil.move(entry_path, target_path)  # 移动文件夹
                success_count += 1
                self.status_bar.config(text=f"分类中({idx+1}/{len(self.file_list)})：{entry_type} '{entry_name}' → {period}/{dept}")
                if log_file:
                    log_file.write(f"[{datetime.datetime.now()}] 成功: {entry_type} '{entry_name}' 移动至 '{target_path}'\n")
            except Exception as e:
                self.status_bar.config(text=f"移动失败：{entry_name} - {str(e)}")
                if log_file:
                    log_file.write(f"[{datetime.datetime.now()}] 错误: {entry_type} '{entry_name}' 移动失败 - {str(e)}\n")
        
        # 完成后关闭日志文件
        if log_file:
            log_file.write(f"=== {datetime.datetime.now()} 分类完成 - 成功: {success_count}, 失败: {len(self.file_list)-success_count} ===\n\n")
            log_file.close()

        # 重置进度条
        self.root.after(0, self.progress_var.set, 0)
        self.status_bar.config(text=f"分类完成！成功处理{success_count}个，{len(self.file_list)-success_count}个未分类。日志已保存至: {log_path}")

    def get_storage_period(self, client, filename, entry_type):
        """调用API获取保管期限和部门（支持双API）"""
        try:
            # 使用实例变量中的规则（支持用户自定义）
            classification_rules = self.classification_rules  # 关键修改点
            
            # 构造发送给API的消息内容（要求返回保管期限和部门）
            request_messages = [
                {"role": "system", "content": 
                 f"你是文件分类助手，需严格根据以下规则判断{entry_type}的保管期限和所属部门：\n"
                 f"----- 分类规则 -----\n"
                 f"{classification_rules}\n"  # 使用动态规则
                 f"请分析{entry_type}名称'{filename}'的保管期限（仅返回'永久'、'长期'或'短期'，30年→长期，10年→短期）和所属部门（按规则中的部门名称），格式为'保管期限-部门'（例如'永久-办公室（党委办公室、党委工作部）'）。\n"
                 f"注意：输出必须为纯文本，禁止使用任何格式符号，仅返回'保管期限-部门'格式的结果。"},
                {"role": "user", "content": "请严格按规则分类，输出'保管期限-部门'格式的结果"}
            ]
            

            # 调用API时根据类型选择模型
            model_name = "doubao-pro-32k-241215" if self.api_type == "doubao" else "deepseek-chat"

            completion = client.chat.completions.create(
                model=model_name,
                messages=request_messages
            )

            # 新增：输出API原始响应数据
            raw_response_log = f"\n==================== API返回原数据 ====================\n" \
                               f"文件名: {filename}（类型: {entry_type}）\n" \
                               f"原数据: {str(completion)[:2000]}...（已截断，完整日志见控制台）\n" \
                               "=====================================================\n"
            self.root.after(0, self.file_display.insert, END, raw_response_log)
            self.root.after(0, self.file_display.see, END)

            # 解析提取结果并输出（绿色字体）
            result = completion.choices[0].message.content.strip()
            if "-" in result and any(period in result for period in ["永久", "长期", "短期"]):
                period, dept = result.split("-", 1)  # 分割为期限和部门
                extract_log = f"[文件名: {filename}] 「提取到的期限分类: {period}」 [提取到的部门分类: {dept}]\n"
                self.root.after(0, self.file_display.insert, END, extract_log, "green")  # 应用绿色标签
            else:
                extract_log = f"[文件名: {filename}] 未成功提取有效分类信息（结果: {result}）\n"
                self.root.after(0, self.file_display.insert, END, extract_log)
            
            self.root.after(0, self.file_display.see, END)  # 自动滚动

            # 校验结果格式（保留原有逻辑）
            if "-" in result and any(period in result for period in ["永久", "长期", "短期"]):
                return result
            else:
                return "未分类-未分类"
        except Exception as e:
            # 异常日志（保持原有格式）
            error_log = f"\n==================== API调用异常 ====================\n" \
                        f"文件名: {filename}（类型: {entry_type}）\n" \
                        f"异常信息: {str(e)}\n" \
                        "=====================================================\n"
            self.root.after(0, self.file_display.insert, END, error_log)
            self.root.after(0, self.file_display.see, END)
            return "未分类-未分类"

    def set_api_key(self):
        """设置API Key的对话框（支持豆包/DeepSeek双API）"""
        top = Toplevel(self.root)
        top.title("设置API Key")
        
        # API类型选择（Radiobutton组）
        api_type_var = StringVar(value=self.api_type)  # 绑定当前选择的API类型
        
        Label(top, text="选择API类型：", font=("微软雅黑", 12)).grid(row=0, column=0, padx=5, pady=5, sticky=W)
        Radiobutton(top, text="豆包API", variable=api_type_var, value="doubao").grid(row=0, column=1, padx=5, pady=5, sticky=W)
        Radiobutton(top, text="DeepSeek API", variable=api_type_var, value="deepseek").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        
        # 豆包API Key输入框
        Label(top, text="豆包API Key：").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        doubao_entry = Entry(top, width=50)
        doubao_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        doubao_entry.insert(0, self.doubao_api_key)  # 显示当前豆包Key
        
        # DeepSeek API Key输入框
        Label(top, text="DeepSeek API Key：").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        deepseek_entry = Entry(top, width=50)
        deepseek_entry.grid(row=2, column=1, padx=5, pady=5, columnspan=2)
        deepseek_entry.insert(0, self.deepseek_api_key)  # 显示当前DeepSeek Key
        
        # 底部状态提示栏（新增）
        status_bar = Label(top, text="就绪", bd=1, relief=SUNKEN, anchor=W, font=("微软雅黑", 10))
        status_bar.grid(row=4, column=0, columnspan=3, sticky=W+E, pady=5)  # 跨3列并横向填充

        def save_key():
            self.api_type = api_type_var.get()  # 保存选择的API类型
            self.doubao_api_key = doubao_entry.get().strip()  # 保存豆包Key
            self.deepseek_api_key = deepseek_entry.get().strip()  # 保存DeepSeek Key
            self.save_config()  # 新增：保存到配置文件
            messagebox.showinfo("保存成功", "API配置已更新并自动保存")
            top.destroy()

        def test_api():
            def run_test():
                selected_type = api_type_var.get()
                test_key = doubao_entry.get().strip() if selected_type == "doubao" else deepseek_entry.get().strip()
                
                # 在线程中更新状态为"正在测试..."
                top.after(0, lambda: status_bar.config(text="正在测试...", fg="black"))
                
                try:
                    if selected_type == "doubao":
                        client = OpenAI(
                            base_url="https://ark.cn-beijing.volces.com/api/v3",
                            api_key=test_key
                        )
                        client.chat.completions.create(
                            model="doubao-pro-32k-241215",
                            messages=[{"role": "system", "content": "测试豆包API连接"}]
                        )
                    else:
                        client = OpenAI(
                            base_url="https://api.deepseek.com",
                            api_key=test_key
                        )
                        client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "system", "content": "测试DeepSeek API连接"}]
                        )
                    # 测试成功后通过after回到主线程更新状态
                    top.after(0, lambda: status_bar.config(text="✓ 测试成功！", fg="green"))
                except Exception as e:
                    # 测试失败后通过after回到主线程更新状态
                    top.after(0, lambda: status_bar.config(text=f"✖️ 测试失败：{str(e)}", fg="red"))
                    print(f"完整异常信息：{e}")

            # 启动新线程执行测试，避免阻塞主线程
            threading.Thread(target=run_test, daemon=True).start()

        # 保存和测试按钮
        Button(top, text="保存", command=save_key).grid(row=3, column=1, padx=5, pady=10, sticky=E)
        Button(top, text="测试", command=test_api).grid(row=3, column=2, padx=5, pady=10, sticky=W)

    def start_classification_thread(self):
        """使用线程启动分类避免界面卡顿"""
        if not self.source_folder:
            messagebox.showwarning("提示", "请先选择需要分类的文件夹")
            return
        threading.Thread(target=self.start_classification, daemon=True).start()

    # 帮助与关于相关对话框
    def show_help(self):
        """显示使用说明"""
        help_text = """使用说明：
        
    一、基本操作
    1. 打开文件夹：点击「开始→打开文件夹」选择需要分类的目录。
    2. 开始分类：确认文件列表后，点击「开始→开始分类」启动分类流程。
    
    二、API配置（自动保存功能）
    1. API Key设置：点击「设置→API Key设置」，选择API类型（豆包/DeepSeek）并输入对应Key。
    2. 自动保存：设置的API Key会自动保存到工具同目录的`config.json`文件中，下次启动时自动加载，无需重复填写。
    3. 首次使用：首次设置后会生成`config.json`文件，后续启动自动读取。
    
    三、分类规则设置
    点击「设置→分类规则设置」可自定义分类规则，修改后会保存到同目录的`rules.txt`文件，下次启动自动加载。"""
        
        messagebox.showinfo("使用说明", help_text)

    def show_faq(self):
        messagebox.showinfo("常见问题", 
            "Q: 为什么文件没被分类？\nA: 可能是API识别失败或文件名无法匹配规则，可检查API Key或手动分类\n\n"
            "Q: 如何修改API Key？\nA: 点击【设置】-【API Key设置】进行修改\n\n"
            "Q: 如何修改分类规则？\nA: 点击【设置】-【分类规则设置】，在弹出窗口中编辑规则后点击保存即可\n\n"
            "Q: 修改的分类规则下次打开软件会保留吗？\nA: 会保留，修改的规则会自动保存到与工具同目录的rules.txt文件，下次启动自动加载最新规则"
        )

    def show_author(self):
        messagebox.showinfo("作者信息", "开发者：史智阳\n联系邮箱：562052228@qq.com")

    def show_copyright(self):
        messagebox.showinfo("版权声明", 
            "开发者：史智阳\n"
            "联系邮箱：562052228@qq.com\n"
            "本软件为内部使用工具，未经授权不得商用"
        )

    def show_update(self):
        """显示版本列表，点击单个版本查看详细说明"""
        top = Toplevel(self.root)
        top.title("更新说明")
        top.geometry("400x300")
        
        # 标题标签
        Label(top, text="选择版本查看详细更新说明：", font=("微软雅黑", 12)).pack(pady=10)
        
        # 版本列表按钮（动态生成）
        for version in self.version_info.keys():
            btn = Button(top, text=version, width=20, command=lambda v=version: self.show_version_details(v))
            btn.pack(pady=5)

    def show_version_details(self, version):
        """显示单个版本的详细说明"""
        info = self.version_info[version]
        details_text = "\n".join(info["details"])  # 将列表转为换行文本
        messagebox.showinfo(info["title"], f"{info['title']}：\n{details_text}")

    def set_classification_rules(self):
        """设置分类规则的对话框"""
        top = Toplevel(self.root)
        top.title("分类规则设置")
        top.geometry("800x600")  # 较大窗口方便编辑长文本
        
        # 提示标签
        Label(top, text="请输入自定义分类规则（支持换行，当前内容为预设规则）：", font=("微软雅黑", 12)).grid(row=0, column=0, padx=10, pady=5, sticky=W)
        
        # 多行文本输入框（显示当前规则）
        rule_text = Text(top, width=100, height=30, wrap=WORD)
        rule_text.grid(row=1, column=0, padx=10, pady=5, columnspan=2)
        rule_text.insert(END, self.classification_rules)  # 加载当前规则
        
        # 保存按钮功能（新增文件写入逻辑）
        def save_rules():
            new_rules = rule_text.get(1.0, END).strip()  # 获取完整输入内容
            self.classification_rules = new_rules  # 更新实例变量
            
            # 保存到本地文件
            try:
                with open(self.rules_file, "w", encoding="utf-8") as f:
                    f.write(new_rules)
                messagebox.showinfo("保存成功", "分类规则已更新并保存到本地文件（rules.txt）")
            except Exception as e:
                messagebox.showerror("保存失败", f"规则保存失败：{str(e)}")
            
            top.destroy()
        
        # 保存按钮
        Button(top, text="保存规则", command=save_rules, width=20).grid(row=2, column=0, padx=10, pady=10, sticky=E)

    def show_get_api(self):
        messagebox.showinfo("获取豆包API指南", 
            "获取豆包API Key步骤：\n"
            "1. 访问火山引擎官网：https://www.volcengine.com/\n"
            "2. 注册/登录火山引擎账号\n"
            "3. 进入「豆包大模型」产品页面，申请API调用权限\n"
            "4. 权限通过后，在控制台「API Key管理」页面获取API Key\n"
            "注意：需确保账号已完成企业实名认证（部分功能需要）"
        )

    def show_get_deepseek_api(self):
        """显示如何获取DeepSeek API的说明"""
        info_text = """获取DeepSeek API的步骤说明：
        
    1. 注册/登录DeepSeek开发者平台
       访问官网：https://www.deepseek.com/，点击「开发者平台」注册或登录账号。
    
    2. 申请API Key
       在控制台中找到「API管理」或「密钥管理」页面，申请新的API Key（需完成企业/个人实名认证）。
    
    3. 查看API文档
       成功申请后，可在「文档中心」查看详细的API调用说明，包括：
       - base_url：https://api.deepseek.com（或https://api.deepseek.com/v1）
       - 支持模型：deepseek-chat（对话模型）、deepseek-reasoner（推理模型）
       - 请求格式：与OpenAI API兼容，可直接使用OpenAI SDK调用。
    
    4. 测试API连接
       在本工具的「设置-API Key设置」中，选择DeepSeek API类型，输入申请的Key后点击测试，验证连接是否成功。"""
        
        messagebox.showinfo("如何获取DeepSeek API", info_text)

    def load_config(self):
        """加载API配置（启动时调用）"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.doubao_api_key = config.get("doubao_api_key", "")
                    self.deepseek_api_key = config.get("deepseek_api_key", "")
                    self.api_type = config.get("api_type", "doubao")  # 默认豆包API
            except Exception as e:
                messagebox.showwarning("配置加载提示", f"读取配置文件失败：{str(e)}，将使用默认配置")

    def save_config(self):
        """保存API配置（保存时调用）"""
        config = {
            "doubao_api_key": self.doubao_api_key,
            "deepseek_api_key": self.deepseek_api_key,
            "api_type": self.api_type
        }
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)  # 使用json模块
            messagebox.showinfo("保存成功", "API配置已保存")
        except Exception as e:
            messagebox.showerror("保存失败", f"配置保存失败：{str(e)}")

    def show_development_purpose(self):
        """显示开发目的和软件简介"""
        purpose_window = Toplevel(self.root)
        purpose_window.title("开发目的与软件简介")
        purpose_window.geometry("600x400")
        
        # 优化排版后的内容（增加标题层级、项目符号和空行）
        content = """
        【开发目的】
        本工具旨在解决企业/机构日常文件归档效率低、分类标准不统一的问题。通过自动化识别文件内容关键词，结合预设的部门分类规则和保管期限规则，实现文件的智能分类与归档，减少人工操作失误，提升档案管理的规范化水平。

        【软件简介】
        「文件自动分类工具」是一款基于AI大语言模型（支持豆包/DeepSeek双API）的智能文件管理工具，核心功能包括：
        • 多维度分类：支持按「部门归属」（如办公室、人力资源部等）和「保管期限」（永久/长期/短期）双维度分类；
        • 规则自定义：提供分类规则设置功能，用户可根据实际业务需求修改部门/期限匹配规则；
        • 多API支持：兼容豆包和DeepSeek大语言模型，支持灵活切换API类型；
        • 可视化操作：提供文件列表可视化展示、实时分类日志输出、操作状态提示等交互功能；
        • 配置持久化：自动保存API Key、分类规则等配置，避免重复设置。

        【适用场景】
        企业行政档案管理
        • 项目资料归档
        • 事业单位文件整理
        • 其他需要规范化分类的场景
        """
        
        text_widget = Text(purpose_window, wrap=WORD, padx=20, pady=20, font=("微软雅黑", 10))
        text_widget.insert(END, content.strip())  # 去除首尾空行
        text_widget.pack(fill=BOTH, expand=True)
        
        scrollbar = Scrollbar(purpose_window, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)

if __name__ == "__main__":
    root = Tk()
    app = FileClassifierApp(root)
    root.mainloop()