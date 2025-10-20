// components/shared/Leaderboard.jsx
import React from 'react';
import '../../styles/Leaderboard.css';

const Leaderboard = ({ leaderboard, showFinal = false }) => {
  return (
    <div className={`leaderboard ${showFinal ? 'final' : ''}`}>
      <h3>{showFinal ? 'Final Results' : 'Live Leaderboard'}</h3>
      
      <div className="leaderboard-list">
        {leaderboard.players?.map((player, index) => (
          <div key={player.player_id} className={`leaderboard-item ${index < 3 ? `rank-${index + 1}` : ''}`}>
            <div className="player-rank">
              {index < 3 ? ['🥇', '🥈', '🥉'][index] : `#${index + 1}`}
            </div>
            <div className="player-info">
              <span className="player-name">{player.nickname}</span>
              {!player.is_connected && <span className="disconnected-indicator">🔴</span>}
            </div>
            <div className="player-score">
              {player.total_score} pts
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Leaderboard;