// components/player/AnswerPanel.jsx
import React from 'react';
import '../../styles/AnswerPanel.css';

const AnswerPanel = ({ choices, selectedAnswer, onAnswerSelect, disabled }) => {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];
  
  return (
    <div className="answer-panel">
      <div className="choices-grid">
        {choices.map((choice, index) => (
          <button
            key={choice.id}
            className={`choice-button ${selectedAnswer === choice.id ? 'selected' : ''}`}
            style={{ '--choice-color': colors[index] }}
            onClick={() => onAnswerSelect(choice.id)}
            disabled={disabled}
          >
            <div className="choice-content">
              <div className="choice-letter">
                {String.fromCharCode(65 + index)}
              </div>
              <div className="choice-text">
                {choice.choice_text}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AnswerPanel;