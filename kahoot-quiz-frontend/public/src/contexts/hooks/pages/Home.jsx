// pages/Home.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Home.css';

const Home = () => {
  return (
    <div className="home-container">
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">QuizBattle</h1>
          <p className="hero-subtitle">Real-time multiplayer quiz game</p>
          <p className="hero-description">
            Create engaging quizzes and challenge your friends in real-time!
          </p>
          
          <div className="cta-buttons">
            <Link to="/host" className="cta-button host-button">
              🎮 Host a Game
            </Link>
            <Link to="/join" className="cta-button join-button">
              🎯 Join a Game
            </Link>
          </div>
        </div>
        
        <div className="hero-features">
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Real-time</h3>
            <p>Live multiplayer experience</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🏆</div>
            <h3>Competitive</h3>
            <p>Live leaderboard and scoring</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎨</div>
            <h3>Customizable</h3>
            <p>Create your own quizzes</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;