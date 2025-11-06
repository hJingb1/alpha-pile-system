// src/components/PileTypeDurationEditor.tsx
import React, { useState, useEffect } from 'react';
import { InputNumber, Button, Table, Popconfirm, Form, message, Tag, Typography } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';

const { Text } = Typography;

// 定义传入的 pile_type_durations 对象的类型
export interface PileTypeDurations {
  [key: string]: number; // 键是字符串类型的桩基类型，值是数字类型的时长
}

interface PileTypeDurationEditorProps {
  value?: PileTypeDurations; // 传入的 pile_type_durations 对象
  onChange?: (newValue: PileTypeDurations) => void; // 当对象改变时调用的回调
  availablePileTypes?: Set<number>; // (可选) 从桩基数据中提取的可用桩基类型
}

interface EditableRowData {
  key: string; // 使用字符串类型的桩基类型作为key
  type: string;
  duration: number;
  isNew?: boolean; // 标记是否为新添加的行（用于编辑状态）
}

const PileTypeDurationEditor: React.FC<PileTypeDurationEditorProps> = ({
  value = {}, // 默认空对象
  onChange,
  availablePileTypes = new Set(),
}) => {
  const [dataSource, setDataSource] = useState<EditableRowData[]>([]);
  const [editingKey, setEditingKey] = useState<string>(''); // 当前正在编辑的行的key
  const [form] = Form.useForm(); // Ant Design Form实例，用于编辑行

  // 当传入的 value 或 availablePileTypes 变化时，更新表格数据源
  useEffect(() => {
    const currentTypesInValue = new Set(Object.keys(value));
    const allTypesToShow = new Set([...currentTypesInValue, ...Array.from(availablePileTypes).map(String)]);

    const newData = Array.from(allTypesToShow).map((typeKey) => ({
      key: typeKey,
      type: typeKey,
      duration: value[typeKey] || 31, // 如果未在value中定义，给一个默认时长
    }));
    setDataSource(newData.sort((a, b) => parseInt(a.type) - parseInt(b.type))); // 按类型排序
  }, [value, availablePileTypes]);

  const isEditing = (record: EditableRowData) => record.key === editingKey;

  // 开始编辑行
  const edit = (record: Partial<EditableRowData> & { key: React.Key }) => {
    form.setFieldsValue({ type: '', duration: 0, ...record });
    setEditingKey(record.key as string);
  };

  // 取消编辑
  const cancel = () => {
    if (dataSource.find(item => item.key === editingKey)?.isNew) {
      // 如果是取消新建的行，则直接删除
      setDataSource(prev => prev.filter(item => item.key !== editingKey));
    }
    setEditingKey('');
  };

  // 保存编辑的行
  const save = async (key: React.Key) => {
    try {
      const row = (await form.validateFields()) as EditableRowData;
      const newData = [...dataSource];
      const index = newData.findIndex((item) => key === item.key);

      if (index > -1) { // 编辑现有行
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row, isNew: false });
        setDataSource(newData);
        setEditingKey('');
      } else { // 添加新行 (理论上应该通过 handleAdd)
        // newData.push({ ...row, key: row.type, isNew: false });
        // setDataSource(newData);
        // setEditingKey('');
      }
      triggerChange(newData);
    } catch (errInfo) {
      console.log('Validate Failed:', errInfo);
      message.error('输入无效，请检查！');
    }
  };

  // 处理表格行的删除
  const handleDelete = (key: React.Key) => {
    const newData = dataSource.filter((item) => item.key !== key);
    setDataSource(newData);
    triggerChange(newData);
  };

  // 添加新的类型-时长条目
  const handleAdd = () => {
    const newKey = `new_${Date.now()}`; // 临时唯一key
    const newEntry: EditableRowData = {
      key: newKey,
      type: '', // 让用户输入
      duration: 31, // 默认时长
      isNew: true,
    };
    setDataSource([...dataSource, newEntry]);
    edit(newEntry); // 直接进入编辑模式
  };

  // 将表格数据源转换为 onChange 回调期望的 PileTypeDurations 对象格式
  const triggerChange = (data: EditableRowData[]) => {
    if (onChange) {
      const newDurations: PileTypeDurations = {};
      data.forEach(item => {
        if (item.type && !isNaN(Number(item.type)) && !isNaN(Number(item.duration))) { // 确保类型和时长有效
          newDurations[item.type.toString()] = Number(item.duration);
        }
      });
      onChange(newDurations);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '桩基类型',
      dataIndex: 'type',
      width: '35%',
      editable: true,
      render: (_: any, record: EditableRowData) => {
        const editing = isEditing(record);
        return editing && record.isNew ? ( // 只有新添加的行才能编辑类型
          <Form.Item
            name="type"
            style={{ margin: 0 }}
            rules={[
              { required: true, message: '请输入类型!' },
              {
                validator: (_, val) => {
                  if (!val) return Promise.resolve();
                  if (!/^\d+$/.test(val)) return Promise.reject(new Error('类型必须是数字!'));
                  if (dataSource.some(item => item.type === val && item.key !== record.key && !item.isNew)) {
                    return Promise.reject(new Error('该类型已存在!'));
                  }
                  return Promise.resolve();
                },
              },
            ]}
          >
            <InputNumber placeholder="类型编号 (数字)" style={{ width: '100%' }} />
          </Form.Item>
        ) : (
          // 如果是来自 availablePileTypes 的类型，给个提示
          availablePileTypes.has(Number(record.type)) ?
            <Tag color="blue">{record.type}</Tag> :
            record.type
        );
      },
    },
    {
      title: '施工时长 (小时)',
      dataIndex: 'duration',
      width: '35%',
      editable: true,
      render: (_: any, record: EditableRowData) => {
        const editing = isEditing(record);
        return editing ? (
          <Form.Item
            name="duration"
            style={{ margin: 0 }}
            rules={[{ required: true, message: '请输入时长!' }]}
          >
            <InputNumber min={1} placeholder="时长 (小时)" style={{ width: '100%' }} />
          </Form.Item>
        ) : (
          record.duration
        );
      },
    },
    {
      title: '操作',
      dataIndex: 'operation',
      render: (_: any, record: EditableRowData) => {
        const editing = isEditing(record);
        return editing ? (
          <span>
            <Button onClick={() => save(record.key)} type="link" style={{ marginRight: 8 }}>
              保存
            </Button>
            <Popconfirm title="确定取消吗?" onConfirm={cancel}>
              <Button type="link" danger>取消</Button>
            </Popconfirm>
          </span>
        ) : (
          <>
            <Button type="link" disabled={editingKey !== ''} onClick={() => edit(record)} icon={<EditOutlined />} style={{ marginRight: 8 }}>
              编辑
            </Button>
            <Popconfirm title="确定删除吗?" onConfirm={() => handleDelete(record.key)}>
              <Button type="link" danger disabled={editingKey !== ''} icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          </>
        );
      },
    },
  ];

  // 合并可编辑的列配置
  const mergedColumns = columns.map((col) => {
    if (!col.editable) {
      return col;
    }
    return {
      ...col,
      onCell: (record: EditableRowData) => ({
        record,
        inputType: col.dataIndex === 'type' && record.isNew ? 'number' : 'number', // 类型和时长都是数字
        dataIndex: col.dataIndex,
        title: col.title,
        editing: isEditing(record),
      }),
    };
  });

  return (
    <Form form={form} component={false}>
      <Button onClick={handleAdd} type="dashed" style={{ marginBottom: 16 }} icon={<PlusOutlined />} disabled={editingKey !== ''}>
        添加类型-时长
      </Button>
      <Table
        components={{
          body: {
            // Ant Design 表格行内编辑通常需要自定义 EditableCell 组件，
            // 这里为了简化，编辑逻辑放在 render 函数中，并通过 Form 实例控制。
            // 更复杂的行内编辑可以参考 Ant Design 官方文档。
          },
        }}
        bordered
        dataSource={dataSource}
        columns={mergedColumns}
        rowClassName="editable-row"
        pagination={false} // 如果条目不多，可以禁用分页
        size="small"
      />
       <Text type="secondary" style={{marginTop: 8, display: 'block', fontSize: '12px'}}>
        提示: 表格会基于上传的桩基数据中出现的类型自动填充，您也可以手动添加或修改。
      </Text>
    </Form>
  );
};

export default PileTypeDurationEditor;