import json
import sys
import os
import argparse

# 在导入 matplotlib 之前设置后端（避免显示问题）
import matplotlib
matplotlib.use('Agg')  # 必须在导入 pyplot 之前设置

# 设置标准输出编码为UTF-8（Windows兼容）
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加详细的错误处理和依赖检查
def check_dependencies():
    """检查必要的依赖包是否安装"""
    missing_deps = []
    
    try:
        import matplotlib
        print(f"[OK] matplotlib 版本: {matplotlib.__version__}")
    except ImportError:
        missing_deps.append("matplotlib")
    
    try:
        import numpy
        print(f"[OK] numpy 版本: {numpy.__version__}")
    except ImportError:
        missing_deps.append("numpy")
    
    if missing_deps:
        print(f"[ERROR] 缺少依赖包: {', '.join(missing_deps)}")
        print("请安装: pip install matplotlib numpy")
        return False
    
    return True

def check_ffmpeg():
    """检查ffmpeg是否可用"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] ffmpeg 可用")
            return True
        else:
            print("[ERROR] ffmpeg 不可用")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("[ERROR] ffmpeg 未找到或无法执行")
        return False
    except Exception as e:
        print(f"[ERROR] 检查ffmpeg时出错: {e}")
        return False

# 检查依赖
print("=== 依赖检查 ===")
if not check_dependencies():
    sys.exit(1)

# 检查ffmpeg（非阻塞性）
ffmpeg_available = check_ffmpeg()

# 现在导入其他包
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    import matplotlib.patches as patches
    import numpy as np
    import math

    print("[OK] matplotlib 组件导入成功")

except Exception as e:
    print(f"[ERROR] 导入matplotlib组件失败: {e}")
    sys.exit(1)

# --- 配置参数 (部分将由命令行参数覆盖) ---
# FORBIDDEN_ZONE_RADIUS = 4 # 旧的固定半径，将被移除或修改
FORBIDDEN_DURATION_HOURS = 36 # 确保为36小时
ANIMATION_DURATION_SECONDS = 60
FPS = 10
# OUTPUT_FILENAME = 'construction_animation.mp4' # Will be set by args
# INPUT_FILENAME = 'schedule.json' # Will be set by args

# --- 绘图参数 ---
PILE_RADIUS_NORMAL = 1.0
PILE_RADIUS_ACTIVE = 2.0
SIZE_SCALING = 40
MARKER_SIZE_NORMAL = PILE_RADIUS_NORMAL**2 * SIZE_SCALING
MARKER_SIZE_ACTIVE = PILE_RADIUS_ACTIVE**2 * SIZE_SCALING
FORBIDDEN_ZONE_ALPHA = 0.2
MACHINE_COLORS = ['red', 'blue', 'green', 'purple', 'orange', 'brown']
NOT_STARTED_COLOR = 'lightgrey'
COMPLETED_COLOR = 'dimgray'

def main(input_filepath, output_filepath):
    print(f"=== 开始处理 ===")
    print(f"输入文件: {input_filepath}")
    print(f"输出文件: {output_filepath}")
    
    # 检查输入文件
    if not os.path.exists(input_filepath):
        print(f"[ERROR] 输入文件不存在: {input_filepath}")
        sys.exit(1)
    
    # 检查输出目录
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        print(f"[ERROR] 输出目录不存在: {output_dir}")
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"[OK] 创建输出目录: {output_dir}")
        except Exception as e:
            print(f"[ERROR] 创建输出目录失败: {e}")
            sys.exit(1)
    
    # --- 加载调度数据 --- 
    try:
        print("正在读取调度数据...")
        with open(input_filepath, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
        print(f"[OK] 成功读取调度数据，共 {len(schedule)} 个任务")
    except FileNotFoundError:
        print(f"[ERROR] 未找到调度文件 '{input_filepath}'。")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON解析错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 读取文件时发生错误: {e}")
        sys.exit(1)

    if not schedule:
        print("[ERROR] 调度文件为空，无法生成动画。")
        sys.exit(1)

    # 验证调度数据结构
    try:
        print("正在验证调度数据结构...")
        required_fields = ['pile_id', 'x', 'y', 'start_hour', 'end_hour', 'machine']
        sample_task = schedule[0]
        for field in required_fields:
            if field not in sample_task:
                print(f"[ERROR] 调度数据缺少必要字段: {field}")
                sys.exit(1)
        print("[OK] 调度数据结构验证通过")
    except Exception as e:
        print(f"[ERROR] 验证调度数据时出错: {e}")
        sys.exit(1)

    # --- 计算时间和空间范围 ---
    all_pile_data = {p['pile_id']: {'x': p['x'], 'y': p['y']} for p in schedule}
    all_x = [p['x'] for p in schedule]
    all_y = [p['y'] for p in schedule]
    max_end_time = max(p['end_hour'] for p in schedule) if schedule else 0
    min_x, max_x = min(all_x) if all_x else 0, max(all_x) if all_x else 10
    min_y, max_y = min(all_y) if all_y else 0, max(all_y) if all_y else 10

    # 动态计算padding时，考虑最大可能的禁区半径
    # 获取所有直径，如果不存在则用一个默认值（例如1）来估算最大禁区半径
    all_diameters = [p.get('diameter', 1.0) for p in schedule] # 使用 .get() 更安全
    max_pile_diameter = max(all_diameters) if all_diameters else 1.0
    max_forbidden_radius_for_padding = max_pile_diameter * 6 

    padding_x = (max_x - min_x) * 0.1 + max_forbidden_radius_for_padding + 1
    padding_y = (max_y - min_y) * 0.1 + max_forbidden_radius_for_padding + 1

    # 降低图像分辨率以减少内存占用
    fig, ax = plt.subplots(figsize=(12, 8))  # 从(12, 8)降低到(10, 6)

    # 配置中文字体（使用 Noto Sans CJK，Docker 容器中已安装）
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'Noto Sans CJK TC', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 减少帧数以降低内存和处理需求
    total_frames = min(ANIMATION_DURATION_SECONDS * FPS, 300)  # 最多300帧
    print(f"调整后的总帧数: {total_frames}")
    
    current_artists = []
    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, verticalalignment='top', zorder=5)  # 字体从12降到10

    def update(frame):
        current_sim_time = (frame / total_frames) * max_end_time
        nonlocal current_artists # Ensure we modify the outer scope's current_artists
        for artist in current_artists:
            artist.remove()
        current_artists.clear()

        # Store pile data along with IDs for text annotation
        not_started_piles_data = [] # {'x': x, 'y': y, 'id': id}
        active_piles_data = []    # {'x': x, 'y': y, 'id': id, 'color': color, 'size': size}
        completed_piles_data = [] # {'x': x, 'y': y, 'id': id}
        
        tasks_in_forbidden_period = []
        # processed_pile_ids = set() # This might lead to issues if a pile ID appears multiple times in schedule for different phases, though unlikely with current data structure

        for task in schedule:
            pile_id = task['pile_id']
            # if pile_id in processed_pile_ids: # Commenting out as per thought, if schedule has multiple entries for same pile (e.g. stages), this would hide them
            #      continue
            start_time = task['start_hour']
            end_time = task['end_hour']
            pile_x = task['x']
            pile_y = task['y']
            machine_idx = task['machine'] - 1

            if current_sim_time < start_time:
                not_started_piles_data.append({'x': pile_x, 'y': pile_y, 'id': pile_id})
            elif start_time <= current_sim_time < end_time:
                active_piles_data.append({
                    'x': pile_x, 
                    'y': pile_y, 
                    'id': pile_id, 
                    'color': MACHINE_COLORS[machine_idx % len(MACHINE_COLORS)], 
                    'size': MARKER_SIZE_ACTIVE
                })
            else: # current_sim_time >= end_time
                completed_piles_data.append({'x': pile_x, 'y': pile_y, 'id': pile_id})
                if current_sim_time < end_time + FORBIDDEN_DURATION_HOURS:
                    tasks_in_forbidden_period.append(task)
            # processed_pile_ids.add(pile_id)


        if not_started_piles_data:
            scatter_not_started = ax.scatter(
                [p['x'] for p in not_started_piles_data], 
                [p['y'] for p in not_started_piles_data],
                color=NOT_STARTED_COLOR, s=MARKER_SIZE_NORMAL, zorder=2
            )
            current_artists.append(scatter_not_started)
            for pile in not_started_piles_data:
                text = ax.text(pile['x'], pile['y'] + PILE_RADIUS_NORMAL*0.5, str(pile['id']), 
                               fontsize=7, ha='center', va='bottom', color='black', zorder=4)
                current_artists.append(text)

        if completed_piles_data:
            scatter_completed = ax.scatter(
                [p['x'] for p in completed_piles_data], 
                [p['y'] for p in completed_piles_data],
                color=COMPLETED_COLOR, s=MARKER_SIZE_NORMAL, zorder=2
            )
            current_artists.append(scatter_completed)
            for pile in completed_piles_data:
                text = ax.text(pile['x'], pile['y'] + PILE_RADIUS_NORMAL*0.5, str(pile['id']), 
                               fontsize=7, ha='center', va='bottom', color='white', zorder=4)
                current_artists.append(text)

        if active_piles_data:
           scatter_active = ax.scatter(
               [p['x'] for p in active_piles_data], 
               [p['y'] for p in active_piles_data],
               c=[p['color'] for p in active_piles_data], 
               s=[p['size'] for p in active_piles_data],
               edgecolors='black', zorder=3
           )
           current_artists.append(scatter_active)
           for pile in active_piles_data:
                text = ax.text(pile['x'], pile['y'] + PILE_RADIUS_ACTIVE*0.3, str(pile['id']), 
                               fontsize=8, ha='center', va='bottom', color='black', weight='bold', zorder=4)
                current_artists.append(text)

        for task in tasks_in_forbidden_period:
            center_x = task['x']
            center_y = task['y']
            pile_diameter = task.get('diameter', 0.5) # 从task获取直径，如果缺少则用一个默认值
            current_forbidden_radius = pile_diameter * 6
            
            circle = patches.Circle((center_x, center_y), radius=current_forbidden_radius,
                                     linewidth=1, edgecolor='orange', facecolor='yellow', alpha=FORBIDDEN_ZONE_ALPHA, zorder=1)
            ax.add_patch(circle)
            current_artists.append(circle)
        time_text.set_text(f'模拟时间: {current_sim_time:.2f} 小时 / {max_end_time:.2f} 小时')
        return current_artists + [time_text]

    ax.set_xlim(min_x - padding_x, max_x + padding_x)
    ax.set_ylim(min_y - padding_y, max_y + padding_y)
    ax.set_xlabel("X 坐标 (米)")
    ax.set_ylabel("Y 坐标 (米)")
    ax.set_title("桩基施工过程动画")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_aspect('equal', adjustable='box')

    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', label='未开始的桩', markerfacecolor=NOT_STARTED_COLOR, markersize=math.sqrt(MARKER_SIZE_NORMAL / math.pi)),
        plt.Line2D([0], [0], marker='o', color='w', label='已完成的桩', markerfacecolor=COMPLETED_COLOR, markersize=math.sqrt(MARKER_SIZE_NORMAL / math.pi)),
    ]
    num_machines_in_schedule = max(p['machine'] for p in schedule) if schedule else 0
    for m_idx in range(num_machines_in_schedule):
         legend_elements.append(
             plt.Line2D([0], [0], marker='o', color='w', label=f'机器 {m_idx+1} 施工中',
                        markerfacecolor=MACHINE_COLORS[m_idx % len(MACHINE_COLORS)], markersize=math.sqrt(MARKER_SIZE_ACTIVE / math.pi), markeredgecolor='black')
         )
    # 更新图例描述
    legend_elements.append(patches.Patch(facecolor='yellow', edgecolor='orange', alpha=FORBIDDEN_ZONE_ALPHA, label='完工禁区 (桩直径 x 6)'))
    ax.legend(handles=legend_elements, loc='upper center',
              bbox_to_anchor=(0.5, -0.1),
              fancybox=True, shadow=False, ncol=len(legend_elements)//2 + len(legend_elements)%2)
    plt.subplots_adjust(bottom=0.2)

    print(f"正在生成动画 (共 {total_frames} 帧) 到 {output_filepath} ... 可能需要一些时间。")
    
    # 如果ffmpeg不可用，尝试其他保存方式
    if not ffmpeg_available:
        print("[WARNING] ffmpeg不可用，尝试使用其他方式保存...")
        try:
            # 尝试使用pillow writer，降低帧率和分辨率
            reduced_frames = min(total_frames, 100)  # 进一步减少帧数
            print(f"降级模式：生成 {reduced_frames} 帧的GIF动画")
            
            # 重新创建动画对象以减少帧数
            def reduced_ani_func(frame):
                # 映射到原始帧范围
                original_frame = int(frame * total_frames / reduced_frames)
                return update(original_frame)
            
            ani_reduced = animation.FuncAnimation(fig, reduced_ani_func, frames=reduced_frames, 
                                                interval=1000/5, blit=True, repeat=False)
            ani_reduced.save(output_filepath.replace('.mp4', '.gif'), writer='pillow', fps=5)
            print(f"[OK] 动画已保存为GIF格式: {output_filepath.replace('.mp4', '.gif')}")
            return
        except Exception as e:
            print(f"[ERROR] 保存GIF也失败: {e}")
            print("[INFO] 尝试保存静态截图...")
            try:
                # 保存几个关键时刻的静态图
                key_frames = [0, total_frames//4, total_frames//2, 3*total_frames//4, total_frames-1]
                for i, frame in enumerate(key_frames):
                    update(frame)
                    static_path = output_filepath.replace('.mp4', f'_frame_{i}.png')
                    fig.savefig(static_path, dpi=100, bbox_inches='tight')
                    print(f"[OK] 已保存静态图: {static_path}")
                return
            except Exception as static_e:
                print(f"[ERROR] 保存静态图也失败: {static_e}")
                sys.exit(1)
    
    # ffmpeg可用时的处理
    try:
        from tqdm import tqdm
        progress_bar = tqdm(total=total_frames, desc="生成动画进度")
        def update_with_progress(frame):
            result = update(frame)
            progress_bar.update(1)
            return result
        ani_func = update_with_progress
    except ImportError:
        print("tqdm 未安装，将不显示进度条。")
        ani_func = update

    ani = animation.FuncAnimation(fig, ani_func, frames=total_frames, interval=1000/FPS, blit=True, repeat=False)
    
    try:
        # 使用更低质量但更稳定的编码参数
        writer = animation.FFMpegWriter(
            fps=FPS,
            metadata=dict(artist='Pile Construction Animation'),
            bitrate=1000,  # 降低比特率
            extra_args=['-vcodec', 'libx264', '-preset', 'ultrafast', '-crf', '28']  # 快速编码，较低质量
        )
        ani.save(output_filepath, writer=writer, dpi=100)  # 从150降低到100
        if 'progress_bar' in locals():
            progress_bar.close()
        print(f"[OK] 动画已保存到 '{output_filepath}'")

        # 清理内存
        plt.close(fig)
        del ani
        import gc
        gc.collect()
        print("[INFO] 视频生成成功，内存已清理")
        return  # 成功后退出
        
    except (subprocess.CalledProcessError, BrokenPipeError, OSError) as e:
        if 'progress_bar' in locals(): 
            progress_bar.close()
        print(f"[ERROR] ffmpeg编码失败: {e}")
        print("[INFO] 尝试生成GIF格式...")
        
        # 降级到GIF格式
        try:
            gif_path = output_filepath.replace('.mp4', '.gif')
            ani_gif = animation.FuncAnimation(fig, update, frames=total_frames, interval=1000/FPS, blit=True, repeat=False)
            ani_gif.save(gif_path, writer='pillow', fps=min(FPS, 5))  # 降低GIF帧率
            print(f"[OK] 已保存为GIF格式: {gif_path}")
            return
        except Exception as gif_e:
            print(f"[ERROR] 保存GIF也失败: {gif_e}")
            sys.exit(1)
            
    except FileNotFoundError:
        if 'progress_bar' in locals(): 
            progress_bar.close()
        print("[ERROR] 无法找到 ffmpeg。请确保已安装 ffmpeg 并且其路径已添加到系统环境变量 PATH 中。")
        print("可以通过以下方式安装ffmpeg:")
        print("  Windows: 下载 https://ffmpeg.org/download.html")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS: brew install ffmpeg")
        sys.exit(1)
        
    except Exception as e:
        if 'progress_bar' in locals(): 
            progress_bar.close()
        print(f"[ERROR] 保存动画时发生未知错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # 最后尝试保存为静态图
        try:
            static_path = output_filepath.replace('.mp4', '_static.png')
            fig.savefig(static_path, dpi=100, bbox_inches='tight')
            print(f"[INFO] 已保存静态图: {static_path}")
        except Exception as static_e:
            print(f"[ERROR] 保存静态图也失败: {static_e}")

        sys.exit(1)

    finally:
        # 清理内存，关闭所有图形
        plt.close('all')
        import gc
        gc.collect()
        print("[INFO] 内存已清理")

if __name__ == '__main__':
    # --- 使用 argparse 解析命令行参数 ---
    parser = argparse.ArgumentParser(description='从调度JSON文件生成施工动画视频。')
    parser.add_argument('input_file', type=str, help='输入的调度JSON文件路径')
    parser.add_argument('output_file', type=str, help='输出的MP4视频文件路径')
    
    args = parser.parse_args()
    
    main(args.input_file, args.output_file)
