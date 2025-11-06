#!/usr/bin/env python3
"""
原版 vs 增强版可视化对比演示脚本
"""

import subprocess
import sys
import os
import json
from example_usage import create_sample_schedule

def run_comparison():
    """运行原版和增强版的对比"""
    
    print("=== 桩基施工可视化对比演示 ===\n")
    
    # 1. 准备测试数据
    print("1. 准备测试数据...")
    schedule = create_sample_schedule()
    
    test_file = "comparison_test.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ 测试数据已生成: {test_file}")
    print(f"   包含 {len(schedule)} 个桩基任务，3台机器")
    
    # 2. 运行原版可视化
    print("\n2. 生成原版可视化...")
    original_output = "original_animation.mp4"
    
    if os.path.exists("val.py"):
        try:
            result = subprocess.run([
                sys.executable, "val.py", test_file, original_output
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"   ✓ 原版动画已生成: {original_output}")
            else:
                print(f"   ✗ 原版生成失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("   ✗ 原版生成超时")
        except Exception as e:
            print(f"   ✗ 原版生成错误: {e}")
    else:
        print("   ✗ 找不到原版脚本 val.py")
    
    # 3. 运行增强版可视化
    print("\n3. 生成增强版可视化...")
    enhanced_output = "enhanced_animation.mp4"
    
    if os.path.exists("val_enhanced.py"):
        try:
            result = subprocess.run([
                sys.executable, "val_enhanced.py", test_file, enhanced_output
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"   ✓ 增强版动画已生成: {enhanced_output}")
            else:
                print(f"   ✗ 增强版生成失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("   ✗ 增强版生成超时")
        except Exception as e:
            print(f"   ✗ 增强版生成错误: {e}")
    else:
        print("   ✗ 找不到增强版脚本 val_enhanced.py")
    
    # 4. 对比结果
    print("\n4. 对比结果:")
    print("=" * 60)
    
    # 检查文件大小
    files_info = []
    for filename, description in [
        (original_output, "原版动画"),
        (enhanced_output, "增强版动画")
    ]:
        if os.path.exists(filename):
            size_mb = os.path.getsize(filename) / (1024*1024)
            files_info.append((filename, description, size_mb, "存在"))
        else:
            # 检查是否有GIF版本
            gif_version = filename.replace('.mp4', '.gif')
            if os.path.exists(gif_version):
                size_mb = os.path.getsize(gif_version) / (1024*1024)
                files_info.append((gif_version, f"{description} (GIF)", size_mb, "存在"))
            else:
                files_info.append((filename, description, 0, "未生成"))
    
    print(f"{'文件名':<25} {'描述':<15} {'大小':<10} {'状态':<8}")
    print("-" * 60)
    for filename, desc, size, status in files_info:
        if status == "存在":
            print(f"{os.path.basename(filename):<25} {desc:<15} {size:.1f}MB{'':<4} {status:<8}")
        else:
            print(f"{os.path.basename(filename):<25} {desc:<15} {'--':<10} {status:<8}")
    
    # 5. 功能对比表
    print(f"\n5. 功能对比:")
    print("=" * 60)
    
    features_comparison = [
        ("功能特性", "原版", "增强版"),
        ("-" * 20, "-" * 10, "-" * 15),
        ("色彩方案", "基础6色", "专业调色板"),
        ("机器显示", "彩色圆点", "钻机图标"),
        ("施工进度", "无", "进度环显示"),
        ("统计信息", "仅时间", "完整面板"),
        ("时间轴", "无", "甘特图"),
        ("禁区显示", "实心圆", "半透明优化"),
        ("字体", "默认", "现代无衬线"),
        ("布局", "简单", "专业分层"),
        ("帧率", "10 FPS", "15 FPS"),
        ("图标", "圆点", "机器图标"),
        ("进度条", "无", "圆形进度环"),
        ("信息面板", "无", "实时统计"),
    ]
    
    for feature, original, enhanced in features_comparison:
        print(f"{feature:<20} {original:<10} {enhanced:<15}")
    
    # 6. 使用建议
    print(f"\n6. 使用建议:")
    print("=" * 60)
    print("原版适用场景:")
    print("  • 快速生成基础动画")
    print("  • 系统资源有限")
    print("  • 简单展示需求")
    print("")
    print("增强版适用场景:")
    print("  • 专业汇报展示")
    print("  • 详细分析需求")
    print("  • 高质量可视化")
    print("  • 多维度信息展示")
    
    # 7. 下一步操作
    print(f"\n7. 下一步操作:")
    print("=" * 60)
    print("查看动画文件:")
    for filename, desc, size, status in files_info:
        if status == "存在":
            print(f"  • {desc}: {os.path.basename(filename)}")
    
    print(f"\n清理临时文件:")
    print(f"  python -c \"import os; [os.remove(f) for f in ['{test_file}'] if os.path.exists(f)]\"")

def quick_test():
    """快速测试功能"""
    print("=== 快速功能测试 ===\n")
    
    # 检查依赖
    dependencies = [
        ("matplotlib", "绘图库"),
        ("numpy", "数值计算"),
        ("seaborn", "色彩方案 (可选)"),
    ]
    
    print("1. 检查依赖包:")
    for package, desc in dependencies:
        try:
            __import__(package)
            print(f"   ✓ {package:<12} - {desc}")
        except ImportError:
            if package == "seaborn":
                print(f"   ⚠ {package:<12} - {desc} (未安装，将使用默认色彩)")
            else:
                print(f"   ✗ {package:<12} - {desc} (缺失)")
    
    # 检查脚本文件
    print(f"\n2. 检查脚本文件:")
    scripts = [
        ("val.py", "原版可视化"),
        ("val_enhanced.py", "增强版可视化"),
        ("example_usage.py", "使用示例"),
    ]
    
    for script, desc in scripts:
        if os.path.exists(script):
            print(f"   ✓ {script:<20} - {desc}")
        else:
            print(f"   ✗ {script:<20} - {desc} (缺失)")
    
    # 检查外部工具
    print(f"\n3. 检查外部工具:")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, timeout=5)
        if result.returncode == 0:
            print("   ✓ ffmpeg           - 视频编码 (支持MP4)")
        else:
            print("   ✗ ffmpeg           - 视频编码 (不可用)")
    except:
        print("   ✗ ffmpeg           - 视频编码 (未安装)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            quick_test()
        elif sys.argv[1] == "compare":
            run_comparison()
        else:
            print("用法:")
            print("  python comparison_demo.py test     - 快速测试")
            print("  python comparison_demo.py compare  - 完整对比")
    else:
        print("桩基施工可视化对比工具")
        print("")
        print("选择运行模式:")
        print("  1. 快速测试环境")
        print("  2. 完整对比演示")
        print("")
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "1":
            quick_test()
        elif choice == "2":
            run_comparison()
        else:
            print("无效选择，退出。")
