// src/services/api.ts
import axios from 'axios';

// --- Pydantic 模型的前端对应类型 ---

// 与后端 PileData 模型对应
interface PileDataApi {
    id: number | string; // 保持与后端一致，后端用的是 int，但JS中数字和字符串ID都常见
    x: number;
    y: number;
    type: number;
    diameter: number;
}

// 与后端 ScheduleRequest 模型对应
export interface ScheduleRequestData {
    piles: PileDataApi[];
    num_machines: number;
    duration_scenario?: string; // 新增：施工时长场景
    weather_buffer_hours?: number; // 新增：天气影响缓冲时间
    monte_carlo_simulations?: number; // 新增：蒙特卡洛模拟次数
    forbidden_duration_hours: number;
    simultaneous_exclude_half_side: number;
    forbidden_zone_diameter_multiplier: number;
    num_zones: number; // 新增：分区数量
    zone_penalty_hours: number; // 新增：跨区域移动惩罚
    solver_num_workers: number;
    solver_max_time: number;
}

// --- 新增：与后端 TaskResponse 模型对应 ---
export interface TaskResponseApi {
    task_id: string;
    status: string; // "pending", "processing" (如果后端有此状态), etc.
    message: string;
}

// --- 新增：与后端 TaskStatusResponse 模型中的 result 部分（即原始 solve_pile_schedule 的结果）对应 ---
// (这个结构与我们之前定义的 ScheduleResponseData 类似，但去掉了 status，因为外层 TaskStatusResponseApi 有 status)
// 模拟统计数据接口
interface SimulatedStatsApi {
    mean: number;
    median: number;
    std: number;
    p10: number;
    p25: number;
    p75: number;
    p90: number;
    min: number;
    max: number;
    num_simulations: number;
}

export interface OptimizationResultData {
    // status: string; // 这个 status 是优化求解器的状态，不是任务状态
    status: string;
    makespan_hours: number | null;
    estimated_makespan_with_buffer?: number | null; // 新增：含天气缓冲的预估总工期
    completion_probability?: number | null; // 新增：计划实现概率
    simulated_stats?: SimulatedStatsApi | null; // 新增：模拟统计信息
    schedule: TaskInfoApi[]; // TaskInfoApi 需要被定义
    statistics: SolverStatisticsApi; // SolverStatisticsApi 需要被定义
    message?: string; 
    api_processing_time?: number; // 后端添加的处理时间
    solver_status?: string;
    // 注意：这里可能需要根据后端 solve_pile_schedule 实际返回的字典键来调整
    // 特别是如果原始结果中也包含一个 status 键 (例如 "OPTIMAL", "FEASIBLE")
    // 为了避免混淆，可以在 TaskStatusResponseApi 中将这个内部 status 重命名或嵌套
}

// 与后端 TaskStatusResponse 模型对应
export interface TaskStatusResponseApi {
    task_id: string;
    status: string; // "pending", "completed", "failed"
    result: OptimizationResultData | { error?: string } | null; // 结果可能是优化结果，也可能是错误对象
    created_at: number | null;
    updated_at: number | null;
}


// --- 以下是之前已有的，但可能需要检查与 OptimizationResultData 的对齐 ---
// (TaskInfoApi 和 SolverStatisticsApi 是 OptimizationResultData 的一部分)
export interface TaskInfoApi {
    pile_id: number | string;
    x: number;
    y: number;
    type: number;
    diameter: number; // 添加直径信息
    zone_id: number; // 新增：分区ID
    start_hour: number;
    end_hour: number;
    duration_hour: number;
    machine: number;
}

interface SolverStatisticsApi {
    branches: number;
    conflicts: number;
    wall_time: number;
}


// 配置 Axios 实例
const API_BASE_URL = import.meta.env.VITE_API_URL || '/';
console.log('[API Config] VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('[API Config] Using baseURL:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL, // 生产环境使用环境变量，开发环境使用代理
  timeout: 600000, // 10分钟超时（优化计算可能需要较长时间）
  headers: {
    'Content-Type': 'application/json',
  }
});

export interface VideoGenerationResponseApi { // 对应后端的 VideoGenerationResponse
  optimization_task_id: string;
  video_generation_status: string; // e.g., "pending_video"
  message: string;
  video_task_id?: string; // 如果后端为视频生成创建了新的独立任务ID
}

// 新增函数
export const triggerVideoGenerationApi = async (optimizationTaskId: string): Promise<VideoGenerationResponseApi> => {
  try {
      const response = await apiClient.post<VideoGenerationResponseApi>(`/schedule/${optimizationTaskId}/generate_video`);
      return response.data;
  } catch (error) {
      // ... (错误处理同其他API调用) ...
      if (axios.isAxiosError(error)) throw new Error(error.response?.data?.detail || '触发视频生成失败');
      throw new Error('触发视频生成时发生意外错误');
  }
};


/**
 * 调用后端 API 创建一个异步的桩基调度任务
 * @param data 请求体，包含桩基数据和配置参数
 * @returns Promise，解析为包含任务ID和初始状态的响应
 */
export const callScheduleApi = async (data: ScheduleRequestData): Promise<TaskResponseApi> => {
  try {
    // POST到 /schedule (不带末尾斜杠，与后端路由匹配)
    const response = await apiClient.post<TaskResponseApi>('/schedule', data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMsg = error.response?.data?.detail || error.message || '创建调度任务失败';
      console.error('API Error (create task):', error.response?.data || error.message);
      throw new Error(errorMsg);
    } else {
      console.error('Unexpected Error (create task):', error);
      throw new Error('创建调度任务时发生意外错误');
    }
  }
};

/**
 * 调用后端 API 查询指定任务ID的状态和结果
 * @param taskId 要查询的任务ID
 * @returns Promise，解析为包含任务状态和结果（如果完成）的响应
 */
export const getTaskStatusApi = async (taskId: string): Promise<TaskStatusResponseApi> => {
    try {
        // GET到 /schedule/{taskId} (不带末尾斜杠)
        const response = await apiClient.get<TaskStatusResponseApi>(`/schedule/${taskId}`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            const errorMsg = error.response?.data?.detail || error.message || '查询任务状态失败';
            console.error('API Error (get task status):', error.response?.data || error.message);
            throw new Error(errorMsg);
        } else {
            console.error('Unexpected Error (get task status):', error);
            throw new Error('查询任务状态时发生意外错误');
        }
    }
};