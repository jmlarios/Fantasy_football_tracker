import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { fantasyAPI } from '../../services/api';
import { FantasyTeamDetail, Player } from '../../types/fantasy';
import PlayerBrowser from './PlayerBrowser';

const Header: React.FC = () => {
  const { logout } = useAuth();

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
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                fontWeight: 'bold',
                transition: 'background-color 0.2s'
              }}
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
      </div>
    </header>
  );
};

const TeamDetailPage: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const [teamDetail, setTeamDetail] = useState<FantasyTeamDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showPlayerBrowser, setShowPlayerBrowser] = useState(false);

  useEffect(() => {
    if (teamId) {
      loadTeamDetail();
    }
  }, [teamId]);

  const loadTeamDetail = async () => {
    try {
      setLoading(true);
      const data = await fantasyAPI.getTeamDetail(Number(teamId));
      setTeamDetail(data);
    } catch (err: any) {
      setError('Failed to load team details');
      console.error('Error loading team:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerAdded = () => {
    setShowPlayerBrowser(false);
    loadTeamDetail(); // Refresh team data
  };

  const handleRemovePlayer = async (playerId: number) => {
    if (!teamId || !confirm('Are you sure you want to remove this player?')) return;

    try {
      await fantasyAPI.removePlayerFromTeam(Number(teamId), playerId);
      loadTeamDetail(); // Refresh team data
    } catch (err: any) {
      alert('Failed to remove player: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSetCaptain = async (playerId: number, isVice: boolean = false) => {
    if (!teamId) return;

    try {
      await fantasyAPI.setCaptain(Number(teamId), { player_id: playerId, is_vice: isVice });
      loadTeamDetail(); // Refresh team data
    } catch (err: any) {
      alert('Failed to set captain: ' + (err.response?.data?.detail || err.message));
    }
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
        <div style={{ fontSize: '1.2rem' }}>Loading team details...</div>
      </div>
    );
  }

  if (error || !teamDetail) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>Team Not Found</h1>
          <p>{error}</p>
          <Link to="/fantasy-teams">← Back to Teams</Link>
        </div>
      </div>
    );
  }

  const { team, players } = teamDetail;
  const budgetUsed = players.reduce((sum, player) => sum + (player.price || 0), 0);
  const remainingBudget = team.total_budget - budgetUsed;

  // Group players by position
  const playersByPosition = {
    GK: players.filter(p => p.position === 'GK'),
    DEF: players.filter(p => p.position === 'DEF'),
    MID: players.filter(p => p.position === 'MID'),
    FWD: players.filter(p => p.position === 'FWD'),
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <Header />

      {/* Team Overview */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '2rem',
            marginBottom: '2rem'
          }}>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                TOTAL POINTS
              </h3>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#059669' }}>
                {team.total_points.toFixed(1)}
              </div>
            </div>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                SQUAD SIZE
              </h3>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
                {players.length}/{team.max_players}
              </div>
            </div>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                BUDGET USED
              </h3>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
                €{(budgetUsed / 1000000).toFixed(1)}M
              </div>
            </div>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                REMAINING
              </h3>
              <div style={{ 
                fontSize: '2rem', 
                fontWeight: 'bold', 
                color: remainingBudget > 0 ? '#10b981' : '#ef4444'
              }}>
                €{(remainingBudget / 1000000).toFixed(1)}M
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowPlayerBrowser(true)}
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              padding: '0.75rem 2rem',
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
            Add Players
          </button>
        </div>

        {/* Squad Formation */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)'
        }}>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            marginBottom: '2rem',
            color: '#1f2937'
          }}>
            Squad Formation
          </h2>

          {Object.entries(playersByPosition).map(([position, positionPlayers]) => (
            <div key={position} style={{ marginBottom: '2rem' }}>
              <h3 style={{
                fontSize: '1.1rem',
                fontWeight: '600',
                marginBottom: '1rem',
                color: '#374151',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                {position} ({positionPlayers.length})
                {position === 'GK' && positionPlayers.length < 1 && <span style={{ color: '#ef4444' }}>⚠️ Need at least 1</span>}
                {position === 'DEF' && positionPlayers.length < 3 && <span style={{ color: '#ef4444' }}>⚠️ Need at least 3</span>}
                {position === 'MID' && positionPlayers.length < 2 && <span style={{ color: '#ef4444' }}>⚠️ Need at least 2</span>}
                {position === 'FWD' && positionPlayers.length < 1 && <span style={{ color: '#ef4444' }}>⚠️ Need at least 1</span>}
              </h3>

              {positionPlayers.length === 0 ? (
                <div style={{
                  border: '2px dashed #d1d5db',
                  borderRadius: '8px',
                  padding: '2rem',
                  textAlign: 'center',
                  color: '#6b7280'
                }}>
                  No {position} players yet
                </div>
              ) : (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                  gap: '1rem'
                }}>
                  {positionPlayers.map((player) => (
                    <div
                      key={player.id}
                      style={{
                        backgroundColor: '#f9fafb',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '1rem',
                        position: 'relative'
                      }}
                    >
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        marginBottom: '0.5rem'
                      }}>
                        <div>
                          <h4 style={{
                            margin: 0,
                            fontSize: '1rem',
                            fontWeight: '600',
                            color: '#1f2937'
                          }}>
                            {player.name}
                            {player.is_captain && <span style={{ color: '#f59e0b' }}> (C)</span>}
                            {player.is_vice_captain && <span style={{ color: '#8b5cf6' }}> (VC)</span>}
                          </h4>
                          <p style={{
                            margin: 0,
                            fontSize: '0.875rem',
                            color: '#6b7280'
                          }}>
                            {player.team}
                          </p>
                        </div>
                        <div style={{
                          fontSize: '0.875rem',
                          fontWeight: '600',
                          color: '#059669'
                        }}>
                          €{((player.price || 0) / 1000000).toFixed(1)}M
                        </div>
                      </div>

                      <div style={{
                        display: 'flex',
                        gap: '0.5rem',
                        marginTop: '1rem'
                      }}>
                        {!player.is_captain && (
                          <button
                            onClick={() => handleSetCaptain(player.id, false)}
                            style={{
                              backgroundColor: '#f59e0b',
                              color: 'white',
                              border: 'none',
                              padding: '0.25rem 0.75rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                          >
                            Captain
                          </button>
                        )}
                        {!player.is_vice_captain && !player.is_captain && (
                          <button
                            onClick={() => handleSetCaptain(player.id, true)}
                            style={{
                              backgroundColor: '#8b5cf6',
                              color: 'white',
                              border: 'none',
                              padding: '0.25rem 0.75rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                          >
                            Vice
                          </button>
                        )}
                        <button
                          onClick={() => handleRemovePlayer(player.id)}
                          style={{
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Player Browser Modal */}
      {showPlayerBrowser && (
        <PlayerBrowser
          teamId={Number(teamId)}
          remainingBudget={remainingBudget}
          currentPlayers={players}
          onClose={() => setShowPlayerBrowser(false)}
          onPlayerAdded={handlePlayerAdded}
        />
      )}
    </div>
  );
};

export default TeamDetailPage;
