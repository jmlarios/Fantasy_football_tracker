import React, { useState } from 'react';
import leagueService, { League } from '../../services/leagueService';

interface UpdateLeagueModalProps {
  isOpen: boolean;
  league: League;
  onClose: () => void;
  onSuccess: () => void;
}

const UpdateLeagueModal: React.FC<UpdateLeagueModalProps> = ({ isOpen, league, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: league.name,
    description: league.description || '',
    max_participants: league.max_participants
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('League name is required');
      return;
    }

    if (formData.max_participants < league.participants) {
      setError(`Max participants cannot be less than current participants (${league.participants})`);
      return;
    }

    if (formData.max_participants < 2 || formData.max_participants > 100) {
      setError('Max participants must be between 2 and 100');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await leagueService.updateLeague(league.id, {
        name: formData.name,
        description: formData.description || undefined,
        max_participants: formData.max_participants
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to update league');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    const confirmMessage = `Are you sure you want to permanently delete "${league.name}"?\n\nThis will:\n• Remove all participants from the league\n• Delete all league data permanently\n• Cannot be undone\n\nType "DELETE" to confirm.`;
    
    const userInput = window.prompt(confirmMessage);
    
    if (userInput !== 'DELETE') {
      if (userInput !== null) {
        setError('Delete cancelled. You must type "DELETE" to confirm.');
      }
      return;
    }

    setError(null);
    setIsDeleting(true);

    try {
      await leagueService.deleteLeague(league.id);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete league');
    } finally {
      setIsDeleting(false);
    }
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
    onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          maxWidth: '500px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
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
            Update League Settings
          </h2>
          <button
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#6b7280',
              padding: '0.25rem'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#1f2937'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#6b7280'}
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          {error && (
            <div style={{
              backgroundColor: '#fef2f2',
              color: '#991b1b',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontSize: '0.875rem',
              border: '1px solid #fecaca'
            }}>
              {error}
            </div>
          )}

          {/* League Name */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '0.5rem'
            }}>
              League Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter league name..."
              maxLength={100}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid #d1d5db',
                fontSize: '1rem',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Description */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '0.5rem'
            }}>
              Description (Optional)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe your league..."
              rows={3}
              maxLength={500}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid #d1d5db',
                fontSize: '1rem',
                resize: 'vertical',
                fontFamily: 'inherit',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Max Participants */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '0.5rem'
            }}>
              Max Participants: {formData.max_participants}
            </label>
            <input
              type="range"
              min={league.participants}
              max="100"
              value={formData.max_participants}
              onChange={(e) => setFormData({ ...formData, max_participants: parseInt(e.target.value) })}
              style={{
                width: '100%',
                cursor: 'pointer'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.75rem',
              color: '#6b7280',
              marginTop: '0.25rem'
            }}>
              <span>{league.participants} (current)</span>
              <span>100</span>
            </div>
          </div>

          {/* Info about private/public */}
          <div style={{
            backgroundColor: '#eff6ff',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            color: '#1e40af'
          }}>
            <strong>Note:</strong> Privacy settings cannot be changed after league creation.
          </div>

          {/* Delete Warning */}
          <div style={{
            backgroundColor: '#fef2f2',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            color: '#991b1b',
            border: '1px solid #fecaca'
          }}>
            <strong>Danger Zone:</strong> Deleting this league will permanently remove all participants and league data. This action cannot be undone.
          </div>

          {/* Actions */}
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column',
            gap: '0.75rem',
            paddingTop: '1rem',
            borderTop: '1px solid #e5e7eb'
          }}>
            {/* Update/Cancel buttons */}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting || isDeleting}
                style={{
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  color: '#374151',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  cursor: (isSubmitting || isDeleting) ? 'not-allowed' : 'pointer',
                  opacity: (isSubmitting || isDeleting) ? 0.5 : 1
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || isDeleting}
                style={{
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  borderRadius: '8px',
                  border: 'none',
                  backgroundColor: (isSubmitting || isDeleting) ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  cursor: (isSubmitting || isDeleting) ? 'not-allowed' : 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (!isSubmitting && !isDeleting) e.currentTarget.style.backgroundColor = '#2563eb';
                }}
                onMouseLeave={(e) => {
                  if (!isSubmitting && !isDeleting) e.currentTarget.style.backgroundColor = '#3b82f6';
                }}
              >
                {isSubmitting ? 'Updating...' : 'Update League'}
              </button>
            </div>

            {/* Delete button */}
            <button
              type="button"
              onClick={handleDelete}
              disabled={isSubmitting || isDeleting}
              style={{
                width: '100%',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: (isSubmitting || isDeleting) ? '#9ca3af' : '#dc2626',
                color: 'white',
                fontSize: '0.875rem',
                fontWeight: '600',
                cursor: (isSubmitting || isDeleting) ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!isSubmitting && !isDeleting) e.currentTarget.style.backgroundColor = '#b91c1c';
              }}
              onMouseLeave={(e) => {
                if (!isSubmitting && !isDeleting) e.currentTarget.style.backgroundColor = '#dc2626';
              }}
            >
              {isDeleting ? 'Deleting...' : 'Delete League Permanently'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UpdateLeagueModal;
