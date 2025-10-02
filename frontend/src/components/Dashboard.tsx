import React from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const handleNavigation = (path: string): void => {
    navigate(path);
  };

  return (
    <div className="container-fluid py-4" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <div className="row">
        <div className="col-12">
          <div className="text-center mb-5">
            <h1 className="display-4 fw-bold text-dark mb-3">
              Welcome back, Jose Maria Larios Madrid! 👋
            </h1>
            <p className="lead text-muted">
              Ready to manage your LaLiga fantasy team?
            </p>
          </div>
        </div>
      </div>

      <div className="row g-4">
        {/* My Fantasy Teams */}
        <div className="col-lg-3 col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-body text-center p-4">
              <div className="mb-3">
                <span style={{ fontSize: '3rem' }}>🏆</span>
              </div>
              <h5 className="card-title fw-bold mb-3">My Fantasy Teams</h5>
              <p className="card-text text-muted mb-4">
                Create and manage your LaLiga fantasy teams
              </p>
              <button 
                className="btn btn-primary btn-lg w-100"
                onClick={() => handleNavigation('/teams')}
              >
                Manage Teams
              </button>
            </div>
          </div>
        </div>

        {/* My Fantasy Leagues */}
        <div className="col-lg-3 col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-body text-center p-4">
              <div className="mb-3">
                <span style={{ fontSize: '3rem' }}>🏅</span>
              </div>
              <h5 className="card-title fw-bold mb-3">My Fantasy Leagues</h5>
              <p className="card-text text-muted mb-4">
                Create private leagues and compete with friends
              </p>
              <button 
                className="btn btn-success btn-lg w-100"
                onClick={() => handleNavigation('/leagues')}
              >
                Manage Leagues
              </button>
            </div>
          </div>
        </div>

        {/* Player Database */}
        <div className="col-lg-3 col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-body text-center p-4">
              <div className="mb-3">
                <span style={{ fontSize: '3rem' }}>🌐</span>
              </div>
              <h5 className="card-title fw-bold mb-3">Player Database</h5>
              <p className="card-text text-muted mb-4">
                Browse and analyze LaLiga players
              </p>
              <button 
                className="btn btn-info btn-lg w-100"
                onClick={() => handleNavigation('/players')}
              >
                Browse Players
              </button>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="col-lg-3 col-md-6">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-body text-center p-4">
              <div className="mb-3">
                <span style={{ fontSize: '3rem' }}>📊</span>
              </div>
              <h5 className="card-title fw-bold mb-3">Statistics</h5>
              <p className="card-text text-muted mb-4">
                Track your team's performance
              </p>
              <button 
                className="btn btn-secondary btn-lg w-100"
                onClick={() => handleNavigation('/stats')}
              >
                View Stats
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
