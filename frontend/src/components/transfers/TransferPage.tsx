import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import FreeAgentTransfer from './FreeAgentTransfer';
import UserTransferMarket from './UserTransferMarket';
import TransferOffers from './TransferOffers';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

// Header component (same as in App.tsx)
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <Link 
                to="/dashboard" 
                style={{ 
                  color: 'white', 
                  textDecoration: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                Dashboard
              </Link>
              <Link 
                to="/fantasy-teams" 
                style={{ 
                  color: 'white', 
                  textDecoration: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                My Teams
              </Link>
              <Link 
                to="/leagues" 
                style={{ 
                  color: 'white', 
                  textDecoration: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                My Leagues
              </Link>
            </div>
            
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
                fontWeight: 'bold'
              }}
            >
              Logout
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
};

const TransferPage: React.FC = () => {
  const { leagueId } = useParams<{ leagueId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'free-agents' | 'user-transfers' | 'offers'>('free-agents');
  const [currentTeamId, setCurrentTeamId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (leagueId) {
      loadCurrentTeam();
    }
  }, [leagueId]);

  const loadCurrentTeam = async () => {
    try {
      const response = await api.get(`/leagues/${leagueId}/my-team`);
      setCurrentTeamId(response.data.league_team_id);
    } catch (err: any) {
      console.error('Error loading current team:', err);
      // If user is not in this league, show appropriate message
      if (err.response?.status === 404) {
        setError(err.response?.data?.detail || 'You are not a member of this league');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!leagueId) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: '#ef4444' }}>League ID is required</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (!currentTeamId) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: '#ef4444' }}>You don't have a team in this league</p>
      </div>
    );
  }

  const tabs = [
    { id: 'free-agents' as const, label: '🆓 Free Agents', component: FreeAgentTransfer },
    { id: 'user-transfers' as const, label: '🤝 User Transfers', component: UserTransferMarket },
    { id: 'offers' as const, label: '📬 My Offers', component: TransferOffers },
  ];

  const ActiveComponent = tabs.find(t => t.id === activeTab)?.component || FreeAgentTransfer;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <Header />
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
        {/* Back Button */}
        <button
          onClick={() => navigate(`/leagues/${leagueId}/team`)}
          style={{
            backgroundColor: '#6b7280',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '6px',
            cursor: 'pointer',
            marginBottom: '1.5rem',
            fontSize: '1rem'
          }}
        >
          ← Back to Team
        </button>

        {/* Page Header */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '12px', 
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
            Transfer Market
          </h1>
          <p style={{ margin: '0.5rem 0 0 0', color: '#6b7280' }}>
            Manage your team transfers and offers
          </p>
        </div>

        {/* Tabs */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden'
        }}>
          <div style={{ 
            display: 'flex', 
            borderBottom: '2px solid #e5e7eb'
          }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  flex: 1,
                  padding: '1rem 2rem',
                  border: 'none',
                  backgroundColor: activeTab === tab.id ? 'white' : '#f9fafb',
                  color: activeTab === tab.id ? '#3b82f6' : '#6b7280',
                  borderBottom: activeTab === tab.id ? '3px solid #3b82f6' : 'none',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: activeTab === tab.id ? 'bold' : 'normal',
                  transition: 'all 0.2s'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div style={{ padding: '2rem' }}>
            <ActiveComponent leagueId={parseInt(leagueId)} currentTeamId={currentTeamId} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransferPage;
