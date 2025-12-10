# 将贴图的Aplha通道值映射为0-1完整区间

import cv2
import numpy as np
import argparse
import os
import shutil
try:
    # 尝试导入PIL以更好地处理TGA文件
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

def save_image_tga(image, output_path):
    """
    保存图像为TGA格式
    
    Args:
        image (numpy.ndarray): 要保存的图像
        output_path (str): 输出文件路径
    """
    # 确保输出路径以.tga结尾
    if not output_path.lower().endswith('.tga'):
        name, _ = os.path.splitext(output_path)
        output_path = name + '.tga'
    
    # 如果PIL可用，使用PIL保存TGA文件以获得更好的兼容性
    if PIL_AVAILABLE:
        try:
            # 转换颜色通道顺序 (OpenCV使用BGR，PIL使用RGB)
            if len(image.shape) == 3 and image.shape[2] >= 3:
                image_rgb = image.copy()
                if image.shape[2] == 4:  # BGRA
                    # BGR to RGB，保持A
                    image_rgb[:, :, 0] = image[:, :, 2]  # R
                    image_rgb[:, :, 2] = image[:, :, 0]  # B
                elif image.shape[2] == 3:  # BGR
                    # BGR to RGB
                    image_rgb[:, :, 0] = image[:, :, 2]  # R
                    image_rgb[:, :, 2] = image[:, :, 0]  # B
                
                # 根据通道数创建PIL图像
                if image.shape[2] == 4:
                    pil_image = Image.fromarray(image_rgb, 'RGBA')
                elif image.shape[2] == 3:
                    pil_image = Image.fromarray(image_rgb, 'RGB')
                else:
                    pil_image = Image.fromarray(image_rgb)
                
                pil_image.save(output_path, 'TGA')
                return True
        except Exception as e:
            print(f"使用PIL保存TGA时出错: {e}")
    
    # 如果PIL不可用或失败，使用OpenCV保存
    # 注意：OpenCV对TGA的支持有限，但对于基本的TGA文件应该可以工作
    return cv2.imwrite(output_path, image)

def load_image_with_fallback(image_path):
    """
    使用多种方法加载图像，支持更多格式包括TGA
    
    Args:
        image_path (str): 图像文件路径
        
    Returns:
        numpy.ndarray: 图像数据，如果失败返回None
    """
    image = None
    
    # 获取文件扩展名
    _, ext = os.path.splitext(image_path)
    
    # 首先尝试使用OpenCV加载
    try:
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is not None:
            print(f"使用OpenCV成功加载图像: {image_path}")
            return image
    except Exception as e:
        print(f"OpenCV加载图像时出现异常: {e}")
    
    # 如果OpenCV失败且是TGA文件且PIL可用，尝试使用PIL
    if PIL_AVAILABLE and ext.lower() in ['.tga', '.tpic']:
        try:
            print(f"尝试使用PIL加载TGA文件: {image_path}")
            pil_image = Image.open(image_path)
            
            # 转换为numpy数组
            if pil_image.mode == 'RGBA':
                # RGBA格式
                image = np.array(pil_image)
                # PIL使用RGB顺序，OpenCV使用BGR顺序，需要转换
                image[:, :, :3] = image[:, :, [2, 1, 0]]  # RGB to BGR
            elif pil_image.mode == 'RGB':
                # RGB格式
                image = np.array(pil_image)
                image = image[:, :, [2, 1, 0]]  # RGB to BGR
            elif pil_image.mode == 'LA':
                # 灰度+Alpha
                image = np.array(pil_image)
                # 转换为BGRA格式
                bgra = np.zeros((image.shape[0], image.shape[1], 4), dtype=image.dtype)
                bgra[:, :, 0] = bgra[:, :, 1] = bgra[:, :, 2] = image[:, :, 0]  # 灰度值复制到BGR
                bgra[:, :, 3] = image[:, :, 1]  # Alpha通道
                image = bgra
            elif pil_image.mode == 'L':
                # 灰度格式
                image = np.array(pil_image)
            else:
                # 其他格式，尝试转换为RGBA
                pil_image = pil_image.convert('RGBA')
                image = np.array(pil_image)
                image[:, :, :3] = image[:, :, [2, 1, 0]]  # RGB to BGR
            
            print(f"使用PIL成功加载图像: {image_path}")
            return image
        except Exception as e:
            print(f"PIL加载图像时出现异常: {e}")
    
    return image

