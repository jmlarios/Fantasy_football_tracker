import React, { useState } from 'react';
import leagueService, { LeagueData } from '../../services/leagueService';
import { useAuth } from '../../contexts/AuthContext';

interface CreateLeagueModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CreateLeagueModal: React.FC<CreateLeagueModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState<LeagueData>({
    name: '',
    description: '',
    is_private: false,
    max_participants: 10
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!user) {
      setError('You must be logged in to create a league');
      return;
    }

    // Validation
    if (!formData.name.trim()) {
      setError('League name is required');
      return;
    }

    if (formData.max_participants < 2 || formData.max_participants > 100) {
      setError('Max participants must be between 2 and 100');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await leagueService.createLeague(formData);
      
      // Reset form
      setFormData({
        name: '',
        description: '',
        is_private: false,
        max_participants: 10
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create league');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      is_private: false,
      max_participants: 10
    });
    setError(null);
    onClose();
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
          borderRadius: '8px',
          maxWidth: '500px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '1.25rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ 
            fontSize: '1.25rem', 
            fontWeight: '600', 
            color: '#1f2937',
            margin: 0
          }}>
            Create New League
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
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '1.25rem' }}>
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
              min="2"
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
              <span>2</span>
              <span>100</span>
            </div>
          </div>

          {/* Privacy Setting */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              padding: '1rem',
              backgroundColor: '#f9fafb',
              borderRadius: '6px',
              border: '1px solid #d1d5db'
            }}>
              <input
                type="checkbox"
                checked={formData.is_private}
                onChange={(e) => setFormData({ ...formData, is_private: e.target.checked })}
                style={{
                  width: '1.125rem',
                  height: '1.125rem',
                  cursor: 'pointer',
                  marginRight: '0.75rem'
                }}
              />
              <div>
                <div style={{ 
                  fontWeight: '500', 
                  color: '#1f2937',
                  fontSize: '0.875rem' 
                }}>
                  {formData.is_private ? 'Private League' : 'Public League'}
                </div>
                <div style={{ 
                  fontSize: '0.75rem', 
                  color: '#6b7280',
                  marginTop: '0.25rem' 
                }}>
                  {formData.is_private 
                    ? 'Only users with the join code can join'
                    : 'Anyone can find and join this league'
                  }
                </div>
              </div>
            </label>
          </div>

          {/* Actions */}
          <div style={{ 
            display: 'flex', 
            gap: '0.75rem',
            paddingTop: '1rem',
            borderTop: '1px solid #e5e7eb'
          }}>
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              style={{
                flex: 1,
                padding: '0.75rem 1.25rem',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                color: '#374151',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                opacity: isSubmitting ? 0.5 : 1
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                flex: 1,
                padding: '0.75rem 1.25rem',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: isSubmitting ? '#9ca3af' : '#3b82f6',
                color: 'white',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: isSubmitting ? 'not-allowed' : 'pointer'
              }}
            >
              {isSubmitting ? 'Creating...' : 'Create League'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateLeagueModal;
