// App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GameProvider } from './contexts/GameContext';
import Home from './pages/Home';
import HostGame from './pages/HostGame';
import JoinGame from './pages/JoinGame';
import GameRoom from './pages/GameRoom';
import './styles/globals.css';

function App() {
  return (
    <GameProvider>
      <Router>
        <div className="app">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/host" element={<HostGame />} />
            <Route path="/join" element={<JoinGame />} />
            <Route path="/game/:roomCode" element={<GameRoom />} />
          </Routes>
        </div>
      </Router>
    </GameProvider>
  );
}

export default App;