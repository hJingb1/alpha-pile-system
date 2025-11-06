import React from 'react';
import { InputNumber, Form, Typography } from 'antd';

const { Text } = Typography;

interface ParameterInputProps {
  label: string;
  value: number;
  onChange: (value: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  // Add props for validation status if needed (e.g., success, error)
}

const ParameterInput: React.FC<ParameterInputProps> = ({ label, value, onChange, min = 1, max, step = 1 }) => {
  return (
    // Using Form.Item for layout and label, though not a full form submission here
    <Form.Item label={<Text strong>{label}</Text>} labelCol={{ span: 24 }} wrapperCol={{ span: 24 }}>
       <InputNumber
         style={{ width: '100%' }}
         value={value}
         onChange={onChange}
         min={min}
         max={max}
         step={step}
       />
    </Form.Item>
  );
};

export default ParameterInput;