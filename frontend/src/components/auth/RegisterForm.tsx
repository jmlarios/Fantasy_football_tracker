import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../contexts/AuthContext';
import { RegisterRequest } from '../../types/auth';

interface RegisterFormData extends RegisterRequest {
  confirmPassword: string;
}

const RegisterForm: React.FC = () => {
  const { register: registerUser } = useAuth();
  const { register, handleSubmit, formState: { errors }, watch } = useForm<RegisterFormData>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const password = watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError('');
    
    try {
      await registerUser(data.name, data.email, data.password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ 
        fontSize: '1.8rem',
        fontWeight: 'bold',
        marginBottom: '0.5rem',
        color: '#1f2937'
      }}>
        Create Account
      </h2>
      <p style={{ 
        color: '#6b7280', 
        marginBottom: '2rem',
        fontSize: '1rem'
      }}>
        Join thousands of LaLiga fantasy managers!
      </p>
      
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
            Full Name
          </label>
          <input
            {...register('name', { 
              required: 'Name is required',
              minLength: {
                value: 2,
                message: 'Name must be at least 2 characters'
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
            placeholder="Enter your full name"
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

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.5rem', 
            fontWeight: '500',
            color: '#374151',
            fontSize: '0.95rem'
          }}>
            Email Address
          </label>
          <input
            {...register('email', { 
              required: 'Email is required',
              pattern: {
                value: /^\S+@\S+$/i,
                message: 'Invalid email address'
              }
            })}
            type="email"
            style={{ 
              width: '100%', 
              padding: '0.875rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '6px',
              fontSize: '1rem',
              transition: 'border-color 0.2s ease',
              outline: 'none'
            }}
            placeholder="Enter your email"
            onFocus={(e) => e.target.style.borderColor = '#10b981'}
            onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
          />
          {errors.email && (
            <p style={{ 
              color: '#dc2626', 
              fontSize: '0.875rem', 
              marginTop: '0.5rem',
              fontWeight: '500'
            }}>
              {errors.email.message}
            </p>
          )}
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.5rem', 
            fontWeight: '500',
            color: '#374151',
            fontSize: '0.95rem'
          }}>
            Password
          </label>
          <input
            {...register('password', { 
              required: 'Password is required',
              minLength: {
                value: 6,
                message: 'Password must be at least 6 characters'
              }
            })}
            type="password"
            style={{ 
              width: '100%', 
              padding: '0.875rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '6px',
              fontSize: '1rem',
              transition: 'border-color 0.2s ease',
              outline: 'none'
            }}
            placeholder="Choose a strong password"
            onFocus={(e) => e.target.style.borderColor = '#10b981'}
            onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
          />
          {errors.password && (
            <p style={{ 
              color: '#dc2626', 
              fontSize: '0.875rem', 
              marginTop: '0.5rem',
              fontWeight: '500'
            }}>
              {errors.password.message}
            </p>
          )}
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.5rem', 
            fontWeight: '500',
            color: '#374151',
            fontSize: '0.95rem'
          }}>
            Confirm Password
          </label>
          <input
            {...register('confirmPassword', { 
              required: 'Please confirm your password',
              validate: value => value === password || 'Passwords do not match'
            })}
            type="password"
            style={{ 
              width: '100%', 
              padding: '0.875rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '6px',
              fontSize: '1rem',
              transition: 'border-color 0.2s ease',
              outline: 'none'
            }}
            placeholder="Confirm your password"
            onFocus={(e) => e.target.style.borderColor = '#10b981'}
            onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
          />
          {errors.confirmPassword && (
            <p style={{ 
              color: '#dc2626', 
              fontSize: '0.875rem', 
              marginTop: '0.5rem',
              fontWeight: '500'
            }}>
              {errors.confirmPassword.message}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          style={{ 
            width: '100%', 
            padding: '0.875rem', 
            backgroundColor: isLoading ? '#9ca3af' : '#10b981', 
            color: 'white', 
            border: 'none', 
            borderRadius: '6px', 
            fontSize: '1rem',
            fontWeight: '600',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s ease'
          }}
          onMouseOver={(e) => {
            if (!isLoading) e.currentTarget.style.backgroundColor = '#059669';
          }}
          onMouseOut={(e) => {
            if (!isLoading) e.currentTarget.style.backgroundColor = '#10b981';
          }}
        >
          {isLoading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>
    </div>
  );
};

export default RegisterForm;
