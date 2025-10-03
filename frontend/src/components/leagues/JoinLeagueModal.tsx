import React, { useState, useEffect } from 'react';
import leagueService, { PublicLeague } from '../../services/leagueService';
import { useAuth } from '../../contexts/AuthContext';

interface JoinLeagueModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const JoinLeagueModal: React.FC<JoinLeagueModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'code' | 'browse'>('code');
  const [joinCode, setJoinCode] = useState('');
  const [publicLeagues, setPublicLeagues] = useState<PublicLeague[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && activeTab === 'browse') {
      loadPublicLeagues();
    }
  }, [isOpen, activeTab]);

  const loadPublicLeagues = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const leagues = await leagueService.getPublicLeagues();
      setPublicLeagues(leagues);
    } catch (err: any) {
      setError('Failed to load public leagues');
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoinByCode = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!user) {
      setError('You must be logged in to join a league');
      return;
    }

    if (!joinCode.trim()) {
      setError('Please enter a join code');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setIsJoining(true);

    try {
      const result = await leagueService.joinLeagueByCode(joinCode.trim());
      setSuccessMessage(`Successfully joined "${result.league_name}"! 🎉`);
      setJoinCode('');
      
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join league');
    } finally {
      setIsJoining(false);
    }
  };

  const handleJoinById = async (leagueId: number, leagueName: string) => {
    if (!user) {
      setError('You must be logged in to join a league');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setIsJoining(true);

    try {
      await leagueService.joinLeagueById(leagueId);
      setSuccessMessage(`Successfully joined "${leagueName}"! 🎉`);
      
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join league');
    } finally {
      setIsJoining(false);
    }
  };

  const handleClose = () => {
    setJoinCode('');
    setError(null);
    setSuccessMessage(null);
    setActiveTab('code');
    onClose();
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  if (!isOpen) return null;

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
    onClick={handleClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          maxWidth: '600px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            color: '#1f2937',
            margin: 0
          }}>
            🚀 Join a League
          </h2>
          <button
            onClick={handleClose}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#6b7280',
              padding: '0.25rem'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#1f2937')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#6b7280')}
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f9fafb'
        }}>
          <button
            onClick={() => setActiveTab('code')}
            style={{
              flex: 1,
              padding: '1rem',
              border: 'none',
              backgroundColor: activeTab === 'code' ? 'white' : 'transparent',
              color: activeTab === 'code' ? '#3b82f6' : '#6b7280',
              fontWeight: '500',
              fontSize: '0.875rem',
              cursor: 'pointer',
              borderBottom: activeTab === 'code' ? '2px solid #3b82f6' : 'none'
            }}
          >
            Join by Code
          </button>
          <button
            onClick={() => setActiveTab('browse')}
            style={{
              flex: 1,
              padding: '1rem',
              border: 'none',
              backgroundColor: activeTab === 'browse' ? 'white' : 'transparent',
              color: activeTab === 'browse' ? '#3b82f6' : '#6b7280',
              fontWeight: '500',
              fontSize: '0.875rem',
              cursor: 'pointer',
              borderBottom: activeTab === 'browse' ? '2px solid #3b82f6' : 'none'
            }}
          >
            Browse Public
          </button>
        </div>

        {/* Messages */}
        <div style={{ padding: '1rem 1.5rem 0 1.5rem' }}>
          {error && (
            <div style={{
              backgroundColor: '#fef2f2',
              color: '#991b1b',
              padding: '0.75rem',
              borderRadius: '6px',
              marginBottom: '1rem',
              fontSize: '0.875rem',
              border: '1px solid #fecaca'
            }}>
              {error}
            </div>
          )}

          {successMessage && (
            <div style={{
              backgroundColor: '#f0fdf4',
              color: '#166534',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontSize: '0.875rem',
              border: '1px solid #bbf7d0'
            }}>
              {successMessage}
            </div>
          )}
        </div>

        {/* Content */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto',
          padding: '0 1.5rem 1.5rem 1.5rem'
        }}>
          {activeTab === 'code' && (
            <form onSubmit={handleJoinByCode}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: '#374151',
                  marginBottom: '0.5rem'
                }}>
                  Enter Join Code
                </label>
                <input
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="e.g., ABC123"
                  maxLength={10}
                  style={{
                    width: '100%',
                    padding: '0.875rem',
                    borderRadius: '8px',
                    border: '2px solid #d1d5db',
                    fontSize: '1.125rem',
                    fontFamily: 'monospace',
                    fontWeight: 'bold',
                    textTransform: 'uppercase',
                    textAlign: 'center',
                    boxSizing: 'border-box'
                  }}
                />
                <p style={{
                  fontSize: '0.75rem',
                  color: '#6b7280',
                  marginTop: '0.5rem',
                  margin: '0.5rem 0 0 0'
                }}>
                  Ask the league creator for their private join code
                </p>
              </div>

              <button
                type="submit"
                disabled={isJoining || !joinCode.trim()}
                style={{
                  width: '100%',
                  padding: '0.875rem',
                  borderRadius: '8px',
                  border: 'none',
                  backgroundColor: isJoining || !joinCode.trim() ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  fontSize: '1rem',
                  fontWeight: 'bold',
                  cursor: isJoining || !joinCode.trim() ? 'not-allowed' : 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (!isJoining && joinCode.trim()) {
                    e.currentTarget.style.backgroundColor = '#2563eb';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isJoining && joinCode.trim()) {
                    e.currentTarget.style.backgroundColor = '#3b82f6';
                  }
                }}
              >
                {isJoining ? 'Joining...' : 'Join League'}
              </button>
            </form>
          )}

          {activeTab === 'browse' && (
            <div>
              {isLoading ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '3rem',
                  color: '#6b7280'
                }}>
                  <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
                  <p>Loading public leagues...</p>
                </div>
              ) : publicLeagues.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '3rem',
                  color: '#6b7280'
                }}>
                  <div style={{ fontSize: '2rem', fontWeight: '600', marginBottom: '1rem', color: '#6b7280' }}>No Leagues</div>
                  <p style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                    No Public Leagues Found
                  </p>
                  <p style={{ fontSize: '0.875rem' }}>
                    Be the first to create a public league!
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {publicLeagues.map((league) => (
                    <div
                      key={league.id}
                      style={{
                        backgroundColor: '#f9fafb',
                        borderRadius: '12px',
                        padding: '1.25rem',
                        border: '1px solid #e5e7eb'
                      }}
                    >
                      <div style={{ marginBottom: '0.75rem' }}>
                        <h3 style={{ 
                          fontSize: '1.125rem', 
                          fontWeight: 'bold', 
                          color: '#1f2937',
                          margin: '0 0 0.5rem 0'
                        }}>
                          {league.name}
                        </h3>
                        {league.description && (
                          <p style={{ 
                            color: '#6b7280', 
                            fontSize: '0.875rem',
                            margin: 0
                          }}>
                            {league.description}
                          </p>
                        )}
                      </div>

                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        paddingTop: '0.75rem',
                        borderTop: '1px solid #e5e7eb'
                      }}>
                        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.875rem' }}>
                          <div>
                            <span style={{ color: '#6b7280' }}>👥 </span>
                            <span style={{ fontWeight: '600', color: '#1f2937' }}>
                              {league.participants}/{league.max_participants}
                            </span>
                          </div>
                          <div>
                            <span style={{ color: '#6b7280' }}>📅 </span>
                            <span style={{ color: '#6b7280' }}>
                              {formatDate(league.created_at)}
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={() => handleJoinById(league.id, league.name)}
                          disabled={isJoining || league.participants >= league.max_participants}
                          style={{
                            backgroundColor: 
                              league.participants >= league.max_participants ? '#e5e7eb' :
                              isJoining ? '#9ca3af' : '#10b981',
                            color: league.participants >= league.max_participants ? '#9ca3af' : 'white',
                            border: 'none',
                            padding: '0.5rem 1.25rem',
                            borderRadius: '6px',
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            cursor: 
                              league.participants >= league.max_participants || isJoining 
                                ? 'not-allowed' 
                                : 'pointer',
                            transition: 'background-color 0.2s'
                          }}
                          onMouseEnter={(e) => {
                            if (league.participants < league.max_participants && !isJoining) {
                              e.currentTarget.style.backgroundColor = '#059669';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (league.participants < league.max_participants && !isJoining) {
                              e.currentTarget.style.backgroundColor = '#10b981';
                            }
                          }}
                        >
                          {league.participants >= league.max_participants ? 'Full' : 'Join'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default JoinLeagueModal;
