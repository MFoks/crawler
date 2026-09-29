import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import LoginForm from './LoginForm';
import CrawlerPage from './CrawlerPage/CrawlerPage';
import AuthGuard from './AuthGuard';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<LoginForm onLoginSuccess={() => {}} />} />

        <Route
          path="/app-crawler"
          element={
            <AuthGuard>
              <CrawlerPage />
            </AuthGuard>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
