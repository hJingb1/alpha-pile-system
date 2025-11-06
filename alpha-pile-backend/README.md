# 桩基施工调度优化系统

基于 Google OR-Tools CP-SAT 求解器的桩基施工调度优化系统，带有 RESTful API 服务。

## 功能特点

- 基于约束规划的施工调度优化
- 支持不同类型和直径的桩基
- 考虑设备数量限制
- 处理空间冲突约束（同时施工区域排除）
- 动态计算完工后的禁区范围（基于桩基直径）
- 通过 FastAPI 提供 RESTful 服务
- 支持异步处理长时间运行的求解任务

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 作为库使用

```python
from main import solve_pile_schedule

# 配置桩基调度参数
config = {
    'num_machines': 3,
    'pile_type_durations': {
        1: 33,  # 类型1桩基，33小时
        2: 31,  # 类型2桩基，31小时
        3: 29   # 类型3桩基，29小时
    },
    'forbidden_duration_hours': 36,
    'simultaneous_exclude_half_side': 16,
    'forbidden_zone_diameter_multiplier': 12,
    'solver_num_workers': 6,
    'solver_max_time': 300,
    'piles': [
        {'id': 1, 'x': 2, 'y': -1, 'type': 1, 'diameter': 1.5},
        # ... 更多桩基数据
    ]
}

# 求解调度问题
result = solve_pile_schedule(config)

# 输出结果
print(f"求解状态: {result['status']}")
print(f"总工期: {result['makespan_hours']} 小时")
print(f"调度计划: {len(result['schedule'])} 个任务")
```

### 作为API服务运行

```bash
# 启动API服务
python api.py
```

服务启动后，可通过以下方式访问：

- API文档：http://localhost:8000/docs 或 http://localhost:8000/redoc
- API端点：
  - POST /schedule - 创建调度计划任务
  - GET /schedule/{task_id} - 获取任务状态和结果

### 异步API使用流程

1. 提交调度任务，获取任务ID：
```bash
curl -X POST http://localhost:8000/schedule -H "Content-Type: application/json" -d @request.json
```

2. 使用任务ID查询任务状态和结果：
```bash
curl http://localhost:8000/schedule/task_1234567890
```

3. 查看任务结果（当状态为"completed"时）

### 测试API

可以使用提供的测试脚本：

```bash
python test_api.py
```

脚本会提交一个调度任务，并轮询任务状态直到完成，然后显示结果。

### API请求示例

```json
POST /schedule

{
  "piles": [
    {"id": 1, "x": 2, "y": -1, "type": 1, "diameter": 1.5},
    {"id": 2, "x": 6, "y": -1, "type": 1, "diameter": 1.5}
  ],
  "num_machines": 3,
  "pile_type_durations": {
    "1": 33,
    "2": 31,
    "3": 29
  },
  "forbidden_duration_hours": 36,
  "simultaneous_exclude_half_side": 16,
  "forbidden_zone_diameter_multiplier": 12,
  "solver_num_workers": 6,
  "solver_max_time": 300
}
```

### API响应示例

1. 提交任务响应:
```json
{
  "task_id": "task_1234567890",
  "status": "pending",
  "message": "任务已创建并在后台处理中"
}
```

2. 查询任务状态响应:
```json
{
  "task_id": "task_1234567890",
  "status": "completed",
  "result": {
    "status": "OPTIMAL",
    "makespan_hours": 123.45,
    "schedule": [...],
    "statistics": {...},
    "api_processing_time": 5.67
  },
  "created_at": 1234567890.12,
  "updated_at": 1234567895.67
}
```

## 参数说明

- `piles`: 桩基数据列表，每个桩基包含id、x、y、type和diameter字段
- `num_machines`: 设备数量
- `pile_type_durations`: 不同类型桩基的施工时长（小时）
- `forbidden_duration_hours`: 禁区持续时长（小时）
- `simultaneous_exclude_half_side`: 同时施工排除区域的半边长（米）
- `forbidden_zone_diameter_multiplier`: 完工禁区直径乘数
- `solver_num_workers`: 求解器工作线程数
- `solver_max_time`: 最大求解时间（秒） 