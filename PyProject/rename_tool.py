try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    from tkinter import Tk as TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import re
import string
from datetime import datetime

"""
工具名：文件改名工具
作者: IvanYYX
邮箱: 523166477@qq.com
时间: 2025年08月20日
使用说明 : python rename_tool.py
    使用Python3运行该脚本，即可打开文件改名工具。
"""

# 使用正则表达式的模式，匹配任何非字母数字字符
pattern = r'[^a-zA-Z0-9]+'

class RenameTool:
    def __init__(self, root):
        self.root = root
        # 初始化日志文件
        with open("rename_tool_debug.log", "w", encoding="utf-8") as f:
            f.write("=== 文件改名工具调试日志 ===\n")
        # 启用拖放支持
        if hasattr(self.root, 'drop_target_register'):
            self.root.drop_target_register('*')
            self.root.dnd_bind('<<Drop>>', self.on_root_drop)
        self.root.title("高级文件改名工具")
        self.root.geometry("500x720")
        self.root.minsize(400, 600)
        
        # 字段配置区域
        config_frame = tk.LabelFrame(root, text="字段配置 (格式: 位置 | 重命名字段)", padx=10, pady=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # 可编辑字段表格 (带独立滚动条)
        table_container = tk.Frame(config_frame)
        table_container.pack(fill="x", expand=True, pady=5)
        
        # 主布局容器
        main_container = tk.Frame(table_container)
        main_container.pack(fill="both", expand=True)
        
        # 左侧表格和滚动条容器
        table_scroll_frame = tk.Frame(main_container)
        table_scroll_frame.pack(side="left", fill="both", expand=True)
        
        # 字段表格
        columns = ("位置", "重命名字段")
        self.field_table = ttk.Treeview(table_scroll_frame, columns=columns, show="headings", height=5)
        self.field_table.column("#0", width=0, stretch=tk.NO)
        self.field_table.column("位置", width=50, anchor="center")
        self.field_table.column("重命名字段", width=150, anchor="w")
        for col in columns:
            self.field_table.heading(col, text=col)
        
        # 滚动条
        yscroll = ttk.Scrollbar(table_scroll_frame, orient="vertical", command=self.field_table.yview)
        self.field_table.configure(yscrollcommand=yscroll.set)
        
        # 表格和滚动条布局
        self.field_table.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        
        # 右侧说明区域
        help_frame = tk.Frame(main_container, width=150)
        help_frame.pack(side="right", fill="y")
        help_text = tk.Label(help_frame, 
                           text="字段配置说明:\n"
                                "{n} - 引用原文件名第n部分\n"
                                "{*} - 引用完整原文件名\n"
                                "下拉选择 数字/字母 递增字段",
                           justify=tk.LEFT, padx=10, wraplength=140)
        help_text.pack(fill="both", expand=True)
        
        # 固定容器高度
        table_container.pack_propagate(False)
        table_container.config(height=150)
        
        # 使字段内容可编辑
        self.field_table.bind("<Double-1>", self.on_double_click)
        self.field_table.pack(fill="x", padx=5, pady=5)
        
        # 字段操作按钮（紧凑布局）
        btn_frame = tk.Frame(config_frame)
        btn_frame.pack(fill="x", pady=(0,5))
        
        tk.Button(btn_frame, text="添加字段", command=self.add_field).pack(side="left", padx=2)
        tk.Button(btn_frame, text="插入字段", command=self.insert_field).pack(side="left", padx=2)
        tk.Button(btn_frame, text="删除字段", command=self.remove_field).pack(side="left", padx=2)
        
        # 递增字段类型选择
        self.incr_type = tk.StringVar()
        self.incr_type.set("数字")
        incr_menu = tk.OptionMenu(btn_frame, self.incr_type, "数字", "大写字母", "小写字母")
        incr_menu.pack(side="left", padx=2)
        tk.Button(btn_frame, text="添加递增", command=self.add_increment_field).pack(side="left", padx=2)
        
        # 字段转换规则区域
        rule_frame = tk.LabelFrame(root, text="字段转换规则 (原字段 → 转换字段)", padx=10, pady=10)
        rule_frame.pack(fill="x", padx=10, pady=5)
        
        # 规则输入行
        rule_input = tk.Frame(rule_frame)
        rule_input.pack(fill="x")
        
        tk.Label(rule_input, text="原字段:").pack(side="left")
        self.orig_entry = tk.Entry(rule_input, width=15)
        self.orig_entry.pack(side="left", padx=5)
        
        tk.Label(rule_input, text="→").pack(side="left")
        self.new_entry = tk.Entry(rule_input, width=15)
        self.new_entry.pack(side="left", padx=5)
        
        tk.Button(rule_input, text="添加规则", command=self.add_rule).pack(side="left", padx=5)
        
        # 规则列表 (带独立滚动条)
        list_container = tk.Frame(rule_frame)
        list_container.pack(fill="x", pady=5)
        
        self.rule_list = tk.Listbox(list_container, height=3)
        yscroll = ttk.Scrollbar(list_container, orient="vertical", command=self.rule_list.yview)
        self.rule_list.configure(yscrollcommand=yscroll.set)
        
        self.rule_list.pack(side="left", fill="x", expand=True)
        yscroll.pack(side="right", fill="y")
        
        # 规则操作按钮（固定高度和最小宽度）
        rule_btn_frame = tk.Frame(rule_frame, height=30)
        rule_btn_frame.pack(fill="x", pady=5)
        rule_btn_frame.pack_propagate(False)
        
        tk.Button(rule_btn_frame, text="删除规则", command=self.remove_rule).pack(side="left", padx=5)
        tk.Button(rule_btn_frame, text="清空规则", command=self.clear_rules).pack(side="left", padx=5)
        
        # 初始化规则
        self.rules = []
        
        # 文件操作区域
        file_frame = tk.LabelFrame(root, text="文件操作", padx=10, pady=10)
        file_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 文件列表框容器（带滚动条）
        list_container = tk.Frame(file_frame)
        list_container.pack(fill="both", expand=True, pady=2)
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # 按钮区域（底部固定）
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill="x", pady=(5,0))
        
        # 文件列表框（支持拖放）
        self.file_list = tk.Listbox(list_container, height=10)
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        self.file_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.file_list.yview)
        self.file_list.config(yscrollcommand=scrollbar.set)
        
        # 设置拖放功能
        if hasattr(self.file_list, 'drop_target_register'):
            self.file_list.drop_target_register('*')
            self.file_list.dnd_bind('<<Drop>>', self.on_drop)
        
        # 文件操作按钮区域（固定高度和最小宽度）
        btn_frame = tk.Frame(file_frame, height=30)
        btn_frame.pack(fill="x", pady=(0,5))
        btn_frame.pack_propagate(False)
        
        # 去除重复字段选项
        self.remove_duplicates = tk.BooleanVar()
        tk.Checkbutton(btn_frame, text="去除重复字段", variable=self.remove_duplicates).pack(side="left", padx=5)
        
        # 文件操作按钮
        tk.Button(btn_frame, text="选择文件", command=self.add_files, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="选择文件夹", command=self.add_folder, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="清空列表", command=self.clear_files, width=10).pack(side="left", padx=5)
        
        # 突出显示执行按钮
        tk.Button(btn_frame, text="执行改名", command=self.rename_files, 
                bg="#4CAF50", fg="white", width=15).pack(side="right", padx=10)
        
        # 初始化字段
        self.reset_fields()
        
    def add_rule_ui(self, parent):
        rule_row = tk.Frame(parent)
        rule_row.pack(fill="x")
        
        tk.Label(rule_row, text="原字段:").pack(side="left")
        orig_entry = tk.Entry(rule_row, width=15)
        orig_entry.pack(side="left")
        
        tk.Label(rule_row, text="→").pack(side="left")
        new_entry = tk.Entry(rule_row, width=15)
        new_entry.pack(side="left")
        
        add_btn = tk.Button(rule_row, text="添加规则", 
                          command=lambda: self.add_rule(orig_entry.get(), new_entry.get()))
        add_btn.pack(side="left")
        
        self.rule_list = tk.Listbox(parent, height=3)
        self.rule_list.pack(fill="x")
        
    def log_operation(self, operation, details):
        """记录操作日志"""
        log_msg = f"[{datetime.now()}] {operation}: {details}\n"
        with open("rename_tool_debug.log", "a", encoding="utf-8") as f:
            f.write(log_msg)
        print(log_msg)

    def add_rule(self):
        """添加字段转换规则"""
        orig = self.orig_entry.get()
        new = self.new_entry.get()
        self.log_operation("添加规则", f"原字段: {orig}, 新字段: {new}")
        if orig and new:
            # 检查是否是字段ID格式(数字)
            if orig.isdigit():
                field_id = int(orig)
                # 查找对应字段
                for child in self.field_table.get_children():
                    pos, field_value = self.field_table.item(child)["values"]
                    if pos == field_id:
                        self.field_table.item(child, values=(pos, new))
                        break
                self.rules.append((f"ID:{orig}", new.strip()))
                self.rule_list.insert(tk.END, f"字段{orig} → {new.strip()}")
            else:
                self.rules.append((orig.strip(), new.strip()))
                self.rule_list.insert(tk.END, f"{orig.strip()} → {new.strip()}")
            self.orig_entry.delete(0, tk.END)
            self.new_entry.delete(0, tk.END)
            
    def remove_rule(self):
        """删除选中的规则"""
        selected = self.rule_list.curselection()
        if selected:
            self.rules.pop(selected[0])
            self.rule_list.delete(selected[0])
            
    def clear_rules(self):
        """清空所有规则"""
        self.rules.clear()
        self.rule_list.delete(0, tk.END)
        
    def on_double_click(self, event):
        """双击编辑字段内容"""
        region = self.field_table.identify("region", event.x, event.y)
        if region == "cell":
            column = self.field_table.identify_column(event.x)
            item = self.field_table.focus()
            
            if column == "#2":  # 只允许编辑字段内容列
                current_value = self.field_table.item(item, "values")[1]
                entry = tk.Entry(self.field_table, width=20)
                entry.insert(0, current_value)
                entry.bind("<Return>", lambda e: self.save_edit(item, entry))
                entry.bind("<FocusOut>", lambda e: entry.destroy())
                entry.place(x=event.x, y=event.y, anchor="w")
                entry.focus_set()
    
    def save_edit(self, item, entry):
        """保存编辑后的字段内容"""
        new_value = entry.get()
        values = list(self.field_table.item(item, "values"))
        values[1] = new_value
        self.field_table.item(item, values=values)
        entry.destroy()
        
    def add_field(self):
        """添加新字段"""
        self.field_table.insert("", tk.END, values=(len(self.field_table.get_children())+1, "新字段"))
        
    def remove_field(self):
        selected = self.field_table.selection()
        if selected:
            self.field_table.delete(selected)
            self.renumber_fields()
        
    def insert_field(self):
        """在选中位置插入新字段"""
        selected = self.field_table.selection()
        if selected:
            # 获取选中项在列表中的索引位置
            index = self.field_table.index(selected[0])
            # 更新后续字段的位置编号
            for i, child in enumerate(self.field_table.get_children()[index:], start=index+1):
                self.field_table.set(child, "位置", str(i+1))
            # 插入新字段，位置编号为选中项的位置编号
            pos = int(self.field_table.item(selected[0], "values")[0])
            self.field_table.insert("", index, values=(pos, "新字段"))
            # 重新编号所有字段
            self.renumber_fields()
        else:
            self.add_field()
            
    def add_increment_field(self):
        """添加递增字段"""
        next_pos = len(self.field_table.get_children()) + 1
        incr_type = self.incr_type.get()
        if incr_type == "数字":
            self.field_table.insert("", tk.END, values=(next_pos, "递增数字"))
        elif incr_type == "大写字母":
            self.field_table.insert("", tk.END, values=(next_pos, "递增大写字母"))
        else:
            self.field_table.insert("", tk.END, values=(next_pos, "递增小写字母"))
        
    def reset_fields(self):
        """重置为示例字段"""
        self.field_table.delete(*self.field_table.get_children())
        sample_fields = [
            (1, "T"),
            (2, "{*}"),
            (3, "递增数字")
        ]
        for pos, field in sample_fields:
            self.field_table.insert("", tk.END, values=(pos, field))
            
    def renumber_fields(self):
        """重新编号所有字段"""
        for i, child in enumerate(self.field_table.get_children(), start=1):
            self.field_table.set(child, "位置", str(i))
            
    def on_root_drop(self, event):
        """处理根窗口拖放事件"""
        if hasattr(event, 'data'):
            files = self.root.tk.splitlist(event.data)
            self.add_dropped_files(files)
            
    def on_drop(self, event):
        """处理列表框拖放事件"""
        if hasattr(event, 'data'):
            files = self.root.tk.splitlist(event.data)
            self.add_dropped_files(files)
            
    def add_dropped_files(self, files):
        """添加拖放的文件"""
        try:
            for f in files:
                path = os.path.normpath(f)
                if os.path.exists(path):
                    if not any(os.path.normpath(self.file_list.get(i)) == path 
                              for i in range(self.file_list.size())):
                        self.file_list.insert(tk.END, path)
                        print(f"添加文件: {path}")  # 调试信息
                    else:
                        print(f"文件已存在: {path}")  # 调试信息
                else:
                    print(f"文件不存在: {path}")  # 调试信息
                    
        except Exception as e:
            messagebox.showerror("错误", f"添加文件失败: {str(e)}")
            print(f"拖放错误: {str(e)}")  # 调试信息
    
    def add_files(self):
        files = filedialog.askopenfilenames()
        self.log_operation("添加文件", f"文件列表: {files}")
        if files:
            for f in files:
                path = os.path.normpath(f)
                if not any(os.path.normpath(self.file_list.get(i)) == path 
                          for i in range(self.file_list.size())):
                    self.file_list.insert(tk.END, path)
                
    def add_folder(self):
        folder = filedialog.askdirectory()
        self.log_operation("添加文件夹", f"文件夹路径: {folder}")
        if folder:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    path = os.path.normpath(os.path.join(root, f))
                    if not any(os.path.normpath(self.file_list.get(i)) == path 
                              for i in range(self.file_list.size())):
                        self.file_list.insert(tk.END, path)
        
    def clear_files(self):
        self.file_list.delete(0, tk.END)
        
    def process_special_tags(self, field, old_name, old_fields, pos):
        """处理特殊标记如{*}和{n}"""
        self.log_operation("特殊标记处理", "位置{}: 开始处理字段: {}".format(pos, field))
        
        # 处理{*}标记 - 替换为完整原始文件名
        if "{*}" in field or "｛*｝" in field:
            self.log_operation("特殊标记处理", "位置{}: 检测到{{*}}标记".format(pos))
            field = field.replace("{*}", old_name).replace("｛*｝", old_name)
            self.log_operation("特殊标记处理", "位置{}: 替换{{*}}后字段: {}".format(pos, field))
        
        # 处理{n}标记 - 替换为原始文件名第n部分并应用字段转换规则
        if re.search(r"[｛{](\d+)[｝}]", field):
            self.log_operation("特殊标记处理", "位置{}: 检测到{{n}}引用".format(pos))
            def replace_field(match):
                idx = int(match.group(1)) - 1
                result = old_fields[idx] if 0 <= idx < len(old_fields) else ""
                # 应用字段转换规则
                for rule_orig, rule_new in self.rules:
                    if rule_orig == result:
                        result = rule_new
                        break
                self.log_operation("特殊标记处理", "位置{}: 替换{{n}}为: {}".format(pos, result))
                return result
            field = re.sub(r"[｛{](\d+)[｝}]", replace_field, field)
            self.log_operation("特殊标记处理", "位置{}: 替换{{n}}后字段: {}".format(pos, field))
        
        return field

    def rename_files(self):
        if not self.file_list.size():
            messagebox.showwarning("警告", "请先添加文件")
            return
        
        self.log_operation("开始改名", f"文件数量: {self.file_list.size()}")
            
        # 初始化递增计数器
        increment_counter = 1
        letter_case = None  # 记录字母递增的大小写状态
        
        success = 0
        for i in range(self.file_list.size()):
            try:
                old_path = self.file_list.get(i)
                dirname = os.path.dirname(old_path)
                old_name, ext = os.path.splitext(os.path.basename(old_path))
                old_fields = re.split(pattern, old_name)
                
                # 构建新文件名
                new_fields = []
                children = list(self.field_table.get_children())
                self.log_operation("字段配置", f"当前字段数: {len(children)}")
                self.log_operation("原始文件名", f"原文件名: {old_name}, 分割后: {old_fields}")
                for idx, child in enumerate(children):
                    pos, new_field = self.field_table.item(child)["values"]
                    self.log_operation("字段处理", f"位置{pos}: 原字段值: {new_field}")
                    self.log_operation("当前规则", f"可用规则: {self.rules}")
                    
                    # 处理特殊标记
                    new_field = self.process_special_tags(new_field, old_name, old_fields, pos)
                    
                    # 应用字段转换规则
                    temp_field = new_field
                    self.log_operation("规则处理", f"位置{pos}: 开始应用转换规则")
                    for rule_orig, rule_new in self.rules:
                        if rule_orig.startswith(f"ID:{pos}"):
                            temp_field = rule_new
                            self.log_operation("规则处理", f"位置{pos}: 应用ID规则 {rule_orig}→{rule_new}")
                            break
                        elif rule_orig in temp_field:
                            self.log_operation("规则处理", f"位置{pos}: 处理规则 {rule_orig}→{rule_new}")
                            temp_field = temp_field.replace(rule_orig, rule_new)
                    new_field = temp_field
                    self.log_operation("字段处理", f"位置{pos}: 最终字段值: {new_field}")
                    
                    # 处理递增数字字段
                    if new_field == "递增数字":
                        self.log_operation("递增处理", f"位置{pos}: 数字递增, 当前值: {increment_counter}")
                        new_field = str(increment_counter)
                        increment_counter += 1
                    # 处理递增字母字段
                    elif new_field in ["递增大写字母", "递增小写字母"]:
                        is_lower = "小写" in new_field
                        self.log_operation("递增处理", "位置{}: 字母递增, 当前值: {}".format(pos, increment_counter))
                        new_field = self.incr_letter("a" if is_lower else "A", increment_counter-1)
                        increment_counter += 1
                        self.log_operation("递增处理", "位置{}: 递增后值: {}".format(pos, new_field))
                    
                    # 保留所有配置字段
                    new_fields.append(new_field)
                
                # 去除重复字段（按'_'分割后判断）
                if self.remove_duplicates.get():
                    # 先按'_'连接再分割，确保格式统一
                    temp_name = "_".join(new_fields)
                    split_fields = re.split(pattern, temp_name)
                    
                    # 去重同时保留顺序
                    seen = set()
                    filtered_fields = []
                    for field in split_fields:
                        if field not in seen:
                            seen.add(field)
                            filtered_fields.append(field)
                    
                    new_fields = filtered_fields
                    self.log_operation("去重处理", f"分割后字段: {split_fields}, 去重后字段: {new_fields}")
                
                # 生成新文件名并确保有效性
                self.log_operation("结果生成", f"组合字段: {new_fields}")
                new_name = "_".join(new_fields)
                self.log_operation("结果生成", f"生成的新文件名: {new_name}")
                # 移除文件名中的非法字符
                new_name = re.sub(r'[\\/*?:"<>|]', '', new_name)
                # 确保扩展名正确
                if not ext.startswith('.'):
                    ext = '.' + ext
                # 规范化路径
                new_path = os.path.normpath(os.path.join(dirname, new_name + ext))
                
                # 确保目标目录存在
                os.makedirs(dirname, exist_ok=True)
                
                # 执行重命名
                os.rename(old_path, new_path)
                success += 1
                self.log_operation("改名成功", f"原文件: {old_path}, 新文件: {new_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"改名失败: {str(e)}")
                continue
                
        messagebox.showinfo("完成", f"成功改名 {success}/{self.file_list.size()} 个文件")
        self.clear_files()
        
    def incr_letter(self, current, step):
        """字母递增逻辑(支持大小写)"""
        if not current:
            return "A"
        if not current.isalpha():
            return "A"
            
        # 判断当前字母大小写
        is_lower = current[-1].islower()
        letters = string.ascii_lowercase if is_lower else string.ascii_uppercase
        idx = letters.index(current[-1].lower() if is_lower else current[-1].upper()) + step
        return letters[idx % len(letters)]

if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk()
    except:
        root = tk.Tk()
    app = RenameTool(root)
    root.mainloop()
