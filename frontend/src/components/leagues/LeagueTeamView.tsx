import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { leagueAPI } from '../../services/api';

interface LeagueTeamData {
  league_team_id: number;
  league_id: number;
  league_name: string;
  team_name: string;
  fantasy_team_id: number;
  league_points: number;
  league_rank: number | null;
  total_budget: number;
  budget_used: number;
  remaining_budget: number;
  players: Player[];
  player_count: number;
}

interface Player {
  id: number;
  name: string;
  team: string;
  position: string;
  price: number;
  is_captain: boolean;
  is_vice_captain: boolean;
  position_in_team: string;
}

const LeagueTeamView: React.FC = () => {
  const { leagueId } = useParams<{ leagueId: string }>();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [teamData, setTeamData] = useState<LeagueTeamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditingName, setIsEditingName] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');

  useEffect(() => {
    if (leagueId) {
      loadTeamData();
    }
  }, [leagueId]);

  const loadTeamData = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await leagueAPI.getMyLeagueTeam(Number(leagueId));
      setTeamData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load your team for this league');
    } finally {
      setLoading(false);
    }
  };

  const handleRenameTeam = async () => {
    if (!newTeamName.trim() || !leagueId) return;

    try {
      await leagueAPI.updateLeagueTeamName(Number(leagueId), newTeamName.trim());
      setTeamData(prev => prev ? { ...prev, team_name: newTeamName.trim() } : null);
      setIsEditingName(false);
      setNewTeamName('');
      alert('Team name updated successfully!');
    } catch (err: any) {
      alert('Failed to update team name. Please try again.');
    }
  };

  const getPositionColor = (position: string) => {
    switch (position.toUpperCase()) {
      case 'GK':
        return '#f59e0b';
      case 'DEF':
        return '#3b82f6';
      case 'MID':
        return '#10b981';
      case 'FWD':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const formatPrice = (price: number) => {
    return `€${(price / 1_000_000).toFixed(1)}M`;
  };

  const formatBudget = (budget: number) => {
    return `€${(budget / 1_000_000).toFixed(1)}M`;
  };

  const groupPlayersByPosition = (players: Player[]) => {
    const groups: { [key: string]: Player[] } = {
      GK: [],
      DEF: [],
      MID: [],
      FWD: []
    };

    players.forEach(player => {
      const pos = player.position_in_team || player.position;
      if (groups[pos]) {
        groups[pos].push(player);
      }
    });

    return groups;
  };

  if (!user) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p>Please log in to view your team</p>
        <Link to="/login">Go to Login</Link>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
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
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <Link 
              to="/dashboard" 
              style={{ 
                color: 'white', 
                textDecoration: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 'bold'
              }}
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
                fontWeight: 'bold'
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
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                fontWeight: 'bold'
              }}
            >
              My Leagues
            </Link>
            
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

      {/* Main Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
          <button
            onClick={() => navigate('/leagues')}
            style={{
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            ← Back to Leagues
          </button>
          
          <button
            onClick={() => navigate(`/leagues/${leagueId}/transfers`)}
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: 'bold'
            }}
          >
            🔄 Transfers
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
            Loading your team...
          </div>
        )}

        {error && (
          <div style={{
            backgroundColor: '#fee2e2',
            color: '#991b1b',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem'
          }}>
            {error}
          </div>
        )}

        {teamData && !loading && (
          <>
            {/* Team Stats */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '2rem',
              marginBottom: '2rem',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}>
              {/* Breadcrumb */}
              <div style={{ 
                fontSize: '0.875rem', 
                color: '#6b7280', 
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Link 
                  to="/leagues" 
                  style={{ color: '#3b82f6', textDecoration: 'none' }}
                >
                  My Leagues
                </Link>
                <span>›</span>
                <span style={{ color: '#1f2937', fontWeight: '500' }}>{teamData.league_name}</span>
              </div>

              {/* Team Name Section */}
              <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {!isEditingName ? (
                  <>
                    <h2 style={{ fontSize: '1.75rem', fontWeight: 'bold', margin: 0, color: '#1f2937' }}>
                      {teamData.team_name || 'My Team'}
                    </h2>
                    <button
                      onClick={() => {
                        setIsEditingName(true);
                        setNewTeamName(teamData.team_name || '');
                      }}
                      style={{
                        backgroundColor: '#f3f4f6',
                        color: '#374151',
                        border: 'none',
                        padding: '0.5rem 1rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                    >
                      ✏️ Rename
                    </button>
                  </>
                ) : (
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flex: 1 }}>
                    <input
                      type="text"
                      value={newTeamName}
                      onChange={(e) => setNewTeamName(e.target.value)}
                      placeholder="Enter new team name"
                      maxLength={100}
                      style={{
                        flex: 1,
                        padding: '0.75rem',
                        border: '2px solid #3b82f6',
                        borderRadius: '6px',
                        fontSize: '1rem'
                      }}
                      autoFocus
                    />
                    <button
                      onClick={handleRenameTeam}
                      style={{
                        backgroundColor: '#10b981',
                        color: 'white',
                        border: 'none',
                        padding: '0.75rem 1rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingName(false);
                        setNewTeamName('');
                      }}
                      style={{
                        backgroundColor: '#f3f4f6',
                        color: '#374151',
                        border: 'none',
                        padding: '0.75rem 1rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1.5rem'
              }}>
                <div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                    League Points
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#8b5cf6' }}>
                    {teamData.league_points}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                    League Rank
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
                    {teamData.league_rank ? `#${teamData.league_rank}` : 'N/A'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                    Budget Used
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1f2937' }}>
                    {formatBudget(teamData.budget_used)}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                    Remaining Budget
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>
                    {formatBudget(teamData.remaining_budget)}
                  </div>
                </div>
              </div>
            </div>

            {/* Players List */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '2rem',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem', color: '#1f2937' }}>
                Squad ({teamData.player_count} players)
              </h3>

              {Object.entries(groupPlayersByPosition(teamData.players)).map(([position, players]) => (
                players.length > 0 && (
                  <div key={position} style={{ marginBottom: '2rem' }}>
                    <div style={{
                      fontSize: '1.125rem',
                      fontWeight: 'bold',
                      color: getPositionColor(position),
                      marginBottom: '1rem',
                      paddingBottom: '0.5rem',
                      borderBottom: `2px solid ${getPositionColor(position)}`
                    }}>
                      {position} ({players.length})
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {players.map(player => (
                        <div key={player.id} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '1rem',
                          backgroundColor: '#f9fafb',
                          borderRadius: '8px',
                          border: player.is_captain ? '2px solid #f59e0b' : player.is_vice_captain ? '2px solid #94a3b8' : '1px solid #e5e7eb'
                        }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                              <span style={{ fontWeight: 'bold', fontSize: '1.125rem', color: '#1f2937' }}>
                                {player.name}
                              </span>
                              {player.is_captain && (
                                <span style={{
                                  backgroundColor: '#f59e0b',
                                  color: 'white',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '4px',
                                  fontSize: '0.75rem',
                                  fontWeight: 'bold'
                                }}>
                                  C
                                </span>
                              )}
                              {player.is_vice_captain && (
                                <span style={{
                                  backgroundColor: '#94a3b8',
                                  color: 'white',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '4px',
                                  fontSize: '0.75rem',
                                  fontWeight: 'bold'
                                }}>
                                  VC
                                </span>
                              )}
                            </div>
                            <div style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                              {player.team}
                            </div>
                          </div>

                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontWeight: 'bold', color: '#1f2937' }}>
                              {formatPrice(player.price)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default LeagueTeamView;
