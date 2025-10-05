import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { fantasyAPI } from '../../services/api';
import { FantasyTeam } from '../../types/fantasy';
import CreateTeamModal from './CreateTeamModal';
import { transferService } from '../../services/transferService';

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

const FantasyTeamsList: React.FC = () => {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<FantasyTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null);
  const [editingTeam, setEditingTeam] = useState<{ id: number; name: string } | null>(null);
  const [newTeamName, setNewTeamName] = useState('');
  const [teamLeagues, setTeamLeagues] = useState<Record<number, any[]>>({});

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = () => setActiveDropdown(null);
    if (activeDropdown !== null) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [activeDropdown]);

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

  const handleEditTeam = (team: FantasyTeam, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setEditingTeam({ id: team.id, name: team.name });
    setNewTeamName(team.name);
    setActiveDropdown(null);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTeam || !newTeamName.trim()) return;

    try {
      await fantasyAPI.updateTeam(editingTeam.id, { name: newTeamName.trim() });
      setTeams(teams.map(t => t.id === editingTeam.id ? { ...t, name: newTeamName.trim() } : t));
      setEditingTeam(null);
      setNewTeamName('');
    } catch (err: any) {
      alert('Failed to update team name: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCancelEdit = () => {
    setEditingTeam(null);
    setNewTeamName('');
  };

  const handleDeleteTeam = async (teamId: number, teamName: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!window.confirm(`Are you sure you want to delete "${teamName}"? This action cannot be undone.`)) {
      setActiveDropdown(null);
      return;
    }

    try {
      await fantasyAPI.deleteTeam(teamId);
      setTeams(teams.filter(t => t.id !== teamId));
      setActiveDropdown(null);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message;
      alert('Failed to delete team: ' + errorMessage);
      setActiveDropdown(null);
    }
  };

  const toggleDropdown = (teamId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setActiveDropdown(activeDropdown === teamId ? null : teamId);
  };

  const handleViewTransfers = async (teamId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      // Fetch leagues for this team
      const response = await transferService.getFantasyTeamLeagues(teamId);
      const leagues = response.leagues;
      
      if (leagues.length === 0) {
        alert('This team is not in any leagues yet. Join a league first to access transfers!');
        navigate('/leagues');
        return;
      }
      
      if (leagues.length === 1) {
        // If only one league, navigate directly to transfers
        navigate(`/leagues/${leagues[0].league_id}/transfers`);
      } else {
        // Multiple leagues - show a simple alert for now (could be improved with modal)
        const leagueNames = leagues.map((l: any, i: number) => `${i + 1}. ${l.league_name}`).join('\n');
        alert(`This team is in multiple leagues:\n\n${leagueNames}\n\nNavigating to the first one...`);
        navigate(`/leagues/${leagues[0].league_id}/transfers`);
      }
    } catch (err: any) {
      console.error('Error fetching team leagues:', err);
      alert('Failed to load leagues for transfers. Please try again.');
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
        <div style={{ fontSize: '1.2rem' }}>Loading your teams...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <Header />

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
              <div
                key={team.id}
                style={{
                  position: 'relative'
                }}
              >
                <Link
                  to={`/fantasy-teams/${team.id}`}
                  style={{
                    textDecoration: 'none',
                    color: 'inherit',
                    display: 'block'
                  }}
                >
                  <div
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
                        margin: 0,
                        flex: 1
                      }}>
                        {team.name}
                      </h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
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
                        {/* Dropdown menu button */}
                        <button
                          onClick={(e) => toggleDropdown(team.id, e)}
                          style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '1.5rem',
                            cursor: 'pointer',
                            padding: '0.25rem',
                            color: '#6b7280',
                            lineHeight: 1
                          }}
                        >
                          ⋮
                        </button>
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
                        {team.player_count ?? 0}/{team.max_players}
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
              
              {/* Transfers Button */}
              <button
                onClick={(e) => handleViewTransfers(team.id, e)}
                style={{
                  width: '100%',
                  marginTop: '0.75rem',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#059669'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#10b981'}
              >
                <span>🔄</span>
                <span>View Transfers</span>
              </button>
              
              {/* Dropdown Menu */}
              {activeDropdown === team.id && (
                <div
                  style={{
                    position: 'absolute',
                    top: '3.5rem',
                    right: '1rem',
                    backgroundColor: 'white',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                    border: '1px solid #e5e7eb',
                    zIndex: 10,
                    minWidth: '150px'
                  }}
                >
                  <button
                    onClick={(e) => handleEditTeam(team, e)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: 'none',
                      background: 'none',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      color: '#374151',
                      borderBottom: '1px solid #f3f4f6',
                      textAlign: 'left'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <span>✏️</span>
                    <span>Edit Name</span>
                  </button>
                  <button
                    onClick={(e) => handleDeleteTeam(team.id, team.name, e)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: 'none',
                      background: 'none',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      color: '#dc2626',
                      textAlign: 'left'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#fef2f2'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <span>🗑️</span>
                    <span>Delete Team</span>
                  </button>
                </div>
              )}
            </div>
            ))}
          </div>
        )}

        {/* Edit Team Name Modal */}
        {editingTeam && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '2rem',
              maxWidth: '400px',
              width: '90%'
            }}>
              <h2 style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                marginBottom: '1.5rem',
                color: '#1f2937'
              }}>
                Edit Team Name
              </h2>
              <form onSubmit={handleSaveEdit}>
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '2px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '1rem',
                    marginBottom: '1.5rem'
                  }}
                  placeholder="Enter new team name"
                  required
                  maxLength={50}
                  autoFocus
                />
                <div style={{
                  display: 'flex',
                  gap: '1rem',
                  justifyContent: 'flex-end'
                }}>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    style={{
                      backgroundColor: '#f3f4f6',
                      color: '#374151',
                      border: 'none',
                      padding: '0.75rem 1.5rem',
                      borderRadius: '6px',
                      fontSize: '1rem',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      backgroundColor: '#10b981',
                      color: 'white',
                      border: 'none',
                      padding: '0.75rem 1.5rem',
                      borderRadius: '6px',
                      fontSize: '1rem',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    Save
                  </button>
                </div>
              </form>
            </div>
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
