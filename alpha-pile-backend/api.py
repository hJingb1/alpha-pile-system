from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Union, Any
import uvicorn
import time
from main import solve_pile_schedule
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Import for serving static files
import subprocess
import uuid
import json
import os
import sys # Import sys
import pprint # <--- 确保导入 pprint

# --- Global Configuration ---
GENERATED_VIDEOS_DIR_NAME = "generated_videos"
# Construct absolute path for the videos directory relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_VIDEOS_PATH = os.path.join(BASE_DIR, GENERATED_VIDEOS_DIR_NAME)

# Ensure the directory exists
os.makedirs(GENERATED_VIDEOS_PATH, exist_ok=True)
# --- End Global Configuration ---

app = FastAPI(
    title="桩基施工调度优化API",
    description="基于CP-SAT求解器的桩基施工调度优化服务",
    version="1.0.0"
)

# Mount the static directory to serve generated videos
# The client will access videos via /generated_videos/filename.mp4
app.mount(f"/{GENERATED_VIDEOS_DIR_NAME}", StaticFiles(directory=GENERATED_VIDEOS_PATH), name=GENERATED_VIDEOS_DIR_NAME)

origins = [
    "http://localhost:5173",  # 前端开发服务器地址
    "http://127.0.0.1:5173",
    "http://localhost",
    "https://perpetual-serenity-production.up.railway.app",  # Railway 前端域名
    "*",  # 临时允许所有来源（生产环境建议只允许特定域名）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 允许这些源的请求
    allow_credentials=True, # 是否支持携带 cookie
    allow_methods=["*"],    # 允许所有 HTTP 方法
    allow_headers=["*"],    # 允许所有 HTTP 请求头
)


# 定义请求模型
class PileData(BaseModel):
    id: int
    x: float
    y: float
    type: int
    diameter: float

class ScheduleRequest(BaseModel):
    piles: List[PileData]
    num_machines: int = Field(gt=0, description="设备数量，必须大于0")
    duration_scenario: Optional[str] = Field(default='expected', description="施工时长场景：expected(期望), pessimistic_90(悲观), most_likely(最可能), random_sample(随机采样)")
    weather_buffer_hours: Optional[float] = Field(default=0.0, ge=0, description="天气影响缓冲时间（小时）")
    monte_carlo_simulations: Optional[int] = Field(default=1000, ge=100, le=10000, description="蒙特卡洛模拟次数")
    forbidden_duration_hours: float = Field(gt=0, description="禁区持续时长（小时）")
    simultaneous_exclude_half_side: float = Field(gt=0, description="同时施工排除区域的半边长（米）")
    forbidden_zone_diameter_multiplier: float = Field(gt=0, description="完工禁区直径乘数")
    num_zones: int = Field(gt=0, description="希望划分的区域数量")
    zone_penalty_hours: float = Field(ge=0, description="跨区域移动惩罚时长（小时）")
    solver_num_workers: int = Field(ge=1, le=64, description="求解器工作线程数")
    solver_max_time: int = Field(ge=1, description="最大求解时间（秒）")

    # V2 风格验证器 - 检查duration_scenario的有效性
    @model_validator(mode='after')
    def validate_duration_scenario(self):
        valid_scenarios = ['expected', 'pessimistic_90', 'most_likely', 'random_sample']
        if self.duration_scenario not in valid_scenarios:
            raise ValueError(f"duration_scenario 必须是以下值之一: {valid_scenarios}")
        return self

# 创建用于存储任务状态的简单内存存储
class TaskStore:
    def __init__(self):
        self.tasks = {}  # 存储任务状态和结果
    
    def add_task(self, task_id, status="pending", result=None):
        self.tasks[task_id] = {"status": status, "result": result, "created_at": time.time()}
    
    def update_task(self, task_id, status, result=None):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            if result is not None:
                self.tasks[task_id]["result"] = result
            self.tasks[task_id]["updated_at"] = time.time()
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)

# 初始化任务存储
task_store = TaskStore()

# 后台任务处理函数
def process_schedule(task_id: str, config_data: dict):
    # --- 添加的日志 ---
    print(f"DEBUG WORKER: Config_data received by process_schedule for task {task_id}:")
    pprint.pprint(config_data)
    # --- 日志结束 ---
    try:
        # 调用求解器
        start_time = time.time()
        result = solve_pile_schedule(config_data)
        elapsed_time = time.time() - start_time
        
        # 添加运行时间
        result["api_processing_time"] = elapsed_time
        
        # 更新任务状态
        task_store.update_task(task_id, "completed", result)
    except Exception as e:
        # 记录错误信息
        task_store.update_task(task_id, "failed", {"error": str(e)})

