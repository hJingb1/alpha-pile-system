import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { BrowserRouter } from 'react-router-dom';
import { ScheduleProvider } from './contexts/ScheduleContext'; // Import Provider
import 'antd/dist/reset.css'; // Ant Design CSS reset
// import './index.css'; // Your global styles (optional)

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <ScheduleProvider> {/* Wrap App with the Provider */}
        <App />
      </ScheduleProvider>
    </BrowserRouter>
  </React.StrictMode>,
);