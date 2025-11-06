// src/pages/PilePlanningPage.tsx
import React, { useState, useMemo, useCallback, useEffect } from 'react';
import {
  Button,
  Row,
  Col,
  Spin,
  Alert,
  Card,
  Typography,
  Statistic,
  message,
  Table,
  Radio,
  Space,
  Tooltip,
  Progress,
} from 'antd';
import { useSchedule } from '../contexts/ScheduleContext';
import PileDataInput from '../components/PileDataInput';
import ParameterInput from '../components/ParameterInput';
import { 
    DownloadOutlined, 
    PlayCircleOutlined, 
    TableOutlined, // 用于表格按钮
    FileTextOutlined, // 用于JSON导出
    PlaySquareOutlined, // 用于视频按钮
    InfoCircleOutlined, // 用于信息提示
} from '@ant-design/icons'; 
import { CSVLink } from "react-csv";
import { TaskInfoApi } from '../services/api'; // 确保从api.ts导入

const { Title, Text } = Typography;

const PilePlanningPage: React.FC = () => {
  const {
    configParams,
    scheduleResult,
    isLoading,
    error,
    pileData,
    runOptimization,
    updateConfigParam,
    currentOptimizationTaskId, // 用于视频生成
    isVideoGenerating,
    currentVideoGenerationTargetId,
    videoUrl,
    videoError,
    generateVideo,
    clearError,
    clearVideoStatus,
  } = useSchedule();

  const [showScheduleTable, setShowScheduleTable] = useState<boolean>(false);

  useEffect(() => {
    if (videoUrl) {
      console.log("Video URL to play/download:", videoUrl);
    }
  }, [videoUrl]);

  const availablePileTypes = useMemo(() => { // 使用 useMemo
    return new Set(pileData.map(p => p.type));
  }, [pileData]);

  const handleParamChange = useCallback((param: keyof typeof configParams, value: any) => {
     if (typeof configParams[param] === 'number') {
        const numValue = value === null || value === undefined ? NaN : Number(value);
        if (!isNaN(numValue)) {
            updateConfigParam(param, numValue);
        } else {
            console.warn(`Invalid number input for ${param}:`, value);
        }
     } 
     else {
        updateConfigParam(param, value); 
     }
  }, [configParams, updateConfigParam]);

  const getCsvData = useCallback(() => { // 使用 useCallback
    if (!scheduleResult || !scheduleResult.schedule || scheduleResult.schedule.length === 0) {
        return { headers: [], data: [] };
    }
    const headers = [
        { label: "桩基ID", key: "pile_id" }, { label: "X坐标", key: "x" },
        { label: "Y坐标", key: "y" }, { label: "类型", key: "type" },
        { label: "分区ID", key: "zone_id" }, // 添加分区ID到CSV
        { label: "开始时间(h)", key: "start_hour" }, { label: "结束时间(h)", key: "end_hour" },
        { label: "持续时间(h)", key: "duration_hour" }, { label: "分配机器", key: "machine" },
        { label: "直径(m)", key: "diameter" }, // 添加直径到CSV
    ];
    const data = scheduleResult.schedule.map((task: TaskInfoApi) => ({ // 明确 task 类型
        ...task,
        start_hour: task.start_hour?.toFixed(2) || 'N/A',
        end_hour: task.end_hour?.toFixed(2) || 'N/A',
        duration_hour: task.duration_hour?.toFixed(2) || 'N/A',
    }));
    return { headers, data };
  }, [scheduleResult]); // 添加依赖

  const { headers: csvHeaders, data: csvData } = getCsvData();

  const handleExportJson = useCallback(() => { // 使用 useCallback
    if (!scheduleResult || !scheduleResult.schedule || scheduleResult.schedule.length === 0) {
        message.warning('没有可导出的调度结果。');
        return;
    }
    const jsonDataToExport = scheduleResult; 
    const jsonData = JSON.stringify(jsonDataToExport, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '桩基调度优化结果.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    message.success('JSON文件已开始下载。');
  }, [scheduleResult]); // 添加依赖

  const handleViewDetailedSchedule = useCallback(() => { // 使用 useCallback
    if (scheduleResult && scheduleResult.schedule && scheduleResult.schedule.length > 0) {
        setShowScheduleTable(prev => !prev);
        if (!showScheduleTable) { 
            setTimeout(() => { 
                const resultCardElement = document.getElementById("optimization-result-card");
                if (resultCardElement) {
                    resultCardElement.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }, 100);
        }
    } else {
        message.info('没有有效的优化结果可供查看。');
        setShowScheduleTable(false);
    }
  }, [scheduleResult, showScheduleTable]);

  const scheduleTableColumns = useMemo(() => [ // 使用 useMemo
    {
      title: '桩基ID', dataIndex: 'pile_id', key: 'pile_id', width: 100, ellipsis: true,
      sorter: (a: TaskInfoApi, b: TaskInfoApi) => {
          const idA = String(a.pile_id); // 统一转为字符串比较
          const idB = String(b.pile_id);
          return idA.localeCompare(idB);
      },
    },
    { title: '分配机器', dataIndex: 'machine', key: 'machine', width: 100, sorter: (a: TaskInfoApi, b: TaskInfoApi) => a.machine - b.machine, },
    { title: '分区ID', dataIndex: 'zone_id', key: 'zone_id', width: 80, sorter: (a: TaskInfoApi, b: TaskInfoApi) => a.zone_id - b.zone_id, },
    { title: '类型', dataIndex: 'type', key: 'type', width: 80, sorter: (a: TaskInfoApi, b: TaskInfoApi) => a.type - b.type, },
    { title: '开始时间 (h)', dataIndex: 'start_hour', key: 'start_hour', width: 120, render: (value?: number) => value?.toFixed(2) || 'N/A', sorter: (a: TaskInfoApi, b: TaskInfoApi) => (a.start_hour || 0) - (b.start_hour || 0), defaultSortOrder: 'ascend' as const, },
    { title: '结束时间 (h)', dataIndex: 'end_hour', key: 'end_hour', width: 120, render: (value?: number) => value?.toFixed(2) || 'N/A', sorter: (a: TaskInfoApi, b: TaskInfoApi) => (a.end_hour || 0) - (b.end_hour || 0), },
    { title: '持续时长 (h)', dataIndex: 'duration_hour', key: 'duration_hour', width: 120, render: (value?: number) => value?.toFixed(2) || 'N/A', },
    { title: 'X坐标', dataIndex: 'x', key: 'x', width: 100, },
    { title: 'Y坐标', dataIndex: 'y', key: 'y', width: 100, },
    { title: '直径 (m)', dataIndex: 'diameter', key: 'diameter', width: 100, },
  ], []); // 空依赖数组，表示列配置不轻易改变

  const handleClearError = useCallback(() => { // 使用 useCallback
    if (typeof clearError === 'function') {
        clearError();
    } else {
        console.warn("clearError function not available in context.");
    }
  }, [clearError]);

  const handleClearVideoStatus = useCallback(() => { // 使用 useCallback
    if (typeof clearVideoStatus === 'function') {
        clearVideoStatus();
    } else {
        console.warn("clearVideoStatus function not available in context.");
    }
  }, [clearVideoStatus]); // 添加依赖

  // 计算风险等级和颜色
  const getRiskLevel = useCallback((probability: number | null | undefined) => {
    if (probability === null || probability === undefined) return { level: '未知', color: '#666' };
    if (probability >= 0.9) return { level: '低风险', color: '#52c41a' };
    if (probability >= 0.7) return { level: '中低风险', color: '#1890ff' };
    if (probability >= 0.5) return { level: '中等风险', color: '#faad14' };
    if (probability >= 0.3) return { level: '高风险', color: '#ff7a45' };
    return { level: '极高风险', color: '#ff4d4f' };
  }, []);

  return (
    <div>
      <Title level={2}>桩基规划与优化</Title>

      <Card title="桩基数据" style={{ marginBottom: 16 }} bordered={false}>
        <PileDataInput />
        <Text type="secondary" style={{marginTop: 8, display: 'block'}}>
            当前桩基数: {pileData.length}, 桩基类型: {availablePileTypes.size > 0 ? Array.from(availablePileTypes).sort((a,b)=>a-b).join(', ') : '未加载数据'}
        </Text>
      </Card>

      <Card title="配置参数" style={{ marginBottom: 16 }} bordered={false}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="施工班组数 (台)" value={configParams.num_machines} onChange={(value) => handleParamChange('num_machines', value)}/>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="施工禁区时长 (h)" value={configParams.forbidden_duration_hours} onChange={(value) => handleParamChange('forbidden_duration_hours', value)}/>
          </Col>
           <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="禁区直径乘数" value={configParams.forbidden_zone_diameter_multiplier} onChange={(value) => handleParamChange('forbidden_zone_diameter_multiplier', value)}/>
          </Col>
           <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="同时施工排除半径 (m)" value={configParams.simultaneous_exclude_half_side} onChange={(value) => handleParamChange('simultaneous_exclude_half_side', value)}/>
          </Col>
           <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="求解最大时间 (s)" value={configParams.solver_max_time} onChange={(value) => handleParamChange('solver_max_time', value)}/>
          </Col>
           <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="求解核心数" value={configParams.solver_num_workers} onChange={(value) => handleParamChange('solver_num_workers', value)}/>
          </Col>
           <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="希望划分的区域数" value={configParams.num_zones} onChange={(value) => handleParamChange('num_zones', value)}/>
          </Col>
           <Col xs={24} sm={12} md={8} lg={6}>
             <ParameterInput label="跨区域移动惩罚 (h)" value={configParams.zone_penalty_hours} onChange={(value) => handleParamChange('zone_penalty_hours', value)}/>
          </Col>
        </Row>
        
        <div style={{marginTop: 24}}>
            <Title level={5} style={{marginBottom: 16}}>施工时长场景选择</Title>
            <Radio.Group 
                value={configParams.duration_scenario} 
                onChange={(e) => handleParamChange('duration_scenario', e.target.value)}
                buttonStyle="solid"
            >
                <Space direction="horizontal" size="small">
                    <Radio.Button value="expected">均值期望时长 </Radio.Button>
                    <Radio.Button value="pessimistic_90">悲观保证时长 </Radio.Button>
                    <Radio.Button value="most_likely">最快可能时长 </Radio.Button>
                    <Radio.Button value="random_sample">随机采样时长 </Radio.Button>
                </Space>
            </Radio.Group>
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                基于对数正态分布 (μ=3.16, σ=0.63) 的施工时长计算。随机采样模式为每个桩基独立抽样不同时长。
            </div>
        </div>
        
        <div style={{marginTop: 24}}>
            <Title level={5} style={{marginBottom: 16}}>风险评估配置</Title>
            <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={8} lg={6}>
                    <ParameterInput 
                        label="蒙特卡洛模拟次数" 
                        value={configParams.monte_carlo_simulations || 1000} 
                        onChange={(value) => handleParamChange('monte_carlo_simulations', value)}
                    />
                </Col>
            </Row>
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                用于评估计划可靠性的模拟次数，建议1000-5000次。次数越多结果越准确但计算时间越长。
            </div>
        </div>
        
        <div style={{marginTop: 24}}>
            <Title level={5} style={{marginBottom: 16}}>天气影响配置</Title>
            <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={8} lg={6}>
                    <ParameterInput 
                        label="天气影响缓冲时间 (h)" 
                        value={configParams.weather_buffer_hours || 0} 
                        onChange={(value) => handleParamChange('weather_buffer_hours', value)}
                    />
                </Col>
            </Row>
            <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                此缓冲时间用于考虑大雨导致的停工期
            </div>
        </div>
      </Card>

      <Row gutter={16} style={{marginBottom: 24}}>
            <Col>
                <Button type="primary" icon={<PlayCircleOutlined />} loading={isLoading} onClick={runOptimization} disabled={pileData.length === 0 || isLoading} size="large">
                    开始优化
                </Button>
            </Col>
            <Col>
                {scheduleResult && scheduleResult.schedule && scheduleResult.schedule.length > 0 ? (
                    <CSVLink
                        data={csvData}
                        headers={csvHeaders}
                        filename={"桩基调度计划.csv"}
                        style={{ textDecoration: 'none' }}
                        target="_blank"
                    >
                        <Button 
                            icon={<DownloadOutlined />} 
                            disabled={isLoading} // isLoading is still a valid disable reason
                        >
                            导出CSV文件
                        </Button>
                    </CSVLink>
                ) : (
                    <Button 
                        icon={<DownloadOutlined />} 
                        disabled // Always disabled if no valid data
                        onClick={() => message.warning('没有可导出的调度数据。')}
                    >
                        导出CSV文件
                    </Button>
                )}
            </Col>
            <Col>
                <Button icon={<FileTextOutlined />} onClick={handleExportJson} disabled={!scheduleResult || !scheduleResult.schedule || scheduleResult.schedule.length === 0 || isLoading}>
                    导出JSON
                </Button>
            </Col>
            <Col>
                <Button icon={<TableOutlined />} disabled={!scheduleResult || !scheduleResult.schedule || scheduleResult.schedule.length === 0 || isLoading} onClick={handleViewDetailedSchedule}>
                    {showScheduleTable ? "隐藏详细计划" : "查看详细计划"}
                </Button>
            </Col>
            <Col>
                <Button
                    icon={<PlaySquareOutlined />}
                    onClick={() => {
                      console.log("Attempting to generate video for task ID:", currentOptimizationTaskId);
                        if (currentOptimizationTaskId && scheduleResult) {
                            handleClearVideoStatus();
                            generateVideo(currentOptimizationTaskId); 
                        } else {
                            message.warning("请先成功运行一次优化以获取任务ID和结果。");
                        }
                    }}
                    loading={isVideoGenerating && currentVideoGenerationTargetId === currentOptimizationTaskId}
                    disabled={!scheduleResult || !scheduleResult.schedule || isLoading || (isVideoGenerating && currentVideoGenerationTargetId === currentOptimizationTaskId) }
                >
                    生成施工动画
                </Button>
            </Col>
       </Row>

      {isLoading && (
          <div style={{textAlign: 'center', padding: '50px 0'}}>
              <Spin tip={"正在处理中..."} size="large"> {/* 使用通用加载提示 */}
                 <div style={{ height: 100 }} /> 
              </Spin>
          </div>
      )}
      {error && !isLoading && (
          <Alert message="操作出错" description={error} type="error" showIcon closable onClose={handleClearError} style={{marginBottom: 24}} />
      )}
      
      {scheduleResult && (
        <Card title="优化结果" style={{ marginTop: 16 }} id="optimization-result-card" bordered={false}> 
          <Row gutter={16} style={{marginBottom: 24}}>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Statistic title="求解状态" value={scheduleResult.solver_status || scheduleResult.status || 'N/A'} />
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              {scheduleResult.makespan_hours !== null && typeof scheduleResult.makespan_hours === 'number' ? (
                <Statistic title="基础总工期 (小时)" value={scheduleResult.makespan_hours.toFixed(2)} precision={2} />
              ) : (
                <Statistic title="基础总工期 (小时)" value="N/A" />
              )}
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              {scheduleResult.estimated_makespan_with_buffer !== null && typeof scheduleResult.estimated_makespan_with_buffer === 'number' ? (
                <Statistic title="含缓冲预估总工期 (小时)" value={scheduleResult.estimated_makespan_with_buffer.toFixed(2)} precision={2} />
              ) : (
                <Statistic title="含缓冲预估总工期 (小时)" value="N/A" />
              )}
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Statistic title="求解时间 (秒)" value={scheduleResult.statistics?.wall_time?.toFixed(2) || 'N/A'} precision={2} />
            </Col>
          </Row>

          {/* 新增：概率评估结果展示 */}
          {scheduleResult.completion_probability !== null && scheduleResult.completion_probability !== undefined && (
            <Card 
              title={
                <span>
                  <InfoCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  计划可靠性评估
                </span>
              } 
              size="small" 
              style={{ marginBottom: 24, backgroundColor: '#fafafa' }}
            >
              <Row gutter={16}>
                <Col xs={24} sm={12} md={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Statistic 
                      title={
                        <Tooltip title="基于蒙特卡洛模拟，实际工期不超过计划工期的概率">
                          计划实现概率
                        </Tooltip>
                      }
                      value={(scheduleResult.completion_probability * 100).toFixed(1)} 
                      suffix="%" 
                      valueStyle={{ 
                        color: getRiskLevel(scheduleResult.completion_probability).color,
                        fontSize: '24px',
                        fontWeight: 'bold'
                      }}
                    />
                    <div style={{ 
                      marginTop: 8, 
                      padding: '4px 12px', 
                      borderRadius: '4px', 
                      backgroundColor: getRiskLevel(scheduleResult.completion_probability).color,
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}>
                      {getRiskLevel(scheduleResult.completion_probability).level}
                    </div>
                  </div>
                </Col>
                <Col xs={24} sm={12} md={16}>
                  {scheduleResult.simulated_stats && (
                    <div>
                      <div style={{ marginBottom: 12 }}>
                        <Text strong>模拟工期分布统计 (基于 {scheduleResult.simulated_stats.num_simulations} 次模拟):</Text>
                      </div>
                      <Row gutter={[8, 8]}>
                        <Col xs={12} sm={8}>
                          <Text type="secondary">平均值: </Text>
                          <Text strong>{scheduleResult.simulated_stats.mean.toFixed(1)}h</Text>
                        </Col>
                        <Col xs={12} sm={8}>
                          <Text type="secondary">中位数: </Text>
                          <Text strong>{scheduleResult.simulated_stats.median.toFixed(1)}h</Text>
                        </Col>
                        <Col xs={12} sm={8}>
                          <Text type="secondary">标准差: </Text>
                          <Text strong>{scheduleResult.simulated_stats.std.toFixed(1)}h</Text>
                        </Col>
                        <Col xs={12} sm={8}>
                          <Text type="secondary">P10: </Text>
                          <Text strong>{scheduleResult.simulated_stats.p10.toFixed(1)}h</Text>
                        </Col>
                        <Col xs={12} sm={8}>
                          <Text type="secondary">P90: </Text>
                          <Text strong>{scheduleResult.simulated_stats.p90.toFixed(1)}h</Text>
                        </Col>
                        <Col xs={12} sm={8}>
                          <Text type="secondary">最大值: </Text>
                          <Text strong>{scheduleResult.simulated_stats.max.toFixed(1)}h</Text>
                        </Col>
                      </Row>
                      <div style={{ marginTop: 12 }}>
                        <Progress
                          percent={scheduleResult.completion_probability * 100}
                          strokeColor={getRiskLevel(scheduleResult.completion_probability).color}
                          size="small"
                          format={(percent) => `${percent?.toFixed(1)}% 可靠性`}
                        />
                      </div>
                    </div>
                  )}
                </Col>
              </Row>
            </Card>
          )}
          
          {showScheduleTable && scheduleResult.schedule && scheduleResult.schedule.length > 0 && (
            <>
              <Title level={4} style={{marginTop: 24, marginBottom: 16}}>详细调度计划</Title>
              <Table<TaskInfoApi>
                dataSource={scheduleResult.schedule} 
                columns={scheduleTableColumns}
                rowKey={(record) => `pile-${record.pile_id}-machine-${record.machine}-start-${record.start_hour}`}
                size="small" bordered
                pagination={{ pageSize: 10, showSizeChanger: true, pageSizeOptions: ['10', '20', '50', '100'], showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 条`, }}
                scroll={{ y: 400, x: 'max-content' }}
                sticky
              /> 
            </>
          )}
          
          {(!scheduleResult.schedule || scheduleResult.schedule.length === 0) && (
            <Text type="secondary" style={{display: 'block', marginTop: 24}}>没有详细的调度数据可显示。</Text>
          )}
        </Card>
      )}

      {/* 视频展示区域 */}
      {currentOptimizationTaskId && currentVideoGenerationTargetId === currentOptimizationTaskId && (
        <>
            {isVideoGenerating && (
                <div style={{textAlign: 'center', padding: '20px 0', marginTop: 16}}>
                    <Spin tip={currentOptimizationTaskId || "视频生成中..."} />
                </div>
            )}
            {videoUrl && !isVideoGenerating && !videoError && (
                <Card title="施工动画预览" style={{ marginTop: 16 }} bordered={false}>
                    <video width="100%" height="auto" controls key={videoUrl}>
                        <source src={videoUrl} type="video/mp4" />
                        您的浏览器不支持HTML5视频。您可以 <a href={videoUrl} download target="_blank" rel="noopener noreferrer">点击这里下载视频</a>。
                    </video>
                    <div style={{marginTop: 8, textAlign: 'center'}}>
                        <a href={videoUrl} download target="_blank" rel="noopener noreferrer">
                            <Button icon={<DownloadOutlined />}>下载视频文件</Button>
                        </a>
                    </div>
                </Card>
            )}
            {videoError && !isVideoGenerating && (
                <Alert message="视频生成错误" description={videoError} type="error" showIcon closable onClose={handleClearVideoStatus} style={{ marginTop: 16 }}/>
            )}
        </>
      )}
    </div>
  );
};

export default PilePlanningPage;