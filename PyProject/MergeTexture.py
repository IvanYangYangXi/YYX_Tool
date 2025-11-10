import os
import re
import sys
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image

"""
纹理合并工具

该工具用于处理纹理贴图文件，根据特定规则合并不同贴图的通道，并生成新的纹理文件。

规则详细说明：
1. 文件分组：
   - 根据文件名基础部分（去除 _D, _A, _N, _R, _S, _AO, _TC 等后缀）进行分组
   - 对于包含"Trunk"的文件，_AO文件需要与对应的基本名称组合并

2. 通道合并规则：
   - 将 _A 贴图的红色通道合并到 _D 贴图的 Alpha 通道，输出为 _DA.tga 文件
   - 将 _R 和 _S 贴图的红色通道分别合并到 _N 贴图的蓝色通道和 Alpha 通道，输出为 _NRS.tga 文件
   - 对于命名包含"Trunk"的文件组：
     * 将 _AO 贴图的红色通道合并到 _D 贴图的 Alpha 通道，输出为 _DAO.tga 文件
     * 将 _R 贴图的红色通道合并到 _N 贴图的蓝色通道，输出为 _NR.tga 文件

3. 输出要求：
   - 所有合并后的纹理文件保存在原目录下的 Textures 子文件夹中
   - 输出格式均为 TGA 格式
   - 只处理包含"Leaf"或"Trunk"关键词的纹理组

使用方法：
1. 将需要处理的文件路径复制到剪贴板，然后运行脚本
2. 或者直接运行脚本，在弹出的文件选择对话框中选择文件
"""

import os
import re
import sys
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image

def get_clipboard_files():
    """
    获取剪贴板中的文件路径
    """
    try:
        # 创建一个隐藏的根窗口
        root = tk.Tk()
        root.withdraw()
        
        # 尝试从剪贴板读取文件路径
        clipboard_content = root.clipboard_get()
        root.destroy()
        
        # 如果剪贴板内容为空或只包含无效字符，则直接打开文件选择对话框
        if not clipboard_content or not clipboard_content.strip():
            print("剪贴板为空")
            raise Exception("剪贴板为空")
        
        print(f"剪贴板内容: {repr(clipboard_content)}")
        
        # 分割可能的多个文件路径
        files = clipboard_content.strip().split('\n')
        file_paths = []
        for file in files:
            file = file.strip().strip('"')
            if file and os.path.exists(file):  # 确保文件路径不为空且文件存在
                file_paths.append(file)
            elif file:  # 如果文件路径不为空但文件不存在
                print(f"文件不存在或无法访问: {file}")
        
        if not file_paths:
            print("剪贴板中没有有效的文件路径")
            raise Exception("剪贴板中没有有效的文件路径")
            
        return file_paths
    except Exception as e:
        print(f"从剪贴板获取文件时出错: {e}")
        # 如果无法从剪贴板获取，提供文件选择对话框
        root = tk.Tk()
        root.withdraw()
        files = filedialog.askopenfilenames(title="选择纹理文件")
        root.destroy()
        file_paths = list(files)
        print(f"通过文件选择对话框选择了 {len(file_paths)} 个文件")
        return file_paths

def group_files_by_name(file_paths):
    """
    根据文件名（除后缀外）对文件进行分组
    """
    groups = {}
    for file_path in file_paths:
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        file_name, ext = os.path.splitext(base_name)
        
        # 对于以_D、_A、_N、_R或_S结尾的文件，将其归类到去掉这些后缀的基础名称组中
        if file_name.endswith("_D") or file_name.endswith("_A") or \
           file_name.endswith("_N") or file_name.endswith("_R") or file_name.endswith("_S"):
            # 提取基础名称（去掉_D、_A、_N、_R或_S）
            base_key = re.sub(r'_[DANRS]$', '', file_name)
        elif file_name.endswith("_AO") and "Trunk" in file_name:
            # 对于Trunk的_AO文件，需要与对应的Trunk组合并
            base_key = re.sub(r'_AO$', '', file_name)
        else:
            base_key = file_name
            
        # 将文件按基础名称分组
        if base_key not in groups:
            groups[base_key] = []
        groups[base_key].append(file_path)
    
    return groups

