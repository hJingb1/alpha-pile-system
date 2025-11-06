import React from 'react';
import { Typography } from 'antd';

const { Title } = Typography;

const ProgressManagerPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>进度管理</Title>
      <p>此页面用于输入实际施工进度，并与计划进行对比。</p>
      {/* Add logic for progress tracking and comparison */}
    </div>
  );
};

export default ProgressManagerPage;