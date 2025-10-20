// contexts/GameContext.jsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const GameContext = createContext();

const gameReducer = (state, action) => {
  switch (action.type) {
    case 'SET_PLAYER':
      return { ...state, player: action.payload };
    case 'SET_ROOM':
      return { ...state, room: action.payload };
    case 'SET_GAME_STATE':
      return { ...state, gameState: action.payload };
    case 'SET_LEADERBOARD':
      return { ...state, leaderboard: action.payload };
    case 'SET_CURRENT_QUESTION':
      return { ...state, currentQuestion: action.payload };
    case 'SET_ANSWER_RESULT':
      return { ...state, answerResult: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
};

const initialState = {
  player: null,
  room: null,
  gameState: 'lobby', // 'lobby', 'question', 'answer', 'leaderboard', 'finished'
  leaderboard: [],
  currentQuestion: null,
  answerResult: null,
  error: null,
};

export const GameProvider = ({ children }) => {
  const [state, dispatch] = useReducer(gameReducer, initialState);
  const { connect, sendMessage, connectionState } = useWebSocket(dispatch);

  const value = {
    ...state,
    dispatch,
    connect,
    sendMessage,
    connectionState,
  };

  return (
    <GameContext.Provider value={value}>
      {children}
    </GameContext.Provider>
  );
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};