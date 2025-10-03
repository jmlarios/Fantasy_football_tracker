import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import leagueService, { League } from '../../services/leagueService';
import { useAuth } from '../../contexts/AuthContext';
import CreateLeagueModal from './CreateLeagueModal';
import JoinLeagueModal from './JoinLeagueModal';
import LeagueCard from './LeagueCard';
import LeaderboardView from './LeaderboardView';
import UpdateLeagueModal from './UpdateLeagueModal';

const LeagueManager: React.FC = () => {
  const { user } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [selectedLeagueForUpdate, setSelectedLeagueForUpdate] = useState<League | null>(null);
  const [selectedLeagueId, setSelectedLeagueId] = useState<number | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    loadLeagues();
  }, []);

  const loadLeagues = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const userLeagues = await leagueService.getUserLeagues();
      setLeagues(userLeagues);
    } catch (err: any) {
      setError('Failed to load your leagues');
      console.error('Error loading leagues:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLeaveLeague = async (leagueId: number) => {
    try {
      await leagueService.leaveLeague(leagueId);
      await loadLeagues(); // Refresh the list
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to leave league');
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleViewLeaderboard = (league: League) => {
    setSelectedLeagueId(league.id);
  };

  const handleUpdateLeague = (league: League) => {
    setSelectedLeagueForUpdate(league);
    setIsUpdateModalOpen(true);
  };

  if (!user) {
    return (
      <>
        <Header />
        <div style={{
          maxWidth: '800px',
          margin: '2rem auto',
          padding: '3rem',
          textAlign: 'center',
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '1rem', color: '#1f2937' }}>
            Login Required
          </h2>
          <p style={{ color: '#6b7280', fontSize: '1.125rem' }}>
            Please log in to manage your fantasy leagues
          </p>
        </div>
      </>
    );
  }

  const Header = () => {
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
            to="/" 
            style={{ 
              color: 'white', 
              textDecoration: 'none',
              fontSize: '1.5rem',
              fontWeight: 'bold'
            }}
          >
            LaLiga Fantasy Tracker
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
                  fontWeight: 'bold',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)'
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

  return (
    <>
      <Header />
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2rem 1rem'
      }}>
      {/* Header */}
      <div style={{
        marginBottom: '2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1f2937',
            margin: '0 0 0.5rem 0'
          }}>
            My Fantasy Leagues
          </h1>
          <p style={{ color: '#6b7280', fontSize: '1rem', margin: 0 }}>
            Compete with friends in fantasy football leagues
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setIsJoinModalOpen(true)}
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#059669')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#10b981')}
          >
            Join League
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2563eb')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#3b82f6')}
          >
            Create League
          </button>
        </div>
      </div>

      {/* Copied notification */}
      {copiedCode && (
        <div style={{
          position: 'fixed',
          top: '2rem',
          right: '2rem',
          backgroundColor: '#10b981',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '8px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          zIndex: 9999,
          fontSize: '0.875rem',
          fontWeight: '600'
        }}>
          Join code copied: {copiedCode}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          color: '#991b1b',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          border: '1px solid #fecaca',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>Error: {error}</span>
          <button
            onClick={loadLeagues}
            style={{
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div style={{
          textAlign: 'center',
          padding: '4rem',
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.06)'
        }}>
          <p style={{ color: '#6b7280', fontSize: '1.125rem' }}>Loading your leagues...</p>
        </div>
      ) : leagues.length === 0 ? (
        /* Empty State */
        <div style={{
          textAlign: 'center',
          padding: '4rem',
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.06)'
        }}>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            color: '#1f2937',
            marginBottom: '1rem' 
          }}>
            No Leagues Yet
          </h2>
          <p style={{ 
            color: '#6b7280', 
            fontSize: '1rem',
            marginBottom: '2rem' 
          }}>
            Create your first league or join an existing one to get started!
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '0.875rem 2rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              Create Your First League
            </button>
            <button
              onClick={() => setIsJoinModalOpen(true)}
              style={{
                backgroundColor: 'white',
                color: '#3b82f6',
                border: '2px solid #3b82f6',
                padding: '0.875rem 2rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              Join a League
            </button>
          </div>
        </div>
      ) : (
        /* Leagues Grid */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: '1.5rem'
        }}>
          {leagues.map((league) => (
            <LeagueCard
              key={league.id}
              league={league}
              onViewLeaderboard={handleViewLeaderboard}
              onLeave={handleLeaveLeague}
              onCopyCode={handleCopyCode}
              onUpdate={handleUpdateLeague}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <CreateLeagueModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={loadLeagues}
      />

      <JoinLeagueModal
        isOpen={isJoinModalOpen}
        onClose={() => setIsJoinModalOpen(false)}
        onSuccess={loadLeagues}
      />

      {selectedLeagueId && (
        <LeaderboardView
          leagueId={selectedLeagueId}
          onClose={() => setSelectedLeagueId(null)}
        />
      )}

      {isUpdateModalOpen && selectedLeagueForUpdate && (
        <UpdateLeagueModal
          isOpen={isUpdateModalOpen}
          league={selectedLeagueForUpdate}
          onClose={() => {
            setIsUpdateModalOpen(false);
            setSelectedLeagueForUpdate(null);
          }}
          onSuccess={loadLeagues}
        />
      )}
      </div>
    </>
  );
};

export default LeagueManager;
