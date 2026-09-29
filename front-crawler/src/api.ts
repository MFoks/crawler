// API helper with JWT token management

const TOKEN_KEY = 'auth_token';
const TOKEN_EXPIRY_KEY = 'token_expiry';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string, expiresIn: number): void {
  localStorage.setItem(TOKEN_KEY, token);
  const expiryTime = Date.now() + (expiresIn * 1000);
  localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
  localStorage.removeItem('sessionStart'); // Clean up old session storage
}

export function isTokenValid(): boolean {
  const token = getToken();
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  
  if (!token || !expiry) return false;
  
  return Date.now() < parseInt(expiry);
}

export async function login(username: string, password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      return { success: false, error: data.detail || 'Invalid credentials' };
    }
    
    const data = await response.json();
    setToken(data.token, data.expires_in);
    return { success: true };
  } catch (error) {
    return { success: false, error: 'Connection error' };
  }
}

export async function verifyToken(): Promise<boolean> {
  const token = getToken();
  if (!token) return false;
  
  // First check local expiry
  if (!isTokenValid()) {
    clearToken();
    return false;
  }
  
  // Then verify with server
  try {
    const response = await fetch('/api/verify-token', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    if (!response.ok) {
      clearToken();
      return false;
    }
    
    return true;
  } catch {
    // Network error - keep token if locally valid
    return isTokenValid();
  }
}

export function logout(): void {
  clearToken();
}

// Authenticated fetch wrapper
export async function apiFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // If unauthorized, clear token
  if (response.status === 401) {
    clearToken();
  }
  
  return response;
}

// Convenience methods
export async function apiGet(url: string): Promise<Response> {
  return apiFetch(url, { method: 'GET' });
}

export async function apiPost(url: string, body?: any): Promise<Response> {
  return apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
}
