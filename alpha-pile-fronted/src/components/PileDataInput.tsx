import React from 'react';
import { Upload, Button, Table, message, Tooltip } from 'antd'; // 导入 Tooltip
import { UploadOutlined, InfoCircleOutlined } from '@ant-design/icons'; // 导入 InfoCircleOutlined
import { useSchedule } from '../contexts/ScheduleContext';
import Papa from 'papaparse'; // 导入 papaparse

// 定义桩基数据的预期结构 (与 Context 和 API 保持一致)
// 注意：在解析CSV时，所有值最初都可能是字符串，需要转换
interface ExpectedPileData {
    id: number | string; // ID 可以是数字或字符串
    x: number;
    y: number;
    type: number;
    diameter: number;
}

const PileDataInput: React.FC = () => {
  // 从全局Context获取加载数据的函数和当前数据
  const { loadPileData, pileData } = useSchedule();

  // 处理文件上传的函数
  const handleFileUpload = (file: File) => {
    // 创建 FileReader 来读取文件内容
    const reader = new FileReader();

    // 文件读取成功后的回调
    reader.onload = (e) => {
      const fileContent = e.target?.result as string; // 获取文件文本内容
      if (fileContent) {
        try {
          // 使用 PapaParse 解析 CSV 文件内容
          Papa.parse<any>(fileContent, { // 使用 any 或定义更精确的CSV行类型
            header: true,        // 将第一行视为表头
            skipEmptyLines: true,// 跳过空行
            dynamicTyping: false, // 关闭自动类型转换，手动处理更可靠
            complete: (results) => { // 解析完成的回调函数
              console.log("Parsed CSV data:", results.data); // 在控制台打印解析结果，方便调试

              // 检查 PapaParse 是否报告了解析错误
              if (results.errors.length > 0) {
                message.error(`CSV解析错误: ${results.errors[0].message}`);
                console.error("CSV Parsing errors:", results.errors);
                return; // 中断处理
              }

              const parsedData = results.data as any[]; // 获取解析后的数据数组

              // --- 验证数据结构并进行类型转换 ---
              if (validateCsvHeaders(parsedData)) {
                // 尝试将每行数据转换为期望的类型结构
                const validatedData: ExpectedPileData[] = parsedData
                  .map((row, index) => {
                    // 对每一行进行转换和基础验证
                    const xNum = parseFloat(row.x);
                    const yNum = parseFloat(row.y);
                    const typeNum = parseInt(row.type, 10); // 明确指定基数为10
                    const diameterNum = parseFloat(row.diameter);

                    // 检查数字转换是否成功 (不是 NaN)
                    if (isNaN(xNum) || isNaN(yNum) || isNaN(typeNum) || isNaN(diameterNum)) {
                      console.warn(`第 ${index + 2} 行数据格式错误，已忽略:`, row); // +2 因为有表头行且索引从0开始
                      return null; // 返回 null 标记此行为无效
                    }

                    return {
                      id: row.id, // ID 可以是字符串或数字，保持原样
                      x: xNum,
                      y: yNum,
                      type: typeNum,
                      diameter: diameterNum,
                    };
                  })
                  .filter((row): row is ExpectedPileData => row !== null); // 过滤掉转换失败的行

                // 检查是否有行因为格式错误被忽略
                if (validatedData.length !== parsedData.length) {
                  message.warning(`部分数据行因包含非数字值或格式错误而被忽略。请检查文件内容。`);
                }

                // 如果最终有有效数据，则更新全局状态
                if (validatedData.length > 0) {
                  loadPileData(validatedData); // 调用 Context 中的函数更新全局状态
                  message.success(`${file.name} 上传并解析成功! 共加载 ${validatedData.length} 条有效桩基数据。`);
                } else {
                  message.error("未能从文件中解析出有效的桩基数据。请检查文件内容和表头。");
                }

              } else {
                // 如果表头验证失败
                message.error('文件格式错误或缺少必要的表头。请确保文件包含: id, x, y, type, diameter');
              }
            },
            error: (error: Error) => { // 处理 PapaParse 可能抛出的其他错误
              message.error(`解析文件时发生错误: ${error.message}`);
              console.error("Parsing file error:", error);
            }
          });
        } catch (parseCatchError: any) {
            // 捕获 Papa.parse 本身可能抛出的同步错误（虽然不常见）
             message.error(`处理文件时发生意外错误: ${parseCatchError.message}`);
             console.error("Unexpected error during parsing:", parseCatchError);
        }
      } else {
        // 如果文件内容为空
        message.error("文件内容为空或无法读取。");
      }
    };

    // 文件读取失败的回调
    reader.onerror = () => {
      message.error(`读取文件 ${file.name} 失败.`);
    };

    // 开始以文本方式读取文件内容
    reader.readAsText(file);

    // 返回 false 来阻止 antd Upload 组件的默认上传行为（即不实际发送文件到服务器）
    return false;
  };

  // --- 验证函数：仅检查表头是否存在 ---
  const validateCsvHeaders = (data: any[]): boolean => {
    // 检查输入是否为非空数组
    if (!Array.isArray(data) || data.length === 0) {
      console.log("Validation failed: Data is not array or is empty.");
      return false; // 不是数组或数组为空
    }
    // 获取第一行数据（假设是表头定义的对象）
    const firstRow = data[0];
    if (!firstRow || typeof firstRow !== 'object') {
      console.log("Validation failed: First row is missing or not an object.");
      // 可能是空文件或只有表头但无数据，或者PapaParse配置错误
      // 针对只有表头的情况，允许通过，后续处理数据时会发现无有效数据
      // 但如果 firstRow 不存在，说明连表头都没有解析出来
      return false;
    }
    // 定义必需的表头列名
    const requiredHeaders = ['id', 'x', 'y', 'type', 'diameter'];
    // 检查第一行对象是否包含所有必需的键（表头）
    const hasAllHeaders = requiredHeaders.every(header => header in firstRow);
    if (!hasAllHeaders) {
      console.log("Validation failed: Missing required headers.", requiredHeaders.filter(h => !(h in firstRow)));
    }
    return hasAllHeaders;
  };

  // --- 配置用于显示已加载数据的表格列 ---
  const columns = [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 80, ellipsis: true }, // ellipsis: 内容过长时显示省略号
      { title: 'X坐标', dataIndex: 'x', key: 'x', width: 100 },
      { title: 'Y坐标', dataIndex: 'y', key: 'y', width: 100 },
      { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
      { title: '直径(m)', dataIndex: 'diameter', key: 'diameter', width: 100 },
  ];

  return (
    <div>
      {/* Ant Design Upload 组件 */}
      <Upload
        beforeUpload={handleFileUpload} // 在上传前执行我们的处理函数
        showUploadList={false} // 不显示默认的文件列表
        accept=".csv" // 限制只能选择 CSV 文件
      >
        <Button icon={<UploadOutlined />}>上传桩基数据 (CSV)</Button>
      </Upload>
      {/* 提示信息 */}
      <p style={{ marginTop: 8, color: '#888', fontSize: '12px' }}>
        请确保文件为CSV格式，第一行为表头，且包含列:
        <Tooltip title="桩的唯一标识符，可以是数字或文本">
          <span style={{ fontWeight: 'bold', margin: '0 4px', cursor: 'help' }}>id</span>
        </Tooltip>,
        <Tooltip title="桩心X坐标，数值类型">
          <span style={{ fontWeight: 'bold', margin: '0 4px', cursor: 'help' }}>x</span>
        </Tooltip>,
        <Tooltip title="桩心Y坐标，数值类型">
          <span style={{ fontWeight: 'bold', margin: '0 4px', cursor: 'help' }}>y</span>
        </Tooltip>,
        <Tooltip title="桩的类型，整数，用于区分不同施工时长">
          <span style={{ fontWeight: 'bold', margin: '0 4px', cursor: 'help' }}>type</span>
        </Tooltip>,
        <Tooltip title="桩的直径（米），数值类型，用于计算禁区">
          <span style={{ fontWeight: 'bold', margin: '0 4px', cursor: 'help' }}>diameter</span>
          <InfoCircleOutlined style={{ marginLeft: '4px', color: '#aaa' }} />
        </Tooltip>
      </p>

      {/* 可选：添加一个表格来预览已加载的数据 */}
      {pileData.length > 0 && (
        <div style={{marginTop: 16}}>
          <h4 style={{marginBottom: 8}}>已加载数据预览 (前 {Math.min(pileData.length, 5)} 条):</h4>
          <Table
              dataSource={pileData} // 使用全局状态中的 pileData
              columns={columns}    // 使用上面定义的列配置
              rowKey="id"          // 使用 id 作为行的唯一标识
              size="small"         // 使用紧凑尺寸
              pagination={{ pageSize: 5 }} // 设置分页，每页显示5条
              scroll={{ y: 200 }} // 固定表头，表格内容高度最多200px，超出则滚动
              bordered             // 显示边框
          />
        </div>
      )}
    </div>
  );
};

export default PileDataInput;