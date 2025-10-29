INTRODUCTION

This project is a Khahoot inspired quiz game which can also be used for voting on simple prompts. The system supports real-time multiplayer interations usingWebsockets which enables both
the hosts and players to communicate instantly during quiz sessions

The application manages database connections, Websocket connections, routes, error handling within a single Fast API application file.

CLIENT REQUIREMENTS

To have control over accepted nickname type

To be able to access results after a session ends

Room security which prevents unauthorized players from participating

OBJECTIVES 

To handle host and player connections securely and efficiently

To accurately record results in a database


SYSTEM ARCHITECTURE

BACKEND

The backend is a real-time, event-driven system designed to manage interative quiz sessions  between a host and multiple players. It's core functional areas are:
. Quiz and question management
. Room creation and session lifecycle
. Real-time communication via WebSocket
. Player participation and scoring logic
. Game state synchronization

Configuration Highlights (from config.py file)

Programming Language: Python

Database: PostgreSQL

Security: Includes secret key and token expiry settings.

WebSocket: Configurable ping/pong intervals and timeout settings

CORS: Defaults to "*"

Logging: Dynamically adjusts log level in debug mode

Schemas and Data Contracts (schemas.py)

The schemas define the data contracts used across API and websocket layers, implemented using Pydantic models for validation and serialization.

class WSMessageType(..):
  ....
Defines both host-originated and player-originated event types.

class WSMessage():
  ...
Is used for consistent serialization of all messages between server and clients

Game Entities

Quiz, Question, Choice, Room, Player and Answer schemas define both the create and response variants.

Leaderboard and Statistics

Summarized data is provided using:
class LeaderboardResponse(..):
  ....

and

class GameStats(..):
  ...

Core Business Logic Services (services.py)

All critical business operations are encapsulated within service classes.

. Quiz creation and retrieval is handled by
 
  class QuizService:
    ...
which validates at least one correct answer per question and uses generate_unique_id() for consistent unique user id generation.

.Lifecycle management of game sessions is the responsiblity of
  
  class RoomService:
    ...

which has the following key functions:

create_room() :       generates unique room codes and initializes new sessions.

get_room_by_code():   retrieves room details using join prefetching.

start_game():         changes room status from waiting -> active.

next_question():      advances question index or marks completion

end_game():           terminates a game session.

