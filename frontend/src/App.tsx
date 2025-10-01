import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';

const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header style={{ 
      backgroundColor: 'white', 
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)', 
      padding: '1rem 2rem' 
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <h1 style={{ margin: 0, color: '#1f2937' }}>LaLiga Fantasy Tracker</h1>
        
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span>Welcome, {user.name}!</span>
            <button
              onClick={logout}
              style={{ 
                backgroundColor: '#ef4444', 
                color: 'white', 
                border: 'none', 
                padding: '0.5rem 1rem', 
                borderRadius: '4px', 
                cursor: 'pointer' 
              }}
            >
              Logout
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link 
              to="/login" 
              style={{ 
                color: '#3b82f6', 
                textDecoration: 'none', 
                padding: '0.5rem 1rem' 
              }}
            >
              Login
            </Link>
            <Link 
              to="/register" 
              style={{ 
                backgroundColor: '#3b82f6', 
                color: 'white', 
                textDecoration: 'none', 
                padding: '0.5rem 1rem', 
                borderRadius: '4px' 
              }}
            >
              Register
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ 
        maxWidth: '800px', 
        margin: '0 auto', 
        textAlign: 'center' 
      }}>
        <h2>Welcome to your Fantasy Dashboard!</h2>
        <p>Hello {user?.name}, you're successfully logged in!</p>
        <div style={{ 
          backgroundColor: 'white', 
          padding: '1.5rem', 
          borderRadius: '8px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          marginTop: '2rem'
        }}>
          <p>🏆 Your fantasy teams and features will appear here soon...</p>
        </div>
      </div>
    </div>
  );
};

const LoginPage: React.FC = () => {
  const { user } = useAuth();
  
  if (user) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div style={{ 
      minHeight: 'calc(100vh - 80px)', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <LoginForm />
      <p style={{ marginTop: '1rem', textAlign: 'center' }}>
        Don't have an account?{' '}
        <Link to="/register" style={{ color: '#3b82f6', textDecoration: 'none' }}>
          Sign up here
        </Link>
      </p>
    </div>
  );
};

const RegisterPage: React.FC = () => {
  const { user } = useAuth();
  
  if (user) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div style={{ 
      minHeight: 'calc(100vh - 80px)', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <RegisterForm />
      <p style={{ marginTop: '1rem', textAlign: 'center' }}>
        Already have an account?{' '}
        <Link to="/login" style={{ color: '#3b82f6', textDecoration: 'none' }}>
          Sign in here
        </Link>
      </p>
    </div>
  );
};

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <div style={{ fontSize: '1.2rem' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <Header />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route 
          path="/dashboard" 
          element={user ? <Dashboard /> : <Navigate to="/login" />} 
        />
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
};

export default App;
