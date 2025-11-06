// src/pages/FileManagerPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Typography, Spin, Alert, Modal, message, Space, Tooltip } from 'antd';
import { DownloadOutlined, DeleteOutlined, EyeOutlined, ExclamationCircleFilled } from '@ant-design/icons';
// import axios from 'axios'; // 如果直接调用下载链接，可能不需要axios，或者封装在api服务里

const { Title, Text } = Typography;
const { confirm } = Modal;

// 假设后端返回的文件元数据结构
interface SavedFileMeta {
  id: string; // 或其他唯一标识符，例如文件名本身
  filename: string;
  created_at: string; // ISO 日期字符串
  size_kb?: number; // 可选，文件大小
  // 可以添加其他元数据，如备注、优化时的参数摘要等
}

// 模拟的API服务 (你需要用真实的API调用替换它们)
// ---------------- MOCK API CALLS (to be replaced) -----------------
const mockFetchSavedFiles = async (): Promise<SavedFileMeta[]> => {
  console.log("Mock API: Fetching saved files...");
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([
        { id: 'schedule_1678886400.json', filename: '初步优化方案_20240315.json', created_at: new Date(Date.now() - 86400000 * 2).toISOString(), size_kb: 15 },
        { id: 'schedule_1678972800.json', filename: '最终版_打桩顺序调整.json', created_at: new Date(Date.now() - 86400000).toISOString(), size_kb: 22 },
        { id: 'schedule_1679059200.json', filename: '测试方案A.json', created_at: new Date().toISOString(), size_kb: 18 },
      ]);
    }, 1000);
  });
};

// 模拟下载，实际应是后端提供下载链接或文件流
const mockDownloadFile = (fileId: string, filenameToSave: string) => {
  console.log(`Mock API: Downloading file ${fileId} as ${filenameToSave}`);
  message.success(`开始下载文件: ${filenameToSave}`);
  // 实际场景：
  // window.location.href = `/api/saved_schedules/${fileId}`; // 直接GET请求下载
  // 或者使用 fetch/axios 获取 blob 并创建下载链接
  const mockContent = JSON.stringify({ message: `这是文件 ${filenameToSave} 的模拟内容` }, null, 2);
  const blob = new Blob([mockContent], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filenameToSave;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const mockDeleteFile = async (fileId: string): Promise<{ success: boolean; message?: string }> => {
  console.log(`Mock API: Deleting file ${fileId}`);
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({ success: true, message: `文件 ${fileId} 已删除 (模拟)` });
    }, 500);
  });
};
// ---------------- END MOCK API CALLS -----------------


const FileManagerPage: React.FC = () => {
  const [files, setFiles] = useState<SavedFileMeta[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedFiles = await mockFetchSavedFiles(); // 替换为真实API调用
      setFiles(fetchedFiles.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())); // 按创建时间降序
    } catch (err: any) {
      setError(err.message || '加载已保存文件列表失败');
      message.error(err.message || '加载已保存文件列表失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles(); // 组件加载时获取文件列表
  }, [fetchFiles]);

  const handleDownload = (record: SavedFileMeta) => {
    // 实际下载应该调用API或直接跳转到下载链接
    mockDownloadFile(record.id, record.filename);
    // 例如: window.location.href = `/api/download_schedule/${record.id}`;
  };

  const handleDelete = (record: SavedFileMeta) => {
    confirm({
      title: `确定要删除文件 "${record.filename}" 吗?`,
      icon: <ExclamationCircleFilled />,
      content: '此操作不可撤销。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          setIsLoading(true); // 可以为删除操作也设置加载状态
          const response = await mockDeleteFile(record.id); // 替换为真实API调用
          if (response.success) {
            message.success(response.message || `文件 "${record.filename}" 已删除`);
            fetchFiles(); // 删除成功后刷新列表
          } else {
            message.error(response.message || `删除文件 "${record.filename}" 失败`);
          }
        } catch (err: any) {
          message.error(err.message || '删除文件时发生错误');
        } finally {
            setIsLoading(false);
        }
      },
    });
  };

  const handlePreview = (record: SavedFileMeta) => {
    // TODO: 实现预览逻辑
    // 可能是加载JSON内容到状态，然后在 PilePlanningPage 中显示
    // 或者在一个 Modal 中显示JSON内容的摘要
    message.info(`预览文件: ${record.filename} (功能待实现)`);
    console.log("Previewing file data (mock):", record);
    // 如果你想将这个文件的内容加载到 PilePlanningPage 的结果区：
    // 1. 需要API下载文件内容 (不仅仅是元数据)
    // 2. 在 ScheduleContext 中添加一个函数，例如 `loadScheduleResultFromFile(resultObject)`
    // 3. 在这里调用该函数，并可能导航到 PilePlanningPage
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      sorter: (a: SavedFileMeta, b: SavedFileMeta) => a.filename.localeCompare(b.filename),
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '保存日期',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 200,
      sorter: (a: SavedFileMeta, b: SavedFileMeta) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (text: string) => new Date(text).toLocaleString(), // 格式化日期显示
    },
    {
        title: '大小 (KB)',
        dataIndex: 'size_kb',
        key: 'size_kb',
        width: 120,
        sorter: (a: SavedFileMeta, b: SavedFileMeta) => (a.size_kb || 0) - (b.size_kb || 0),
        render: (size?: number) => size ? `${size.toFixed(1)} KB` : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_: any, record: SavedFileMeta) => (
        <Space size="middle">
          <Tooltip title="下载此方案">
            <Button icon={<DownloadOutlined />} onClick={() => handleDownload(record)}>
              下载
            </Button>
          </Tooltip>
          <Tooltip title="预览/加载此方案 (待实现)">
            <Button icon={<EyeOutlined />} onClick={() => handlePreview(record)} disabled> 
              预览
            </Button>
          </Tooltip>
          <Tooltip title="删除此方案">
            <Button danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>
              删除
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (isLoading && files.length === 0) { // 初始加载时显示 Spin
    return (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin tip="正在加载已保存文件列表..." size="large" />
        </div>
    );
  }

  if (error && files.length === 0) { // 初始加载错误时显示 Alert
    return <Alert message="加载错误" description={error} type="error" showIcon />;
  }

  return (
    <div>
      <Title level={2} style={{ marginBottom: 24 }}>文件管理</Title>
      <Button onClick={fetchFiles} loading={isLoading} style={{ marginBottom: 16 }}>
        刷新列表
      </Button>
      <Table<SavedFileMeta>
        columns={columns}
        dataSource={files}
        rowKey="id"
        loading={isLoading && files.length > 0} // 刷新时表格也显示加载状态
        pagination={{ pageSize: 10, showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 条` }}
        bordered
      />
    </div>
  );
};

export default FileManagerPage;