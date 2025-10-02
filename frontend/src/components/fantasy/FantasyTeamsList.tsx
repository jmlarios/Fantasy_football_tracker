import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fantasyAPI } from '../../services/api';
import { FantasyTeam } from '../../types/fantasy';
import CreateTeamModal from './CreateTeamModal';

const FantasyTeamsList: React.FC = () => {
  const [teams, setTeams] = useState<FantasyTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      setLoading(true);
      console.log('Loading fantasy teams...');
      const teamsData = await fantasyAPI.getTeams();
      console.log('Teams loaded:', teamsData);
      setTeams(teamsData);
    } catch (err: any) {
      console.error('Error loading teams:', err);
      setError('Failed to load fantasy teams: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleTeamCreated = (newTeam: FantasyTeam) => {
    setTeams([...teams, newTeam]);
    setShowCreateModal(false);
  };

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh',
        backgroundColor: '#f8fafc',
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '1.2rem' }}>Loading your teams...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      {/* Header */}
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
            to="/dashboard" 
            style={{ 
              color: 'white', 
              textDecoration: 'none',
              fontSize: '1.5rem',
              fontWeight: 'bold'
            }}
          >
            ⚽ LaLiga Fantasy Tracker
          </Link>
          
          <Link 
            to="/dashboard"
            style={{ 
              color: 'white', 
              textDecoration: 'none', 
              padding: '0.75rem 1.5rem',
              border: '2px solid white',
              borderRadius: '6px',
              fontSize: '1rem',
              fontWeight: '500'
            }}
          >
            ← Back to Dashboard
          </Link>
        </div>
      </header>

      {/* Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: '2rem' 
        }}>
          <h1 style={{ 
            fontSize: '2.5rem', 
            fontWeight: 'bold', 
            color: '#1f2937',
            margin: 0
          }}>
            My Fantasy Teams
          </h1>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <span>+</span>
            Create New Team
          </button>
        </div>

        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            color: '#dc2626',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '2rem',
            border: '1px solid #fecaca'
          }}>
            {error}
          </div>
        )}

        {teams.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏆</div>
            <h2 style={{ 
              fontSize: '1.5rem', 
              fontWeight: '600', 
              marginBottom: '1rem',
              color: '#1f2937'
            }}>
              No Fantasy Teams Yet
            </h2>
            <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
              Create your first LaLiga fantasy team and start competing!
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '1rem 2rem',
                borderRadius: '8px',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Create Your First Team
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '1.5rem'
          }}>
            {teams.map((team) => (
              <Link
                key={team.id}
                to={`/fantasy-teams/${team.id}`}
                style={{
                  textDecoration: 'none',
                  color: 'inherit'
                }}
              >
                <div
                  key={team.id}
                  style={{
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    padding: '1.5rem',
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
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '1rem'
                  }}>
                    <h3 style={{
                      fontSize: '1.3rem',
                      fontWeight: '600',
                      color: '#1f2937',
                      margin: 0
                    }}>
                      {team.name}
                    </h3>
                    <div style={{
                      backgroundColor: '#f3f4f6',
                      color: '#374151',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '20px',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}>
                      ID: {team.id}
                    </div>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1rem',
                    marginBottom: '1rem'
                  }}>
                    <div>
                      <div style={{
                        fontSize: '0.875rem',
                        color: '#6b7280',
                        marginBottom: '0.25rem'
                      }}>
                        Total Points
                      </div>
                      <div style={{
                        fontSize: '1.5rem',
                        fontWeight: 'bold',
                        color: '#059669'
                      }}>
                        {team.total_points.toFixed(1)}
                      </div>
                    </div>
                    <div>
                      <div style={{
                        fontSize: '0.875rem',
                        color: '#6b7280',
                        marginBottom: '0.25rem'
                      }}>
                        Squad Size
                      </div>
                      <div style={{
                        fontSize: '1.5rem',
                        fontWeight: 'bold',
                        color: '#3b82f6'
                      }}>
                        0/{team.max_players}
                      </div>
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '1rem',
                    borderTop: '1px solid #f3f4f6'
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#6b7280'
                    }}>
                      Budget: €{(team.total_budget / 1000000).toFixed(0)}M
                    </div>
                    <div style={{
                      color: '#3b82f6',
                      fontSize: '0.875rem',
                      fontWeight: '600'
                    }}>
                      Manage Team →
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {showCreateModal && (
          <CreateTeamModal
            onClose={() => setShowCreateModal(false)}
            onTeamCreated={handleTeamCreated}
          />
        )}
      </div>
    </div>
  );
};

export default FantasyTeamsList;
