import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { fantasyAPI } from '../../services/api';
import { FantasyTeam, CreateTeamRequest } from '../../types/fantasy';

interface CreateTeamModalProps {
  onClose: () => void;
  onTeamCreated: (team: FantasyTeam) => void;
}

const CreateTeamModal: React.FC<CreateTeamModalProps> = ({ onClose, onTeamCreated }) => {
  const { register, handleSubmit, formState: { errors } } = useForm<CreateTeamRequest>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const onSubmit = async (data: CreateTeamRequest) => {
    setIsLoading(true);
    setError('');
    
    try {
      const newTeam = await fantasyAPI.createTeam(data);
      onTeamCreated(newTeam);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create team');
    } finally {
      setIsLoading(false);
    }
  };

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
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '2rem',
        maxWidth: '500px',
        width: '90%',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem'
        }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: '#1f2937',
            margin: 0
          }}>
            Create New Fantasy Team
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

        <form onSubmit={handleSubmit(onSubmit)}>
          {error && (
            <div style={{
              backgroundColor: '#fef2f2',
              color: '#dc2626',
              padding: '0.75rem',
              borderRadius: '6px',
              marginBottom: '1.5rem',
              border: '1px solid #fecaca',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: '500',
              color: '#374151',
              fontSize: '0.95rem'
            }}>
              Team Name
            </label>
            <input
              {...register('name', {
                required: 'Team name is required',
                minLength: {
                  value: 3,
                  message: 'Team name must be at least 3 characters'
                },
                maxLength: {
                  value: 50,
                  message: 'Team name must be less than 50 characters'
                }
              })}
              type="text"
              style={{
                width: '100%',
                padding: '0.875rem',
                border: '2px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '1rem',
                transition: 'border-color 0.2s ease',
                outline: 'none'
              }}
              placeholder="Enter your team name"
              onFocus={(e) => e.target.style.borderColor = '#10b981'}
              onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
            />
            {errors.name && (
              <p style={{
                color: '#dc2626',
                fontSize: '0.875rem',
                marginTop: '0.5rem',
                fontWeight: '500'
              }}>
                {errors.name.message}
              </p>
            )}
          </div>

          <div style={{
            backgroundColor: '#f9fafb',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem'
          }}>
            <h4 style={{
              fontSize: '1rem',
              fontWeight: '600',
              color: '#1f2937',
              marginBottom: '0.5rem'
            }}>
              Team Setup
            </h4>
            <ul style={{
              margin: 0,
              paddingLeft: '1.2rem',
              color: '#6b7280',
              fontSize: '0.9rem'
            }}>
              <li>Starting budget: €100M</li>
              <li>Maximum 15 players</li>
              <li>Must have: 2 GK, 5 DEF, 5 MID, 3 FWD</li>
              <li>Select 11 players for each matchday</li>
            </ul>
          </div>

          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'flex-end'
          }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                backgroundColor: '#f3f4f6',
                color: '#374151',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                backgroundColor: isLoading ? '#9ca3af' : '#10b981',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s ease'
              }}
            >
              {isLoading ? 'Creating...' : 'Create Team'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTeamModal;
