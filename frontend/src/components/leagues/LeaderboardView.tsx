import React, { useEffect, useState } from 'react';
import leagueService, { LeaderboardData } from '../../services/leagueService';

interface LeaderboardViewProps {
  leagueId: number;
  onClose: () => void;
}

const LeaderboardView: React.FC<LeaderboardViewProps> = ({ leagueId, onClose }) => {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLeaderboard();
  }, [leagueId]);

  const loadLeaderboard = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const leaderboardData = await leagueService.getLeagueLeaderboard(leagueId);
      setData(leaderboardData);
    } catch (err: any) {
      setError(err.message || 'Failed to load leaderboard');
    } finally {
      setIsLoading(false);
    }
  };

  const getMedalEmoji = (rank: number): string => {
    switch (rank) {
      case 1: return '🥇';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return '🏅';
    }
  };

  if (isLoading) {
    return (
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
      }}
      onClick={onClose}
      >
        <div
          style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '3rem',
            textAlign: 'center',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⏳</div>
          <p style={{ color: '#6b7280', fontSize: '1.125rem' }}>Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
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
      }}
      onClick={onClose}
      >
        <div
          style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '2rem',
            maxWidth: '400px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ 
            backgroundColor: '#fef2f2',
            color: '#991b1b',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            border: '1px solid #fecaca'
          }}>
            {error}
          </div>
          <button
            onClick={onClose}
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#3b82f6',
              color: 'white',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
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
      zIndex: 1000,
      padding: '1rem'
    }}
    onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          maxWidth: '800px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h2 style={{ 
                fontSize: '1.75rem', 
                fontWeight: 'bold', 
                color: 'white',
                margin: '0 0 0.5rem 0'
              }}>
                {data.league.name}
              </h2>
              {data.league.description && (
                <p style={{ 
                  color: 'rgba(255, 255, 255, 0.9)', 
                  fontSize: '0.875rem',
                  margin: 0
                }}>
                  {data.league.description}
                </p>
              )}
              <div style={{ 
                marginTop: '0.75rem',
                color: 'rgba(255, 255, 255, 0.9)',
                fontSize: '0.875rem'
              }}>
                {data.league.participants} / {data.league.max_participants} participants
              </div>
            </div>
            <button
              onClick={onClose}
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                fontSize: '1.5rem',
                cursor: 'pointer',
                color: 'white',
                padding: '0.25rem 0.5rem',
                borderRadius: '6px'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)')}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Leaderboard */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
          {data.leaderboard.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '3rem',
              color: '#6b7280'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
              <p style={{ fontSize: '1.125rem', fontWeight: '600' }}>
                No scores yet
              </p>
              <p style={{ fontSize: '0.875rem' }}>
                Scores will appear once matchdays are processed
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {data.leaderboard.map((entry) => (
                <div
                  key={entry.team_id}
                  style={{
                    backgroundColor: entry.is_current_user ? '#eff6ff' : '#f9fafb',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    border: entry.is_current_user ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    transition: 'transform 0.2s',
                    cursor: 'default'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateX(4px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateX(0)';
                  }}
                >
                  {/* Rank */}
                  <div style={{
                    minWidth: '3rem',
                    textAlign: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold'
                  }}>
                    {getMedalEmoji(entry.rank)}
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#6b7280',
                      fontWeight: '600'
                    }}>
                      #{entry.rank}
                    </div>
                  </div>

                  {/* User & Team Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontSize: '1.125rem',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      marginBottom: '0.25rem'
                    }}>
                      {entry.team_name}
                      {entry.is_current_user && (
                        <span style={{
                          marginLeft: '0.5rem',
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          fontSize: '0.75rem',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          fontWeight: '600'
                        }}>
                          YOU
                        </span>
                      )}
                    </div>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#6b7280'
                    }}>
                      {entry.user_name}
                    </div>
                  </div>

                  {/* Points */}
                  <div style={{
                    minWidth: '5rem',
                    textAlign: 'right'
                  }}>
                    <div style={{
                      fontSize: '1.75rem',
                      fontWeight: 'bold',
                      color: entry.rank === 1 ? '#f59e0b' : entry.rank === 2 ? '#9ca3af' : entry.rank === 3 ? '#d97706' : '#1f2937'
                    }}>
                      {entry.total_points}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: '#6b7280',
                      fontWeight: '600'
                    }}>
                      points
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer with user rank if applicable */}
        {data.user_rank && (
          <div style={{
            padding: '1rem 1.5rem',
            borderTop: '2px solid #e5e7eb',
            backgroundColor: '#f9fafb'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#374151'
            }}>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LeaderboardView;
