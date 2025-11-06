import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  DesktopOutlined,
  FileOutlined,
  PieChartOutlined,
  TeamOutlined,
  UserOutlined,
  SettingOutlined,
  CloudUploadOutlined,
  ProjectOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Layout, Menu, theme, Avatar } from 'antd';
import './MainLayout.css'; // For custom layout styling

const { Header, Content, Footer, Sider } = Layout;

// Map pathnames to menu keys
const pathToKeyMap: { [key: string]: string } = {
  '/planning': '1',
  '/files': '2',
  '/progress': '3',
};

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation(); // Get current location

  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // Determine default selected key based on current path
  const currentKey = pathToKeyMap[location.pathname] || '1'; // Default to '1' if path not found

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    // console.log('click ', e);
    switch (e.key) {
      case '1':
        navigate('/planning');
        break;
      case '2':
        navigate('/files');
        break;
      case '3':
        navigate('/progress');
        break;
      default:
        navigate('/');
    }
  };

  const items: MenuProps['items'] = [
    {
      key: '1',
      icon: <ProjectOutlined />,
      label: '桩基规划',
    },
    {
      key: '2',
      icon: <FileOutlined />,
      label: '文件管理',
    },
    {
      key: '3',
      icon: <LineChartOutlined />,
      label: '进度管理',
    },
  ];


  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)} theme="dark">
        <div className="logo-vertical">
           <Avatar shape="square" size="large" src="/logo_placeholder.png" style={{ margin: '16px auto', display: 'block' }}/>
           {!collapsed && <span className="logo-text">Alpha_Pile</span>}
        </div>
        <Menu
            theme="dark"
            defaultSelectedKeys={[currentKey]} // Set selected key based on current path
            mode="inline"
            items={items}
            onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        {/* Optional Header */}
        {/* <Header style={{ padding: 0, background: colorBgContainer }} /> */}
        <Content style={{ margin: '16px' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {/* Page content renders here */}
            <Outlet />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          Alpha_Pile ©{new Date().getFullYear()} Created with Ant Design & React
        </Footer>
      </Layout>
    </Layout>
  );
};

export default MainLayout;