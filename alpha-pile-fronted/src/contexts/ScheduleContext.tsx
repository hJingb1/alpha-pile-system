// src/contexts/ScheduleContext.tsx
import React, {
  createContext,
  useState,
  useContext,
  ReactNode,
  useCallback,
  useRef,
  useEffect,
} from 'react';
import {
  callScheduleApi,
  getTaskStatusApi,
  triggerVideoGenerationApi,
  ScheduleRequestData,
  TaskResponseApi,
  TaskStatusResponseApi,
  OptimizationResultData, // 确保从 api.ts 导出
  VideoGenerationResponseApi,
} from '../services/api';

// --- 类型定义 ---

interface PileData {
  id: number | string;
  x: number;
  y: number;
  type: number;
  diameter: number;
}

// ScheduleResultDisplayData 现在直接使用 OptimizationResultData
// OptimizationResultData 应该包含求解器的 'status' (e.g., "OPTIMAL")
export type ScheduleResultDisplayData = OptimizationResultData;

interface ScheduleContextState {
  pileData: PileData[];
  configParams: Omit<ScheduleRequestData, 'piles'>;
  scheduleResult: ScheduleResultDisplayData | null;
  isLoading: boolean; // True if either optimization or video generation (for the current target) is active
  error: string | null;
  
  currentOptimizationTaskId: string | null; // ID of the optimization task being tracked
  currentDisplayStatus: string | null; // User-facing status message

  isVideoGenerating: boolean; // Specifically for video generation process
  currentVideoGenerationTargetId: string | null; // ID of the optimization task for which video is being generated
  videoUrl: string | null;
  videoError: string | null;



  loadPileData: (data: PileData[]) => void;
  updateConfigParam: (param: keyof Omit<ScheduleRequestData, 'piles'>, value: any) => void;
  runOptimization: () => Promise<void>;
  generateVideo: (optimizationTaskId: string) => Promise<void>;
  clearError: () => void;
  clearVideoStatus: () => void;
}

const defaultConfigParams: Omit<ScheduleRequestData, 'piles'> = {
  num_machines: 3,
  duration_scenario: 'expected',
  weather_buffer_hours: 0.0,
  monte_carlo_simulations: 1000,
  forbidden_duration_hours: 36,
  simultaneous_exclude_half_side: 10,
  forbidden_zone_diameter_multiplier: 12,
  num_zones: 3,
  zone_penalty_hours: 10,
  solver_num_workers: 6,
  solver_max_time: 360,
};

const ScheduleContext = createContext<ScheduleContextState | undefined>(undefined);

interface ScheduleProviderProps {
  children: ReactNode;
}

