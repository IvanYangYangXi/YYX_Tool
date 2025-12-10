#!/usr/bin/env python3
"""
改进版NumPy/OpenCV兼容性修复脚本
增加了更好的错误处理和用户反馈
"""

import sys
import subprocess
import os
import platform

def print_header():
    print("=" * 70)
    print("改进版 NumPy/OpenCV 兼容性修复工具")
    print("=" * 70)
    print("此脚本将帮助您解决 'numpy.core.multiarray failed to import' 错误")
    print()

def get_system_info():
    """获取系统相关信息"""
    print("[1/6] 检查系统环境信息...")
    try:
        print(f"  操作系统: {platform.system()} {platform.release()}")
        print(f"  架构: {platform.machine()}")
        print(f"  Python 版本: {sys.version}")
        print(f"  Python 路径: {sys.executable}")
        
        # 检查是否在虚拟环境中
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
        print(f"  虚拟环境: {'是' if in_venv else '否'}")
        print()
        return True
    except Exception as e:
        print(f"  获取系统信息时出错: {e}")
        print()
        return False

def check_current_state():
    """检查当前状态"""
    print("[2/6] 检查当前包状态...")
    
    # 检查pip版本
    try:
        pip_version = subprocess.check_output([sys.executable, '-m', 'pip', '--version'], 
                                            stderr=subprocess.STDOUT, universal_newlines=True)
        print(f"  Pip 版本: {pip_version.split()[1]}")
    except Exception as e:
        print(f"  检查pip版本时出错: {e}")
    
    # 检查已安装的包
    packages = ['numpy', 'opencv-python', 'opencv-contrib-python']
    installed_packages = []
    
    for package in packages:
        try:
            # 使用pip show检查
            result = subprocess.check_output([sys.executable, '-m', 'pip', 'show', package], 
                                           stderr=subprocess.STDOUT, universal_newlines=True)
            for line in result.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    print(f"  ✓ {package}: {version}")
                    installed_packages.append(package)
                    break
        except subprocess.CalledProcessError:
            print(f"  ✗ {package}: 未安装")
        except Exception as e:
            print(f"  ? {package}: 检查时出错 ({e})")
    
    print()
    return installed_packages

def uninstall_packages(packages):
    """卸载包"""
    print("[3/6] 卸载现有包...")
    
    if not packages:
        print("  没有找到需要卸载的包")
        print()
        return True
    
    success_count = 0
    for package in packages:
        try:
            print(f"  卸载 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', package, '-y'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    ✓ {package} 卸载成功")
            success_count += 1
        except subprocess.CalledProcessError:
            print(f"    ! {package} 卸载失败（可能未安装）")
        except Exception as e:
            print(f"    ? {package} 卸载异常: {e}")
    
    print(f"  完成 ({success_count}/{len(packages)} 包卸载成功)")
    print()
    return True

def upgrade_pip():
    """升级pip"""
    print("[4/6] 升级pip...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✓ Pip 升级成功")
    except subprocess.CalledProcessError as e:
        print(f"  ! Pip 升级失败: {e}")
        return False
    except Exception as e:
        print(f"  ? Pip 升级异常: {e}")
        return False
    
    print()
    return True

def install_packages():
    """安装包"""
    print("[5/6] 安装新包...")
    
    packages = ['numpy', 'opencv-python']
    success_count = 0
    
    for package in packages:
        try:
            print(f"  安装 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    ✓ {package} 安装成功")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"    ✗ {package} 安装失败: {e}")
            return False
        except Exception as e:
            print(f"    ? {package} 安装异常: {e}")
            return False
    
    print(f"  完成 ({success_count}/{len(packages)} 包安装成功)")
    print()
    return True

def verify_installation():
    """验证安装"""
    print("[6/6] 验证安装...")
    
    # 测试基本导入
    tests = [
        ("import numpy", "import numpy"),
        ("import cv2", "import cv2"),
        ("numpy功能测试", "import numpy as np; arr = np.array([1, 2, 3])"),
        ("cv2功能测试", "import cv2; import numpy as np; blank = np.zeros((10, 10, 3), dtype=np.uint8)")
    ]
    
    success_count = 0
    for test_name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"  ✓ {test_name}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {test_name}: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}")
    
    print(f"  完成 ({success_count}/{len(tests)} 测试通过)")
    
    if success_count == len(tests):
        print("\n" + "=" * 70)
        print("🎉 恭喜！NumPy 和 OpenCV 已成功安装并可以正常工作")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("⚠️  部分测试失败，请检查上面的错误信息")
        print("=" * 70)
        return False

def manual_steps():
    """提供手动步骤"""
    print("\n如果自动修复失败，请尝试以下手动步骤:")
    print("-" * 50)
    print("1. 打开命令提示符 (CMD)")
    print("2. 执行以下命令:")
    print("   pip uninstall numpy opencv-python opencv-contrib-python -y")
    print("   pip install --upgrade pip")
    print("   pip install --no-cache-dir numpy opencv-python")
    print("3. 验证安装:")
    print("   python -c \"import numpy; import cv2; print('SUCCESS')\"")
    print()

def main():
    print_header()
    
    try:
        # 获取系统信息
        get_system_info()
        
        # 检查当前状态
        installed_packages = check_current_state()
        
        # 卸载现有包
        uninstall_packages(installed_packages)
        
        # 升级pip
        if not upgrade_pip():
            print("警告: Pip升级失败，将继续执行后续步骤...")
            print()
        
        # 安装新包
        if not install_packages():
            print("错误: 包安装失败")
            manual_steps()
            return False
        
        # 验证安装
        success = verify_installation()
        
        if not success:
            manual_steps()
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        return False
    except Exception as e:
        print(f"\n程序执行过程中发生未预期的错误:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        import traceback
        print("\n详细追踪信息:")
        traceback.print_exc()
        manual_steps()
        return False

if __name__ == "__main__":
    try:
        success = main()
        # 不强制退出，让用户看到结果
        if not success:
            input("\n按 Enter 键退出...")
    except Exception as e:
        print(f"脚本执行出错: {e}")
        input("\n按 Enter 键退出...")