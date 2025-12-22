#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
贴图通道转换脚本
递归搜索目录下的所有贴图，根据名称后缀识别贴图通道转换规则，
将_MRA贴图的R通道覆盖到_C贴图的A通道，并另存为_DM后缀的新纹理，
所有操作的贴图格式都是tga格式
"""

import os
import cv2
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox
import sys


def load_tga_image(file_path):
    """
    使用多种方法加载TGA图像，提高兼容性
    遵循TGA格式处理最佳实践
    
    Args:
        file_path (str): TGA文件路径
        
    Returns:
        numpy.ndarray: 图像数据，OpenCV格式(BGR或BGRA)
    """
    # 方法1: 使用PIL加载
    try:
        # 使用PIL打开图像
        pil_image = Image.open(file_path)
        
        # 转换为numpy数组
        if pil_image.mode == 'RGBA':
            # RGBA格式
            rgba_array = np.array(pil_image)
            # PIL使用RGBA，OpenCV使用BGRA
            bgra_array = rgba_array[:, :, [2, 1, 0, 3]]  # RGB->BGR, A保持不变
            print(f"PIL读取成功 (RGBA): {file_path}")
            return bgra_array
        elif pil_image.mode == 'RGB':
            # RGB格式
            rgb_array = np.array(pil_image)
            # PIL使用RGB，OpenCV使用BGR
            bgr_array = rgb_array[:, :, [2, 1, 0]]  # RGB->BGR
            print(f"PIL读取成功 (RGB): {file_path}")
            return bgr_array
        elif pil_image.mode == 'P':  # 调色板模式
            # 转换为RGB
            pil_image = pil_image.convert('RGB')
            rgb_array = np.array(pil_image)
            bgr_array = rgb_array[:, :, [2, 1, 0]]
            print(f"PIL读取成功 (Palette->RGB): {file_path}")
            return bgr_array
        elif pil_image.mode == 'LA':  # 灰度+Alpha
            # 转换为RGBA
            pil_image = pil_image.convert('RGBA')
            rgba_array = np.array(pil_image)
            bgra_array = rgba_array[:, :, [2, 1, 0, 3]]
            print(f"PIL读取成功 (LA->RGBA): {file_path}")
            return bgra_array
        elif pil_image.mode == 'L':  # 灰度
            gray_array = np.array(pil_image)
            print(f"PIL读取成功 (L): {file_path}")
            return gray_array
        else:
            # 其他格式，尝试转换为RGBA再处理
            pil_image = pil_image.convert('RGBA')
            rgba_array = np.array(pil_image)
            bgra_array = rgba_array[:, :, [2, 1, 0, 3]]
            print(f"PIL读取成功 (Other->{pil_image.mode}->RGBA): {file_path}")
            return bgra_array
    except Exception as e:
        print(f"PIL读取图像失败: {file_path}, 错误: {str(e)}")
    
    # 方法2: 回退到OpenCV
    try:
        image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if image is not None:
            print(f"OpenCV读取成功: {file_path}")
            return image
        else:
            print(f"OpenCV无法读取图像: {file_path}")
    except Exception as e:
        print(f"OpenCV读取图像失败: {file_path}, 错误: {str(e)}")
    
    # 如果两种方法都失败
    return None


def convert_texture_channels(base_directory):
    """
    递归搜索目录中的贴图，根据名称后缀识别贴图通道转换规则，
    将_MRA贴图的R通道覆盖到_C贴图的A通道，并另存为_DM后缀的新纹理。

    Args:
        base_directory (str): 要搜索的基础目录路径
        
    Returns:
        list: 生成的文件路径列表
    """
    generated_files = []
    
    # 检查基础目录是否存在
    if not os.path.exists(base_directory):
        print(f"错误: 目录不存在: {base_directory}")
        return generated_files
        
    # 遍历目录及其子目录
    for root, dirs, files in os.walk(base_directory):
        print(f"正在扫描目录: {root}")
        
        # 创建文件映射，按基础名称分组
        file_map = {}

        # 筛选出相关的贴图文件
        for file in files:
            if file.lower().endswith('.tga'):
                # 获取文件名（不含扩展名）
                base_name = os.path.splitext(file)[0]

                # 按照后缀分类文件
                if base_name.endswith('_C'):
                    base_key = base_name[:-2]  # 移除 "_C"
                    if base_key not in file_map:
                        file_map[base_key] = {}
                    file_map[base_key]['C'] = os.path.join(root, file)
                elif base_name.endswith('_MRA'):
                    base_key = base_name[:-4]  # 移除 "_MRA"
                    if base_key not in file_map:
                        file_map[base_key] = {}
                    file_map[base_key]['MRA'] = os.path.join(root, file)
                elif base_name.endswith('_NCE'):
                    base_key = base_name[:-4]  # 移除 "_NCE"
                    if base_key not in file_map:
                        file_map[base_key] = {}
                    file_map[base_key]['NCE'] = os.path.join(root, file)
                elif base_name.endswith('_UniqueMask'):
                    base_key = base_name[:-10]  # 移除 "_UniqueMask"
                    if base_key not in file_map:
                        file_map[base_key] = {}
                    file_map[base_key]['UniqueMask'] = os.path.join(root, file)

        # 处理每一对匹配的文件
        processed_count = 0
        total_files = sum(1 for fg in file_map.values() if 'NCE' in fg)
        current_file = 0
        
        for base_key, file_group in file_map.items():
            if 'C' in file_group and 'MRA' in file_group:
                c_file_path = file_group['C']
                mra_file_path = file_group['MRA']
                
                # 构造输出文件路径
                dm_file_path = os.path.join(root, f"{base_key}_DM.tga")
                
                # 执行通道转换
                if process_texture_conversion(c_file_path, mra_file_path, dm_file_path):
                    generated_files.append(dm_file_path)
                    processed_count += 1
                    
            # 处理ORS贴图创建
            if 'C' in file_group and 'MRA' in file_group:
                c_file_path = file_group['C']
                mra_file_path = file_group['MRA']
                
                # 构造ORS输出文件路径
                ors_file_path = os.path.join(root, f"{base_key}_ORS.tga")
                
                # 创建ORS贴图
                if create_ors_texture(c_file_path, mra_file_path, ors_file_path):
                    generated_files.append(ors_file_path)
                    processed_count += 1
                    
            # 处理N贴图和S贴图创建
            if 'NCE' in file_group:
                current_file += 1
                progress = int(current_file/total_files*100) if total_files > 0 else 0
                print(f"\n处理进度: {current_file}/{total_files} ({progress}%)")
                print(f"正在处理: {base_key}")
                
                nce_file_path = file_group['NCE']
                
                # 构造N和S输出文件路径
                n_file_path = os.path.join(root, f"{base_key}_N.tga")
                s_file_path = os.path.join(root, f"{base_key}_S.tga")
                special_mask_file_path = os.path.join(root, f"{base_key}_SpecialMask.tga")
                
                # 创建N贴图
                if create_n_texture(nce_file_path, n_file_path):
                    generated_files.append(n_file_path)
                    processed_count += 1
                    
                # 创建S贴图和Special贴图
                unique_mask_path = file_group.get('UniqueMask', None)
                # 如果上面的方法没有找到UniqueMask，尝试其他匹配方式
                if unique_mask_path is None:
                    # 查找是否有匹配的UniqueMask文件（不带下划线前缀的情况）
                    potential_unique_mask = f"{base_key}UniqueMask"
                    for file in files:
                        if os.path.splitext(file)[0] == potential_unique_mask:
                            unique_mask_path = os.path.join(root, file)
                            print(f"通过备用方法找到UniqueMask文件: {file}")
                            break
                    
                    # 如果还是没找到，尝试直接构造文件名
                    if unique_mask_path is None:
                        potential_unique_mask_file = f"{base_key}_UniqueMask.tga"
                        potential_path = os.path.join(root, potential_unique_mask_file)
                        if os.path.exists(potential_path):
                            unique_mask_path = potential_path
                            print(f"通过文件名构造找到UniqueMask文件: {potential_unique_mask_file}")
                
                success = create_s_and_special_textures(nce_file_path, unique_mask_path, s_file_path, special_mask_file_path)
                if success:
                    generated_files.append(special_mask_file_path)
                    if os.path.exists(s_file_path):
                        generated_files.append(s_file_path)
                    processed_count += 1
                    print(f"完成处理: {base_key}")
                else:
                    print(f"处理失败: {base_key}")

        if total_files > 0:
            print(f"\n总体进度: 完成 {processed_count}/{total_files} 个文件的处理")

        if processed_count > 0:
            print(f"在目录 {root} 中处理了 {processed_count} 个操作")
            
    return generated_files


def process_texture_conversion(c_file_path, mra_file_path, dm_file_path):
    """
    将_MRA贴图的R通道覆盖到_C贴图的A通道，并保存为_DM后缀的新纹理

    Args:
        c_file_path (str): _C贴图文件路径
        mra_file_path (str): _MRA贴图文件路径
        dm_file_path (str): 输出_DM贴图文件路径
        
    Returns:
        bool: 是否成功处理
    """
    try:
        print(f"\n处理DM文件对:")
        print(f"  C文件: {os.path.basename(c_file_path)}")
        print(f"  MRA文件: {os.path.basename(mra_file_path)}")
        
        # 读取_C贴图 (Color贴图)
        c_image = load_tga_image(c_file_path)
        if c_image is None:
            print(f"无法读取C文件: {c_file_path}")
            return False

        # 读取_MRA贴图 (Metallic-Roughness-Ambient Occlusion贴图)
        mra_image = load_tga_image(mra_file_path)
        if mra_image is None:
            print(f"无法读取MRA文件: {mra_file_path}")
            return False

        # 检查图像尺寸是否匹配
        if c_image.shape[:2] != mra_image.shape[:2]:
            print(f"图像尺寸不匹配:")
            print(f"  {c_file_path}: {c_image.shape[:2]}")
            print(f"  {mra_file_path}: {mra_image.shape[:2]}")
            return False

        # 如果_C贴图没有alpha通道，则添加一个
        if len(c_image.shape) == 2:
            # 灰度图像，转换为BGRA
            height, width = c_image.shape
            b_channel = c_image
            g_channel = c_image
            r_channel = c_image
            a_channel = np.full((height, width), 255, dtype=c_image.dtype)
            c_image = np.stack([b_channel, g_channel, r_channel, a_channel], axis=2)
            print("为灰度图像添加了alpha通道")
        elif len(c_image.shape) == 3 and c_image.shape[2] == 3:
            # BGR图像，添加alpha通道，默认值为255(完全不透明)
            alpha_channel = np.full((c_image.shape[0], c_image.shape[1], 1), 255, dtype=c_image.dtype)
            c_image = np.concatenate((c_image, alpha_channel), axis=2)
            print("为BGR图像添加了alpha通道")

        # 获取_MRA贴图的R通道 (在BGR格式中，R通道是索引2)
        # 确保我们能正确获取红色通道
        if len(mra_image.shape) == 3:
            mra_r_channel = mra_image[:, :, 2]  # BGR格式中的R通道
            print(f"从MRA图像获取R通道，形状: {mra_r_channel.shape}")
        elif len(mra_image.shape) == 2:
            mra_r_channel = mra_image  # 灰度图像
            print(f"从MRA图像获取灰度通道，形状: {mra_r_channel.shape}")
        else:
            print(f"MRA图像格式未知: {mra_image.shape}")
            return False

        # 将_MRA贴图的R通道赋值给_C贴图的A通道 (索引3)
        c_image[:, :, 3] = mra_r_channel
        print("成功将MRA的R通道复制到C图像的A通道")

        # 保存为_DM贴图
        if save_tga_image(c_image, dm_file_path):
            print(f"成功生成文件: {os.path.basename(dm_file_path)}")
            return True
        else:
            print(f"保存文件失败: {dm_file_path}")
            return False

    except Exception as e:
        print(f"处理DM文件时出错:")
        print(f"  C文件: {c_file_path}")
        print(f"  MRA文件: {mra_file_path}")
        print(f"  错误: {str(e)}")
        return False


def create_ors_texture(c_file_path, mra_file_path, ors_file_path):
    """
    创建_ORS贴图：
    1. 将_MRA贴图的B通道放到_ORS贴图的R通道
    2. 将_MRA贴图的G通道放到_ORS贴图的G通道
    3. _ORS贴图的B通道填0.3的值
    4. 将_C贴图的A通道放到_ORS贴图的A通道

    Args:
        c_file_path (str): _C贴图文件路径
        mra_file_path (str): _MRA贴图文件路径
        ors_file_path (str): 输出_ORS贴图文件路径
        
    Returns:
        bool: 是否成功创建
    """
    try:
        print(f"\n创建ORS贴图:")
        print(f"  C文件: {os.path.basename(c_file_path)}")
        print(f"  MRA文件: {os.path.basename(mra_file_path)}")
        
        # 读取_C贴图和_MRA贴图
        c_image = load_tga_image(c_file_path)
        if c_image is None:
            print(f"无法读取C文件: {c_file_path}")
            return False
            
        mra_image = load_tga_image(mra_file_path)
        if mra_image is None:
            print(f"无法读取MRA文件: {mra_file_path}")
            return False

        # 检查图像尺寸是否匹配
        if c_image.shape[:2] != mra_image.shape[:2]:
            print(f"图像尺寸不匹配:")
            print(f"  {c_file_path}: {c_image.shape[:2]}")
            print(f"  {mra_file_path}: {mra_image.shape[:2]}")
            return False

        height, width = c_image.shape[:2]
        
        # 创建ORS贴图 (BGRA格式)
        ors_image = np.zeros((height, width, 4), dtype=np.uint8)
        
        # 1. 将_MRA贴图的B通道(索引0)放到_ORS贴图的R通道(索引2)
        if len(mra_image.shape) == 3:
            ors_image[:, :, 2] = mra_image[:, :, 0]  # B->R
        elif len(mra_image.shape) == 2:
            ors_image[:, :, 2] = mra_image  # 灰度->R
            
        # 2. 将_MRA贴图的G通道(索引1)放到_ORS贴图的G通道(索引1)
        if len(mra_image.shape) == 3:
            ors_image[:, :, 1] = mra_image[:, :, 1]  # G->G
        elif len(mra_image.shape) == 2:
            ors_image[:, :, 1] = mra_image  # 灰度->G
            
        # 3. _ORS贴图的B通道(索引0)填0.3的值 (约77)
        ors_image[:, :, 0] = np.full((height, width), int(0.3 * 255), dtype=np.uint8)
        
        # 4. 将_C贴图的A通道放到_ORS贴图的A通道(索引3)
        if len(c_image.shape) == 3 and c_image.shape[2] == 4:
            ors_image[:, :, 3] = c_image[:, :, 3]  # A->A
        else:
            # 如果C图像没有alpha通道，默认为255
            ors_image[:, :, 3] = np.full((height, width), 255, dtype=np.uint8)
            
        # 保存ORS贴图
        if save_tga_image(ors_image, ors_file_path):
            print(f"成功生成ORS文件: {os.path.basename(ors_file_path)}")
            return True
        else:
            print(f"保存ORS文件失败: {ors_file_path}")
            return False
            
    except Exception as e:
        print(f"创建ORS贴图时出错:")
        print(f"  C文件: {c_file_path}")
        print(f"  MRA文件: {mra_file_path}")
        print(f"  错误: {str(e)}")
        return False


def create_n_texture(nce_file_path, n_file_path):
    """
    创建_N贴图：
    1. 将_NCE后缀的RG通道放到_N后缀RG通道
    2. 通过RG通道的法线信息计算出法线B通道的值

    Args:
        nce_file_path (str): _NCE贴图文件路径
        n_file_path (str): 输出_N贴图文件路径
        
    Returns:
        bool: 是否成功创建
    """
    try:
        print(f"\n创建N贴图:")
        print(f"  NCE文件: {os.path.basename(nce_file_path)}")
        
        # 读取_NCE贴图
        nce_image = load_tga_image(nce_file_path)
        if nce_image is None:
            print(f"无法读取NCE文件: {nce_file_path}")
            return False

        height, width = nce_image.shape[:2]
        
        # 创建N贴图 (BGR格式)
        n_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 1. 将_NCE的RG通道放到_N的RG通道
        if len(nce_image.shape) == 3:
            n_image[:, :, 2] = nce_image[:, :, 2]  # R->R
            n_image[:, :, 1] = nce_image[:, :, 1]  # G->G
        elif len(nce_image.shape) == 2:
            # 灰度图像，复制到RG通道
            n_image[:, :, 2] = nce_image  # 灰度->R
            n_image[:, :, 1] = nce_image  # 灰度->G
            
        # 2. 通过RG通道计算法线B通道的值
        # 法线贴图公式: B = sqrt(1 - R^2 - G^2)
        # 归一化RG通道到[-1, 1]范围
        r_norm = n_image[:, :, 2].astype(np.float32) / 127.5 - 1.0
        g_norm = n_image[:, :, 1].astype(np.float32) / 127.5 - 1.0
        
        # 计算B通道
        b_squared = 1.0 - np.square(r_norm) - np.square(g_norm)
        b_norm = np.sqrt(np.maximum(b_squared, 0))  # 防止负数开方
        
        # 转换回[0, 255]范围
        n_image[:, :, 0] = ((b_norm + 1.0) * 127.5).astype(np.uint8)  # B通道
        
        # 保存N贴图
        if save_tga_image(n_image, n_file_path):
            print(f"成功生成N文件: {os.path.basename(n_file_path)}")
            return True
        else:
            print(f"保存N文件失败: {n_file_path}")
            return False
            
    except Exception as e:
        print(f"创建N贴图时出错:")
        print(f"  NCE文件: {nce_file_path}")
        print(f"  错误: {str(e)}")
        return False


def create_s_and_special_textures(nce_file_path, unique_mask_path, s_file_path, special_mask_file_path):
    """
    创建_S贴图和SpecialMask贴图：
    1. 创建_S贴图填纯黑色（但如果_NCE贴图的A通道亮度值不超过0.1则不创建）
    2. SpecialMask贴图的通道规则：
       R: _NCE贴图B通道
       G: _UniqueMask贴图R通道
       B: _UniqueMask贴图B通道
       A: _UniqueMask贴图A通道

    Args:
        nce_file_path (str): _NCE贴图文件路径
        unique_mask_path (str): _UniqueMask贴图文件路径
        s_file_path (str): 输出_S贴图文件路径
        special_mask_file_path (str): 输出_SpecialMask贴图文件路径
        
    Returns:
        bool: 是否成功创建
    """
    try:
        print(f"\n创建S贴图和SpecialMask贴图:")
        print(f"  NCE文件: {os.path.basename(nce_file_path)}")
        if unique_mask_path:
            print(f"  UniqueMask文件: {os.path.basename(unique_mask_path)}")
        else:
            print("  未找到对应的UniqueMask文件")
        
        # 读取_NCE贴图
        nce_image = load_tga_image(nce_file_path)
        if nce_image is None:
            print(f"无法读取NCE文件: {nce_file_path}")
            return False

        height, width = nce_image.shape[:2]
        
        # 检查_NCE贴图的A通道是否超过0.1的亮度值
        nce_has_non_black_alpha = False
        if len(nce_image.shape) == 3 and nce_image.shape[2] == 4:
            # 检查alpha通道最大值是否超过0.1 (在0-1区间)
            max_alpha_value = np.max(nce_image[:, :, 3]) / 255.0
            if max_alpha_value > 0.1:
                nce_has_non_black_alpha = True
                print(f"NCE贴图的A通道最大亮度值为 {max_alpha_value:.3f}，超过阈值0.1")
            else:
                print(f"NCE贴图的A通道最大亮度值为 {max_alpha_value:.3f}，未超过阈值0.1，视为纯黑色")
        else:
            # 没有alpha通道，视为纯黑色
            print("NCE贴图没有alpha通道，视为纯黑色")
        
        # 1. 创建_S贴图填纯黑色（除非NCE的A通道亮度值超过0.1）
        if nce_has_non_black_alpha:
            s_image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # 将_NCE后缀的A通道放到_S的B通道(索引0)
            if len(nce_image.shape) == 3 and nce_image.shape[2] == 4:
                s_image[:, :, 0] = nce_image[:, :, 3]  # A->B
            else:
                # 如果NCE图像没有alpha通道，默认为0
                s_image[:, :, 0] = np.zeros((height, width), dtype=np.uint8)
                
            # 保存S贴图
            if save_tga_image(s_image, s_file_path):
                print(f"成功生成S文件: {os.path.basename(s_file_path)}")
            else:
                print(f"保存S文件失败: {s_file_path}")
                return False
        else:
            print("由于NCE贴图的A通道亮度值未超过0.1，跳过S贴图创建")
        
        # 2. 创建SpecialMask贴图
        # 读取_UniqueMask贴图
        unique_mask_image = None
        if unique_mask_path and os.path.exists(unique_mask_path):
            unique_mask_image = load_tga_image(unique_mask_path)
            if unique_mask_image is None:
                print(f"无法读取UniqueMask文件: {unique_mask_path}")
            else:
                print(f"成功读取UniqueMask文件: {os.path.basename(unique_mask_path)}, 尺寸: {unique_mask_image.shape}")
                # 检查尺寸是否匹配
                if unique_mask_image.shape[:2] != (height, width):
                    print(f"警告: UniqueMask图像尺寸 {unique_mask_image.shape[:2]} 与NCE图像尺寸 {(height, width)} 不匹配")
        else:
            if unique_mask_path:
                print(f"UniqueMask文件不存在: {unique_mask_path}")
            else:
                print("没有提供UniqueMask文件路径")
        
        # 创建SpecialMask贴图 (BGRA格式)
        special_mask_image = np.zeros((height, width, 4), dtype=np.uint8)
        
        # R: _NCE贴图B通道(索引0)
        if len(nce_image.shape) == 3:
            special_mask_image[:, :, 2] = nce_image[:, :, 0]  # B->R
            print("已设置SpecialMask的R通道（来自NCE的B通道）")
        elif len(nce_image.shape) == 2:
            special_mask_image[:, :, 2] = nce_image  # 灰度->R
            print("已设置SpecialMask的R通道（来自NCE的灰度通道）")
            
        # G: _UniqueMask贴图R通道(索引2)，如果没有则为0
        if unique_mask_image is not None:
            if len(unique_mask_image.shape) == 3 and unique_mask_image.shape[2] >= 3:
                special_mask_image[:, :, 1] = unique_mask_image[:, :, 2]  # R->G
                print("已设置SpecialMask的G通道（来自UniqueMask的R通道）")
            elif len(unique_mask_image.shape) == 2:
                # 灰度图像，复制到G通道
                special_mask_image[:, :, 1] = unique_mask_image
                print("已设置SpecialMask的G通道（来自UniqueMask的灰度通道）")
            else:
                special_mask_image[:, :, 1] = np.zeros((height, width), dtype=np.uint8)
                print("已设置SpecialMask的G通道（默认为0）")
        else:
            special_mask_image[:, :, 1] = np.zeros((height, width), dtype=np.uint8)
            print("已设置SpecialMask的G通道（默认为0，因为没有UniqueMask）")
            
        # B: _UniqueMask贴图B通道(索引0)，如果没有则为0
        if unique_mask_image is not None:
            if len(unique_mask_image.shape) == 3 and unique_mask_image.shape[2] >= 3:
                special_mask_image[:, :, 0] = unique_mask_image[:, :, 0]  # B->B
                print("已设置SpecialMask的B通道（来自UniqueMask的B通道）")
            elif len(unique_mask_image.shape) == 2:
                # 灰度图像，复制到B通道
                special_mask_image[:, :, 0] = unique_mask_image
                print("已设置SpecialMask的B通道（来自UniqueMask的灰度通道）")
            else:
                special_mask_image[:, :, 0] = np.zeros((height, width), dtype=np.uint8)
                print("已设置SpecialMask的B通道（默认为0）")
        else:
            special_mask_image[:, :, 0] = np.zeros((height, width), dtype=np.uint8)
            print("已设置SpecialMask的B通道（默认为0，因为没有UniqueMask）")
            
        # A: _UniqueMask贴图A通道(索引3)，如果没有则为255
        if unique_mask_image is not None:
            if len(unique_mask_image.shape) == 3 and unique_mask_image.shape[2] == 4:
                special_mask_image[:, :, 3] = unique_mask_image[:, :, 3]  # A->A
                print("已设置SpecialMask的A通道（来自UniqueMask的A通道）")
            elif len(unique_mask_image.shape) == 3 and unique_mask_image.shape[2] == 3:
                # 3通道图像，使用平均值作为A通道基础
                special_mask_image[:, :, 3] = np.mean(unique_mask_image, axis=2, dtype=np.uint8)
                print("已设置SpecialMask的A通道（来自UniqueMask的平均值）")
            elif len(unique_mask_image.shape) == 2:
                # 灰度图像，直接用作A通道
                special_mask_image[:, :, 3] = unique_mask_image
                print("已设置SpecialMask的A通道（来自UniqueMask的灰度通道）")
            else:
                special_mask_image[:, :, 3] = np.full((height, width), 255, dtype=np.uint8)
                print("已设置SpecialMask的A通道（默认为255）")
        else:
            special_mask_image[:, :, 3] = np.full((height, width), 255, dtype=np.uint8)
            print("已设置SpecialMask的A通道（默认为255，因为没有UniqueMask）")
        
        # 保存SpecialMask贴图
        if save_tga_image(special_mask_image, special_mask_file_path):
            print(f"成功生成SpecialMask文件: {os.path.basename(special_mask_file_path)}")
            return True
        else:
            print(f"保存SpecialMask文件失败: {special_mask_file_path}")
            return False
            
    except Exception as e:
        print(f"创建S贴图和SpecialMask贴图时出错:")
        print(f"  NCE文件: {nce_file_path}")
        print(f"  错误: {str(e)}")
        return False


def save_tga_image(image, file_path):
    """
    使用PIL保存TGA图像（遵循TGA格式处理最佳实践）

    Args:
        image (numpy.ndarray): 要保存的图像数据
        file_path (str): 输出文件路径
        
    Returns:
        bool: 是否成功保存
    """
    try:
        # 将OpenCV的BGR格式转换为PIL的RGB格式
        if len(image.shape) == 3 and image.shape[2] >= 3:
            # BGR到RGB转换
            if image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)
            elif image.shape[2] == 4:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                pil_image = Image.fromarray(rgb_image)
            
            # 保存为TGA格式
            pil_image.save(file_path, format='TGA')
            print(f"使用PIL成功保存TGA文件: {file_path}")
            return True
        elif len(image.shape) == 2:
            # 灰度图像
            pil_image = Image.fromarray(image)
            pil_image.save(file_path, format='TGA')
            print(f"使用PIL成功保存灰度TGA文件: {file_path}")
            return True
        else:
            print(f"不支持的图像格式用于保存: {image.shape}")
            return False
    except Exception as e:
        print(f"使用PIL保存图像失败: {file_path}, 错误: {str(e)}")
        # 回退到OpenCV保存方法
        try:
            cv2.imwrite(file_path, image)
            print(f"使用OpenCV成功保存图像: {file_path}")
            return True
        except Exception as e2:
            print(f"使用OpenCV保存图像也失败了: {file_path}, 错误: {str(e2)}")
            return False


def select_directory():
    """
    弹出文件夹选择对话框，让用户选择要处理的目录
    
    Returns:
        str: 用户选择的目录路径，如果取消选择则返回None
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)  # 确保对话框在最前面
    
    directory = filedialog.askdirectory(
        title="请选择包含贴图文件的目录",
        initialdir=os.path.abspath(".")
    )
    
    root.destroy()
    return directory


