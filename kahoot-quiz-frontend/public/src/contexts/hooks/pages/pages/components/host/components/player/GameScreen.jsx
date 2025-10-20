// components/player/GameScreen.jsx
import React, { useState, useEffect } from 'react';
import { useGame } from '../../contexts/GameContext';
import AnswerPanel from './AnswerPanel';
import Leaderboard from '../shared/Leaderboard';
import '../../styles/GameScreen.css';

const GameScreen = () => {
  const { gameState, currentQuestion, leaderboard, sendMessage, answerResult } = useGame();
  const [timeLeft, setTimeLeft] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);

  useEffect(() => {
    if (gameState === 'question' && currentQuestion) {
      setTimeLeft(currentQuestion.time_limit);
      setSelectedAnswer(null);
      
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [gameState, currentQuestion]);

  const handleAnswerSelect = (choiceId) => {
    if (selectedAnswer || timeLeft <= 0) return;
    
    setSelectedAnswer(choiceId);
    
    // Calculate response time
    const responseTime = currentQuestion.time_limit - timeLeft;
    
    // Send answer to server
    sendMessage({
      type: 'answer_submitted',
      data: {
        question_id: currentQuestion.id,
        choice_id: choiceId,
        response_time: responseTime
      }
    });
  };

  if (gameState === 'lobby') {
    return (
      <div className="game-screen lobby">
        <div className="waiting-room">
          <h2>Waiting for game to start...</h2>
          <div className="loading-spinner"></div>
          <p>The host will start the game soon!</p>
        </div>
      </div>
    );
  }

  if (gameState === 'question') {
    return (
      <div className="game-screen question">
        <div className="question-header">
          <div className="question-number">
            Question {currentQuestion?.order_index + 1}
          </div>
          <div className="timer">
            ⏱️ {timeLeft}s
          </div>
          <div className="points">
            🎯 {currentQuestion?.points} points
          </div>
        </div>

        <div className="question-content">
          <h2 className="question-text">{currentQuestion?.question_text}</h2>
          
          <AnswerPanel
            choices={currentQuestion?.choices || []}
            selectedAnswer={selectedAnswer}
            onAnswerSelect={handleAnswerSelect}
            disabled={!!selectedAnswer || timeLeft <= 0}
          />
        </div>

        {selectedAnswer && (
          <div className="answer-submitted">
            <p>✅ Answer submitted! Waiting for others...</p>
          </div>
        )}
      </div>
    );
  }

  if (gameState === 'answer') {
    return (
      <div className="game-screen answer">
        <div className="answer-result">
          {answerResult?.is_correct ? (
            <div className="result-correct">
              <h2>🎉 Correct!</h2>
              <p>+{answerResult.points_earned} points</p>
            </div>
          ) : (
            <div className="result-incorrect">
              <h2>❌ Incorrect</h2>
              <p>Better luck next time!</p>
            </div>
          )}
        </div>
        
        <Leaderboard leaderboard={leaderboard} />
      </div>
    );
  }

  if (gameState === 'finished') {
    return (
      <div className="game-screen finished">
        <div className="final-results">
          <h2>Game Over! 🏆</h2>
          <Leaderboard leaderboard={leaderboard} showFinal={true} />
        </div>
      </div>
    );
  }

  return <div>Loading...</div>;
};

export default GameScreen;