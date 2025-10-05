import React, { useState, useEffect } from 'react';
import { transferService, TransferOffer } from '../../services/transferService';

interface Props {
  leagueId: number;
  currentTeamId: number;
}

const TransferOffers: React.FC<Props> = ({ leagueId, currentTeamId }) => {
  const [receivedOffers, setReceivedOffers] = useState<TransferOffer[]>([]);
  const [sentOffers, setSentOffers] = useState<TransferOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'received' | 'sent'>('received');

  useEffect(() => {
    loadOffers();
  }, [leagueId, currentTeamId]);

  const loadOffers = async () => {
    try {
      setLoading(true);
      const [received, sent] = await Promise.all([
        transferService.getTransferOffers(leagueId, currentTeamId, 'received'),
        transferService.getTransferOffers(leagueId, currentTeamId, 'sent'),
      ]);
      setReceivedOffers(received.offers || []);
      setSentOffers(sent.offers || []);
    } catch (err: any) {
      console.error('Error loading offers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (offerId: number) => {
    if (!window.confirm('Accept this transfer offer?')) return;

    try {
      await transferService.acceptTransferOffer(leagueId, offerId);
      alert('Transfer offer accepted!');
      loadOffers();
    } catch (err: any) {
      alert('Failed to accept offer: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleReject = async (offerId: number) => {
    if (!window.confirm('Reject this transfer offer?')) return;

    try {
      await transferService.rejectTransferOffer(leagueId, offerId);
      alert('Transfer offer rejected');
      loadOffers();
    } catch (err: any) {
      alert('Failed to reject offer: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCancel = async (offerId: number) => {
    if (!window.confirm('Cancel this transfer offer?')) return;

    try {
      await transferService.cancelTransferOffer(leagueId, offerId);
      alert('Transfer offer cancelled');
      loadOffers();
    } catch (err: any) {
      alert('Failed to cancel offer: ' + (err.response?.data?.detail || err.message));
    }
  };

  const renderOffer = (offer: TransferOffer, type: 'received' | 'sent') => {
    const isExpired = offer.is_expired;
    const isPending = offer.status === 'pending';

    return (
      <div
        key={offer.id}
        style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          backgroundColor: isExpired ? '#f9fafb' : 'white',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', marginTop: 0 }}>
              {offer.player_requested.name}
            </h4>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              {offer.player_requested.position} • {offer.player_requested.team}
            </div>
          </div>
          <div
            style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '20px',
              fontSize: '0.875rem',
              fontWeight: '500',
              backgroundColor:
                offer.status === 'pending'
                  ? '#fef3c7'
                  : offer.status === 'accepted'
                  ? '#d1fae5'
                  : offer.status === 'rejected'
                  ? '#fee2e2'
                  : '#f3f4f6',
              color:
                offer.status === 'pending'
                  ? '#92400e'
                  : offer.status === 'accepted'
                  ? '#065f46'
                  : offer.status === 'rejected'
                  ? '#991b1b'
                  : '#374151',
            }}
          >
            {offer.status.charAt(0).toUpperCase() + offer.status.slice(1)}
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            {type === 'received' ? 'From' : 'To'}: <strong>{type === 'received' ? offer.from_team.user_name : offer.to_team.user_name}</strong> ({type === 'received' ? offer.from_team.name : offer.to_team.name})
          </div>
          
          {offer.offer_type === 'money' ? (
            <div style={{ fontSize: '0.95rem', marginTop: '0.75rem' }}>
              💰 Offering: <strong style={{ color: '#059669' }}>€{(offer.money_offered! / 1000000).toFixed(1)}M</strong>
            </div>
          ) : (
            offer.player_offered && (
              <div style={{ fontSize: '0.95rem', marginTop: '0.75rem' }}>
                🔄 Offering Player: <strong>{offer.player_offered.name}</strong> ({offer.player_offered.position})
              </div>
            )
          )}
        </div>

        {isPending && !isExpired && (
          <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '1rem' }}>
            Expires {offer.time_until_expiry}
          </div>
        )}

        {isExpired && (
          <div style={{ fontSize: '0.875rem', color: '#dc2626', marginBottom: '1rem' }}>
            ⏰ Expired
          </div>
        )}

        {type === 'received' && isPending && !isExpired && (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={() => handleAccept(offer.id)}
              style={{
                flex: 1,
                padding: '0.75rem',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              ✓ Accept
            </button>
            <button
              onClick={() => handleReject(offer.id)}
              style={{
                flex: 1,
                padding: '0.75rem',
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              ✗ Reject
            </button>
          </div>
        )}

        {type === 'sent' && isPending && !isExpired && (
          <button
            onClick={() => handleCancel(offer.id)}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Cancel Offer
          </button>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Loading offers...</div>
      </div>
    );
  }

  const offers = activeTab === 'received' ? receivedOffers : sentOffers;

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', marginTop: 0 }}>
        Transfer Offers
      </h2>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        Manage your incoming and outgoing transfer offers
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #e5e7eb' }}>
        <button
          onClick={() => setActiveTab('received')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            borderBottom: activeTab === 'received' ? '2px solid #3b82f6' : '2px solid transparent',
            backgroundColor: 'transparent',
            color: activeTab === 'received' ? '#3b82f6' : '#6b7280',
            fontWeight: '600',
            cursor: 'pointer',
          }}
        >
          Received ({receivedOffers.length})
        </button>
        <button
          onClick={() => setActiveTab('sent')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            borderBottom: activeTab === 'sent' ? '2px solid #3b82f6' : '2px solid transparent',
            backgroundColor: 'transparent',
            color: activeTab === 'sent' ? '#3b82f6' : '#6b7280',
            fontWeight: '600',
            cursor: 'pointer',
          }}
        >
          Sent ({sentOffers.length})
        </button>
      </div>

      {/* Offers List */}
      {offers.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '3rem',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
        }}>
          <p style={{ color: '#6b7280' }}>
            No {activeTab === 'received' ? 'received' : 'sent'} offers
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {offers.map((offer) => renderOffer(offer, activeTab))}
        </div>
      )}
    </div>
  );
};

export default TransferOffers;
