import React from 'react'
import './styles/globals.css'

function App() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🎮 QuizBattle - Kahoot-Style Quiz Game</h1>
      <p>Frontend is working! Ready to build the game.</p>
      <div>
        <button style={{ margin: '10px', padding: '10px 20px' }}>Host Game</button>
        <button style={{ margin: '10px', padding: '10px 20px' }}>Join Game</button>
      </div>
    </div>
  );
}

export default App;