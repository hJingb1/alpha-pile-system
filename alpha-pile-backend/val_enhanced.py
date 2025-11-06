import json
import sys
import os
import argparse
import math
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

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
    
    try:
        import seaborn
        print(f"[OK] seaborn 版本: {seaborn.__version__}")
    except ImportError:
        print("[WARNING] seaborn 未安装，将使用默认色彩方案")
    
    if missing_deps:
        print(f"[ERROR] 缺少依赖包: {', '.join(missing_deps)}")
        print("请安装: pip install matplotlib numpy seaborn")
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
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import FancyBboxPatch, Rectangle
    import numpy as np
    
    # 尝试导入seaborn以获得更好的色彩方案
    try:
        import seaborn as sns
        SEABORN_AVAILABLE = True
        # 设置专业的调色板
        sns.set_palette("husl")
        PROFESSIONAL_COLORS = sns.color_palette("husl", 8).as_hex()
    except ImportError:
        SEABORN_AVAILABLE = False
        # 后备专业色彩方案（基于Adobe Color的推荐）
        PROFESSIONAL_COLORS = [
            '#FF6B6B',  # 珊瑚红
            '#4ECDC4',  # 青绿色
            '#45B7D1',  # 天蓝色
            '#96CEB4',  # 薄荷绿
            '#FFEAA7',  # 浅黄色
            '#DDA0DD',  # 紫罗兰
            '#98D8C8',  # 浅绿色
            '#F7DC6F'   # 金黄色
        ]
    
    # 配置matplotlib后端和字体
    plt.switch_backend('Agg')  # 使用非交互式后端
    
    # 设置更现代的字体
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['grid.alpha'] = 0.3
    
    print("[OK] matplotlib 和字体配置成功")
    
except Exception as e:
    print(f"[ERROR] 导入matplotlib组件失败: {e}")
    sys.exit(1)

@dataclass
class PileState:
    """桩的状态数据类"""
    pile_id: str
    x: float
    y: float
    machine_id: int
    start_time: float
    end_time: float
    diameter: float
    status: str  # 'not_started', 'active', 'completed'
    progress: float = 0.0  # 施工进度 0-1

@dataclass
class MachineState:
    """机器状态数据类"""
    machine_id: int
    current_pile_id: Optional[str]
    position: Tuple[float, float]
    status: str  # 'idle', 'working', 'moving'
    color: str
    last_position: Optional[Tuple[float, float]] = None

