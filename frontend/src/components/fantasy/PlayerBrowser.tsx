import React, { useState, useEffect } from 'react';
import { fantasyAPI } from '../../services/api';
import { Player, TeamPlayer } from '../../types/fantasy';

interface PlayerBrowserProps {
  teamId: number;
  remainingBudget: number;
  currentPlayers: TeamPlayer[];
  onClose: () => void;
  onPlayerAdded: () => void;
}

const PlayerBrowser: React.FC<PlayerBrowserProps> = ({
  teamId,
  remainingBudget,
  currentPlayers,
  onClose,
  onPlayerAdded
}) => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedPosition, setSelectedPosition] = useState('');
  const [teams, setTeams] = useState<string[]>([]);

  useEffect(() => {
    loadTeams();
    searchPlayers();
  }, []);

  useEffect(() => {
    searchPlayers();
  }, [searchQuery, selectedTeam, selectedPosition]);

  const loadTeams = async () => {
    try {
      const teamsData = await fantasyAPI.getTeamsInfo();
      setTeams(teamsData.map(t => t.name));
    } catch (err) {
      console.error('Error loading teams:', err);
    }
  };

  const searchPlayers = async () => {
    try {
      setLoading(true);
      const playersData = await fantasyAPI.searchPlayers({
        q: searchQuery || undefined,
        team: selectedTeam || undefined,
        position: selectedPosition || undefined,
        limit: 100
      });
      
      // Filter out players already in the team
      const currentPlayerIds = currentPlayers.map(p => p.id);
      const availablePlayers = playersData.filter(p => !currentPlayerIds.includes(p.id));
      
      setPlayers(availablePlayers);
    } catch (err: any) {
      setError('Failed to load players');
      console.error('Error loading players:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPlayer = async (player: Player) => {
    if (player.price > remainingBudget) {
      alert('Insufficient budget for this player');
      return;
    }

    try {
      await fantasyAPI.addPlayerToTeam(teamId, { player_id: player.id });
      onPlayerAdded();
    } catch (err: any) {
      alert('Failed to add player: ' + (err.response?.data?.detail || err.message));
    }
  };

  const canAffordPlayer = (player: Player) => player.price <= remainingBudget;

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
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '1200px',
        maxHeight: '90vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: '#1f2937',
            margin: 0
          }}>
            Add Players to Team
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#6b7280'
            }}
          >
            ×
          </button>
        </div>

        {/* Budget Info */}
        <div style={{
          padding: '1rem 1.5rem',
          backgroundColor: '#f9fafb',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            gap: '2rem',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Remaining Budget: </span>
              <span style={{ 
                fontSize: '1.1rem', 
                fontWeight: 'bold', 
                color: remainingBudget > 0 ? '#10b981' : '#ef4444'
              }}>
                €{(remainingBudget / 1000000).toFixed(1)}M
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Squad: </span>
              <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#3b82f6' }}>
                {currentPlayers.length}/15
              </span>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div style={{
          padding: '1rem 1.5rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem'
        }}>
          <input
            type="text"
            placeholder="Search players..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.875rem'
            }}
          />
          <select
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.875rem'
            }}
          >
            <option value="">All Positions</option>
            <option value="GK">Goalkeeper</option>
            <option value="DEF">Defender</option>
            <option value="MID">Midfielder</option>
            <option value="FWD">Forward</option>
          </select>
          <select
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '0.875rem'
            }}
          >
            <option value="">All Teams</option>
            {teams.map(team => (
              <option key={team} value={team}>{team}</option>
            ))}
          </select>
        </div>

        {/* Players List */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '1rem'
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              Loading players...
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#ef4444' }}>
              {error}
            </div>
          ) : players.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
              No players found matching your criteria
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '1rem'
            }}>
              {players.map((player) => {
                const affordable = canAffordPlayer(player);
                return (
                  <div
                    key={player.id}
                    style={{
                      backgroundColor: affordable ? 'white' : '#fef2f2',
                      border: `1px solid ${affordable ? '#e5e7eb' : '#fecaca'}`,
                      borderRadius: '8px',
                      padding: '1rem',
                      opacity: affordable ? 1 : 0.7
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
                        </h4>
                        <p style={{
                          margin: 0,
                          fontSize: '0.875rem',
                          color: '#6b7280'
                        }}>
                          {player.team} • {player.position}
                        </p>
                      </div>
                      <div style={{
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: affordable ? '#059669' : '#ef4444'
                      }}>
                        €{(player.price / 1000000).toFixed(1)}M
                      </div>
                    </div>

                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '1rem',
                      fontSize: '0.875rem',
                      color: '#6b7280'
                    }}>
                      <span>Goals: {player.goals}</span>
                      <span>Assists: {player.assists}</span>
                    </div>

                    <button
                      onClick={() => handleAddPlayer(player)}
                      disabled={!affordable}
                      style={{
                        width: '100%',
                        backgroundColor: affordable ? '#10b981' : '#d1d5db',
                        color: 'white',
                        border: 'none',
                        padding: '0.5rem',
                        borderRadius: '6px',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        cursor: affordable ? 'pointer' : 'not-allowed'
                      }}
                    >
                      {affordable ? 'Add to Team' : 'Cannot Afford'}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerBrowser;
