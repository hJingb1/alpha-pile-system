from ortools.sat.python import cp_model
import math
import numpy as np
import json
from sklearn.cluster import KMeans
from scipy.stats import lognorm  # 新增：用于对数正态分布
import random

def get_duration_from_distribution(mu=3.16, sigma=0.63, scenario='expected'):
    """
    根据对数正态分布计算施工时长
    
    Args:
        mu: 对数正态分布的对数均值参数
        sigma: 对数正态分布的对数标准差参数
        scenario: 计算场景 ('expected', 'pessimistic_90', 'most_likely')
        
    Returns:
        float: 计算出的施工时长（小时）
    """
    if scenario == 'expected':
        # 对数正态分布的期望值: exp(mu + sigma^2/2)
        return math.exp(mu + sigma**2 / 2)
    elif scenario == 'pessimistic_90':
        # 90%分位数（悲观场景）
        return lognorm.ppf(0.895, s=sigma, scale=math.exp(mu))
    elif scenario == 'most_likely':
        # 众数：exp(mu - sigma^2)
        return math.exp(mu - sigma**2)
    else:
        # 默认返回期望值
        return math.exp(mu + sigma**2 / 2)

def generate_random_durations(num_piles, mu=3.16, sigma=0.63, random_seed=None):
    """
    为每个桩基生成随机的施工时长
    
    Args:
        num_piles: 桩基数量
        mu: 对数正态分布的对数均值参数
        sigma: 对数正态分布的对数标准差参数
        random_seed: 随机种子，用于可重现的结果
        
    Returns:
        list: 每个桩基的随机施工时长（小时）
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # 使用scipy生成对数正态分布的随机样本
    durations = lognorm.rvs(s=sigma, scale=math.exp(mu), size=num_piles)
    return durations.tolist()

def simulate_schedule_execution(schedule, pile_durations_dict, forbidden_duration_hours=36, 
                               simultaneous_exclude_half_side=10, forbidden_zone_diameter_multiplier=12):
    """
    模拟调度计划的执行，计算实际完成时间
    
    Args:
        schedule: 调度计划列表
        pile_durations_dict: 字典，桩基ID到实际时长的映射
        forbidden_duration_hours: 禁区持续时长
        simultaneous_exclude_half_side: 同时施工排除半径
        forbidden_zone_diameter_multiplier: 完工禁区直径乘数
        
    Returns:
        float: 模拟的总工期（小时）
    """
    # 按机器分组任务
    tasks_by_machine = {}
    for task in schedule:
        machine = task['machine']
        if machine not in tasks_by_machine:
            tasks_by_machine[machine] = []
        tasks_by_machine[machine].append(task.copy())
    
    # 为每台机器按开始时间排序任务
    for machine in tasks_by_machine:
        tasks_by_machine[machine].sort(key=lambda x: x['start_hour'])
    
    # 模拟执行过程
    pile_actual_end_times = {}  # 存储每个桩基的实际结束时间
    machine_current_time = {machine: 0.0 for machine in tasks_by_machine}
    
    # 按照原计划的开始时间顺序处理所有任务
    all_tasks_sorted = sorted(schedule, key=lambda x: x['start_hour'])
    
    for task in all_tasks_sorted:
        pile_id = task['pile_id']
        machine = task['machine']
        
        # 获取这个桩基的实际时长
        actual_duration = pile_durations_dict.get(pile_id, task['duration_hour'])
        
        # 确定实际开始时间（不能早于机器空闲时间）
        earliest_start = machine_current_time[machine]
        
        # 检查空间约束（简化版本，只考虑完工禁区）
        for other_pile_id, other_end_time in pile_actual_end_times.items():
            if other_pile_id != pile_id:
                # 计算距离（从原始调度中获取坐标）
                other_task = next((t for t in schedule if t['pile_id'] == other_pile_id), None)
                if other_task:
                    dx = task['x'] - other_task['x']
                    dy = task['y'] - other_task['y']
                    distance = math.sqrt(dx**2 + dy**2)
                    
                    # 计算禁区半径
                    pile_diameter = other_task.get('diameter', 1.0)
                    forbidden_radius = pile_diameter * forbidden_zone_diameter_multiplier / 2
                    
                    # 如果在禁区内，需要等待禁区时间结束
                    if distance <= forbidden_radius:
                        forbidden_end_time = other_end_time + forbidden_duration_hours
                        earliest_start = max(earliest_start, forbidden_end_time)
        
        # 设置实际开始和结束时间
        actual_start = earliest_start
        actual_end = actual_start + actual_duration
        
        # 更新记录
        pile_actual_end_times[pile_id] = actual_end
        machine_current_time[machine] = actual_end
    
    # 返回最大结束时间作为总工期
    return max(pile_actual_end_times.values()) if pile_actual_end_times else 0.0

def evaluate_plan_robustness(schedule, original_makespan, num_simulations=1000, mu=3.16, sigma=0.63, 
                           config_params=None):
    """
    使用蒙特卡洛模拟评估调度计划的鲁棒性
    
    Args:
        schedule: CP-SAT求解出的调度计划
        original_makespan: 原始计划的总工期
        num_simulations: 蒙特卡洛模拟次数
        mu, sigma: 对数正态分布参数
        config_params: 配置参数字典
        
    Returns:
        dict: 包含概率评估和统计摘要的字典
    """
    if not schedule or len(schedule) == 0:
        return {
            'completion_probability': None,
            'simulated_stats': None,
            'error': 'Empty schedule'
        }
    
    # 提取桩基ID列表
    pile_ids = [task['pile_id'] for task in schedule]
    unique_pile_ids = list(set(pile_ids))
    
    # 获取配置参数
    forbidden_duration_hours = config_params.get('forbidden_duration_hours', 36) if config_params else 36
    simultaneous_exclude_half_side = config_params.get('simultaneous_exclude_half_side', 10) if config_params else 10
    forbidden_zone_diameter_multiplier = config_params.get('forbidden_zone_diameter_multiplier', 12) if config_params else 12
    
    simulated_makespans = []
    
    try:
        for sim in range(num_simulations):
            # 为每个桩基生成随机时长
            random_durations = generate_random_durations(len(unique_pile_ids), mu, sigma, 
                                                       random_seed=sim)  # 使用模拟次数作为种子确保可重现
            pile_durations_dict = dict(zip(unique_pile_ids, random_durations))
            
            # 模拟调度执行
            simulated_makespan = simulate_schedule_execution(
                schedule, pile_durations_dict, forbidden_duration_hours,
                simultaneous_exclude_half_side, forbidden_zone_diameter_multiplier
            )
            simulated_makespans.append(simulated_makespan)
        
        # 计算统计信息
        simulated_makespans = np.array(simulated_makespans)
        completion_probability = np.mean(simulated_makespans <= original_makespan)
        
        stats = {
            'mean': float(np.mean(simulated_makespans)),
            'median': float(np.median(simulated_makespans)),
            'std': float(np.std(simulated_makespans)),
            'p10': float(np.percentile(simulated_makespans, 10)),
            'p25': float(np.percentile(simulated_makespans, 25)),
            'p75': float(np.percentile(simulated_makespans, 75)),
            'p90': float(np.percentile(simulated_makespans, 90)),
            'min': float(np.min(simulated_makespans)),
            'max': float(np.max(simulated_makespans)),
            'num_simulations': num_simulations
        }
        
        return {
            'completion_probability': float(completion_probability),
            'simulated_stats': stats,
            'error': None
        }
    
    except Exception as e:
        return {
            'completion_probability': None,
            'simulated_stats': None,
            'error': f'Simulation error: {str(e)}'
        }

def cluster_piles(piles: list, num_clusters: int) -> list:
    """
    使用K-Means对桩基坐标进行聚类分区
    
    Args:
        piles: 桩基数据列表，每个桩基包含x、y坐标
        num_clusters: 期望的聚类数量
        
    Returns:
        list: 添加了zone_id字段的桩基数据列表
    """
    if len(piles) == 0:
        return piles
    
    # 如果桩基数量少于聚类数，直接分配
    if len(piles) <= num_clusters:
        new_piles = []
        for i, pile in enumerate(piles):
            new_pile = pile.copy()
            new_pile['zone_id'] = i
            new_piles.append(new_pile)
        return new_piles
    
    # 提取坐标数据
    coordinates = np.array([[pile['x'], pile['y']] for pile in piles])
    
    # 执行K-Means聚类
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(coordinates)
    
    # 将聚类结果添加到桩基数据中
    new_piles = []
    for i, pile in enumerate(piles):
        new_pile = pile.copy()
        new_pile['zone_id'] = int(cluster_labels[i])
        new_piles.append(new_pile)
    
    return new_piles

def solve_pile_schedule(config_data):
    """
    求解桩基施工调度问题
    
    Args:
        config_data (dict): 配置参数字典，包含：
            - piles: 桩基数据列表，每个桩基包含id、x、y、type和diameter字段
            - num_machines: 设备数量
            - duration_scenario: 施工时长场景 ('expected', 'pessimistic_90', 'most_likely', 'random_sample')
            - weather_buffer_hours: 天气影响缓冲时间（小时）
            - monte_carlo_simulations: 蒙特卡洛模拟次数（默认1000）
            - forbidden_duration_hours: 禁区持续时长（小时）
            - simultaneous_exclude_half_side: 同时施工排除区域的半边长（米）
            - forbidden_zone_diameter_multiplier: 完工禁区直径乘数（默认为6）
            - solver_num_workers: 求解器工作线程数
            - solver_max_time: 最大求解时间（秒）
            
    Returns:
        dict: 求解结果，包含：
            - status: 求解状态
            - makespan_hours: 总工期（小时）
            - estimated_makespan_with_buffer: 含天气缓冲的预估总工期（小时）
            - completion_probability: 计划实现概率
            - simulated_stats: 模拟统计信息
            - schedule: 详细调度计划
            - statistics: 求解统计信息
    """
    # 从配置中读取参数
    original_pile_data = config_data['piles']
    N_MACHINES = config_data['num_machines']
    TIME_UNIT_SCALE = 10  # 时间单位转换因子，保持为内部固定值
    
    # 获取施工时长场景和天气缓冲参数
    duration_scenario = config_data.get('duration_scenario', 'expected')
    weather_buffer_hours = config_data.get('weather_buffer_hours', 0.0)
    monte_carlo_simulations = config_data.get('monte_carlo_simulations', 1000)
    
    # 获取分区配置参数
    num_zones = config_data.get('num_zones', N_MACHINES)  # 默认等于设备数量
    zone_penalty_hours = config_data.get('zone_penalty_hours', 10)  # 默认10小时惩罚
    
    # 对桩基进行聚类分区
    pile_data = cluster_piles(original_pile_data, num_zones)
    
    # 获取桩基数量
    N_PILES = len(pile_data)
    N_ZONES = num_zones
    
    # 计算施工时长
    pile_durations_tenths = []
    if duration_scenario == 'random_sample':
        # 改进的随机采样场景：使用多次采样的统计值
        print(f"使用多次采样统计进行优化...")
        num_samples_for_optimization = 100  # 用于优化的采样次数
        all_samples = []
        for _ in range(num_samples_for_optimization):
            samples = generate_random_durations(N_PILES)
            all_samples.append(samples)
        
        # 转换为numpy数组以便计算统计值
        all_samples = np.array(all_samples)
        
        # 使用P75分位数（较为保守的策略）
        optimization_durations = np.percentile(all_samples, 75, axis=0)
        
        print(f"优化使用P75分位数时长，样本平均值: {np.mean(optimization_durations):.1f}h")
        
        for duration_hours in optimization_durations:
            pile_durations_tenths.append(int(duration_hours * TIME_UNIT_SCALE))
    else:
        # 确定性场景：所有桩基使用统一时长
        uniform_duration_hours = get_duration_from_distribution(scenario=duration_scenario)
        for pile in pile_data:
            pile_durations_tenths.append(int(uniform_duration_hours * TIME_UNIT_SCALE))

    # 计算桩基之间的距离
    pile_distances = {}
    for i in range(N_PILES):
        for j in range(N_PILES):
            if i != j:
                dx = pile_data[i]['x'] - pile_data[j]['x']
                dy = pile_data[i]['y'] - pile_data[j]['y']
                pile_distances[(i,j)] =  math.sqrt(dx**2 + dy**2)
    
    # 预计算空间约束
    simulataneous_spatial_conflicts = {}
    for i in range(N_PILES):
        for j in range(N_PILES):
            if i != j:
                if pile_distances[(i,j)] <= config_data['simultaneous_exclude_half_side']:
                    simulataneous_spatial_conflicts[(i,j)] = True
    
    # 获取禁区直径乘数
    forbidden_zone_diameter_multiplier = config_data.get('forbidden_zone_diameter_multiplier', 12)
    
    # 计算完工禁区 - 使用每个桩基的直径
    forbidden_zone_spatial_conflicts = {}
    for i in range(N_PILES):
        for j in range(N_PILES):
            if i != j:
                # 获取桩基i的直径，如果未指定则使用默认值1米
                pile_i_diameter = pile_data[i].get('diameter', 1.0)
                
                # 计算桩基i的禁区半径 (直径 * 乘数 / 2)
                forbidden_radius = pile_i_diameter * forbidden_zone_diameter_multiplier / 2
                
                # 如果j在i的禁区内
                if pile_distances[(i,j)] <= forbidden_radius:
                    forbidden_zone_spatial_conflicts[(i,j)] = True
    
    # 确保时间参数是整数
    forbidden_duration_tenths = int(config_data['forbidden_duration_hours'] * TIME_UNIT_SCALE)
    horizen = int(sum(pile_durations_tenths))
    
    # 创建模型
    model = cp_model.CpModel()
    
    # 创建变量
    start_vars = {}
    end_vars = {}
    task_intervals = {}
    for i in range(N_PILES):
        start_vars[i] = model.NewIntVar(0, horizen, f'start_{i}')
        end_vars[i] = model.NewIntVar(0, horizen, f'end_{i}')
        task_intervals[i] = model.NewIntervalVar(start_vars[i], pile_durations_tenths[i], end_vars[i], f'pile_{i}')
    
    # 可选间隔变量
    task_on_machine = {}
    is_on_machine = {}
    for i in range(N_PILES):
        for m in range(N_MACHINES):
            is_on_machine[i,m] = model.NewBoolVar(f'is_on_machine_{i}_{m}')
            task_on_machine[i,m] = model.NewOptionalIntervalVar(
                start_vars[i],
                pile_durations_tenths[i],
                end_vars[i],
                is_on_machine[i,m],
                f'pile_{i}_on_machine_{m}'
            )
    
    # 分区约束变量
    is_working_in_zone = {}
    for m in range(N_MACHINES):
        for z in range(N_ZONES):
            is_working_in_zone[m, z] = model.NewBoolVar(f'machine_{m}_working_in_zone_{z}')
    
    num_zones_worked = {}
    for m in range(N_MACHINES):
        num_zones_worked[m] = model.NewIntVar(0, N_ZONES, f'num_zones_worked_machine_{m}')
    
    total_zone_switches = model.NewIntVar(0, N_MACHINES * N_ZONES, 'total_zone_switches')
    
    # 添加约束
    for m in range(N_MACHINES):
        model.AddNoOverlap([task_on_machine[(i,m)] for i in range(N_PILES)])
    
    for i in range(N_PILES):
        model.AddExactlyOne([is_on_machine[i,m] for m in range(N_MACHINES)])
    
    # 分区约束：如果机器m处理分区z中的任何桩基，则is_working_in_zone[m,z]为True
    for m in range(N_MACHINES):
        for z in range(N_ZONES):
            piles_in_zone_z = [i for i in range(N_PILES) if pile_data[i]['zone_id'] == z]
            if piles_in_zone_z:
                # 如果机器m处理分区z中的任何桩基，则is_working_in_zone[m,z]为True
                model.AddMaxEquality(is_working_in_zone[m, z], [is_on_machine[i, m] for i in piles_in_zone_z])
    
    # 计算每台机器工作的分区总数
    for m in range(N_MACHINES):
        model.Add(num_zones_worked[m] == sum(is_working_in_zone[m, z] for z in range(N_ZONES)))
    
    # 计算总的分区工作数
    model.Add(total_zone_switches == sum(num_zones_worked[m] for m in range(N_MACHINES)))
    
    # 空间约束1：同时施工排除区域
    for i in range(N_PILES):
        for j in range(i + 1, N_PILES):
            if (i,j) in simulataneous_spatial_conflicts:
                lit_i_before_j = model.NewBoolVar(f'lit_{i}_before_{j}')
                model.Add(end_vars[i] <= start_vars[j]).OnlyEnforceIf(lit_i_before_j)
                model.Add(end_vars[i] > start_vars[j]).OnlyEnforceIf(lit_i_before_j.Not())
                
                lit_j_before_i = model.NewBoolVar(f'lit_{j}_before_{i}')
                model.Add(end_vars[j] <= start_vars[i]).OnlyEnforceIf(lit_j_before_i)
                model.Add(end_vars[j] > start_vars[i]).OnlyEnforceIf(lit_j_before_i.Not())
                
                same_machine_ij_bool = model.NewBoolVar(f'same_machine_{i}_{j}')
                literals_both_on_m = []
                for m in range(N_MACHINES):
                    lit_both_on_m = model.NewBoolVar(f'lit_both_on_m_{i}_{j}_{m}')
                    model.AddImplication(lit_both_on_m, is_on_machine[i, m])
                    model.AddImplication(lit_both_on_m, is_on_machine[j, m])
                    model.AddBoolOr([is_on_machine[i, m].Not(), is_on_machine[j, m].Not()]).OnlyEnforceIf(lit_both_on_m.Not())
                    literals_both_on_m.append(lit_both_on_m)
                
                model.AddBoolOr(literals_both_on_m).OnlyEnforceIf(same_machine_ij_bool)
                for lit in literals_both_on_m:
                    model.AddImplication(lit, same_machine_ij_bool)
                
                model.AddBoolOr([lit_i_before_j, lit_j_before_i, same_machine_ij_bool])
    
    # 空间约束2：完工禁区
    for i in range(N_PILES):
        for j in range(N_PILES):
            if i == j:
                continue
            if (i, j) in forbidden_zone_spatial_conflicts:
                j_starts_after_i_ends_bool = model.NewBoolVar(f'j_starts_after_i_ends_{i}_{j}')
                model.Add(start_vars[j] >= end_vars[i]).OnlyEnforceIf(j_starts_after_i_ends_bool)
                model.Add(start_vars[j] < end_vars[i]).OnlyEnforceIf(j_starts_after_i_ends_bool.Not())
                model.Add(start_vars[j] >= end_vars[i] + forbidden_duration_tenths).OnlyEnforceIf(j_starts_after_i_ends_bool)
    
    # 目标函数
    makespan = model.NewIntVar(0, horizen, 'makespan')
    model.AddMaxEquality(makespan, [end_vars[i] for i in range(N_PILES)])
    
    # 计算分区惩罚（确保不为负数）
    zone_penalty_coefficient = int(zone_penalty_hours * TIME_UNIT_SCALE)
    zone_penalty_term = model.NewIntVar(0, zone_penalty_coefficient * N_MACHINES * N_ZONES, 'zone_penalty_term')
    excess_zones = model.NewIntVar(0, N_MACHINES * N_ZONES, 'excess_zones')
    
    # excess_zones = max(0, total_zone_switches - N_MACHINES)
    model.AddMaxEquality(excess_zones, [0, total_zone_switches - N_MACHINES])
    model.Add(zone_penalty_term == zone_penalty_coefficient * excess_zones)
    
    # 组合目标函数
    objective = model.NewIntVar(0, horizen + zone_penalty_coefficient * N_MACHINES * N_ZONES, 'objective')
    model.Add(objective == makespan + zone_penalty_term)
    model.Minimize(objective)
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = config_data.get('solver_num_workers', 3)
    solver.parameters.max_time_in_seconds = config_data.get('solver_max_time', 300)
    
    status = solver.Solve(model)
    
    # 准备返回结果
    result = {
        'status': solver.StatusName(status),
        'makespan_hours': None,
        'estimated_makespan_with_buffer': None,
        'completion_probability': None,
        'simulated_stats': None,
        'schedule': [],
        'statistics': {
            'branches': solver.NumBranches(),
            'conflicts': solver.NumConflicts(),
            'wall_time': solver.WallTime()
        }
    }
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        makespan_hours = solver.Value(makespan) / TIME_UNIT_SCALE
        result['makespan_hours'] = makespan_hours
        
        # 收集调度结果
        for i in range(N_PILES):
            start_time_tenths = solver.Value(start_vars[i])
            end_time_tenths = solver.Value(end_vars[i])
            duration_tenths = pile_durations_tenths[i]
            
            for m in range(N_MACHINES):
                if solver.Value(is_on_machine[i,m]):
                    task_info = {
                        'pile_id': pile_data[i]['id'],
                        'x': pile_data[i]['x'],
                        'y': pile_data[i]['y'],
                        'type': pile_data[i].get('type', 1),  # 添加类型信息
                        'diameter': pile_data[i].get('diameter', 1.0),  # 添加直径信息
                        'zone_id': pile_data[i].get('zone_id', 0),  # 添加分区信息
                        'start_hour': start_time_tenths / TIME_UNIT_SCALE,
                        'end_hour': end_time_tenths / TIME_UNIT_SCALE,
                        'duration_hour': duration_tenths / TIME_UNIT_SCALE,
                        'machine': m + 1
                    }
                    result['schedule'].append(task_info)
                    break
        
        # 按开始时间排序
        result['schedule'].sort(key=lambda x: x['start_hour'])
        
        # 计算含天气缓冲的预估总工期
        estimated_makespan_with_buffer = makespan_hours + weather_buffer_hours
        result['estimated_makespan_with_buffer'] = estimated_makespan_with_buffer
        
        # 进行概率评估
        if result['schedule']:
            print(f"开始进行蒙特卡洛模拟，模拟次数: {monte_carlo_simulations}")
            robustness_eval = evaluate_plan_robustness(
                result['schedule'], 
                makespan_hours,  # 使用基础工期（不含缓冲）
                monte_carlo_simulations,
                config_params=config_data
            )
            result['completion_probability'] = robustness_eval['completion_probability']
            result['simulated_stats'] = robustness_eval['simulated_stats']
            if robustness_eval.get('error'):
                print(f"概率评估出现错误: {robustness_eval['error']}")
    
    return result

# 示例配置
default_config = {
    'num_machines': 3,
    'duration_scenario': 'expected',
    'weather_buffer_hours': 0.0,
    'forbidden_duration_hours': 36,
    'simultaneous_exclude_half_side': 16,
    'forbidden_zone_diameter_multiplier': 12,  # 新增：禁区直径乘数
    'num_zones': 3,  # 新增：分区数量
    'zone_penalty_hours': 10,  # 新增：跨区域移动惩罚
    'solver_num_workers': 6,
    'solver_max_time': 600,
    'piles': [
    {'id':1,'x':2,'y':-1, 'type':1, 'diameter':1.5},
{'id':2,'x':6,'y':-1, 'type':1, 'diameter':1.5},
{'id':3,'x':20,'y':-2, 'type':1, 'diameter':1.5},
{'id':4,'x':24,'y':-2, 'type':1, 'diameter':1.5},
{'id':5,'x':36,'y':-3, 'type':1, 'diameter':1.5},
{'id':6,'x':40,'y':-3, 'type':1, 'diameter':1.5},
{'id':7,'x':56,'y':-3, 'type':1, 'diameter':1.5},
{'id':8,'x':60,'y':-3, 'type':1, 'diameter':1.5},
{'id':9,'x':65,'y':-3, 'type':1, 'diameter':1.0},
{'id':10,'x':69,'y':-3, 'type':1, 'diameter':1.5},
{'id':11,'x':74,'y':-3, 'type':1, 'diameter':1.5},
{'id':12,'x':78,'y':-3, 'type':1, 'diameter':1.5},
{'id':13,'x':82,'y':-3, 'type':1, 'diameter':1.5},
{'id':14,'x':87,'y':-3, 'type':1, 'diameter':1.5},
{'id':15,'x':92,'y':-3, 'type':1, 'diameter':1.5},
{'id':16,'x':96,'y':-3, 'type':1, 'diameter':1.5},
{'id':17,'x':101,'y':-3, 'type':1, 'diameter':1.5},
{'id':18,'x':105,'y':-3, 'type':1, 'diameter':1.5},
{'id':19,'x':25,'y':-7, 'type':2, 'diameter':1.2},
{'id':20,'x':25,'y':-11, 'type':2, 'diameter':1.2},
{'id':21,'x':28,'y':-11, 'type':2, 'diameter':1.2},
{'id':22,'x':28,'y':-7, 'type':2, 'diameter':1.2},
{'id':23,'x':55,'y':-7, 'type':2, 'diameter':1.2},
{'id':24,'x':55,'y':-11, 'type':2, 'diameter':1.2},
{'id':25,'x':58,'y':-11, 'type':2, 'diameter':1.2},
{'id':26,'x':58,'y':-7, 'type':2, 'diameter':1.2},
{'id':27,'x':83,'y':-7, 'type':2, 'diameter':1.2},
{'id':28,'x':86,'y':-7, 'type':2, 'diameter':1.2},
{'id':29,'x':86,'y':-11, 'type':2, 'diameter':1.2},
{'id':30,'x':83,'y':-11, 'type':2, 'diameter':1.2},
{'id':31,'x':105,'y':-14, 'type':3, 'diameter':1.0},
{'id':32,'x':105,'y':-18, 'type':3, 'diameter':1.0},
{'id':33,'x':105,'y':-21, 'type':3, 'diameter':1.0},
{'id':34,'x':101,'y':-21, 'type':3, 'diameter':1.0},
{'id':35,'x':101,'y':-18, 'type':3, 'diameter':1.0},
{'id':36,'x':101,'y':-14, 'type':3, 'diameter':1.0},
{'id':37,'x':95,'y':-12, 'type':3, 'diameter':1.0},
{'id':38,'x':95,'y':-16, 'type':3, 'diameter':1.0},
{'id':39,'x':91,'y':-14, 'type':3, 'diameter':1.0},
{'id':40,'x':94,'y':-19, 'type':3, 'diameter':1.0},
{'id':41,'x':96,'y':-23, 'type':3, 'diameter':1.0},
{'id':42,'x':92,'y':-23, 'type':3, 'diameter':1.0},
{'id':43,'x':87,'y':-14, 'type':3, 'diameter':1.0},
{'id':44,'x':83,'y':-14, 'type':3, 'diameter':1.0},
{'id':45,'x':78,'y':-15, 'type':3, 'diameter':1.0},
{'id':46,'x':74,'y':-15, 'type':3, 'diameter':1.0},
{'id':47,'x':76,'y':-12, 'type':3, 'diameter':1.0},
{'id':48,'x':66,'y':-12, 'type':3, 'diameter':1.0},
{'id':49,'x':68,'y':-15, 'type':3, 'diameter':1.0},
{'id':50,'x':64,'y':-15, 'type':3, 'diameter':1.0},
{'id':51,'x':59,'y':-14, 'type':3, 'diameter':1.0},
{'id':52,'x':55,'y':-14, 'type':3, 'diameter':1.0},
{'id':53,'x':51,'y':-14, 'type':3, 'diameter':1.0},
{'id':54,'x':47,'y':-14, 'type':3, 'diameter':1.0},
{'id':55,'x':40,'y':-13, 'type':3, 'diameter':1.0},
{'id':56,'x':38,'y':-16, 'type':3, 'diameter':1.0},
{'id':57,'x':36,'y':-13, 'type':3, 'diameter':1.0},
{'id':58,'x':33,'y':-14, 'type':3, 'diameter':1.0},
{'id':59,'x':29,'y':-14, 'type':3, 'diameter':1.0},
{'id':60,'x':24,'y':-14, 'type':3, 'diameter':1.0},
{'id':61,'x':21,'y':-16, 'type':3, 'diameter':1.0},
{'id':62,'x':21,'y':-12, 'type':3, 'diameter':1.0},
{'id':63,'x':13,'y':-12, 'type':3, 'diameter':1.0},
{'id':64,'x':13,'y':-16, 'type':3, 'diameter':1.0},

]
}

if __name__ == '__main__':
    # 使用默认配置运行求解器
    result = solve_pile_schedule(default_config)
    
    # 打印结果
    print(f'求解状态：{result["status"]}')
    if result['makespan_hours'] is not None:
        print(f'最优解：{result["makespan_hours"]:.2f}小时')
        
        print('\n----详细调度计划----')
        # 按机器分组显示任务
        tasks_by_machine = {}
        for task in result['schedule']:
            machine = task['machine']
            if machine not in tasks_by_machine:
                tasks_by_machine[machine] = []
            tasks_by_machine[machine].append(task)
        
        for m in sorted(tasks_by_machine.keys()):
            print(f'\n机器 {m} 任务:')
            for task in tasks_by_machine[m]:
                print(f'  桩基 {task["pile_id"]} (X:{task["x"]}, Y:{task["y"]}, 类型:{task["type"]}, 直径:{task["diameter"]}, 分区:{task["zone_id"]}): '
                      f'开始 {task["start_hour"]:.2f}h, 结束 {task["end_hour"]:.2f}h '
                      f'(持续 {task["duration_hour"]:.2f}h)')
        
        # 保存到JSON文件
        output_filename = 'schedule.json'
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(result['schedule'], f, ensure_ascii=False, indent=4)
            print(f"\n成功将调度结果保存到 {output_filename}")
        except IOError as e:
            print(f"\n错误：无法写入文件 {output_filename}. 原因: {e}")
    
    print('--------------------------------')
    print(f'求解统计：')
    print(f'分支数量：{result["statistics"]["branches"]}')
    print(f'冲突数量：{result["statistics"]["conflicts"]}')
    print(f'求解时间：{result["statistics"]["wall_time"]:.2f}秒')














