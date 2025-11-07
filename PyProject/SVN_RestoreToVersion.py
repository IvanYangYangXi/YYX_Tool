import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import pyperclip
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import win32clipboard
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_ENABLED = True
except ImportError:
    DND_ENABLED = False

class SVNRestoreTool:
    def __init__(self, master):
        self.master = master
        master.title("SVN版本还原工具 - 剪贴板增强版")
        master.geometry("500x700")  # 调整窗口大小
        
        # 主界面布局
        self.setup_ui()
        
        # 存储文件列表
        self.files_to_restore = []
    
    def setup_ui(self):
        """初始化用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件操作区域
        self.setup_file_operations(main_frame)
        
        # 文件列表区域
        self.setup_file_list(main_frame)
        
        # 版本输入区域
        self.setup_version_input(main_frame)
        
        # 操作按钮
        self.setup_action_buttons(main_frame)
        
        # 状态显示区域
        self.setup_status_display(main_frame)
    
    def setup_file_operations(self, parent):
        """设置文件操作区域"""
        file_op_frame = ttk.LabelFrame(parent, text="文件操作", padding="10")
        file_op_frame.pack(fill=tk.X, pady=5)
        
        # 剪贴板按钮
        ttk.Button(
            file_op_frame,
            text="从剪贴板添加文件",
            command=self.add_files_from_clipboard
        ).pack(side=tk.LEFT, padx=5)
        
        # 文件选择按钮
        ttk.Button(
            file_op_frame,
            text="选择文件",
            command=self.select_files
        ).pack(side=tk.LEFT, padx=5)
        
        # 文件夹选择按钮
        ttk.Button(
            file_op_frame,
            text="选择文件夹",
            command=self.select_folder
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_file_list(self, parent):
        """设置文件列表区域"""
        file_frame = ttk.LabelFrame(parent, text="文件列表", padding="10")
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建列表框和滚动条
        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文件列表操作按钮
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_frame, text="清空列表", command=self.clear_file_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
    
    def setup_version_input(self, parent):
        """设置版本号输入区域"""
        version_frame = ttk.LabelFrame(parent, text="版本设置", padding="10")
        version_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(version_frame, text="目标版本号:").pack(side=tk.LEFT)
        self.version_entry = ttk.Entry(version_frame, width=15)
        self.version_entry.pack(side=tk.LEFT, padx=5)
        self.version_entry.insert(0, "")  # 设置默认版本号
        
        # 添加版本号验证
        self.version_entry.bind('<FocusOut>', self.validate_version)
        self.version_entry.bind('<Return>', self.execute_restore)
    
    def setup_action_buttons(self, parent):
        """设置操作按钮"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 将执行还原、清除所有和清空状态按钮横向排列
        button_frame = ttk.Frame(btn_frame)
        button_frame.pack()
        
        self.restore_btn = ttk.Button(
            button_frame, 
            text="执行还原",
            command=self.execute_restore,
            state=tk.DISABLED
        )
        self.restore_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="清除所有",
            command=self.clear_all
        ).pack(side=tk.LEFT, padx=10, pady=5)
        
        # 将清空状态按钮放在清除所有按钮后面
        ttk.Button(
            button_frame,
            text="清空状态",
            command=self.clear_status
        ).pack(side=tk.LEFT, padx=10, pady=5)
    
    def setup_status_display(self, parent):
        """设置状态显示区域"""
        status_frame = ttk.LabelFrame(parent, text="操作状态", padding="10")
        status_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        
        self.status_text = tk.Text(status_frame, height=15, state=tk.DISABLED)  # 增加默认高度
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def clear_status(self):
        """清空状态显示"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def add_files_from_clipboard(self):
        """从剪贴板添加文件"""
        # 首先尝试获取剪贴板中的文件路径
        paths = self.get_files_from_clipboard()
        
        if not paths:
            self.update_status("=" * 50, is_warning=True)
            self.update_status("剪贴板为空或未找到有效文件!", is_warning=True)
            self.update_status("操作指南:", is_warning=True)
            self.update_status("方法一 (推荐):", is_warning=True)
            self.update_status("1. 在文件资源管理器中选择文件或文件夹", is_warning=True)
            self.update_status("2. 按 Ctrl+C 复制文件", is_warning=True)
            self.update_status("3. 点击此按钮从剪贴板添加文件", is_warning=True)
            self.update_status("", is_warning=True)
            self.update_status("方法二:", is_warning=True)
            self.update_status("- 点击'选择文件'按钮手动选择文件", is_warning=True)
            self.update_status("- 点击'选择文件夹'按钮手动选择文件夹", is_warning=True)
            self.update_status("=" * 50, is_warning=True)
            return

        added_count = 0
        for path in paths:
            if os.path.exists(path):
                if path not in self.files_to_restore:
                    self.files_to_restore.append(path)
                    self.file_listbox.insert(tk.END, path)
                    added_count += 1
                    self.update_status(f"已添加: {path}")
                else:
                    self.update_status(f"已存在: {path}", is_warning=True)
            else:
                self.update_status(f"路径不存在: {path}", is_error=True)

        if added_count > 0:
            self.restore_btn.config(state=tk.NORMAL)
            self.update_status(f"成功从剪贴板添加 {added_count} 个文件/文件夹")
        else:
            self.update_status("没有添加任何有效路径", is_warning=True)
            # 提供备选方案
            self.update_status("提示: 您可以通过'选择文件'或'选择文件夹'按钮手动添加文件", is_warning=True)
    
    def get_files_from_clipboard(self):
        """
        从剪贴板获取文件路径
        支持两种情况:
        1. 复制文件路径文本
        2. 复制文件本身(Windows特有)
        """
        paths = []
        
        # 方法1: 尝试获取文本形式的路径
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content and isinstance(clipboard_content, str):
                # 解析剪贴板内容，支持多行路径和单行多个路径
                lines = clipboard_content.strip().split('\n')
                for line in lines:
                    # 处理一行中可能包含的多个路径（以空格或制表符分隔）
                    line_paths = line.strip().split()
                    for path in line_paths:
                        # 去除路径两端的引号
                        cleaned_path = path.strip().strip('"').strip("'")
                        if cleaned_path and cleaned_path not in paths:
                            # 验证是否为有效路径
                            if os.path.exists(cleaned_path):
                                paths.append(cleaned_path)
        except Exception as e:
            self.update_status(f"读取剪贴板文本时出错: {str(e)}", is_error=True)
        
        # 如果通过文本方式没有获取到路径，且在Windows环境下，尝试获取实际复制的文件
        if not paths and WIN32_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                try:
                    # 尝试获取剪贴板中的文件列表（CF_HDROP格式）
                    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                        files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                        if files:
                            for file in files:
                                if os.path.exists(file) and file not in paths:
                                    paths.append(file)
                finally:
                    win32clipboard.CloseClipboard()
            except Exception as e:
                self.update_status(f"读取剪贴板文件时出错: {str(e)}", is_error=True)
        
        return paths
    
    def select_files(self):
        """选择文件"""
        files = filedialog.askopenfilenames(title="选择要还原的文件")
        if files:
            added_count = 0
            for file_path in files:
                if file_path not in self.files_to_restore:
                    self.files_to_restore.append(file_path)
                    self.file_listbox.insert(tk.END, file_path)
                    added_count += 1
            
            if added_count > 0:
                self.restore_btn.config(state=tk.NORMAL)
                self.update_status(f"成功添加 {added_count} 个文件")
    
    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要还原的文件夹")
        if folder:
            if folder not in self.files_to_restore:
                self.files_to_restore.append(folder)
                self.file_listbox.insert(tk.END, folder)
                self.restore_btn.config(state=tk.NORMAL)
                self.update_status(f"成功添加文件夹: {folder}")
            else:
                self.update_status("文件夹已存在", is_warning=True)
    
    def clear_file_list(self):
        """清空文件列表"""
        self.files_to_restore.clear()
        self.file_listbox.delete(0, tk.END)
        self.restore_btn.config(state=tk.DISABLED)
        self.update_status("已清空文件列表")
    
    def remove_selected(self):
        """移除选中的文件"""
        selections = self.file_listbox.curselection()
        if not selections:
            self.update_status("请选择要移除的文件", is_warning=True)
            return
        
        # 从后往前删除，避免索引问题
        for i in reversed(selections):
            self.file_listbox.delete(i)
            self.files_to_restore.pop(i)
        
        if not self.files_to_restore:
            self.restore_btn.config(state=tk.DISABLED)
        
        self.update_status(f"已移除 {len(selections)} 个项目")
    
    def clear_all(self):
        """清除所有内容"""
        self.clear_file_list()
        self.version_entry.delete(0, tk.END)
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.update_status("已清除所有内容")
    
    def validate_version(self, event=None):
        """验证版本号输入"""
        version = self.version_entry.get().strip()
        if version and not version.isdigit():
            self.update_status("错误: 版本号必须为数字", is_error=True)
            self.version_entry.delete(0, tk.END)
            return False
        return True
    
    def execute_restore(self, event=None):
        """执行SVN还原操作"""
        if not self.validate_version():
            return
        
        version = self.version_entry.get().strip()
        if not version:
            self.update_status("错误: 请输入版本号", is_error=True)
            return
        
        if not self.files_to_restore:
            self.update_status("错误: 请先添加文件", is_error=True)
            return
        
        # 询问用户确认操作
        confirm = messagebox.askyesno(
            "确认操作",
            f"确定要处理 {len(self.files_to_restore)} 个文件/文件夹到版本 {version} 吗？\n\n"
            "注意：这将覆盖当前文件内容！"
        )
        
        if not confirm:
            return
        
        self.update_status(f"开始处理文件到版本 {version}...")
        
        success_count = 0
        failed_files = []  # 记录处理失败的文件
        
        for file_path in self.files_to_restore:
            try:
                # 检查文件/文件夹是否存在
                if not os.path.exists(file_path):
                    self.update_status(f"错误: 文件/文件夹不存在 {file_path}", is_error=True)
                    failed_files.append(file_path)
                    continue
                
                # 如果是文件夹，递归处理其中的文件
                if os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            if not self.process_file(full_path, version):
                                failed_files.append(full_path)
                            else:
                                success_count += 1
                else:
                    # 处理单个文件
                    if self.process_file(file_path, version):
                        success_count += 1
                    else:
                        failed_files.append(file_path)
                        
            except Exception as e:
                self.update_status(f"处理 {file_path} 时发生异常: {str(e)}", is_error=True)
                failed_files.append(file_path)
        
        self.update_status(f"操作完成: 成功处理 {success_count} 个文件")
        
        # 显示处理失败的文件
        if failed_files:
            self.update_status("=" * 50, is_error=True)
            self.update_status("以下文件处理失败:", is_error=True)
            for failed_file in failed_files:
                self.update_status(failed_file, is_error=True)
            self.update_status("=" * 50, is_error=True)
        
        if success_count > 0:
            messagebox.showinfo("完成", f"成功处理 {success_count} 个文件到版本 {version}")
    
    def is_readded_file(self, file_path, target_version=None):
        """
        检查文件是否是已删除后重新添加的文件
        通过检查SVN日志中指定版本之后是否存在删除操作来判断
        """
        try:
            # 首先检查文件是否在SVN控制下
            if not self.is_file_under_svn(file_path):
                # 如果文件当前不在SVN控制下，检查上级目录日志
                return self.check_file_deleted_in_parent_log(file_path, target_version)
            
            # 获取文件的完整SVN日志信息
            cmd = ['svn', 'log', '--xml', file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                return self.check_file_deleted_in_parent_log(file_path, target_version)
            
            # 解析XML日志
            try:
                root = ET.fromstring(result.stdout)
                log_entries = root.findall('.//logentry')
                
                # 检查指定版本之后是否存在删除操作
                if target_version:
                    target_rev = int(target_version)
                    delete_keywords = ['delete', 'remove', 'del', 'deleted', 'removed', 'rm']
                    for entry in log_entries:
                        revision = int(entry.get('revision'))
                        # 只检查目标版本之后的记录
                        if revision > target_rev:
                            msg = entry.find('msg')
                            if msg is not None and msg.text is not None:
                                msg_text = msg.text.lower()
                                for keyword in delete_keywords:
                                    if keyword in msg_text:
                                        self.update_status(f"检测到版本 {target_version} 之后有删除操作: {msg.text}", is_warning=True)
                                        return True
                
                # 如果没有在文件自身日志中找到删除操作，检查上级目录日志
                return self.check_file_deleted_in_parent_log(file_path, target_version)
                
            except ET.ParseError:
                return self.check_file_deleted_in_parent_log(file_path, target_version)
                
        except Exception as e:
            self.update_status(f"检查重新添加文件时出错: {str(e)}", is_error=True)
            return self.check_file_deleted_in_parent_log(file_path, target_version)
    
    def check_file_deleted_in_parent_log(self, file_path, target_version=None):
        """
        检查上级目录日志，确定文件是否被删除
        """
        try:
            parent_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            
            # 获取上级目录的完整SVN日志信息
            cmd = ['svn', 'log', '--xml', parent_dir]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                return False
            
            # 解析XML日志
            try:
                root = ET.fromstring(result.stdout)
                log_entries = root.findall('.//logentry')
                
                # 检查指定版本之后是否存在删除该文件的操作
                if target_version:
                    target_rev = int(target_version)
                    for entry in log_entries:
                        revision = int(entry.get('revision'))
                        # 只检查目标版本之后的记录
                        if revision > target_rev:
                            # 获取该版本的详细变更信息
                            diff_cmd = ['svn', 'log', '-v', '-r', str(revision), parent_dir]
                            diff_result = subprocess.run(
                                diff_cmd,
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                            
                            if diff_result.returncode == 0 and file_name in diff_result.stdout:
                                # 检查是否包含删除操作
                                lines = diff_result.stdout.split('\n')
                                for line in lines:
                                    if line.strip().startswith('D') and file_name in line:
                                        self.update_status(f"在上级目录日志中检测到版本 {revision} 删除文件 {file_name}", is_warning=True)
                                        return True
                
                return False
                
            except ET.ParseError:
                return False
                
        except Exception as e:
            self.update_status(f"检查上级目录日志时出错: {str(e)}", is_error=True)
            return False
    
    def process_file(self, file_path, version):
        """处理单个文件"""
        try:
            # 检查文件是否在SVN控制下
            if not self.is_file_under_svn(file_path):
                self.update_status(f"警告: {file_path} 不在SVN控制下", is_warning=True)
                return False
            
            # 检查文件是否是已删除后重新添加的文件
            is_readded_file = self.is_readded_file(file_path, version)
            if is_readded_file:
                self.update_status(f"检测到: {file_path} 是已删除后重新添加的文件", is_warning=True)
                self.update_status(f"跳过: {file_path} 避免还原已删除后重新添加的文件导致损坏", is_error=True)
                return False
            
            # 检查指定版本是否存在且可访问
            if not self.is_version_accessible(file_path, version):
                self.update_status(f"提示: {file_path} 在版本 {version} 中不可直接访问", is_warning=True)
                return False
            
            # 使用svn cat命令获取指定版本的文件内容
            cmd = ['svn', 'cat', '-r', version, file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # 将指定版本的内容写入文件，这样会成为本地修改
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                self.update_status(f"成功: {file_path} 已处理到版本 {version}，现在是本地修改")
                return True
            else:
                self.update_status(f"失败: {file_path} - {result.stderr.strip()}", is_error=True)
                return False
                
        except Exception as e:
            self.update_status(f"处理文件 {file_path} 时发生异常: {str(e)}", is_error=True)
            return False
    
    def is_version_in_history(self, file_path, version):
        """
        检查指定版本是否在文件的历史记录中
        """
        try:
            cmd = ['svn', 'log', '--xml', file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                return False
            
            root = ET.fromstring(result.stdout)
            log_entries = root.findall('.//logentry')
            
            target_version = int(version)
            for entry in log_entries:
                revision = int(entry.get('revision'))
                if revision == target_version:
                    return True
            
            return False
        except Exception:
            return False
    
    def is_file_under_svn(self, file_path):
        """检查文件是否在SVN控制下"""
        try:
            cmd = ['svn', 'info', file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except:
            return False
    
    def is_version_accessible(self, file_path, version):
        """检查指定版本的文件是否可访问"""
        try:
            # 使用svn info检查版本是否存在于文件历史中
            cmd = ['svn', 'info', '-r', version, file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 如果返回码为0，表示版本存在
            return result.returncode == 0
        except:
            return False
    
    def update_status(self, message, is_error=False, is_warning=False):
        """更新状态显示"""
        self.status_text.config(state=tk.NORMAL)
        
        # 插入消息
        tag = "error" if is_error else ("warning" if is_warning else "info")
        self.status_text.insert(tk.END, message + "\n", tag)
        
        # 配置标签样式
        self.status_text.tag_config("error", foreground="red")
        self.status_text.tag_config("warning", foreground="orange")
        self.status_text.tag_config("info", foreground="black")
        
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

def main():
    try:
        root = tk.Tk() if not DND_ENABLED else TkinterDnD.Tk()
        app = SVNRestoreTool(root)
        root.mainloop()
    except Exception as e:
        print(f"程序启动出错: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()