# 后台任务函数，用于运行动画生成脚本
def run_animation_generation(optimization_task_id: str, schedule_data_path: str, output_video_filename: str, video_output_dir: str):
    # BASE_DIR is .../alpha-pile-backend (directory of api.py)
    # val.py is assumed to be in the same directory as api.py (BASE_DIR)
    animation_script_abs_path = os.path.join(BASE_DIR, "val.py") # Corrected script name and path
    
    # video_output_dir is already GENERATED_VIDEOS_PATH (absolute path to .../alpha-pile-backend/generated_videos)
    output_video_abs_path = os.path.join(video_output_dir, output_video_filename)
    
    python_executable = sys.executable

    print(f"=== 视频生成调试信息 ===")
    print(f"Python 可执行文件: {python_executable}")
    print(f"动画脚本路径: {animation_script_abs_path}")
    print(f"输入JSON路径: {schedule_data_path}")
    print(f"输出视频路径: {output_video_abs_path}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查文件是否存在
    if not os.path.exists(animation_script_abs_path):
        error_message = f"动画脚本不存在: {animation_script_abs_path}"
        print(error_message)
        updated_result_for_store = {
            **(task_store.get_task(optimization_task_id).get("result") or {}),
            "video_generation_status": "failed",
            "video_error": error_message
        }
        task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store)
        return
    
    if not os.path.exists(schedule_data_path):
        error_message = f"调度数据文件不存在: {schedule_data_path}"
        print(error_message)
        updated_result_for_store = {
            **(task_store.get_task(optimization_task_id).get("result") or {}),
            "video_generation_status": "failed",
            "video_error": error_message
        }
        task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store)
        return

    try:
        # The command now correctly calls val.py
        # schedule_data_path is the input JSON path, output_video_abs_path is the output MP4 path
        command = [python_executable, animation_script_abs_path, schedule_data_path, output_video_abs_path]
        print(f"执行命令: {' '.join(command)}")
        
        # 尝试不同的subprocess调用方式
        try:
            # 首先尝试带超时的调用
            process = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, 
                timeout=300,  # 5分钟超时
                cwd=BASE_DIR,  # 设置工作目录
                env=os.environ.copy()  # 继承环境变量
            )
        except subprocess.TimeoutExpired:
            error_message = "视频生成超时（5分钟）"
            print(error_message)
            updated_result_for_store = {
                **(task_store.get_task(optimization_task_id).get("result") or {}),
                "video_generation_status": "failed",
                "video_error": error_message
            }
            task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store)
            return

        # 详细记录subprocess结果
        print(f"进程返回码: {process.returncode}")
        print(f"STDOUT内容: '{process.stdout}'")
        print(f"STDERR内容: '{process.stderr}'")
        print(f"STDOUT长度: {len(process.stdout) if process.stdout else 0}")
        print(f"STDERR长度: {len(process.stderr) if process.stderr else 0}")

        if process.returncode == 0:
            # Video generation successful
            if os.path.exists(output_video_abs_path):
                updated_result_for_store = {
                    **(task_store.get_task(optimization_task_id).get("result") or {}),
                    "video_generation_status": "completed",
                    "video_url": f"/{GENERATED_VIDEOS_DIR_NAME}/{output_video_filename}" # URL is relative for web serving
                }
                print(f"✓ 视频生成成功: {output_video_abs_path}")
                task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store)
            else:
                error_message = f"进程成功但输出文件未创建: {output_video_abs_path}"
                print(error_message)
                updated_result_for_store = {
                    **(task_store.get_task(optimization_task_id).get("result") or {}),
                    "video_generation_status": "failed",
                    "video_error": error_message
                }
                task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store)
        else:
            # Video generation failed
            error_details = []
            if process.stdout and process.stdout.strip():
                error_details.append(f"STDOUT: {process.stdout.strip()}")
            if process.stderr and process.stderr.strip():
                error_details.append(f"STDERR: {process.stderr.strip()}")
            
            if not error_details:
                error_details.append("无详细错误信息")
            
            error_message = f"动画脚本失败 (代码 {process.returncode}). {'; '.join(error_details)}"
            print(error_message)
            
            updated_result_for_store = {
                **(task_store.get_task(optimization_task_id).get("result") or {}),
                "video_generation_status": "failed",
                "video_error": error_message
            }
            task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store)

    except FileNotFoundError as e:
        # This block catches if python_executable or animation_script_abs_path is not found by subprocess.run
        error_message = f"subprocess FileNotFoundError: {str(e)}. Python: '{python_executable}', Script: '{animation_script_abs_path}'"
        print(error_message)
        updated_result_for_store_fnf = {
            **(task_store.get_task(optimization_task_id).get("result") or {}),
            "video_generation_status": "failed",
            "video_error": error_message
        }
        task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store_fnf)
    except Exception as e:
        # Catch any other unexpected errors during subprocess execution
        error_message = f"视频生成异常: {str(e)} (类型: {type(e).__name__})"
        print(error_message)
        import traceback
        traceback.print_exc()
        updated_result_for_store_exc = {
            **(task_store.get_task(optimization_task_id).get("result") or {}),
            "video_generation_status": "failed",
            "video_error": error_message
        }
        task_store.update_task(optimization_task_id, status="completed", result=updated_result_for_store_exc)


