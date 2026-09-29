// src/components/LoginForm.tsx
import React, { useState, ChangeEvent, FormEvent, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './LoginForm.module.css';
import { login, isTokenValid } from './api';

const LoginForm: React.FC<{ onLoginSuccess: () => void }> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if already logged in with valid token
    if (isTokenValid()) {
      onLoginSuccess();
      navigate('/app-crawler');
    }
  }, [navigate, onLoginSuccess]);

  const handleUsernameChange = (e: ChangeEvent<HTMLInputElement>) => {
    setUsername(e.target.value);
    setError(null);
  };

  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    setError(null);
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const result = await login(username, password);
    
    setIsLoading(false);
    
    if (result.success) {
      onLoginSuccess();
      navigate('/app-crawler');
    } else {
      setError(result.error || 'Invalid login details.');
    }
  };

  return (
    <div className={styles.loginContainer}>
      <form className={styles.loginBox} onSubmit={handleSubmit}>
        <h2 className={styles.title}>Login</h2>
        {error && (
          <div style={{ color: '#ff4444', marginBottom: '10px', fontSize: '14px' }}>
            {error}
          </div>
        )}
        <input
          type="text"
          className={styles.input}
          placeholder="username"
          value={username}
          onChange={handleUsernameChange}
          disabled={isLoading}
        />
        <input
          type="password"
          className={styles.input}
          placeholder="******"
          value={password}
          onChange={handlePasswordChange}
          disabled={isLoading}
        />
        <button type="submit" className={styles.loginButton} disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'LOGIN'}
        </button>
        <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
          Session valid for 6 hours
        </div>
      </form>
    </div>
  );
};

export default LoginForm;
