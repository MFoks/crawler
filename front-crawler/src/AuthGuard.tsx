// src/components/AuthGuard.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { verifyToken, clearToken } from './api';

interface Props {
  children: React.ReactNode;
}

const AuthGuard: React.FC<Props> = ({ children }) => {
  const navigate = useNavigate();
  const [isVerifying, setIsVerifying] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const valid = await verifyToken();
      
      if (!valid) {
        clearToken();
        navigate('/login');
      } else {
        setIsAuthenticated(true);
      }
      
      setIsVerifying(false);
    };

    checkAuth();
  }, [navigate]);

  // Show loading while verifying
  if (isVerifying) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Verifying session...
      </div>
    );
  }

  // Only render children if authenticated
  return isAuthenticated ? <>{children}</> : null;
};

export default AuthGuard;