def identify_leaf_textures(groups):
    """
    识别包含Leaf或Trunk字段的图片资源
    """
    leaf_groups = {}
    for name, files in groups.items():
        # 检查文件名是否包含"Leaf"或"Trunk"
        if "Leaf" in name or "Trunk" in name:
            leaf_groups[name] = files
    
    return leaf_groups

def merge_texture_channels(leaf_groups):
    """
    将后缀为"_A"的贴图R通道合并到后缀"_D"的A通道，并存储为新的资源修改后缀名为"_DA"
    同时将_R和_S文件的R通道分别合并到_N文件的BA通道，并存储为后缀名_NRS
    """
    for name, files in leaf_groups.items():
        # 查找_D和_A文件
        d_file = None
        a_file = None
        
        # 查找_N、_R和_S文件
        n_file = None
        r_file = None
        s_file = None
        
        # 查找Trunk相关的文件
        ao_file = None
        
        for file in files:
            base_name = os.path.basename(file)
            file_name, ext = os.path.splitext(base_name)
            
            if file_name.endswith("_D"):
                d_file = file
            elif file_name.endswith("_A"):
                a_file = file
            elif file_name.endswith("_N"):
                n_file = file
            elif file_name.endswith("_R"):
                r_file = file
            elif file_name.endswith("_S"):
                s_file = file
            elif file_name.endswith("_AO"):
                ao_file = file
        
        # 如果同时存在_D和_A文件，则进行合并
        if d_file and a_file:
            try:
                # 读取图像
                print(f"正在处理: {d_file} 和 {a_file}")
                
                # 使用Pillow读取TGA文件
                def load_tga_image(file_path):
                    try:
                        # 使用Pillow读取
                        img_pil = Image.open(file_path)
                        
                        # 转换为numpy数组
                        img_array = np.array(img_pil)
                        
                        # 转换为OpenCV格式
                        if img_array.ndim == 3:
                            # PIL使用RGB，OpenCV使用BGR
                            if img_array.shape[2] == 3:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                            elif img_array.shape[2] == 4:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                            else:
                                img_cv = img_array
                        else:
                            img_cv = img_array
                            
                        return img_cv
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {e}")
                        return None
                
                img_d = load_tga_image(d_file)
                img_a = load_tga_image(a_file)
                
                # 检查文件是否成功读取
                if img_d is None:
                    print(f"警告: 无法读取文件 {d_file}")
                    continue
                if img_a is None:
                    print(f"警告: 无法读取文件 {a_file}")
                    continue
                
                # 确保图像是四通道（RGBA）
                if len(img_d.shape) == 3 and img_d.shape[2] == 3:
                    # 添加alpha通道
                    alpha_channel = np.ones((img_d.shape[0], img_d.shape[1], 1), dtype=img_d.dtype) * 255
                    img_d = np.concatenate((img_d, alpha_channel), axis=2)
                elif len(img_d.shape) == 2:
                    # 灰度图转RGBA
                    img_d = cv2.cvtColor(img_d, cv2.COLOR_GRAY2RGBA)
                
                # 确保A贴图是单通道或获取其R通道
                if len(img_a.shape) == 3:
                    if img_a.shape[2] >= 3:
                        # 获取R通道 (在OpenCV中是第3个通道，索引为2)
                        r_channel = img_a[:, :, 2]
                    else:
                        r_channel = img_a[:, :, 0]
                else:
                    r_channel = img_a
                
                # 将A贴图的R通道复制到D贴图的Alpha通道
                img_d[:, :, 3] = r_channel
                
                # 生成新文件名，将_D改为_DA
                new_name = re.sub(r'_D$', '_DA', os.path.splitext(d_file)[0])
                
                # 确保输出目录存在
                output_dir = os.path.join(os.path.dirname(d_file), "Textures")
                os.makedirs(output_dir, exist_ok=True)
                
                # 输出为tga格式
                output_path = os.path.join(output_dir, os.path.basename(new_name) + ".tga")
                
                # 保存合并后的图像
                # 转换回Pillow格式进行保存
                if len(img_d.shape) == 3 and img_d.shape[2] == 4:
                    # BGRA转RGBA
                    img_pil = cv2.cvtColor(img_d, cv2.COLOR_BGRA2RGBA)
                elif len(img_d.shape) == 3 and img_d.shape[2] == 3:
                    # BGR转RGB
                    img_pil = cv2.cvtColor(img_d, cv2.COLOR_BGR2RGB)
                else:
                    img_pil = img_d
                    
                # 使用Pillow保存
                Image.fromarray(img_pil).save(output_path)
                print(f"合并成功: {output_path}")
                
            except Exception as e:
                print(f"处理文件组 {name} 时出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 如果同时存在_N、_R和_S文件，则进行合并
        if n_file and r_file and s_file:
            try:
                # 读取图像
                print(f"正在处理: {n_file}, {r_file} 和 {s_file}")
                
                # 使用Pillow读取TGA文件
                def load_tga_image(file_path):
                    try:
                        # 使用Pillow读取
                        img_pil = Image.open(file_path)
                        
                        # 转换为numpy数组
                        img_array = np.array(img_pil)
                        
                        # 转换为OpenCV格式
                        if img_array.ndim == 3:
                            # PIL使用RGB，OpenCV使用BGR
                            if img_array.shape[2] == 3:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                            elif img_array.shape[2] == 4:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                            else:
                                img_cv = img_array
                        else:
                            img_cv = img_array
                            
                        return img_cv
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {e}")
                        return None
                
                img_n = load_tga_image(n_file)
                img_r = load_tga_image(r_file)
                img_s = load_tga_image(s_file)
                
                # 检查文件是否成功读取
                if img_n is None:
                    print(f"警告: 无法读取文件 {n_file}")
                    continue
                if img_r is None:
                    print(f"警告: 无法读取文件 {r_file}")
                    continue
                if img_s is None:
                    print(f"警告: 无法读取文件 {s_file}")
                    continue
                
                # 确保_N图像是四通道（RGBA）
                if len(img_n.shape) == 3 and img_n.shape[2] == 3:
                    # 添加alpha通道
                    alpha_channel = np.ones((img_n.shape[0], img_n.shape[1], 1), dtype=img_n.dtype) * 255
                    img_n = np.concatenate((img_n, alpha_channel), axis=2)
                elif len(img_n.shape) == 2:
                    # 灰度图转RGBA
                    img_n = cv2.cvtColor(img_n, cv2.COLOR_GRAY2RGBA)
                
                # 确保_R和_S贴图是单通道或获取其R通道
                def get_red_channel(img):
                    if len(img.shape) == 3:
                        if img.shape[2] >= 3:
                            # 获取R通道 (在OpenCV中是第3个通道，索引为2)
                            return img[:, :, 2]
                        else:
                            return img[:, :, 0]
                    else:
                        return img
                
                r_channel = get_red_channel(img_r)
                s_channel = get_red_channel(img_s)
                
                # 将_R贴图的R通道复制到_N贴图的B通道（索引0）
                # 将_S贴图的R通道复制到_N贴图的A通道（索引3）
                img_n[:, :, 0] = r_channel  # B通道
                img_n[:, :, 3] = s_channel  # A通道
                
                # 生成新文件名，将_N改为_NRS
                new_name = re.sub(r'_N$', '_NRS', os.path.splitext(n_file)[0])
                
                # 确保输出目录存在
                output_dir = os.path.join(os.path.dirname(n_file), "Textures")
                os.makedirs(output_dir, exist_ok=True)
                
                # 输出为tga格式
                output_path = os.path.join(output_dir, os.path.basename(new_name) + ".tga")
                
                # 保存合并后的图像
                # 转换回Pillow格式进行保存
                if len(img_n.shape) == 3 and img_n.shape[2] == 4:
                    # BGRA转RGBA
                    img_pil = cv2.cvtColor(img_n, cv2.COLOR_BGRA2RGBA)
                elif len(img_n.shape) == 3 and img_n.shape[2] == 3:
                    # BGR转RGB
                    img_pil = cv2.cvtColor(img_n, cv2.COLOR_BGR2RGB)
                else:
                    img_pil = img_n
                    
                # 使用Pillow保存为tga格式
                Image.fromarray(img_pil).save(output_path)
                print(f"合并成功: {output_path}")
                
            except Exception as e:
                print(f"处理文件组 {name} 时出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 处理Trunk相关的文件
        # 如果同时存在_D和_AO文件，则进行合并为_DAO
        if d_file and ao_file and "Trunk" in name:
            try:
                # 读取图像
                print(f"正在处理Trunk文件: {d_file} 和 {ao_file}")
                
                # 使用Pillow读取TGA文件
                def load_tga_image(file_path):
                    try:
                        # 使用Pillow读取
                        img_pil = Image.open(file_path)
                        
                        # 转换为numpy数组
                        img_array = np.array(img_pil)
                        
                        # 转换为OpenCV格式
                        if img_array.ndim == 3:
                            # PIL使用RGB，OpenCV使用BGR
                            if img_array.shape[2] == 3:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                            elif img_array.shape[2] == 4:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                            else:
                                img_cv = img_array
                        else:
                            img_cv = img_array
                            
                        return img_cv
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {e}")
                        return None
                
                img_d = load_tga_image(d_file)
                img_ao = load_tga_image(ao_file)
                
                # 检查文件是否成功读取
                if img_d is None:
                    print(f"警告: 无法读取文件 {d_file}")
                    continue
                if img_ao is None:
                    print(f"警告: 无法读取文件 {ao_file}")
                    continue
                
                # 确保图像是四通道（RGBA）
                if len(img_d.shape) == 3 and img_d.shape[2] == 3:
                    # 添加alpha通道
                    alpha_channel = np.ones((img_d.shape[0], img_d.shape[1], 1), dtype=img_d.dtype) * 255
                    img_d = np.concatenate((img_d, alpha_channel), axis=2)
                elif len(img_d.shape) == 2:
                    # 灰度图转RGBA
                    img_d = cv2.cvtColor(img_d, cv2.COLOR_GRAY2RGBA)
                
                # 确保AO贴图是单通道或获取其R通道
                if len(img_ao.shape) == 3:
                    if img_ao.shape[2] >= 3:
                        # 获取R通道 (在OpenCV中是第3个通道，索引为2)
                        r_channel = img_ao[:, :, 2]
                    else:
                        r_channel = img_ao[:, :, 0]
                else:
                    r_channel = img_ao
                
                # 将AO贴图的R通道复制到D贴图的Alpha通道
                img_d[:, :, 3] = r_channel
                
                # 生成新文件名，将_D改为_DAO
                new_name = re.sub(r'_D$', '_DAO', os.path.splitext(d_file)[0])
                
                # 确保输出目录存在
                output_dir = os.path.join(os.path.dirname(d_file), "Textures")
                os.makedirs(output_dir, exist_ok=True)
                
                # 输出为tga格式
                output_path = os.path.join(output_dir, os.path.basename(new_name) + ".tga")
                
                # 保存合并后的图像
                # 转换回Pillow格式进行保存
                if len(img_d.shape) == 3 and img_d.shape[2] == 4:
                    # BGRA转RGBA
                    img_pil = cv2.cvtColor(img_d, cv2.COLOR_BGRA2RGBA)
                elif len(img_d.shape) == 3 and img_d.shape[2] == 3:
                    # BGR转RGB
                    img_pil = cv2.cvtColor(img_d, cv2.COLOR_BGR2RGB)
                else:
                    img_pil = img_d
                    
                # 使用Pillow保存
                Image.fromarray(img_pil).save(output_path)
                print(f"Trunk合并成功: {output_path}")
                
            except Exception as e:
                print(f"处理Trunk文件组 {name} 时出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 如果同时存在_N和_R文件（Trunk相关），则进行合并为_NR
        if n_file and r_file and "Trunk" in name:
            try:
                # 读取图像
                print(f"正在处理Trunk文件: {n_file} 和 {r_file}")
                
                # 使用Pillow读取TGA文件
                def load_tga_image(file_path):
                    try:
                        # 使用Pillow读取
                        img_pil = Image.open(file_path)
                        
                        # 转换为numpy数组
                        img_array = np.array(img_pil)
                        
                        # 转换为OpenCV格式
                        if img_array.ndim == 3:
                            # PIL使用RGB，OpenCV使用BGR
                            if img_array.shape[2] == 3:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                            elif img_array.shape[2] == 4:
                                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                            else:
                                img_cv = img_array
                        else:
                            img_cv = img_array
                            
                        return img_cv
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {e}")
                        return None
                
                img_n = load_tga_image(n_file)
                img_r = load_tga_image(r_file)
                
                # 检查文件是否成功读取
                if img_n is None:
                    print(f"警告: 无法读取文件 {n_file}")
                    continue
                if img_r is None:
                    print(f"警告: 无法读取文件 {r_file}")
                    continue
                
                # 确保_N图像是四通道（RGBA）
                if len(img_n.shape) == 3 and img_n.shape[2] == 3:
                    # 添加alpha通道
                    alpha_channel = np.ones((img_n.shape[0], img_n.shape[1], 1), dtype=img_n.dtype) * 255
                    img_n = np.concatenate((img_n, alpha_channel), axis=2)
                elif len(img_n.shape) == 2:
                    # 灰度图转RGBA
                    img_n = cv2.cvtColor(img_n, cv2.COLOR_GRAY2RGBA)
                
                # 确保_R贴图是单通道或获取其R通道
                if len(img_r.shape) == 3:
                    if img_r.shape[2] >= 3:
                        # 获取R通道 (在OpenCV中是第3个通道，索引为2)
                        r_channel = img_r[:, :, 2]
                    else:
                        r_channel = img_r[:, :, 0]
                else:
                    r_channel = img_r
                
                # 将_R贴图的R通道复制到_N贴图的B通道（索引0）
                img_n[:, :, 0] = r_channel  # B通道
                
                # 生成新文件名，将_N改为_NR
                new_name = re.sub(r'_N$', '_NR', os.path.splitext(n_file)[0])
                
                # 确保输出目录存在
                output_dir = os.path.join(os.path.dirname(n_file), "Textures")
                os.makedirs(output_dir, exist_ok=True)
                
                # 输出为tga格式
                output_path = os.path.join(output_dir, os.path.basename(new_name) + ".tga")
                
                # 保存合并后的图像
                # 转换回Pillow格式进行保存
                if len(img_n.shape) == 3 and img_n.shape[2] == 4:
                    # BGRA转RGBA
                    img_pil = cv2.cvtColor(img_n, cv2.COLOR_BGRA2RGBA)
                elif len(img_n.shape) == 3 and img_n.shape[2] == 3:
                    # BGR转RGB
                    img_pil = cv2.cvtColor(img_n, cv2.COLOR_BGR2RGB)
                else:
                    img_pil = img_n
                    
                # 使用Pillow保存为tga格式
                Image.fromarray(img_pil).save(output_path)
                print(f"Trunk合并成功: {output_path}")
                
            except Exception as e:
                print(f"处理Trunk文件组 {name} 时出错: {e}")
                import traceback
                traceback.print_exc()

def main():
    print("开始处理纹理合并...")
    
    # 获取文件路径
    file_paths = get_clipboard_files()
    if not file_paths:
        print("未找到文件")
        return
    
    print(f"找到 {len(file_paths)} 个文件")
    for i, path in enumerate(file_paths):
        print(f"  {i+1}. {path}")
    
    # 按文件名分组
    groups = group_files_by_name(file_paths)
    print(f"文件分组完成，共 {len(groups)} 组")
    for name, files in groups.items():
        print(f"  组 '{name}' 包含 {len(files)} 个文件:")
        for file in files:
            print(f"    - {file}")
    
    # 识别Leaf纹理
    leaf_groups = identify_leaf_textures(groups)
    print(f"识别到 {len(leaf_groups)} 个Leaf纹理组")
    for name, files in leaf_groups.items():
        print(f"  Leaf组 '{name}' 包含 {len(files)} 个文件:")
        for file in files:
            print(f"    - {file}")
    
    # 合并通道
    merge_texture_channels(leaf_groups)
    
    print("纹理合并处理完成")

if __name__ == "__main__":
    main()