import React from 'react';
import { League } from '../../services/leagueService';

interface LeagueCardProps {
  league: League;
  onViewLeaderboard: (league: League) => void;
  onLeave?: (leagueId: number) => void;
  onCopyCode?: (code: string) => void;
  onUpdate?: (league: League) => void;
}

const LeagueCard: React.FC<LeagueCardProps> = ({ 
  league, 
  onViewLeaderboard, 
  onLeave,
  onCopyCode,
  onUpdate 
}) => {
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '1.25rem',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb'
    }}
    >
      {/* Header */}
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
          <h3 style={{ 
            fontSize: '1.25rem', 
            fontWeight: 'bold', 
            color: '#1f2937',
            margin: 0 
          }}>
            {league.name}
          </h3>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {league.is_creator && (
              <span style={{
                backgroundColor: '#f3f4f6',
                color: '#374151',
                padding: '0.25rem 0.5rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: '500'
              }}>
                Creator
              </span>
            )}
            <span style={{
              backgroundColor: '#f3f4f6',
              color: '#374151',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: '500'
            }}>
              {league.is_private ? 'Private' : 'Public'}
            </span>
          </div>
        </div>

        {league.description && (
          <p style={{ 
            color: '#6b7280', 
            fontSize: '0.875rem',
            margin: '0.5rem 0 0 0'
          }}>
            {league.description}
          </p>
        )}
      </div>

      {/* Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '1rem',
        marginBottom: '1rem',
        padding: '1rem',
        backgroundColor: '#f9fafb',
        borderRadius: '6px'
      }}>
        <div>
          <div style={{ 
            fontSize: '0.75rem', 
            color: '#6b7280', 
            fontWeight: '500',
            marginBottom: '0.25rem' 
          }}>
            Participants
          </div>
          <div style={{ 
            fontSize: '1.25rem', 
            fontWeight: '600',
            color: '#1f2937'
          }}>
            {league.participants} / {league.max_participants}
          </div>
        </div>
        
        <div>
          <div style={{ 
            fontSize: '0.75rem', 
            color: '#6b7280', 
            fontWeight: '500',
            marginBottom: '0.25rem' 
          }}>
            Created
          </div>
          <div style={{ 
            fontSize: '0.875rem', 
            fontWeight: '500',
            color: '#1f2937'
          }}>
            {formatDate(league.created_at)}
          </div>
        </div>
      </div>

      {/* Join Code (if private and creator) */}
      {league.is_private && league.is_creator && league.join_code && (
        <div style={{
          backgroundColor: '#f9fafb',
          padding: '0.75rem',
          borderRadius: '6px',
          marginBottom: '1rem',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ 
            fontSize: '0.75rem', 
            color: '#6b7280', 
            fontWeight: '500',
            marginBottom: '0.25rem' 
          }}>
            Join Code
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center' 
          }}>
            <code style={{ 
              fontSize: '1rem', 
              fontWeight: '600',
              color: '#1f2937',
              fontFamily: 'monospace'
            }}>
              {league.join_code}
            </code>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCopyCode?.(league.join_code!);
              }}
              style={{
                backgroundColor: '#f3f4f6',
                color: '#374151',
                border: '1px solid #d1d5db',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Copy
            </button>
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            window.location.href = `/leagues/${league.id}/team`;
          }}
          style={{
            flex: '1 1 auto',
            backgroundColor: '#8b5cf6',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.25rem',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          View My Team
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onViewLeaderboard(league);
          }}
          style={{
            flex: '1 1 auto',
            backgroundColor: '#6b7280',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.25rem',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          View Leaderboard
        </button>

        {league.is_creator && onUpdate && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onUpdate(league);
            }}
            style={{
              flex: '1 1 auto',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.25rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Update Settings
          </button>
        )}

        {!league.is_creator && onLeave && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (window.confirm(`Are you sure you want to leave "${league.name}"?`)) {
                onLeave(league.id);
              }
            }}
            style={{
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Leave
          </button>
        )}
      </div>
    </div>
  );
};

export default LeagueCard;
