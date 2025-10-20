// pages/HostGame.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import QuizCreator from '../components/host/QuizCreator';
import HostLobby from '../components/host/HostLobby';
import { createRoom, createQuiz } from '../services/api';
import '../styles/HostGame.css';

const HostGame = () => {
  const [step, setStep] = useState('create'); // 'create', 'lobby'
  const [quiz, setQuiz] = useState(null);
  const [room, setRoom] = useState(null);
  const navigate = useNavigate();

  const handleQuizCreated = async (quizData) => {
    try {
      // Create quiz in backend
      const createdQuiz = await createQuiz(quizData);
      setQuiz(createdQuiz);
      
      // Create room with the quiz
      const roomData = {
        quiz_id: createdQuiz.id,
        host_name: 'Game Host', // In real app, get from user
        max_players: 50
      };
      
      const createdRoom = await createRoom(roomData);
      setRoom(createdRoom);
      setStep('lobby');
      
    } catch (error) {
      console.error('Failed to create game:', error);
      alert('Failed to create game. Please try again.');
    }
  };

  const handleStartGame = () => {
    // This would trigger WebSocket message to start game
    console.log('Starting game...');
  };

  if (step === 'create') {
    return (
      <div className="host-container">
        <div className="host-header">
          <h1>Create Your Quiz</h1>
          <p>Design an engaging quiz for your players</p>
        </div>
        <QuizCreator onQuizCreated={handleQuizCreated} />
      </div>
    );
  }

  return (
    <div className="host-container">
      <HostLobby 
        room={room}
        quiz={quiz}
        onStartGame={handleStartGame}
      />
    </div>
  );
};

export default HostGame;