class VideoGenerationResponse(BaseModel):
    optimization_task_id: str
    video_generation_status: str
    message: str
    video_task_id: Optional[str] = None # 可以用一个新的ID跟踪视频任务，或直接更新优化任务

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None

class VideoGenerationResponse(BaseModel):
    optimization_task_id: str
    video_generation_status: str
    message: str
    video_task_id: Optional[str] = None # 可以用一个新的ID跟踪视频任务，或直接更新优化任务

@app.post("/schedule", tags=["调度"], response_model=TaskResponse)
async def create_schedule(request: ScheduleRequest, background_tasks: BackgroundTasks):
    """
    创建桩基施工调度计划任务
    
    根据输入的配置数据，在后台异步计算最优的桩基施工调度方案。
    返回一个任务ID，可以用于查询任务状态和结果。
    
    返回：
        - task_id: 任务ID
        - status: 任务状态
        - message: 提示消息
    """
    try:
        # 生成任务ID
        task_id = f"task_{int(time.time())}"

        # --- 添加的日志 ---
        print("DEBUG API: Raw request.model_dump() from frontend:")
        pprint.pprint(request.model_dump())
        # --- 日志结束 ---
        
        # 将Pydantic模型转换为dict
        config_data = request.model_dump()
        
        # 将piles列表中的每个PileData对象转换为dict
        config_data['piles'] = [pile.model_dump() for pile in request.piles]

        # --- 添加的日志 ---
        print("DEBUG API: Processed config_data to be passed to solver and background task:")
        pprint.pprint(config_data)
        # --- 日志结束 ---
        
        # 创建任务记录
        task_store.add_task(task_id)
        
        # 添加到后台任务
        background_tasks.add_task(process_schedule, task_id, config_data)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "任务已创建并在后台处理中"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@app.get("/schedule/{task_id}", tags=["调度"], response_model=TaskStatusResponse)
async def get_schedule_status(task_id: str):
    """
    获取桩基施工调度计划任务状态
    
    根据任务ID查询任务的状态和结果。
    
    返回：
        - task_id: 任务ID
        - status: 任务状态 (pending, completed, failed)
        - result: 完成时返回调度计划结果
    """
    task = task_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"找不到任务 {task_id}")
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "result": task.get("result"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at", task.get("created_at"))
    }

@app.get("/", tags=["信息"])
async def root():
    """
    获取API信息
    """
    return {
        "message": "桩基施工调度优化API",
        "version": "1.0.0",
        "docs": "/docs 或 /redoc"
    }

@app.post("/schedule/{optimization_task_id}/generate_video", tags=["可视化"], response_model=VideoGenerationResponse)
async def trigger_video_generation(optimization_task_id: str, background_tasks: BackgroundTasks):
    optimization_task = task_store.get_task(optimization_task_id)
    if not optimization_task:
        raise HTTPException(status_code=404, detail=f"找不到优化任务 {optimization_task_id}")
    if optimization_task["status"] != "completed" or not optimization_task.get("result"):
        raise HTTPException(status_code=400, detail="优化任务尚未完成或没有结果，无法生成视频。")

    if "schedule" not in optimization_task["result"]:
        raise HTTPException(status_code=400, detail="优化结果中缺少调度数据(schedule)")

    # Define the path for the schedule JSON file within the generated videos directory
    schedule_json_filename = f"schedule_for_{optimization_task_id}.json"
    schedule_json_path = os.path.join(GENERATED_VIDEOS_PATH, schedule_json_filename)

    try:
        with open(schedule_json_path, 'w', encoding='utf-8') as f:
            json.dump(optimization_task["result"]["schedule"], f, ensure_ascii=False, indent=4)
    except Exception as e:
        # Log the error for server-side debugging
        print(f"Error saving schedule JSON to {schedule_json_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存调度数据到临时文件失败: {str(e)}")

    video_filename = f"animation_{optimization_task_id}_{int(time.time())}.mp4"
    
    try:
        task_store.update_task(optimization_task_id, status="completed",
                               result={
                                   **(optimization_task.get("result") or {}),
                                   "video_generation_status": "pending_video",
                                   "video_url": None
                               })
    except Exception as e:
        # Log the error for server-side debugging
        print(f"Error updating task store before starting video generation for {optimization_task_id}: {str(e)}")
        # Attempt to clean up the schedule.json if updating task store fails before background task starts
        if os.path.exists(schedule_json_path):
            try:
                os.remove(schedule_json_path)
            except Exception as remove_e:
                print(f"Error cleaning up schedule_json_path {schedule_json_path}: {remove_e}")
        raise HTTPException(status_code=500, detail=f"更新任务状态以准备视频生成时失败: {str(e)}")

    background_tasks.add_task(run_animation_generation, optimization_task_id, schedule_json_path, video_filename, GENERATED_VIDEOS_PATH)

    return {
        "optimization_task_id": optimization_task_id,
        "video_generation_status": "pending_video",
        "message": "视频生成任务已在后台启动。"
    }


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 