def show_completion_message(generated_files):
    """
    显示处理完成消息和生成的文件列表
    
    Args:
        generated_files (list): 生成的文件路径列表
    """
    if not generated_files:
        messagebox.showinfo("处理完成", "处理已完成，但没有生成新文件。")
        return
    
    message = f"处理已完成！共生成 {len(generated_files)} 个文件：\n\n"
    for file_path in generated_files:
        message += f"{os.path.basename(file_path)}\n"
    
    message += f"\n文件保存在各自原始文件所在的目录中。"
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showinfo("处理完成", message)
    root.destroy()


def main():
    """
    主函数
    """
    print("=" * 50)
    print("贴图通道转换工具")
    print("=" * 50)
    
    # 检查是否通过命令行参数提供了目录
    if len(sys.argv) > 1:
        base_directory = sys.argv[1]
    else:
        # 弹窗让用户选择目录
        base_directory = select_directory()
        if not base_directory:
            print("未选择目录，程序退出。")
            return
    
    # 如果目录存在则执行转换
    if os.path.exists(base_directory):
        print(f"开始处理目录: {base_directory}")
        generated_files = convert_texture_channels(base_directory)
        print("\n" + "=" * 50)
        print("处理完成!")
        print(f"总共生成 {len(generated_files)} 个文件")
        print("=" * 50)
        
        # 显示完成消息
        show_completion_message(generated_files)
    else:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showerror("错误", f"目录不存在: {base_directory}\n请确保选择的目录存在。")
        root.destroy()
        print(f"目录不存在: {base_directory}")


if __name__ == "__main__":
    main()