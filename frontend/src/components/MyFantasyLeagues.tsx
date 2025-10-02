import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import leagueService, { League, LeagueData, PublicLeague, LeaderboardData } from '../services/leagueService';

interface CreateFormData {
  name: string;
  description: string;
  is_private: boolean;
  max_participants: number;
}

interface JoinFormData {
  join_code: string;
}

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
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                fontWeight: 'bold',
                transition: 'background-color 0.2s'
              }}
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

const MyFantasyLeagues: React.FC = () => {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateForm, setShowCreateForm] = useState<boolean>(false);
  const [showJoinForm, setShowJoinForm] = useState<boolean>(false);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [showLeaderboard, setShowLeaderboard] = useState<boolean>(false);
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardData | null>(null);
  
  const [createForm, setCreateForm] = useState<CreateFormData>({
    name: '',
    description: '',
    is_private: false,
    max_participants: 20
  });
  
  const [joinForm, setJoinForm] = useState<JoinFormData>({
    join_code: ''
  });
  
  const [publicLeagues, setPublicLeagues] = useState<PublicLeague[]>([]);
  const [joinTab, setJoinTab] = useState<'code' | 'public'>('code');

  useEffect(() => {
    loadUserLeagues();
  }, []);

  const loadUserLeagues = async (): Promise<void> => {
    setLoading(true);
    try {
      const userLeagues = await leagueService.getUserLeagues();
      setLeagues(userLeagues);
    } catch (error) {
      console.error('Error loading leagues:', error);
      setLeagues([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const loadPublicLeagues = async (): Promise<void> => {
    try {
      const leagues = await leagueService.getPublicLeagues();
      setPublicLeagues(leagues);
    } catch (error) {
      console.error('Error loading public leagues:', error);
      setPublicLeagues([]);
    }
  };

  const handleCreateLeague = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!createForm.name.trim()) return;

    try {
      const leagueData: LeagueData = {
        name: createForm.name,
        description: createForm.description || undefined,
        is_private: createForm.is_private,
        max_participants: createForm.max_participants
      };

      await leagueService.createLeague(leagueData);
      setShowCreateForm(false);
      setCreateForm({ name: '', description: '', is_private: false, max_participants: 20 });
      loadUserLeagues();
      alert('League created successfully!');
    } catch (error) {
      alert('Failed to create league. Please try again.');
    }
  };

  const handleJoinLeague = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!joinForm.join_code.trim()) return;

    try {
      const result = await leagueService.joinLeagueByCode(joinForm.join_code.trim().toUpperCase());
      setShowJoinForm(false);
      setJoinForm({ join_code: '' });
      loadUserLeagues();
      alert(`Successfully joined "${result.league_name}"!`);
    } catch (error) {
      alert('Failed to join league. Please check the join code and try again.');
    }
  };

  const handleJoinPublicLeague = async (leagueId: number, leagueName: string): Promise<void> => {
    if (!window.confirm(`Join "${leagueName}"?`)) return;

    try {
      const result = await leagueService.joinLeagueById(leagueId);
      loadUserLeagues();
      alert(`Successfully joined "${result.league_name}"!`);
    } catch (error) {
      alert('Failed to join league. Please try again.');
    }
  };

  const handleViewLeaderboard = async (league: League): Promise<void> => {
    try {
      const data = await leagueService.getLeagueLeaderboard(league.id);
      setLeaderboardData(data);
      setSelectedLeague(league);
      setShowLeaderboard(true);
    } catch (error) {
      alert('Failed to load leaderboard. Please try again.');
    }
  };

  const copyJoinCode = (joinCode: string): void => {
    navigator.clipboard.writeText(joinCode).then(() => {
      alert('Join code copied to clipboard!');
    }).catch(() => {
      alert('Failed to copy join code');
    });
  };

  const handleCreateFormChange = (field: keyof CreateFormData, value: string | boolean | number): void => {
    setCreateForm(prev => ({ ...prev, [field]: value }));
  };

  // Show leaderboard view
  if (showLeaderboard && leaderboardData && selectedLeague) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
        <Header />
        <div style={{ 
          padding: '3rem 2rem',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '2rem'
          }}>
            <div>
              <h1 style={{ 
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '0.5rem'
              }}>
                {selectedLeague.name} - Leaderboard 🏆
              </h1>
              <p style={{ 
                fontSize: '1.2rem',
                color: '#6b7280'
              }}>
                {leaderboardData.league.participants} participants competing
              </p>
            </div>
            <button 
              style={{
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
              onClick={() => setShowLeaderboard(false)}
            >
              ← Back to Leagues
            </button>
          </div>

          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
            overflow: 'hidden'
          }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Rank</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Manager</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Team</th>
                    <th style={{ padding: '1rem', textAlign: 'right', fontWeight: '600' }}>Points</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboardData.leaderboard.map((entry) => (
                    <tr 
                      key={entry.user_id}
                      style={{ 
                        backgroundColor: entry.is_current_user ? '#eff6ff' : 'white',
                        borderBottom: '1px solid #e5e7eb'
                      }}
                    >
                      <td style={{ padding: '1rem' }}>
                        <span style={{ fontSize: '1.1rem', fontWeight: '600' }}>
                          {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          {entry.user_name}
                          {entry.is_current_user && (
                            <span style={{
                              backgroundColor: '#3b82f6',
                              color: 'white',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: '500'
                            }}>
                              You
                            </span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '1rem', color: '#6b7280' }}>{entry.team_name}</td>
                      <td style={{ padding: '1rem', textAlign: 'right' }}>
                        <span style={{ fontSize: '1.1rem', fontWeight: '600', color: '#1f2937' }}>
                          {entry.total_points.toFixed(1)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main leagues view with styled UI
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <Header />
      <div style={{ 
        padding: '3rem 2rem',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <h1 style={{ 
              fontSize: '2.5rem',
              fontWeight: 'bold',
              color: '#1f2937',
              marginBottom: '0.5rem'
            }}>
              My Fantasy Leagues 🏅
            </h1>
            <p style={{ 
              fontSize: '1.2rem',
              color: '#6b7280'
            }}>
              Create private leagues and compete with friends
            </p>
          </div>
          <div style={{ 
            display: 'flex', 
            gap: '1rem',
            flexShrink: 0
          }}>
            <button 
              style={{
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
              onClick={() => setShowCreateForm(true)}
            >
              + Create League
            </button>
            <button 
              style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
              onClick={() => {
                setShowJoinForm(true);
                if (joinTab === 'public') loadPublicLeagues();
              }}
            >
              Join League
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '300px' 
          }}>
            <div style={{ 
              color: '#6b7280',
              fontSize: '1.2rem'
            }}>
              Loading your leagues...
            </div>
          </div>
        ) : (
          <>
            {/* Stats Cards */}
            <div style={{ 
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1.5rem',
              marginBottom: '2rem'
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '1.5rem',
                borderRadius: '12px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
                  {leagues.length}
                </div>
                <div style={{ color: '#6b7280', marginTop: '0.5rem' }}>Total Leagues</div>
              </div>
              <div style={{
                backgroundColor: 'white',
                padding: '1.5rem',
                borderRadius: '12px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
                  {leagues.filter(l => l.is_creator).length}
                </div>
                <div style={{ color: '#6b7280', marginTop: '0.5rem' }}>Leagues Created</div>
              </div>
              <div style={{
                backgroundColor: 'white',
                padding: '1.5rem',
                borderRadius: '12px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
                  {leagues.filter(l => !l.is_creator).length}
                </div>
                <div style={{ color: '#6b7280', marginTop: '0.5rem' }}>Leagues Joined</div>
              </div>
            </div>

            {/* Empty state or leagues list */}
            {leagues.length === 0 ? (
              <div style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '3rem',
                textAlign: 'center',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)'
              }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏅</div>
                <h3 style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '600', 
                  color: '#1f2937',
                  marginBottom: '0.5rem'
                }}>
                  No leagues yet
                </h3>
                <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
                  Create your own league or join an existing one to get started!
                </p>
                <div style={{ 
                  display: 'flex', 
                  gap: '1rem', 
                  justifyContent: 'center',
                  flexWrap: 'wrap'
                }}>
                  <button 
                    style={{
                      backgroundColor: '#10b981',
                      color: 'white',
                      border: 'none',
                      padding: '0.75rem 2rem',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                    onClick={() => setShowCreateForm(true)}
                  >
                    Create Your First League
                  </button>
                  <button 
                    style={{
                      backgroundColor: 'transparent',
                      color: '#3b82f6',
                      border: '2px solid #3b82f6',
                      padding: '0.75rem 2rem',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                    onClick={() => setShowJoinForm(true)}
                  >
                    Join a League
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ 
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '1.5rem'
              }}>
                {leagues.map((league) => (
                  <div 
                    key={league.id} 
                    style={{
                      backgroundColor: 'white',
                      borderRadius: '12px',
                      padding: '1.5rem',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
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
                      alignItems: 'start',
                      marginBottom: '1rem',
                      flexWrap: 'wrap',
                      gap: '0.5rem'
                    }}>
                      <h3 style={{ 
                        fontSize: '1.25rem',
                        fontWeight: '600',
                        color: '#1f2937',
                        margin: 0,
                        wordBreak: 'break-word'
                      }}>
                        {league.name}
                      </h3>
                      <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                        {league.is_creator && (
                          <span style={{
                            backgroundColor: '#10b981',
                            color: 'white',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '500'
                          }}>
                            Creator
                          </span>
                        )}
                        {league.is_private && (
                          <span style={{
                            backgroundColor: '#6b7280',
                            color: 'white',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '500'
                          }}>
                            Private
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {league.description && (
                      <p style={{ 
                        color: '#6b7280', 
                        fontSize: '0.9rem',
                        marginBottom: '1rem',
                        lineHeight: '1.4',
                        wordBreak: 'break-word'
                      }}>
                        {league.description}
                      </p>
                    )}
                    
                    <div style={{ 
                      color: '#6b7280',
                      fontSize: '0.9rem',
                      marginBottom: '1rem'
                    }}>
                      👥 {league.participants} / {league.max_participants} participants
                    </div>
                    
                    {league.is_creator && league.join_code && (
                      <div style={{ 
                        backgroundColor: '#f3f4f6',
                        padding: '0.75rem',
                        borderRadius: '6px',
                        marginBottom: '1rem'
                      }}>
                        <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                          Join Code:
                        </div>
                        <code 
                          style={{ 
                            fontSize: '1rem',
                            fontWeight: '600',
                            color: '#1f2937',
                            cursor: 'pointer',
                            wordBreak: 'break-all'
                          }}
                          onClick={() => copyJoinCode(league.join_code!)}
                          title="Click to copy"
                        >
                          {league.join_code}
                        </code>
                      </div>
                    )}
                    
                    <button 
                      style={{
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        padding: '0.75rem 1.5rem',
                        borderRadius: '6px',
                        fontSize: '0.9rem',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        width: '100%'
                      }}
                      onClick={() => handleViewLeaderboard(league)}
                    >
                      View Leaderboard →
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Create League Modal */}
        {showCreateForm && (
          <div style={{ 
            position: 'fixed', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            backgroundColor: 'rgba(0,0,0,0.5)', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            zIndex: 1000 
          }}>
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '12px', 
              padding: '2rem', 
              maxWidth: '500px', 
              width: '90%' 
            }}>
              <h3 style={{ 
                fontSize: '1.5rem',
                fontWeight: 'bold',
                marginBottom: '1.5rem',
                color: '#1f2937'
              }}>
                Create New League
              </h3>
              <form onSubmit={handleCreateLeague}>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    League Name *
                  </label>
                  <input
                    type="text"
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '6px',
                      fontSize: '1rem',
                      transition: 'border-color 0.2s ease'
                    }}
                    value={createForm.name}
                    onChange={(e) => handleCreateFormChange('name', e.target.value)}
                    placeholder="Enter league name"
                    required
                    maxLength={100}
                    onFocus={(e) => e.target.style.borderColor = '#10b981'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  />
                </div>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Description (Optional)
                  </label>
                  <textarea
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '6px',
                      fontSize: '1rem',
                      minHeight: '80px',
                      transition: 'border-color 0.2s ease'
                    }}
                    value={createForm.description}
                    onChange={(e) => handleCreateFormChange('description', e.target.value)}
                    placeholder="Describe your league (optional)"
                    maxLength={500}
                    onFocus={(e) => e.target.style.borderColor = '#10b981'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  />
                </div>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Maximum Participants
                  </label>
                  <select
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '6px',
                      fontSize: '1rem'
                    }}
                    value={createForm.max_participants}
                    onChange={(e) => handleCreateFormChange('max_participants', parseInt(e.target.value))}
                  >
                    <option value={10}>10 participants</option>
                    <option value={20}>20 participants</option>
                    <option value={50}>50 participants</option>
                  </select>
                </div>
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={createForm.is_private}
                      onChange={(e) => handleCreateFormChange('is_private', e.target.checked)}
                      style={{ marginRight: '0.5rem' }}
                    />
                    <span style={{ fontWeight: '500', color: '#374151' }}>
                      Private League (requires join code)
                    </span>
                  </label>
                  {createForm.is_private && (
                    <p style={{ 
                      fontSize: '0.875rem', 
                      color: '#6b7280', 
                      marginTop: '0.5rem',
                      marginLeft: '1.5rem'
                    }}>
                      A unique join code will be generated for inviting members
                    </p>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                  <button 
                    type="button" 
                    style={{
                      padding: '0.75rem 1.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      backgroundColor: 'white',
                      color: '#374151',
                      cursor: 'pointer',
                      fontWeight: '500'
                    }}
                    onClick={() => setShowCreateForm(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: '#10b981',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    Create League
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Join League Modal */}
        {showJoinForm && (
          <div style={{ 
            position: 'fixed', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            backgroundColor: 'rgba(0,0,0,0.5)', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            zIndex: 1000 
          }}>
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '12px', 
              padding: '2rem', 
              maxWidth: '500px', 
              width: '90%' 
            }}>
              <h3 style={{ 
                fontSize: '1.5rem',
                fontWeight: 'bold',
                marginBottom: '1.5rem',
                color: '#1f2937'
              }}>
                Join League
              </h3>
              
              {/* Tab Navigation */}
              <div style={{ 
                display: 'flex', 
                marginBottom: '1.5rem',
                backgroundColor: '#f3f4f6',
                borderRadius: '8px',
                padding: '0.25rem'
              }}>
                <button
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    backgroundColor: joinTab === 'code' ? 'white' : 'transparent',
                    color: joinTab === 'code' ? '#1f2937' : '#6b7280',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onClick={() => setJoinTab('code')}
                >
                  Join Code
                </button>
                <button
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    backgroundColor: joinTab === 'public' ? 'white' : 'transparent',
                    color: joinTab === 'public' ? '#1f2937' : '#6b7280',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onClick={() => {
                    setJoinTab('public');
                    loadPublicLeagues();
                  }}
                >
                  Public Leagues
                </button>
              </div>
              
              {joinTab === 'code' ? (
                <form onSubmit={handleJoinLeague}>
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '0.5rem', 
                      fontWeight: '500',
                      color: '#374151'
                    }}>
                      League Join Code
                    </label>
                    <input
                      type="text"
                      style={{ 
                        width: '100%', 
                        padding: '0.75rem', 
                        border: '2px solid #e5e7eb', 
                        borderRadius: '6px',
                        fontSize: '1rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        transition: 'border-color 0.2s ease'
                      }}
                      value={joinForm.join_code}
                      onChange={(e) => setJoinForm({...joinForm, join_code: e.target.value.toUpperCase()})}
                      placeholder="Enter 8-character code"
                      maxLength={8}
                      onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                      onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                    />
                    <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.5rem' }}>
                      Enter the 8-character code provided by the league creator
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                    <button 
                      type="button" 
                      style={{
                        padding: '0.75rem 1.5rem',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        backgroundColor: 'white',
                        color: '#374151',
                        cursor: 'pointer',
                        fontWeight: '500'
                      }}
                      onClick={() => setShowJoinForm(false)}
                    >
                      Cancel
                    </button>
                    <button 
                      type="submit"
                      style={{
                        padding: '0.75rem 1.5rem',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontWeight: 'bold',
                        cursor: 'pointer'
                      }}
                    >
                      Join League
                    </button>
                  </div>
                </form>
              ) : (
                <div>
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ 
                      fontSize: '1rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '0.5rem'
                    }}>
                      Available Public Leagues
                    </h4>
                    <div style={{ 
                      maxHeight: '300px', 
                      overflowY: 'auto',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px'
                    }}>
                      {publicLeagues.length === 0 ? (
                        <div style={{ 
                          padding: '2rem', 
                          textAlign: 'center', 
                          color: '#6b7280' 
                        }}>
                          No public leagues available
                        </div>
                      ) : (
                        publicLeagues.map((league) => (
                          <div 
                            key={league.id}
                            style={{
                              padding: '1rem',
                              borderBottom: '1px solid #f3f4f6',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center'
                            }}
                          >
                            <div>
                              <h5 style={{ 
                                margin: 0, 
                                fontWeight: '600',
                                color: '#1f2937'
                              }}>
                                {league.name}
                              </h5>
                              {league.description && (
                                <p style={{ 
                                  margin: '0.25rem 0 0 0', 
                                  fontSize: '0.875rem',
                                  color: '#6b7280'
                                }}>
                                  {league.description}
                                </p>
                              )}
                              <p style={{ 
                                margin: '0.25rem 0 0 0', 
                                fontSize: '0.875rem',
                                color: '#6b7280'
                              }}>
                                {league.participants}/{league.max_participants} members
                              </p>
                            </div>
                            <button
                              style={{
                                backgroundColor: '#10b981',
                                color: 'white',
                                border: 'none',
                                padding: '0.5rem 1rem',
                                borderRadius: '4px',
                                fontSize: '0.875rem',
                                fontWeight: '500',
                                cursor: 'pointer'
                              }}
                              onClick={() => handleJoinPublicLeague(league.id, league.name)}
                            >
                              Join
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button 
                      type="button" 
                      style={{
                        padding: '0.75rem 1.5rem',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        backgroundColor: 'white',
                        color: '#374151',
                        cursor: 'pointer',
                        fontWeight: '500'
                      }}
                      onClick={() => setShowJoinForm(false)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyFantasyLeagues;
