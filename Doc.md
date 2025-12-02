# 🎮 Real-Time Quiz & Voting App  
Kahoot-Inspired Multiplayer Quiz System (FastAPI + WebSockets + PostgreSQL)

This project is a **real-time interactive quiz and voting platform**, inspired by Kahoot.  
It supports instant communication between **hosts** and **players** using WebSockets, secure session handling, nickname control, and persistent result tracking via PostgreSQL.

---

## 🚀 Features

- 🔌 Real-time multiplayer using WebSockets  
- 🛡️ Secure room system preventing unauthorized joins  
- 🎯 Custom nickname validation rules  
- 📊 Full result tracking & post-session statistics  
- 🧠 Real-time host ↔ player synchronization  
- 🗃️ Database-backed quiz & scoring  
- 🧩 Single FastAPI application managing routes, DB, WebSockets, and errors  

---

## 📌 Table of Contents
- [Client Requirements](#client-requirements)  
- [Objectives](#objectives)  
- [System Architecture](#system-architecture)  
  - [Backend](#backend)  
  - [Database](#database)  
  - [Frontend](#frontend)  
- [Game Lifecycle](#game-lifecycle)  
- [Error Handling and Logging](#error-handling-and-logging)  
- [Backend Summary](#backend-summary)  

---

## ✅ Client Requirements

- Control over accepted nickname type  
- Ability to access results after session ends  
- Room security preventing unauthorized participation  

---

## 🎯 Objectives

- Handle host and player connections securely and efficiently  
- Accurately record results in the database  

---

# 🏗 System Architecture

## 🔧 Backend

The backend is a **real-time, event-driven system** implemented with **FastAPI**, responsible for orchestrating quiz sessions, handling WebSocket connections, and managing room lifecycles.

### Core Functional Areas
- Quiz & question management  
- Room creation and session lifecycle  
- Real-time WebSocket communication  
- Player participation and scoring  
- Game state synchronization  

---

## ⚙️ Configuration Highlights (`config.py`)

| Setting | Details |
|--------|---------|
| Programming Language | Python |
| Database | PostgreSQL |
| Security | Secret key + token expiry |
| WebSockets | Custom ping/pong intervals and timeouts |
| CORS | Defaults to `"*"` |
| Logging | Adaptive logging level in debug mode |

---

## 📦 Schemas & Data Contracts (`schemas.py`)

Schemas use **Pydantic** for request/response validation.

### WebSocket Message Types
`WSMessageType` enumerates event categories for both host and player.

### WebSocket Message Format
`WSMessage` ensures all messages follow a single consistent structure.

### Game Entities
Schemas define:
- Quiz  
- Question  
- Choice  
- Room  
- Player  
- Answer

Each has **Create** and **Response** variants.

### Statistics
- `LeaderboardResponse`
- `GameStats`

---

## 🧠 Core Business Logic (`services.py`)

All major operations are handled by specialized service classes.

### **QuizService**
- Creates and retrieves quizzes  
- Ensures each question has at least one correct answer  
- Generates unique IDs  

### **RoomService**
Handles the entire room and game lifecycle:
- `create_room()` → generates unique room code  
- `get_room_by_code()`  
- `start_game()` → transitions from `waiting → active`  
- `next_question()` → advances quiz state  
- `end_game()` → marks completion  

### **PlayerService**
- Validates player join requests  
- Prevents duplicates via `DuplicatePlayerException`  
- Enforces capacity limits  

### **ScoreService**
- Records player answers  
- Generates leaderboards and statistics  

---

## ⚡ Real-Time Communication

### WebSocket Manager (`websocket_manager.py`)
Handles:
- Tracking active connections  
- Broadcasting to all clients in a room  
- Direct host/player messaging  
- Clean disconnections  
- Mapping sockets to rooms and roles  

### WebSocket Controller (`websocket_handler.py`)
Acts as the real-time event router:
- Dispatches host actions  
- Processes player submissions  
- Interprets `WSMessageType`  
- Sends updates via the WebSocket Manager  

---

# 🔄 Game Lifecycle

| State | Trigger | Next State |
|--------|---------|-------------|
| waiting | Host starts game | active |
| active | All questions answered or host ends game | completed |
| completed | (none) | end of session |

---

# ❗ Error Handling and Logging

Custom exceptions ensure clear, controlled failures:
- `RoomNotFoundException`  
- `PlayerNotFoundException`  
- `DuplicateAnswerException`  
- `DuplicatePlayerException`  
- `GameStateException`

Logging is centralized and provides contextual information for debugging.

---

# 🧩 Backend Summary

The architecture cleanly separates:
- **Transport Layer** → WebSocket networking  
- **Business Logic** → Services  
- **Data Models** → Pydantic schemas  

This enables:
- Maintainability  
- Testability  
- Scalability  

---

# 🗄 Database
*(This section can be filled with ER diagrams, migrations, or table structures.)*

---

# 🖥️ Frontend
*(Add build instructions, UI screenshots, and WebSocket usage once frontend is finished.)*

---

# 🤝 Contributing
Pull requests and feature suggestions are welcome.

---

# 📜 License
MIT License (or any license you choose).