export const ScheduleProvider: React.FC<ScheduleProviderProps> = ({ children }) => {
  const [pileData, setPileData] = useState<PileData[]>([]);
  const [configParams, setConfigParams] = useState(defaultConfigParams);
  const [scheduleResult, setScheduleResult] = useState<ScheduleResultDisplayData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [currentOptimizationTaskId, setCurrentOptimizationTaskId] = useState<string | null>(null);
  const [currentDisplayStatus, setCurrentDisplayStatus] = useState<string | null>(null);

  const [isVideoGenerating, setIsVideoGenerating] = useState<boolean>(false);
  const [currentVideoGenerationTargetId, setCurrentVideoGenerationTargetId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoError, setVideoError] = useState<string | null>(null);



  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Refs to hold the latest values of states for use in useCallback without re-creating it
  const currentVideoGenerationTargetIdRef = useRef(currentVideoGenerationTargetId);
  const isVideoGeneratingRef = useRef(isVideoGenerating);

  useEffect(() => {
    currentVideoGenerationTargetIdRef.current = currentVideoGenerationTargetId;
    isVideoGeneratingRef.current = isVideoGenerating;
  }, [currentVideoGenerationTargetId, isVideoGenerating]);


  const loadPileData = useCallback((data: PileData[]) => {
    setPileData(data);
    const types = new Set(data.map(p => p.type));
    console.log("Loaded pile types:", types);
    // 移除了对 pile_type_durations 的自动设置，因为现在使用统一的对数正态分布
  }, []);

  const updateConfigParam = useCallback((param: keyof Omit<ScheduleRequestData, 'piles'>, value: any) => {
    setConfigParams(prev => ({ ...prev, [param]: value }));
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const clearVideoStatus = useCallback(() => {
    setVideoUrl(null);
    setVideoError(null);
    setIsVideoGenerating(false); // Important to reset this
    setCurrentVideoGenerationTargetId(null); // And this
    setCurrentDisplayStatus(prev => {
      if (prev?.includes("视频")) return scheduleResult ? `优化结果: ${scheduleResult.status}` : "请开始新的优化";
      return prev;
    });
  }, [scheduleResult]);


  const pollOptimizationTaskStatus = useCallback(async (taskId: string) => {
    if (!taskId) {
      console.warn("[POLL STATUS] Attempted to poll with no taskId.");
      setIsLoading(false); // Stop loading if no task id
      return;
    }
    if (pollTimeoutRef.current) clearTimeout(pollTimeoutRef.current);

    // Use refs for latest state in async callbacks to avoid stale closures
    const targetVideoId = currentVideoGenerationTargetIdRef.current;
    const videoIsCurrentlyGenerating = isVideoGeneratingRef.current;

    setCurrentDisplayStatus(`查询任务 ${taskId.slice(-6)} 状态...`);

    try {
      const statusResponse = await getTaskStatusApi(taskId);
      console.log(`[POLL STATUS] Task [${taskId}] Response:`, statusResponse);
      console.log(`[POLL STATUS] Current targetVideoId: ${targetVideoId}, videoIsCurrentlyGenerating: ${videoIsCurrentlyGenerating}`);

      const optimizationOutcome = statusResponse.result as (OptimizationResultData & {
        video_generation_status?: string;
        video_url?: string | null;
        video_error?: string | null;
      }) | { error?: string } | null;

      const hasErrorProperty = (obj: any): obj is { error: string } => obj && typeof obj.error === 'string';
      const isOptimizationData = (obj: any): obj is OptimizationResultData => 
          obj && typeof obj.schedule !== 'undefined' && typeof obj.status !== 'undefined';

      if (statusResponse.status === "completed") {
        setIsLoading(false); // Base assumption, may be overridden by video
        
        if (isOptimizationData(optimizationOutcome)) {
          setScheduleResult(optimizationOutcome); // This is ScheduleResultDisplayData
          setCurrentDisplayStatus(`优化任务 ${taskId.slice(-6)} 完成: ${optimizationOutcome.status}`);

          if (optimizationOutcome.status && optimizationOutcome.status !== 'OPTIMAL' && optimizationOutcome.status !== 'FEASIBLE') {
            // Only set error if video is NOT the current process, or video also failed
            if (!videoIsCurrentlyGenerating || (optimizationOutcome.video_generation_status && optimizationOutcome.video_generation_status !== 'pending_video')) {
                 setError(`优化求解器: ${optimizationOutcome.status} - ${optimizationOutcome.message || '无详细信息'}`);
            }
          }
        } else if (hasErrorProperty(optimizationOutcome)) {
          setError(`优化任务处理错误: ${optimizationOutcome.error}`);
          setScheduleResult(null); setCurrentDisplayStatus("优化任务失败。");
        } else {
          setError('优化结果格式未知。');
          setScheduleResult(null); setCurrentDisplayStatus("优化结果异常。");
        }

        // Video specific logic, only if this taskId was targeted for video generation
        if (targetVideoId === taskId) {
          console.log("[POLL STATUS] Video target ID matches. Checking video status in result...");
          if (isOptimizationData(optimizationOutcome) && 
              optimizationOutcome.video_generation_status === "completed" && 
              optimizationOutcome.video_url) {
            console.log("[POLL STATUS] Video COMPLETED. Setting URL.");
            setVideoUrl(optimizationOutcome.video_url);
            setIsVideoGenerating(false); // Video generation部分已完成
            setCurrentDisplayStatus("视频已生成！");
          } else if (isOptimizationData(optimizationOutcome) && 
              optimizationOutcome.video_generation_status === "failed") {
            console.log("[POLL STATUS] Video FAILED.");
            const videoErr = isOptimizationData(optimizationOutcome) ? 
              (optimizationOutcome.video_error || "视频生成失败 (未知原因)") : 
              "视频生成失败 (未知原因)";
            setVideoError(videoErr);
            setError(prevError => prevError ? `${prevError}\n视频生成失败: ${videoErr}` : `视频生成失败: ${videoErr}`);
            setIsVideoGenerating(false);
            setCurrentDisplayStatus("视频生成失败。");
          } else if (isOptimizationData(optimizationOutcome) && 
              (optimizationOutcome.video_generation_status === "pending_video" || 
               optimizationOutcome.video_generation_status === "pending")) {
            console.log("[POLL STATUS] Video PENDING (", optimizationOutcome.video_generation_status, "). Re-polling.");
            setCurrentDisplayStatus(`视频仍在生成中 (${optimizationOutcome.video_generation_status})...`);
            setIsLoading(true); // Keep global loading true
            setIsVideoGenerating(true); // Keep video generating true
            pollTimeoutRef.current = setTimeout(() => pollOptimizationTaskStatus(taskId), 5000);
            // Return here to prevent setIsLoading(false) at the end of "completed" block if video is still pending
            return; 
          } else if (videoIsCurrentlyGenerating && isOptimizationData(optimizationOutcome) && !optimizationOutcome.video_generation_status) {
            console.log("[POLL STATUS] Video was triggered, but no video status in outcome yet. Re-polling.");
            setCurrentDisplayStatus(`等待视频状态更新...`);
            setIsLoading(true);
            setIsVideoGenerating(true);
            pollTimeoutRef.current = setTimeout(() => pollOptimizationTaskStatus(taskId), 5000);
            return;
          } else {
            // Video was targeted, but status is not actionable or already handled
            console.log("[POLL STATUS] Video targeted, but status not actionable (Current status:", 
              isOptimizationData(optimizationOutcome) ? optimizationOutcome.video_generation_status : "未知",")");
            setIsVideoGenerating(false); // Assume done if not explicitly pending
          }
        }
        // If we reach here, optimization is complete. If video was generating and is now done (completed/failed), isLoading should be false.
        // If video was not targeted, isLoading should be false.
        if (!isVideoGeneratingRef.current) { // Check the ref for the latest value
             setIsLoading(false);
        }

      } else if (statusResponse.status === "pending") {
        setIsLoading(true);
        if (videoIsCurrentlyGenerating && targetVideoId === taskId) {
            setCurrentDisplayStatus(`视频生成处理中 (优化任务 ${taskId.slice(-6)})...`);
        } else {
            setCurrentDisplayStatus(`优化任务 ${taskId.slice(-6)} 处理中...`);
        }
        pollTimeoutRef.current = setTimeout(() => pollOptimizationTaskStatus(taskId), 5000);
      } else { // Optimization task failed or unknown status
        const errorMsg = (optimizationOutcome && hasErrorProperty(optimizationOutcome) ? optimizationOutcome.error : statusResponse.status) || '未知后端错误';
        setError(`优化任务失败: ${errorMsg}`);
        setIsLoading(false); setCurrentOptimizationTaskId(null); setCurrentDisplayStatus("优化任务失败。");
        setScheduleResult(null); setIsVideoGenerating(false); setCurrentVideoGenerationTargetId(null);
      }
    } catch (err: any) {
      setError(`查询状态时出错: ${err.message}`);
      setIsLoading(false); setCurrentOptimizationTaskId(null); setCurrentDisplayStatus("查询状态失败。");
      setScheduleResult(null); setIsVideoGenerating(false); setCurrentVideoGenerationTargetId(null);
    }
  }, []); // useCallback with empty deps, relies on refs for latest state inside, or pass states as args.
            // For simplicity with setTimeout, using refs is one way. A more robust way might involve
            // making pollOptimizationTaskStatus not a useCallback, or carefully managing its dependencies.
            // Let's try with empty deps and refs first.
  const optimizationPollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const runOptimization = useCallback(async () => {
    if (optimizationPollTimeoutRef.current) clearTimeout(optimizationPollTimeoutRef.current);
    clearError();
    clearVideoStatus(); // Clear any previous video related states

    setIsLoading(true);
    setScheduleResult(null);
    setCurrentOptimizationTaskId(null);
    setCurrentDisplayStatus("创建优化任务...");

    const pileDataForApi = pileData.map(p => ({ // Ensure IDs are consistent if needed, e.g. all numbers or all strings
      ...p,
      id: String(p.id) // Or Number(p.id) depending on backend Pydantic model expectation for pile id
    }));

    const requestData: ScheduleRequestData = {
      piles: pileDataForApi, // 使用转换后的 pileData
      num_machines: configParams.num_machines,
      duration_scenario: configParams.duration_scenario,
      weather_buffer_hours: configParams.weather_buffer_hours,
      monte_carlo_simulations: configParams.monte_carlo_simulations,
      forbidden_duration_hours: configParams.forbidden_duration_hours,
      simultaneous_exclude_half_side: configParams.simultaneous_exclude_half_side,
      forbidden_zone_diameter_multiplier: configParams.forbidden_zone_diameter_multiplier,
      num_zones: configParams.num_zones,
      zone_penalty_hours: configParams.zone_penalty_hours,
      solver_num_workers: configParams.solver_num_workers,
      solver_max_time: configParams.solver_max_time,
    };
    
    // --- 添加的日志 --- 
    console.log("Frontend ScheduleContext: requestData to be sent to API:", JSON.stringify(requestData, null, 2));
    // --- 日志结束 ---
      
    try {
      const taskCreationResponse: TaskResponseApi = await callScheduleApi(requestData);
      if (taskCreationResponse.task_id && taskCreationResponse.status === "pending") {
        setCurrentOptimizationTaskId(taskCreationResponse.task_id);
        setCurrentDisplayStatus(`优化任务 ${taskCreationResponse.task_id.slice(-6)} 已创建...`);
        pollOptimizationTaskStatus(taskCreationResponse.task_id); // Initial poll
      } else { /* ... error handling ... */ }
    } catch (err: any) { /* ... error handling ... */ }
  }, [pileData, configParams, pollOptimizationTaskStatus, clearError, clearVideoStatus]);

  const generateVideo = useCallback(async (optimizationTaskId: string) => {
    if (!optimizationTaskId) { /* ... error handling ... */ return; }
    console.log("[GENERATE VIDEO] For task ID:", optimizationTaskId);
    
    // Clear previous video specific states before starting new one for this target
    setVideoUrl(null);
    setVideoError(null);

    setIsVideoGenerating(true);
    setCurrentVideoGenerationTargetId(optimizationTaskId);
    setIsLoading(true); // Global loading indicator
    setCurrentDisplayStatus(`请求为任务 ${optimizationTaskId.slice(-6)} 生成视频...`);

    try {
      const response = await triggerVideoGenerationApi(optimizationTaskId);
      console.log("[GENERATE VIDEO] Trigger API response:", response.message);
      // Backend will update the optimization task with video_generation_status: "pending_video"
      // So, we just need to ensure polling continues or restarts for this optimizationTaskId
      setCurrentDisplayStatus(response.message + ` 开始轮询更新...`);
      pollOptimizationTaskStatus(optimizationTaskId); // Re-initiate polling to catch video status updates
    } catch (err: any) { /* ... error handling, ensure flags are reset ... */ 
        const errorMsg = err.message || "触发视频生成API失败";
        setVideoError(errorMsg);
        setError(prev => prev ? `${prev}\n视频生成请求失败: ${errorMsg}` : `视频生成请求失败: ${errorMsg}`);
        setIsVideoGenerating(false);
        setCurrentVideoGenerationTargetId(null); 
        setIsLoading(false);
    }
  }, [pollOptimizationTaskStatus]);

  useEffect(() => {
    return () => { // Cleanup on unmount
      if (optimizationPollTimeoutRef.current) {
        clearTimeout(optimizationPollTimeoutRef.current);
      }
    };
  }, []);

  const value = {
    pileData, configParams, scheduleResult, isLoading, error,
    currentOptimizationTaskId, currentDisplayStatus,
    isVideoGenerating, currentVideoGenerationTargetId, videoUrl, videoError,
    loadPileData, updateConfigParam, runOptimization, generateVideo,
    clearError, clearVideoStatus,
  };

  return <ScheduleContext.Provider value={value}>{children}</ScheduleContext.Provider>;
};

export const useSchedule = (): ScheduleContextState => {
  const context = useContext(ScheduleContext);
  if (context === undefined) {
    throw new Error('useSchedule must be used within a ScheduleProvider');
  }
  return context;
};