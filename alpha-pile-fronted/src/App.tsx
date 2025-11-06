import { Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import PilePlanningPage from './pages/PilePlanningPage';
import FileManagerPage from './pages/FileManagerPage';
// import ProgressManagerPage from './pages/ProgressManagerPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<PilePlanningPage />} /> {/* Default page */}
        <Route path="planning" element={<PilePlanningPage />} />
        <Route path="files" element={<FileManagerPage />} />
        {/* <Route path="progress" element={<ProgressManagerPage />} /> */}
        {/* Add other routes if needed */}
      </Route>
    </Routes>
  );
}

export default App;