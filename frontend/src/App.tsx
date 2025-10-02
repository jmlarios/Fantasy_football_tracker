import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import FantasyTeamsList from './components/fantasy/FantasyTeamsList';
import TeamDetailPage from './components/fantasy/TeamDetailPage';

const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header style={{ 
      backgroundColor: '#1f2937', 
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', 
      padding: '1rem 3rem' 
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <Link 
          to="/" 
          style={{ 
            color: 'white', 
            textDecoration: 'none',
            fontSize: '1.5rem',
            fontWeight: 'bold'
          }}
        >
          ⚽ LaLiga Fantasy Tracker
        </Link>
        
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <span style={{ color: 'white' }}>Welcome, {user.name}!</span>
            <button
              onClick={logout}
              style={{ 
                backgroundColor: '#ef4444', 
                color: 'white', 
                border: 'none', 
                padding: '0.75rem 1.5rem', 
                borderRadius: '6px', 
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '500'
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
                color: 'white', 
                textDecoration: 'none', 
                padding: '0.75rem 1.5rem',
                border: '2px solid white',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '500',
                transition: 'all 0.3s ease'
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
                padding: '0.75rem 1.5rem', 
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '500',
                transition: 'all 0.3s ease'
              }}
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};

const HomePage: React.FC = () => {
  const { user } = useAuth();

  if (user) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Header />
      
      {/* Hero Section */}
      <div style={{ 
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '4rem 2rem'
      }}>
        <div style={{ 
          maxWidth: '1200px',
          width: '100%',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '4rem',
          alignItems: 'center'
        }}>
          {/* Left Side - Content */}
          <div style={{ color: 'white' }}>
            <h1 style={{ 
              fontSize: '3.5rem', 
              fontWeight: 'bold', 
              marginBottom: '1.5rem',
              lineHeight: '1.1'
            }}>
              Master Your<br />
              LaLiga Fantasy
            </h1>
            <p style={{ 
              fontSize: '1.3rem', 
              marginBottom: '2rem',
              opacity: 0.9,
              lineHeight: '1.6'
            }}>
              Build your ultimate LaLiga fantasy team, track player performances, 
              manage transfers, and compete with friends in the most comprehensive 
              Spanish football fantasy platform.
            </p>
            
            <div style={{ 
              display: 'flex', 
              gap: '1rem',
              marginBottom: '3rem'
            }}>
              <Link 
                to="/register" 
                style={{ 
                  backgroundColor: '#10b981', 
                  color: 'white', 
                  textDecoration: 'none', 
                  padding: '1rem 2rem', 
                  borderRadius: '8px',
                  fontSize: '1.1rem',
                  fontWeight: '600',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                  transition: 'transform 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'
              }
              >
                Start Playing Free
              </Link>
              <Link 
                to="/login" 
                style={{ 
                  backgroundColor: 'transparent', 
                  color: 'white', 
                  textDecoration: 'none', 
                  padding: '1rem 2rem', 
                  borderRadius: '8px',
                  fontSize: '1.1rem',
                  fontWeight: '600',
                  border: '2px solid white',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                  e.currentTarget.style.color = '#667eea';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = 'white';
                }}
              >
                I Have an Account
              </Link>
            </div>

            {/* Features */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>⚽</span>
                <span>Real LaLiga Players</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>📊</span>
                <span>Live Statistics</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🔄</span>
                <span>Transfer Management</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🏆</span>
                <span>Fantasy Leagues</span>
              </div>
            </div>
          </div>

          {/* Right Side - Preview */}
          <div style={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(10px)',
            borderRadius: '16px',
            padding: '2rem',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <div style={{ 
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '1.5rem',
              marginBottom: '1rem'
            }}>
              <h3 style={{ 
                margin: '0 0 1rem 0', 
                color: '#1f2937',
                fontSize: '1.2rem'
              }}>
                Quick Preview
              </h3>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '1rem',
                fontSize: '0.9rem'
              }}>
                <div>
                  <strong>Team Budget:</strong><br />
                  €100,000,000
                </div>
                <div>
                  <strong>Squad Size:</strong><br />
                  15 Players
                </div>
                <div>
                  <strong>Free Transfers:</strong><br />
                  2 per Matchday
                </div>
                <div>
                  <strong>Captain Bonus:</strong><br />
                  2x Points
                </div>
              </div>
            </div>
            
            <div style={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              borderRadius: '8px',
              padding: '1rem',
              textAlign: 'center',
              color: '#1f2937'
            }}>
              <p style={{ margin: 0, fontWeight: '500' }}>
                Join thousands of LaLiga fans!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <Header />
      <div style={{ 
        padding: '3rem 2rem',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <div style={{ 
          textAlign: 'center',
          marginBottom: '3rem'
        }}>
          <h1 style={{ 
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: '#1f2937',
            marginBottom: '1rem'
          }}>
            Welcome back, {user?.name}! 👋
          </h1>
          <p style={{ 
            fontSize: '1.2rem',
            color: '#6b7280'
          }}>
            Ready to manage your LaLiga fantasy team?
          </p>
        </div>
        
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem'
        }}>
          <Link 
            to="/fantasy-teams"
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{ 
              backgroundColor: 'white', 
              padding: '2rem', 
              borderRadius: '12px', 
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
              border: '1px solid #e5e7eb',
              transition: 'all 0.2s ease',
              cursor: 'pointer'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.07)';
            }}
            >
              <h3 style={{ 
                fontSize: '1.3rem',
                fontWeight: '600',
                marginBottom: '1rem',
                color: '#1f2937'
              }}>
                🏆 My Fantasy Teams
              </h3>
              <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
                Create and manage your LaLiga fantasy teams
              </p>
              <div style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                padding: '0.75rem 1.5rem',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '500',
                textAlign: 'center'
              }}>
                Manage Teams
              </div>
            </div>
          </Link>

          <div style={{ 
            backgroundColor: 'white', 
            padding: '2rem', 
            borderRadius: '12px', 
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ 
              fontSize: '1.3rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: '#1f2937'
            }}>
              ⚽ Player Database
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
              Browse and analyze LaLiga players
            </p>
            <button style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '6px',
              fontSize: '1rem',
              fontWeight: '500',
              cursor: 'pointer',
              width: '100%'
            }}>
              Browse Players
            </button>
          </div>

          <div style={{ 
            backgroundColor: 'white', 
            padding: '2rem', 
            borderRadius: '12px', 
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ 
              fontSize: '1.3rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: '#1f2937'
            }}>
              📊 Statistics
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
              Track your team's performance
            </p>
            <button style={{
              backgroundColor: '#8b5cf6',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '6px',
              fontSize: '1rem',
              fontWeight: '500',
              cursor: 'pointer',
              width: '100%'
            }}>
              View Stats
            </button>
          </div>
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
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Header />
      <div style={{ 
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden',
          maxWidth: '900px',
          width: '100%',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          minHeight: '500px'
        }}>
          {/* Left side - Form */}
          <div style={{ padding: '3rem' }}>
            <LoginForm />
            <p style={{ 
              marginTop: '1.5rem', 
              textAlign: 'center',
              color: '#6b7280'
            }}>
              Don't have an account?{' '}
              <Link 
                to="/register" 
                style={{ 
                  color: '#3b82f6', 
                  textDecoration: 'none',
                  fontWeight: '500'
                }}
              >
                Sign up here
              </Link>
            </p>
          </div>
          
          {/* Right side - Info */}
          <div style={{ 
            backgroundColor: '#1f2937',
            color: 'white',
            padding: '3rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center'
          }}>
            <h2 style={{ 
              fontSize: '2rem',
              fontWeight: 'bold',
              marginBottom: '1rem'
            }}>
              Welcome Back!
            </h2>
            <p style={{ 
              fontSize: '1.1rem',
              opacity: 0.9,
              lineHeight: '1.6'
            }}>
              Sign in to access your fantasy teams, manage transfers, 
              and compete in LaLiga fantasy leagues.
            </p>
            <div style={{ marginTop: '2rem' }}>
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>✓</span> Manage your fantasy teams
              </div>
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>✓</span> Track player performances
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>✓</span> Join fantasy leagues
              </div>
            </div>
          </div>
        </div>
      </div>
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
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Header />
      <div style={{ 
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden',
          maxWidth: '900px',
          width: '100%',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          minHeight: '600px'
        }}>
          {/* Left side - Info */}
          <div style={{ 
            backgroundColor: '#10b981',
            color: 'white',
            padding: '3rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center'
          }}>
            <h2 style={{ 
              fontSize: '2rem',
              fontWeight: 'bold',
              marginBottom: '1rem'
            }}>
              Join LaLiga Fantasy!
            </h2>
            <p style={{ 
              fontSize: '1.1rem',
              opacity: 0.9,
              lineHeight: '1.6',
              marginBottom: '2rem'
            }}>
              Create your account and start building your ultimate LaLiga fantasy team today.
            </p>
            <div>
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>🚀</span> Quick & easy setup
              </div>
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>💰</span> €100M starting budget
              </div>
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>⚽</span> All LaLiga players available
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span>🏆</span> Compete with friends
              </div>
            </div>
          </div>
          
          {/* Right side - Form */}
          <div style={{ padding: '3rem' }}>
            <RegisterForm />
            <p style={{ 
              marginTop: '1.5rem', 
              textAlign: 'center',
              color: '#6b7280'
            }}>
              Already have an account?{' '}
              <Link 
                to="/login" 
                style={{ 
                  color: '#3b82f6', 
                  textDecoration: 'none',
                  fontWeight: '500'
                }}
              >
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
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
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ 
          color: 'white',
          fontSize: '1.5rem',
          fontWeight: '500'
        }}>
          Loading...
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route 
        path="/dashboard" 
        element={user ? <Dashboard /> : <Navigate to="/login" />} 
      />
      <Route 
        path="/fantasy-teams" 
        element={user ? <FantasyTeamsList /> : <Navigate to="/login" />} 
      />
      <Route 
        path="/fantasy-teams/:teamId" 
        element={user ? <TeamDetailPage /> : <Navigate to="/login" />} 
      />
    </Routes>
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
