import React, { useState, useEffect } from 'react';
import { transferService, LeagueTeam, Player } from '../../services/transferService';

interface Props {
  leagueId: number;
  currentTeamId: number;
}

const UserTransferMarket: React.FC<Props> = ({ leagueId, currentTeamId }) => {
  const [teams, setTeams] = useState<LeagueTeam[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<LeagueTeam | null>(null);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [offerType, setOfferType] = useState<'money' | 'player_exchange'>('money');
  const [moneyOffer, setMoneyOffer] = useState('');
  const [playerExchange, setPlayerExchange] = useState<Player | null>(null);
  const [playerOut, setPlayerOut] = useState<Player | null>(null); // Player to drop for money offers
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [myPlayers, setMyPlayers] = useState<Player[]>([]);

  useEffect(() => {
    loadTeams();
  }, [leagueId]);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const response = await transferService.getLeagueTeams(leagueId);
      // Filter out current user's team using is_current_user flag
      const otherTeams = response.teams.filter((t: LeagueTeam) => !t.is_current_user);
      const currentTeam = response.teams.find((t: LeagueTeam) => t.is_current_user);
      
      setTeams(otherTeams);
      if (currentTeam) {
        setMyPlayers(currentTeam.players || []);
      }
    } catch (err: any) {
      setError('Failed to load teams: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOffer = async () => {
    if (!selectedTeam || !selectedPlayer) return;

    if (offerType === 'money') {
      if (!moneyOffer || parseFloat(moneyOffer) <= 0) {
        alert('Please enter a valid money offer');
        return;
      }
      if (!playerOut) {
        alert('Please select a player to drop from your squad');
        return;
      }
    }

    if (offerType === 'player_exchange' && !playerExchange) {
      alert('Please select a player to exchange');
      return;
    }

    try {
      setSubmitting(true);
      const result = await transferService.createTransferOffer(leagueId, {
        to_team_id: selectedTeam.id,
        player_id: selectedPlayer.id,
        offer_type: offerType,
        money_offered: offerType === 'money' ? parseFloat(moneyOffer) : undefined,
        player_offered_id: offerType === 'player_exchange' ? playerExchange?.id : undefined,
        player_out_id: offerType === 'money' ? playerOut?.id : undefined,
      });

      // Check if the result indicates success
      if (result.success === false) {
        const errors = result.errors || ['Unknown error'];
        alert('Failed to create offer: ' + errors.join(', '));
        return;
      }

      alert('Transfer offer sent successfully!');
      setSelectedTeam(null);
      setSelectedPlayer(null);
      setMoneyOffer('');
      setPlayerExchange(null);
    } catch (err: any) {
      alert('Failed to create offer: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Loading teams...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', marginTop: 0 }}>
        User Transfer Market
      </h2>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        Make offers to buy players from other teams in your league
      </p>

      {error && (
        <div style={{
          backgroundColor: '#fee',
          color: '#c00',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
        }}>
          {error}
        </div>
      )}

      {teams.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '3rem',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
        }}>
          <p style={{ color: '#6b7280' }}>No other teams in this league yet</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {/* Team Selection */}
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.75rem' }}>
              Select Team
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
              {teams.map((team) => (
                <button
                  key={team.id}
                  onClick={() => {
                    setSelectedTeam(team);
                    setSelectedPlayer(null);
                  }}
                  style={{
                    padding: '1rem',
                    border: selectedTeam?.id === team.id ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                    borderRadius: '8px',
                    backgroundColor: selectedTeam?.id === team.id ? '#eff6ff' : 'white',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{team.team_name}</div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>{team.user_name}</div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.5rem' }}>
                    {team.players?.length || 0} players
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Player Selection */}
          {selectedTeam && (
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.75rem' }}>
                Select Player from {selectedTeam.team_name}
              </h3>
              {selectedTeam.players && selectedTeam.players.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                  {selectedTeam.players.map((player) => (
                    <button
                      key={player.id}
                      onClick={() => setSelectedPlayer(player)}
                      style={{
                        padding: '1rem',
                        border: selectedPlayer?.id === player.id ? '2px solid #10b981' : '1px solid #e5e7eb',
                        borderRadius: '8px',
                        backgroundColor: selectedPlayer?.id === player.id ? '#f0fdf4' : 'white',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <div style={{ fontWeight: '600' }}>{player.name}</div>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {player.position} • {player.team}
                      </div>
                      <div style={{ fontSize: '0.875rem', color: '#059669', marginTop: '0.5rem', fontWeight: '600' }}>
                        €{(player.price / 1000000).toFixed(1)}M
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                  <p style={{ color: '#6b7280' }}>This team has no players</p>
                </div>
              )}
            </div>
          )}

          {/* Offer Configuration */}
          {selectedPlayer && (
            <div style={{
              padding: '1.5rem',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              backgroundColor: 'white',
            }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem' }}>
                Create Offer for {selectedPlayer.name}
              </h3>

              {/* Offer Type */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: '500', marginBottom: '0.5rem' }}>
                  Offer Type
                </label>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    onClick={() => setOfferType('money')}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      border: offerType === 'money' ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                      borderRadius: '8px',
                      backgroundColor: offerType === 'money' ? '#eff6ff' : 'white',
                      cursor: 'pointer',
                      fontWeight: '600',
                    }}
                  >
                    💰 Money Offer
                  </button>
                  <button
                    onClick={() => setOfferType('player_exchange')}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      border: offerType === 'player_exchange' ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                      borderRadius: '8px',
                      backgroundColor: offerType === 'player_exchange' ? '#eff6ff' : 'white',
                      cursor: 'pointer',
                      fontWeight: '600',
                    }}
                  >
                    🔄 Player Exchange
                  </button>
                </div>
              </div>

              {/* Money Offer Input */}
              {offerType === 'money' && (
                <>
                  <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', fontWeight: '500', marginBottom: '0.5rem' }}>
                      Offer Amount (€)
                    </label>
                    <input
                      type="number"
                      value={moneyOffer}
                      onChange={(e) => setMoneyOffer(e.target.value)}
                      placeholder="e.g., 5000000 for 5M"
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '1rem',
                      }}
                    />
                    {moneyOffer && (
                      <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        = €{(parseFloat(moneyOffer) / 1000000).toFixed(1)}M
                      </div>
                    )}
                  </div>

                  <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', fontWeight: '500', marginBottom: '0.5rem' }}>
                      Select Player to Drop from Your Squad
                    </label>
                    {myPlayers.length > 0 ? (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
                        {myPlayers.map((player) => (
                          <button
                            key={player.id}
                            onClick={() => setPlayerOut(player)}
                            style={{
                              padding: '0.75rem',
                              border: playerOut?.id === player.id ? '2px solid #ef4444' : '1px solid #e5e7eb',
                              borderRadius: '8px',
                              backgroundColor: playerOut?.id === player.id ? '#fef2f2' : 'white',
                              cursor: 'pointer',
                              textAlign: 'left',
                            }}
                          >
                            <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{player.name}</div>
                            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                              {player.position} • €{(player.price / 1000000).toFixed(1)}M
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
                        <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>You have no players to drop</p>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Player Exchange Selection */}
              {offerType === 'player_exchange' && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontWeight: '500', marginBottom: '0.5rem' }}>
                    Select Your Player to Offer
                  </label>
                  {myPlayers.length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
                      {myPlayers.map((player) => (
                        <button
                          key={player.id}
                          onClick={() => setPlayerExchange(player)}
                          style={{
                            padding: '0.75rem',
                            border: playerExchange?.id === player.id ? '2px solid #10b981' : '1px solid #e5e7eb',
                            borderRadius: '8px',
                            backgroundColor: playerExchange?.id === player.id ? '#f0fdf4' : 'white',
                            cursor: 'pointer',
                            textAlign: 'left',
                          }}
                        >
                          <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{player.name}</div>
                          <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                            {player.position} • €{(player.price / 1000000).toFixed(1)}M
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
                      <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>You have no players to offer</p>
                    </div>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <button
                onClick={handleCreateOffer}
                disabled={submitting}
                style={{
                  width: '100%',
                  padding: '1rem',
                  backgroundColor: submitting ? '#9ca3af' : '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                }}
              >
                {submitting ? 'Sending Offer...' : 'Send Transfer Offer'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UserTransferMarket;
