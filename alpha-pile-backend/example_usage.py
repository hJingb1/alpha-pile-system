#!/usr/bin/env python3
"""
增强版桩基施工可视化工具使用示例
"""

import json
import os
import sys

def create_sample_schedule():
    """创建示例调度数据"""
    
    # 示例：一个小型桩基工程，包含20个桩，使用3台机器
    schedule = []
    
    # 定义桩位（4x5的网格布局）
    pile_positions = []
    for i in range(4):
        for j in range(5):
            pile_positions.append({
                'id': i * 5 + j + 1,
                'x': i * 10,  # 10米间距
                'y': j * 8    # 8米间距
            })
    
    # 分配施工时间和机器
    current_time = 0
    machine_schedules = {1: 0, 2: 0, 3: 0}  # 每台机器的当前时间
    
    for i, pos in enumerate(pile_positions):
        pile_id = str(pos['id'])
        
        # 选择当前最空闲的机器
        machine_id = min(machine_schedules.keys(), 
                        key=lambda x: machine_schedules[x])
        
        # 施工时间：6-12小时不等
        duration = 6 + (i % 7)  # 6到12小时的施工时间
        start_time = machine_schedules[machine_id]
        end_time = start_time + duration
        
        # 更新机器时间表
        machine_schedules[machine_id] = end_time + 2  # 加2小时转移时间
        
        # 添加到调度
        schedule.append({
            'pile_id': pile_id,
            'x': pos['x'],
            'y': pos['y'],
            'start_hour': start_time,
            'end_hour': end_time,
            'machine': machine_id,
            'diameter': 1.0 + (i % 3) * 0.2  # 1.0到1.4米的直径
        })
    
    return schedule

def main():
    """主函数：创建示例数据并运行可视化"""
    
    print("=== 增强版桩基施工可视化示例 ===")
    
    # 1. 创建示例调度数据
    print("1. 创建示例调度数据...")
    schedule = create_sample_schedule()
    
    # 保存到JSON文件
    sample_file = "sample_schedule.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)
    
    print(f"   样例数据已保存到: {sample_file}")
    print(f"   包含 {len(schedule)} 个桩基任务")
    print(f"   使用 3 台施工机器")
    
    # 显示调度概览
    total_duration = max(task['end_hour'] for task in schedule)
    print(f"   总施工时长: {total_duration:.1f} 小时")
    
    # 2. 运行增强版可视化
    print("\n2. 运行增强版可视化...")
    output_file = "enhanced_construction_animation.mp4"
    
    # 检查可视化脚本是否存在
    if not os.path.exists("val_enhanced.py"):
        print("   [ERROR] 找不到 val_enhanced.py 文件")
        print("   请确保该文件在当前目录中")
        return
    
    # 导入并运行可视化
    try:
        from val_enhanced import main as visualize_main
        visualize_main(sample_file, output_file)
        print(f"\n[SUCCESS] 动画已生成: {output_file}")
        
    except ImportError as e:
        print(f"   [ERROR] 导入可视化模块失败: {e}")
        print("   请检查依赖包是否已安装: pip install matplotlib numpy seaborn")
        
    except Exception as e:
        print(f"   [ERROR] 运行可视化时出错: {e}")
        
        # 尝试使用命令行方式
        print("   尝试使用命令行方式运行...")
        import subprocess
        try:
            subprocess.run([sys.executable, "val_enhanced.py", sample_file, output_file], 
                         check=True)
            print(f"   [SUCCESS] 动画已生成: {output_file}")
        except subprocess.CalledProcessError as cmd_e:
            print(f"   [ERROR] 命令行运行也失败: {cmd_e}")
    
    # 3. 显示结果信息
    print(f"\n3. 查看结果:")
    print(f"   输入数据: {sample_file}")
    print(f"   输出动画: {output_file} (如果成功生成)")
    print(f"\n提示:")
    print(f"   - 如果没有安装 ffmpeg，会生成 .gif 格式")
    print(f"   - 动画展示了机器图标、施工进度环、甘特图等增强功能")
    print(f"   - 右上角显示实时统计信息")

def print_schedule_info():
    """显示调度数据的详细信息"""
    
    if not os.path.exists("sample_schedule.json"):
        print("请先运行 main() 生成示例数据")
        return
    
    with open("sample_schedule.json", 'r', encoding='utf-8') as f:
        schedule = json.load(f)
    
    print("\n=== 调度数据详情 ===")
    print(f"总桩数: {len(schedule)}")
    
    # 按机器分组统计
    machine_stats = {}
    for task in schedule:
        machine = task['machine']
        if machine not in machine_stats:
            machine_stats[machine] = {
                'count': 0,
                'total_time': 0,
                'start_time': float('inf'),
                'end_time': 0
            }
        
        stats = machine_stats[machine]
        stats['count'] += 1
        stats['total_time'] += task['end_hour'] - task['start_hour']
        stats['start_time'] = min(stats['start_time'], task['start_hour'])
        stats['end_time'] = max(stats['end_time'], task['end_hour'])
    
    print("\n机器工作统计:")
    for machine_id, stats in sorted(machine_stats.items()):
        print(f"  机器 {machine_id}:")
        print(f"    负责桩数: {stats['count']}")
        print(f"    工作时长: {stats['total_time']:.1f} 小时")
        print(f"    工作时段: {stats['start_time']:.1f}h - {stats['end_time']:.1f}h")
    
    # 时间线统计
    total_time = max(task['end_hour'] for task in schedule)
    print(f"\n总工期: {total_time:.1f} 小时 ({total_time/24:.1f} 天)")
    
    # 空间分布
    x_coords = [task['x'] for task in schedule]
    y_coords = [task['y'] for task in schedule]
    print(f"\n施工区域:")
    print(f"  X范围: {min(x_coords)} - {max(x_coords)} 米")
    print(f"  Y范围: {min(y_coords)} - {max(y_coords)} 米")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        print_schedule_info()
    else:
        main()
