import React, { useState, useEffect } from 'react';
import { transferService, Player } from '../../services/transferService';

interface FreeAgentTransferProps {
  leagueId: number;
  currentTeamId: number;
}

const FreeAgentTransfer: React.FC<FreeAgentTransferProps> = ({ leagueId, currentTeamId }) => {
  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [myPlayers, setMyPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [position, setPosition] = useState('');
  const [search, setSearch] = useState('');

  const [selectedPlayerIn, setSelectedPlayerIn] = useState<Player | null>(null);
  const [selectedPlayerOut, setSelectedPlayerOut] = useState<Player | null>(null);
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    loadData();
  }, [leagueId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const myTeamResponse = await fetch(`http://localhost:5000/leagues/${leagueId}/my-team`, {
        credentials: 'include',
      });
      const myTeamData = await myTeamResponse.json();
      setMyPlayers(myTeamData.players || []);

      await loadAvailablePlayers();
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailablePlayers = async () => {
    try {
      const filters: any = {};
      if (position) filters.position = position;
      if (search) filters.search = search;

      const response = await transferService.getAvailablePlayers(leagueId, filters);
      setAvailablePlayers(response.players || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load available players');
    }
  };

  const handleTransferClick = (player: Player) => {
    setSelectedPlayerIn(player);
    setShowDialog(true);
  };

  const handleExecuteTransfer = async () => {
    if (!selectedPlayerIn || !currentTeamId) return;

    // Only require selectedPlayerOut if team has 11 players
    const squadSize = myPlayers.length;
    if (squadSize >= 11 && !selectedPlayerOut) {
      setError('You must select a player to drop (team has 11 players)');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await transferService.executeFreeAgentTransfer(
        leagueId,
        currentTeamId,
        selectedPlayerIn.id,
        selectedPlayerOut?.id // Will be undefined if not selected
      );

      if (result.success) {
        setSuccess(result.message || 'Transfer completed successfully!');
        setShowDialog(false);
        setSelectedPlayerIn(null);
        setSelectedPlayerOut(null);
        await loadData();
      } else {
        setError(result.errors?.join(', ') || 'Transfer failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute transfer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginTop: 0, color: '#1f2937' }}>Free Agent Market</h2>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        Buy players not owned by any team in your league
      </p>

      {error && (
        <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '1rem', borderRadius: '6px', marginBottom: '1rem' }}>
          {error}
          <button onClick={() => setError(null)} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
        </div>
      )}

      {success && (
        <div style={{ backgroundColor: '#d1fae5', color: '#065f46', padding: '1rem', borderRadius: '6px', marginBottom: '1rem' }}>
          {success}
          <button onClick={() => setSuccess(null)} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Position</label>
          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #d1d5db' }}
          >
            <option value="">All</option>
            <option value="GK">Goalkeeper</option>
            <option value="DEF">Defender</option>
            <option value="MID">Midfielder</option>
            <option value="FWD">Forward</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Search</label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Player name..."
            style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #d1d5db' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'end' }}>
          <button
            onClick={loadAvailablePlayers}
            style={{
              width: '100%',
              padding: '0.5rem 1rem',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            Apply Filters
          </button>
        </div>
      </div>

      {/* Available Players */}
      {loading && !showDialog ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>Loading...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
          {availablePlayers.map((player) => (
            <div
              key={player.id}
              style={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '1rem'
              }}
            >
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>{player.name}</h3>
              <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>{player.team}</p>
              <div style={{ margin: '0.75rem 0' }}>
                <span style={{
                  display: 'inline-block',
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#dbeafe',
                  color: '#1e40af',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  marginRight: '0.5rem'
                }}>
                  {player.position}
                </span>
                <span style={{
                  display: 'inline-block',
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#fef3c7',
                  color: '#92400e',
                  borderRadius: '4px',
                  fontSize: '0.85rem'
                }}>
                  €{player.price.toFixed(1)}M
                </span>
              </div>
              <button
                onClick={() => handleTransferClick(player)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Buy Player
              </button>
            </div>
          ))}
        </div>
      )}

      {availablePlayers.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
          No available players found
        </div>
      )}

      {/* Transfer Dialog */}
      {showDialog && (
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
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h2 style={{ marginTop: 0 }}>Complete Transfer</h2>

            {selectedPlayerIn && (
              <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Player In:</p>
                <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem' }}>
                  <h3 style={{ margin: 0 }}>{selectedPlayerIn.name}</h3>
                  <p style={{ margin: '0.5rem 0 0 0', color: '#6b7280' }}>
                    {selectedPlayerIn.team} • {selectedPlayerIn.position} • €{selectedPlayerIn.price.toFixed(1)}M
                  </p>
                </div>
              </div>
            )}

            <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>
              {myPlayers.length >= 11 
                ? 'Select Player to Drop (Required - Team has 11 players):' 
                : `Select Player to Drop (Optional - Team has ${myPlayers.length} players):`
              }
            </p>
            <div style={{ display: 'grid', gap: '0.5rem', marginBottom: '1rem' }}>
              {myPlayers.map((player) => (
                <div
                  key={player.id}
                  onClick={() => setSelectedPlayerOut(player)}
                  style={{
                    border: `2px solid ${selectedPlayerOut?.id === player.id ? '#3b82f6' : '#e5e7eb'}`,
                    borderRadius: '8px',
                    padding: '1rem',
                    cursor: 'pointer',
                    backgroundColor: selectedPlayerOut?.id === player.id ? '#eff6ff' : 'white'
                  }}
                >
                  <h4 style={{ margin: 0 }}>{player.name}</h4>
                  <p style={{ margin: '0.5rem 0 0 0', color: '#6b7280', fontSize: '0.9rem' }}>
                    {player.team} • {player.position} • €{player.price.toFixed(1)}M
                  </p>
                </div>
              ))}
            </div>

            {selectedPlayerIn && (
              <div style={{ backgroundColor: '#dbeafe', padding: '1rem', borderRadius: '6px', marginBottom: '1rem' }}>
                <strong>Net Cost:</strong> €{selectedPlayerOut 
                  ? (selectedPlayerIn.price - selectedPlayerOut.price).toFixed(1)
                  : selectedPlayerIn.price.toFixed(1)
                }M
              </div>
            )}

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowDialog(false)}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteTransfer}
                disabled={loading || (myPlayers.length >= 11 && !selectedPlayerOut)}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: (loading || (myPlayers.length >= 11 && !selectedPlayerOut)) ? '#9ca3af' : '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: (loading || (myPlayers.length >= 11 && !selectedPlayerOut)) ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold'
                }}
              >
                {loading ? 'Processing...' : 'Confirm Transfer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FreeAgentTransfer;
