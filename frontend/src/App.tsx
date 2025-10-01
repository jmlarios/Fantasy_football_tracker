import React from 'react';

const App: React.FC = () => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#f3f4f6',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ 
          fontSize: '2.5rem', 
          fontWeight: 'bold', 
          color: '#111827', 
          marginBottom: '1rem' 
        }}>
          LaLiga Fantasy Tracker
        </h1>
        <p style={{ 
          fontSize: '1.25rem', 
          color: '#4b5563', 
          marginBottom: '2rem' 
        }}>
          Welcome to your fantasy football dashboard!
        </p>
        <div style={{ 
          backgroundColor: '#ffffff', 
          padding: '1.5rem', 
          borderRadius: '0.5rem', 
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          maxWidth: '400px',
          margin: '0 auto'
        }}>
          <p style={{ color: '#374151', marginBottom: '0.5rem' }}>
            Frontend is running successfully! 🚀
          </p>
          <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Authentication and features coming soon...
          </p>
        </div>
      </div>
    </div>
  );
};

export default App;