class EnhancedConstructionVisualizer:
    """增强版施工可视化器"""
    
    def __init__(self):
        # --- 配置参数 ---
        self.FORBIDDEN_DURATION_HOURS = 36
        self.ANIMATION_DURATION_SECONDS = 60  # 固定1分钟时长
        self.FPS = 10  # 降低帧率加速渲染
        
        # --- 专业视觉参数 ---
        self.PILE_RADIUS_NORMAL = 1.0
        self.PILE_RADIUS_ACTIVE = 1.5
        self.SIZE_SCALING = 50
        self.FORBIDDEN_ZONE_ALPHA = 0.15  # 降低透明度
        
        # 专业色彩方案
        self.MACHINE_COLORS = PROFESSIONAL_COLORS
        self.NOT_STARTED_COLOR = '#E8E8E8'  # 浅灰色
        self.COMPLETED_COLOR = '#2C3E50'    # 深蓝灰色
        self.FORBIDDEN_COLOR = '#FFE4B5'    # 浅橙色
        self.FORBIDDEN_EDGE_COLOR = '#FFA500'  # 橙色边框
        
        # 动画相关
        self.total_frames = 0
        self.max_end_time = 0
        self.schedule = []
        self.machines = {}
        self.pile_positions = {}
        
        # 渲染进度跟踪
        self.render_start_time = None
        self.frames_rendered = 0
        
        # 统计数据
        self.stats = {
            'total_piles': 0,
            'completed_piles': 0,
            'active_machines': 0,
            'total_machines': 0,
            'current_time': 0.0,
            'progress_percentage': 0.0
        }
        
    def load_schedule(self, input_filepath: str) -> List[Dict]:
        """加载并验证调度数据"""
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
            
        return schedule
    
    def initialize_data(self, schedule: List[Dict]):
        """初始化数据结构"""
        self.schedule = schedule
        self.stats['total_piles'] = len(schedule)
        
        # 计算时间和空间范围
        all_x = [p['x'] for p in schedule]
        all_y = [p['y'] for p in schedule]
        self.max_end_time = max(p['end_hour'] for p in schedule) if schedule else 0
        self.min_x, self.max_x = min(all_x), max(all_x)
        self.min_y, self.max_y = min(all_y), max(all_y)
        
        # 初始化机器状态
        machine_ids = list(set(p['machine'] for p in schedule))
        self.stats['total_machines'] = len(machine_ids)
        
        for i, machine_id in enumerate(machine_ids):
            self.machines[machine_id] = MachineState(
                machine_id=machine_id,
                current_pile_id=None,
                position=(0, 0),
                status='idle',
                color=self.MACHINE_COLORS[i % len(self.MACHINE_COLORS)]
            )
        
        # 初始化甘特图相关变量
        self.gantt_ax = None
        self.last_gantt_frame = -1
        
        # 存储桩位置信息
        for task in schedule:
            self.pile_positions[task['pile_id']] = (task['x'], task['y'])
        
        # 计算动态padding
        all_diameters = [p.get('diameter', 1.0) for p in schedule]
        max_pile_diameter = max(all_diameters) if all_diameters else 1.0
        max_forbidden_radius = max_pile_diameter * 6
        
        self.padding_x = (self.max_x - self.min_x) * 0.15 + max_forbidden_radius
        self.padding_y = (self.max_y - self.min_y) * 0.15 + max_forbidden_radius
        
        # 设置总帧数 - 限制在1分钟内
        self.total_frames = self.ANIMATION_DURATION_SECONDS * self.FPS  # 固定600帧
        print(f"总帧数: {self.total_frames} (1分钟动画)")
    
    def print_progress_bar(self, current: int, total: int, width: int = 50, elapsed_time: float = 0):
        """打印进度条"""
        progress = current / total
        filled_width = int(width * progress)
        
        # 计算速度和预估剩余时间
        if elapsed_time > 0 and current > 0:
            fps = current / elapsed_time
            eta = (total - current) / fps if fps > 0 else 0
            speed_info = f" | 速度: {fps:.1f} 帧/秒 | 预计剩余: {eta:.0f}秒"
        else:
            speed_info = ""
        
        bar = '█' * filled_width + '░' * (width - filled_width)
        percentage = progress * 100
        
        print(f'\r渲染进度: [{bar}] {percentage:.1f}% ({current}/{total}){speed_info}', end='', flush=True)
        
        if current == total:
            print()  # 完成后换行
    
    def get_pile_states(self, current_time: float) -> Tuple[List[PileState], List]:
        """获取当前时间所有桩的状态"""
        pile_states = []
        forbidden_zones = []
        
        for task in self.schedule:
            pile_id = task['pile_id']
            start_time = task['start_hour']
            end_time = task['end_hour']
            diameter = task.get('diameter', 1.0)
            
            # 计算施工进度
            if current_time < start_time:
                status = 'not_started'
                progress = 0.0
            elif start_time <= current_time < end_time:
                status = 'active'
                progress = (current_time - start_time) / (end_time - start_time)
            else:
                status = 'completed'
                progress = 1.0
                
                # 检查是否在禁区期间
                if current_time < end_time + self.FORBIDDEN_DURATION_HOURS:
                    forbidden_zones.append({
                        'x': task['x'],
                        'y': task['y'],
                        'radius': diameter * 6,
                        'pile_id': pile_id
                    })
            
            pile_states.append(PileState(
                pile_id=pile_id,
                x=task['x'],
                y=task['y'],
                machine_id=task['machine'],
                start_time=start_time,
                end_time=end_time,
                diameter=diameter,
                status=status,
                progress=progress
            ))
        
        return pile_states, forbidden_zones
    
    def update_machine_states(self, pile_states: List[PileState], current_time: float):
        """更新机器状态"""
        # 重置所有机器状态
        for machine in self.machines.values():
            machine.status = 'idle'
            machine.current_pile_id = None
        
        active_machines = 0
        
        # 更新活跃机器状态
        for pile in pile_states:
            if pile.status == 'active':
                machine = self.machines[pile.machine_id]
                machine.status = 'working'
                machine.current_pile_id = pile.pile_id
                
                # 平滑移动到目标位置
                target_pos = (pile.x, pile.y)
                if machine.last_position and machine.last_position != target_pos:
                    # 简单的线性插值移动（实际应用中可以更复杂）
                    machine.position = target_pos
                else:
                    machine.position = target_pos
                machine.last_position = target_pos
                active_machines += 1
        
        self.stats['active_machines'] = active_machines
    
    def draw_machine_icon(self, ax, x: float, y: float, color: str, size: float = 1.0):
        """绘制机器图标（简化的钻机图标）"""
        # 主体矩形
        main_body = Rectangle((x-0.8*size, y-0.6*size), 1.6*size, 1.2*size, 
                             facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(main_body)
        
        # 钻杆
        drill_rod = Rectangle((x-0.1*size, y+0.6*size), 0.2*size, 1.0*size,
                             facecolor='gray', edgecolor='black', linewidth=1)
        ax.add_patch(drill_rod)
        
        return [main_body, drill_rod]
    
    def create_info_panel(self, ax, current_time: float):
        """创建信息统计面板（双列布局优化版本）"""
        # 计算统计数据
        completed_count = sum(1 for task in self.schedule if current_time >= task['end_hour'])
        self.stats['completed_piles'] = completed_count
        self.stats['current_time'] = current_time
        
        # 改进的进度计算：基于工程量完成百分比而非时间
        self.stats['progress_percentage'] = (completed_count / self.stats['total_piles']) * 100
        
        # 面板位置和尺寸（稍微增大以容纳双列布局）
        panel_x = 0.70
        panel_y = 0.97
        panel_width = 0.28
        panel_height = 0.20
        
        # 创建面板背景（更柔和的设计）
        panel_bg = FancyBboxPatch((panel_x, panel_y - panel_height), panel_width, panel_height,
                                 boxstyle="round,pad=0.01",
                                 facecolor='#FAFAFA', 
                                 edgecolor='#DDDDDD',
                                 alpha=0.98,
                                 linewidth=1.2,
                                 zorder=100,  # 确保在最顶层
                                 transform=ax.transAxes)
        ax.add_patch(panel_bg)
        
        # 标题居中显示（不加粗）
        title_y = panel_y - 0.025
        title_text = ax.text(panel_x + panel_width/2, title_y, "工程进度概览",
                           transform=ax.transAxes, fontsize=14,
                           fontweight='normal', color='#2C3E50',
                           ha='center', va='top', zorder=101)
        
        # 添加标题下的分隔线（增加间距）
        line_y = title_y - 0.035  # 增加与标题的间距
        line = plt.Line2D([panel_x + 0.02, panel_x + panel_width - 0.02], 
                         [line_y, line_y],
                         color='#CCCCCC', linewidth=1, alpha=0.8,
                         transform=ax.transAxes, zorder=101)
        ax.add_line(line)
        
        # 双列数据布局
        left_column = {
            '总进度': f"{self.stats['progress_percentage']:.1f}%",
            '已完成': f"{completed_count}/{self.stats['total_piles']}"
        }
        
        right_column = {
            '活跃机器': f"{self.stats['active_machines']}/{self.stats['total_machines']}",
            '当前时间': f"{current_time:.1f}h"
        }
        
        # 列对齐设置（调整位置以适应14号字体）
        # left_label_x = panel_x + panel_width * 0.35  # 左移起始位置
        left_value_x = panel_x + panel_width * 0.25   # 左列冒号对齐位置，右移以容纳更长的标签
        # right_label_x = panel_x + 0.15  # 右列起始位置左移
        right_value_x = panel_x + panel_width * 0.75 # 右列冒号对齐位置，右移以容纳更长的标签
        
        line_height = 0.042  # 增加行高以适应14号字体
        start_y = line_y - 0.025
        
        text_elements = [title_text, line]
        
        # 绘制左列
        for i, (label, value) in enumerate(left_column.items()):
            y_pos = start_y - i * line_height
            
            # 标签（右对齐到冒号位置，冒号前加空格）
            label_text = ax.text(left_value_x - 0.01, y_pos, f"{label} :",
                               transform=ax.transAxes, fontsize=14,  # 放大字体
                               color='#34495E', ha='right', va='top', zorder=101)
            
            # 数值（左对齐，从冒号后开始）
            value_text = ax.text(left_value_x + 0.01, y_pos, value,
                               transform=ax.transAxes, fontsize=14,  # 放大字体
                               fontweight='bold', color='#2980B9',
                               ha='left', va='top', zorder=101)
            
            text_elements.extend([label_text, value_text])
        
        # 绘制右列
        for i, (label, value) in enumerate(right_column.items()):
            y_pos = start_y - i * line_height
            
            # 标签（右对齐到冒号位置，冒号前加空格）
            label_text = ax.text(right_value_x - 0.01, y_pos, f"{label} :",
                               transform=ax.transAxes, fontsize=14,  # 放大字体
                               color='#34495E', ha='right', va='top', zorder=101)
            
            # 数值（左对齐，从冒号后开始）
            value_text = ax.text(right_value_x + 0.01, y_pos, value,
                               transform=ax.transAxes, fontsize=14,  # 放大字体
                               fontweight='bold', color='#2980B9',
                               ha='left', va='top', zorder=101)
            
            text_elements.extend([label_text, value_text])
        
        return [panel_bg] + text_elements
    
    def create_gantt_chart(self, gs, current_time: float, frame: int):
        """创建甘特图显示（优化版）"""
        # 只每10帧更新一次甘特图以提升性能
        if frame % 10 != 0 and hasattr(self, 'last_gantt_frame') and self.last_gantt_frame != -1:
            return
        
        self.last_gantt_frame = frame
        
        # 创建甘特图子图
        if hasattr(self, 'gantt_ax') and self.gantt_ax:
            self.gantt_ax.clear()
        else:
            self.gantt_ax = plt.subplot(gs[1, :])
        
        gantt_ax = self.gantt_ax
        
        # 按机器分组显示任务
        machine_tasks = defaultdict(list)
        for task in self.schedule:
            machine_tasks[task['machine']].append(task)
        
        # 绘制甘特图
        y_pos = 0
        machine_labels = []
        
        for machine_id in sorted(machine_tasks.keys()):
            tasks = sorted(machine_tasks[machine_id], key=lambda x: x['start_hour'])
            machine_color = self.machines[machine_id].color
            
            for task in tasks:
                start = task['start_hour']
                duration = task['end_hour'] - task['start_hour']
                
                # 绘制任务条
                bar = gantt_ax.barh(y_pos, duration, left=start, height=0.6,
                                   color=machine_color, alpha=0.7, edgecolor='black')
                
                # 添加桩编号标签
                if duration > 5:  # 只在足够宽的条上显示标签
                    gantt_ax.text(start + duration/2, y_pos, str(task['pile_id']),
                                 ha='center', va='center', fontsize=7, fontweight='bold')
            
            machine_labels.append(f'机器 {machine_id}')
            y_pos += 1
        
        # 绘制当前时间线
        gantt_ax.axvline(x=current_time, color='red', linewidth=2, alpha=0.8, linestyle='--')
        
        # 设置甘特图样式
        gantt_ax.set_yticks(range(len(machine_labels)))
        gantt_ax.set_yticklabels(machine_labels)
        gantt_ax.set_xlabel('时间 (小时)')
        gantt_ax.set_title('施工时间轴 (甘特图)', fontweight='normal', pad=10)
        gantt_ax.grid(True, alpha=0.3, axis='x')
        gantt_ax.set_xlim(0, self.max_end_time * 1.05)
        
        # 添加时间标记
        time_ticks = np.linspace(0, self.max_end_time, 8)
        gantt_ax.set_xticks(time_ticks)
        gantt_ax.set_xticklabels([f'{t:.0f}h' for t in time_ticks])
    
    def update_frame(self, frame: int, ax, gantt_gs, current_artists):
        """更新单帧动画"""
        # 更新渲染进度
        self.frames_rendered = frame + 1
        if self.render_start_time is None:
            self.render_start_time = time.time()
        
        elapsed = time.time() - self.render_start_time
        
        # 每5帧显示一次进度条以减少输出频率
        if frame % 5 == 0 or frame == self.total_frames - 1:
            self.print_progress_bar(self.frames_rendered, self.total_frames, elapsed_time=elapsed)
        
        # 计算当前时间
        current_time = (frame / self.total_frames) * self.max_end_time
        
        # 清除之前的图形元素
        for artist in current_artists:
            if hasattr(artist, 'remove'):
                artist.remove()
        current_artists.clear()
        
        # 获取当前状态
        pile_states, forbidden_zones = self.get_pile_states(current_time)
        self.update_machine_states(pile_states, current_time)
        
        # 按状态分类桩
        not_started_piles = [p for p in pile_states if p.status == 'not_started']
        active_piles = [p for p in pile_states if p.status == 'active']
        completed_piles = [p for p in pile_states if p.status == 'completed']
        
        # 绘制禁区（最底层）
        for zone in forbidden_zones:
            circle = patches.Circle((zone['x'], zone['y']), zone['radius'],
                                   facecolor=self.FORBIDDEN_COLOR,
                                   edgecolor=self.FORBIDDEN_EDGE_COLOR,
                                   alpha=self.FORBIDDEN_ZONE_ALPHA,
                                   linewidth=1, zorder=1)
            ax.add_patch(circle)
            current_artists.append(circle)
        
        # 绘制未开始的桩
        if not_started_piles:
            x_coords = [p.x for p in not_started_piles]
            y_coords = [p.y for p in not_started_piles]
            scatter = ax.scatter(x_coords, y_coords,
                               color=self.NOT_STARTED_COLOR,
                               s=self.PILE_RADIUS_NORMAL**2 * self.SIZE_SCALING,
                               edgecolors='gray', linewidth=0.5, zorder=3, alpha=0.8)
            current_artists.append(scatter)
            
            # 添加桩编号
            for pile in not_started_piles:
                text = ax.text(pile.x, pile.y + self.PILE_RADIUS_NORMAL*0.8, 
                             str(pile.pile_id), fontsize=7, ha='center', va='bottom',
                             color='black', zorder=5)
                current_artists.append(text)
        
        # 绘制已完成的桩
        if completed_piles:
            x_coords = [p.x for p in completed_piles]
            y_coords = [p.y for p in completed_piles]
            scatter = ax.scatter(x_coords, y_coords,
                               color=self.COMPLETED_COLOR,
                               s=self.PILE_RADIUS_NORMAL**2 * self.SIZE_SCALING,
                               edgecolors='white', linewidth=1, zorder=3)
            current_artists.append(scatter)
            
            # 添加桩编号
            for pile in completed_piles:
                text = ax.text(pile.x, pile.y + self.PILE_RADIUS_NORMAL*0.8,
                             str(pile.pile_id), fontsize=7, ha='center', va='bottom',
                             color='white', zorder=5, fontweight='bold')
                current_artists.append(text)
        
        # 绘制施工中的桩和机器
        for pile in active_piles:
            machine_color = self.machines[pile.machine_id].color
            
            # 绘制施工进度环
            progress_radius = self.PILE_RADIUS_ACTIVE * 1.2
            progress_angle = pile.progress * 360
            
            # 背景圆环
            bg_circle = patches.Circle((pile.x, pile.y), progress_radius,
                                     fill=False, edgecolor='lightgray',
                                     linewidth=4, zorder=2)
            ax.add_patch(bg_circle)
            current_artists.append(bg_circle)
            
            # 进度圆环
            if progress_angle > 0:
                wedge = patches.Wedge((pile.x, pile.y), progress_radius, -90, 
                                    -90 + progress_angle, width=0.3,
                                    facecolor=machine_color, edgecolor=machine_color,
                                    linewidth=2, zorder=2)
                ax.add_patch(wedge)
                current_artists.append(wedge)
            
            # 中心桩
            center_scatter = ax.scatter([pile.x], [pile.y],
                                      color=machine_color,
                                      s=self.PILE_RADIUS_ACTIVE**2 * self.SIZE_SCALING,
                                      edgecolors='black', linewidth=2, zorder=4)
            current_artists.append(center_scatter)
            
            # 绘制机器图标
            machine_icons = self.draw_machine_icon(ax, pile.x, pile.y + 3, machine_color, 0.8)
            current_artists.extend(machine_icons)
            
            # 桩编号和机器编号
            pile_text = ax.text(pile.x, pile.y + self.PILE_RADIUS_ACTIVE*0.5,
                              str(pile.pile_id), fontsize=8, ha='center', va='bottom',
                              color='white', zorder=5, fontweight='bold')
            machine_text = ax.text(pile.x, pile.y + 4.5, f'M{pile.machine_id}',
                                 fontsize=7, ha='center', va='center',
                                 color='black', zorder=5, fontweight='bold')
            current_artists.extend([pile_text, machine_text])
        
        # 创建信息面板
        info_elements = self.create_info_panel(ax, current_time)
        current_artists.extend(info_elements)
        
        # 更新甘特图（降低更新频率）
        if hasattr(self, 'gantt_ax'):
            pass  # 甘特图已存在，只在特定帧更新
        self.create_gantt_chart(gantt_gs, current_time, frame)
        
        return current_artists
    
    def create_animation(self, output_filepath: str):
        """创建并保存动画"""
        # 创建图形布局
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.3)
        
        # 主绘图区域
        ax = plt.subplot(gs[0, 0])
        ax.set_xlim(self.min_x - self.padding_x, self.max_x + self.padding_x)
        ax.set_ylim(self.min_y - self.padding_y, self.max_y + self.padding_y)
        ax.set_xlabel("X 坐标 (米)", fontweight='normal')
        ax.set_ylabel("Y 坐标 (米)", fontweight='normal')
        ax.set_title("智能桩基施工过程可视化", fontsize=16, fontweight='normal', pad=20)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.set_aspect('equal', adjustable='box')
        
        # 设置背景色
        ax.set_facecolor('#FAFAFA')
        
        # 创建图例
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', label='未开始',
                      markerfacecolor=self.NOT_STARTED_COLOR, markersize=8),
            plt.Line2D([0], [0], marker='o', color='w', label='已完成',
                      markerfacecolor=self.COMPLETED_COLOR, markersize=8),
        ]
        
        # 添加机器图例
        for i, machine_id in enumerate(sorted(self.machines.keys())):
            if i < len(self.MACHINE_COLORS):
                legend_elements.append(
                    plt.Line2D([0], [0], marker='s', color='w', 
                              label=f'机器 {machine_id}',
                              markerfacecolor=self.machines[machine_id].color, 
                              markersize=8, markeredgecolor='black')
                )
        
        # 添加禁区图例
        legend_elements.append(
            patches.Patch(facecolor=self.FORBIDDEN_COLOR, 
                         edgecolor=self.FORBIDDEN_EDGE_COLOR,
                         alpha=self.FORBIDDEN_ZONE_ALPHA, 
                         label='完工禁区 (36h)')
        )
        
        ax.legend(handles=legend_elements, loc='upper left', 
                 bbox_to_anchor=(0, 1), framealpha=0.9, 
                 fancybox=True, shadow=True)
        
        plt.subplots_adjust(bottom=0.1, top=0.95, left=0.08, right=0.95)
        
        # 动画状态
        current_artists = []
        
        def animate(frame):
            return self.update_frame(frame, ax, gs, current_artists)
        
        print(f"开始生成高级动画...")
        print(f"  └─ 总帧数: {self.total_frames} 帧")
        print(f"  └─ 动画时长: {self.ANIMATION_DURATION_SECONDS} 秒") 
        print(f"  └─ 帧率: {self.FPS} FPS")
        print(f"  └─ 输出文件: {output_filepath}")
        print("="*60)
        
        # 创建动画
        ani = animation.FuncAnimation(fig, animate, frames=self.total_frames,
                                    interval=1000/self.FPS, blit=False, repeat=False)
        
        # 保存动画
        self.save_animation(ani, output_filepath, fig)
    
    def save_animation(self, ani, output_filepath: str, fig):
        """保存动画到文件"""
        print("\n" + "="*60)
        print("开始保存动画文件...")
        
        save_start_time = time.time()
        
        if not ffmpeg_available:
            print("[WARNING] ffmpeg不可用，将保存为GIF格式...")
            try:
                gif_path = output_filepath.replace('.mp4', '.gif')
                ani.save(gif_path, writer='pillow', fps=max(1, self.FPS//2))
                save_time = time.time() - save_start_time
                print(f"[OK] 动画已保存为GIF: {gif_path}")
                print(f"保存耗时: {save_time:.1f} 秒")
                return
            except Exception as e:
                print(f"[ERROR] 保存GIF失败: {e}")
                self.save_static_frames(fig, output_filepath)
                return
        
        try:
            # 使用快速编码设置保存MP4
            writer = animation.FFMpegWriter(
                fps=self.FPS,
                metadata=dict(artist='Enhanced Pile Construction Visualizer'),
                bitrate=1500,  # 降低比特率
                extra_args=['-vcodec', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-pix_fmt', 'yuv420p']
            )
            ani.save(output_filepath, writer=writer, dpi=100)  # 降低DPI
            
            save_time = time.time() - save_start_time
            total_time = time.time() - self.render_start_time if self.render_start_time else save_time
            
            print(f"[OK] 高级动画已保存到: {output_filepath}")
            print(f"保存耗时: {save_time:.1f} 秒")
            print(f"总耗时: {total_time:.1f} 秒")
            print("="*60)
            
        except Exception as e:
            print(f"[ERROR] 保存MP4失败: {e}")
            print("[INFO] 尝试保存为GIF...")
            try:
                gif_path = output_filepath.replace('.mp4', '.gif')
                ani.save(gif_path, writer='pillow', fps=max(1, self.FPS//2))
                save_time = time.time() - save_start_time
                print(f"[OK] 动画已保存为GIF: {gif_path}")
                print(f"保存耗时: {save_time:.1f} 秒")
            except Exception as gif_e:
                print(f"[ERROR] 保存GIF也失败: {gif_e}")
                self.save_static_frames(fig, output_filepath)
    
    def save_static_frames(self, fig, output_filepath: str):
        """保存静态关键帧"""
        print("[INFO] 保存静态关键帧...")
        key_frames = [0, self.total_frames//4, self.total_frames//2, 
                     3*self.total_frames//4, self.total_frames-1]
        
        for i, frame in enumerate(key_frames):
            try:
                # 这里需要手动调用update函数来更新帧
                static_path = output_filepath.replace('.mp4', f'_frame_{i}.png')
                fig.savefig(static_path, dpi=150, bbox_inches='tight')
                print(f"[OK] 已保存静态图: {static_path}")
            except Exception as e:
                print(f"[ERROR] 保存静态图失败: {e}")

def main(input_filepath: str, output_filepath: str):
    """主函数"""
    print(f"=== 开始处理高级可视化 ===")
    print(f"输入文件: {input_filepath}")
    print(f"输出文件: {output_filepath}")
    
    # 检查输入文件
    if not os.path.exists(input_filepath):
        print(f"[ERROR] 输入文件不存在: {input_filepath}")
        sys.exit(1)
    
    # 检查输出目录
    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"[OK] 创建输出目录: {output_dir}")
        except Exception as e:
            print(f"[ERROR] 创建输出目录失败: {e}")
            sys.exit(1)
    
    # 创建可视化器
    visualizer = EnhancedConstructionVisualizer()
    
    # 加载和初始化数据
    schedule = visualizer.load_schedule(input_filepath)
    visualizer.initialize_data(schedule)
    
    # 创建和保存动画
    visualizer.create_animation(output_filepath)
    
    print("=== 高级可视化完成 ===")

if __name__ == '__main__':
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='生成增强版桩基施工动画')
    parser.add_argument('input_file', type=str, help='输入的调度JSON文件路径')
    parser.add_argument('output_file', type=str, help='输出的动画文件路径')
    
    args = parser.parse_args()
    
    main(args.input_file, args.output_file)