def create_backup(image_path):
    """
    创建原图的备份文件
    
    Args:
        image_path (str): 原图像路径
        
    Returns:
        str: 备份文件路径
    """
    # 创建备份文件名
    name, ext = os.path.splitext(image_path)
    backup_path = f"{name}_backup{ext}"
    
    # 创建备份
    try:
        shutil.copy2(image_path, backup_path)
        print(f"原图已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"创建备份失败: {e}")
        return None

def process_alpha_channel(image_path, output_path=None):
    """
    处理图像的Alpha通道
    
    算法步骤：
    1. 读取图像的Alpha通道
    2. 计算Alpha通道的最大值和最小值
    3. 计算max(|max-0.5|, |min-0.5|)
    4. 计算缩放比例 ratio = 0.5 / 上述值
    5. 对每个像素执行: ratio * (pixel - 0.5) + 0.5
    6. 将结果写回图像的Alpha通道
    
    Args:
        image_path (str): 输入图像路径
        output_path (str): 输出图像路径，默认为None，表示覆盖原图
    """
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图像文件不存在: {image_path}")
    
    # 创建备份文件
    backup_path = create_backup(image_path)
    
    # 使用多种方法加载图像
    image = load_image_with_fallback(image_path)
    
    if image is None:
        supported_formats = "PNG, JPG, JPEG, BMP, TIFF, TGA"
        raise ValueError(f"无法读取图像: {image_path}\n"
                        f"支持的格式: {supported_formats}\n"
                        f"{'提示: 安装Pillow库可以获得更好的TGA支持' if not PIL_AVAILABLE else ''}")
    
    # 检查是否有alpha通道
    has_alpha = False
    if len(image.shape) == 3:
        if image.shape[2] >= 4:
            has_alpha = True
        elif image.shape[2] == 3:
            # RGB格式，添加Alpha通道
            print("警告: 图像没有Alpha通道，将创建默认Alpha通道(全不透明)")
            alpha_channel = np.full((image.shape[0], image.shape[1]), 255, dtype=image.dtype)
            image = np.dstack((image, alpha_channel))
            has_alpha = True
    elif len(image.shape) == 2:
        # 灰度图像，转换为RGBA
        print("警告: 灰度图像，将转换为RGBA格式")
        rgba = np.zeros((image.shape[0], image.shape[1], 4), dtype=image.dtype)
        rgba[:, :, 0] = rgba[:, :, 1] = rgba[:, :, 2] = image
        rgba[:, :, 3] = 255  # 全不透明
        image = rgba
        has_alpha = True
    
    if not has_alpha:
        raise ValueError(f"图像不包含alpha通道: {image_path}\n"
                        f"图像形状: {image.shape}")
    
    # 提取alpha通道 (转换为0-1范围)
    alpha_channel = image[:, :, 3].astype(np.float32) / 255.0
    
    # 获取最大值和最小值
    alpha_min = np.min(alpha_channel)
    alpha_max = np.max(alpha_channel)
    
    print(f"Alpha通道最小值: {alpha_min:.4f}")
    print(f"Alpha通道最大值: {alpha_max:.4f}")
    
    # 计算 |max-0.5| 和 |min-0.5|
    max_diff = abs(alpha_max - 0.5)
    min_diff = abs(alpha_min - 0.5)
    
    # 取绝对值大的数
    scale_factor = max(max_diff, min_diff)
    
    print(f"缩放因子(最大差值): {scale_factor:.4f}")
    
    # 计算比率
    if scale_factor == 0:
        ratio = 1.0  # 避免除零错误
    else:
        ratio = 0.5 / scale_factor
    
    print(f"应用比率: {ratio:.4f}")
    
    # 应用变换: ratio * (pixel - 0.5) + 0.5
    transformed_alpha = ratio * (alpha_channel - 0.5) + 0.5
    
    # 转换回0-255范围并确保值在有效范围内
    transformed_alpha = np.clip(transformed_alpha * 255.0, 0, 255).astype(np.uint8)
    
    # 将处理后的alpha通道写回图像
    image[:, :, 3] = transformed_alpha
    
    # 确定输出路径（默认覆盖原图）
    if output_path is None:
        output_path = image_path  # 覆盖原图
    
    # 保存图像为TGA格式
    success = save_image_tga(image, output_path)
    
    if success:
        print(f"图像已保存到: {output_path}")
        if backup_path:
            print(f"原图备份保存在: {backup_path}")
    else:
        raise IOError(f"无法保存图像到: {output_path}")

def select_file_gui():
    """
    使用GUI弹窗选择文件
    
    Returns:
        str: 选择的文件路径，如果取消选择则返回None
    """
    if not TK_AVAILABLE:
        print("错误: 当前环境不支持GUI文件选择功能 (tkinter不可用)")
        return None
        
    # 创建隐藏的根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口
    root.attributes('-topmost', True)  # 置于顶层
    
    # 打开文件选择对话框，支持更多格式
    file_path = filedialog.askopenfilename(
        title="选择包含Alpha通道的图像文件",
        filetypes=[
            ("常用图像格式", "*.png *.tga *.tif *.tiff"),
            ("PNG文件", "*.png"),
            ("TGA文件", "*.tga *.tpic"),
            ("TIFF文件", "*.tif *.tiff"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("BMP文件", "*.bmp"),
            ("所有文件", "*.*")
        ]
    )
    
    # 销毁根窗口
    root.destroy()
    
    return file_path if file_path else None

def main():
    parser = argparse.ArgumentParser(description='处理图像的Alpha通道')
    parser.add_argument('input', nargs='?', help='输入图像路径')
    parser.add_argument('-o', '--output', help='输出图像路径(可选)')
    parser.add_argument('--no-gui', action='store_true', help='禁用GUI文件选择（使用命令行参数）')
    
    args = parser.parse_args()
    
    # 默认使用GUI，除非明确禁用或提供了输入文件
    use_gui_by_default = not args.no_gui and not args.input
    
    try:
        if args.input:
            # 处理提供的图像
            process_alpha_channel(args.input, args.output)
            
        elif use_gui_by_default:
            # 使用GUI选择文件（默认行为）
            print("请在弹出的窗口中选择图像文件...")
            if not PIL_AVAILABLE:
                print("提示: 安装Pillow库 (pip install Pillow) 可以获得更好的TGA文件支持")
            input_file = select_file_gui()
            
            if input_file is None:
                print("未选择文件，程序退出")
                exit(0)
                
            if not os.path.exists(input_file):
                print(f"错误: 选择的文件不存在: {input_file}")
                exit(1)
                
            print(f"已选择文件: {input_file}")
            process_alpha_channel(input_file, args.output)
            
        else:
            # 没有提供任何输入且禁用了GUI
            parser.print_help()
            print("\n错误: 必须提供输入图像路径或允许使用GUI选择文件")
            exit(1)
            
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

if __name__ == "__main__":
    main()