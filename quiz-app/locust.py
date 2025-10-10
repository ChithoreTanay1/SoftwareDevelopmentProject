from locust import HttpUser, task, between, TaskSet
import random
import json
import time
import uuid
from websocket import create_connection
import threading

class QuizHostTasks(TaskSet):
    def on_start(self):
        """Setup for host - create quiz and room"""
        self.host_id = f"host_{uuid.uuid4().hex[:8]}"
        self.room_code = None
        self.quiz_id = None
        
        # Create a quiz first
        quiz_data = {
            "title": f"Test Quiz {uuid.uuid4().hex[:4]}",
            "description": "Load testing quiz",
            "created_by": self.host_id,
            "questions": [
                {
                    "question_text": "What is 2 + 2?",
                    "question_type": "multiple_choice",
                    "time_limit": 30,
                    "points": 100,
                    "order_index": 0,
                    "choices": [
                        {"choice_text": "3", "is_correct": False, "order_index": 0},
                        {"choice_text": "4", "is_correct": True, "order_index": 1},
                        {"choice_text": "5", "is_correct": False, "order_index": 2}
                    ]
                },
                {
                    "question_text": "What color is the sky?",
                    "question_type": "multiple_choice",
                    "time_limit": 20,
                    "points": 100,
                    "order_index": 1,
                    "choices": [
                        {"choice_text": "Red", "is_correct": False, "order_index": 0},
                        {"choice_text": "Blue", "is_correct": True, "order_index": 1},
                        {"choice_text": "Green", "is_correct": False, "order_index": 2}
                    ]
                }
            ]
        }
        
        with self.client.post("/api/v1/quizzes", 
                             json=quiz_data,
                             catch_response=True,
                             name="Create Quiz") as response:
            if response.status_code == 201:
                self.quiz_id = response.json()["data"]["quiz_id"]
            else:
                response.failure(f"Failed to create quiz: {response.text}")

        # Create room
        if self.quiz_id:
            room_data = {
                "quiz_id": self.quiz_id,
                "host_name": f"Host_{self.host_id}",
                "max_players": 50
            }
            
            with self.client.post("/api/v1/rooms", 
                                 json=room_data,
                                 catch_response=True,
                                 name="Create Room") as response:
                if response.status_code == 201:
                    self.room_code = response.json()["data"]["room_code"]
                    print(f"Host {self.host_id} created room {self.room_code}")
                else:
                    response.failure(f"Failed to create room: {response.text}")

    @task(1)
    def start_game(self):
        """Start the game"""
        if not self.room_code:
            return
            
        with self.client.post(f"/api/v1/rooms/{self.room_code}/start",
                             catch_response=True,
                             name="Start Game") as response:
            if response.status_code != 200:
                response.failure(f"Failed to start game: {response.text}")

    @task(3)
    def get_room_info(self):
        """Check room status"""
        if not self.room_code:
            return
            
        with self.client.get(f"/api/v1/rooms/{self.room_code}",
                           catch_response=True,
                           name="Get Room Info") as response:
            if response.status_code != 200:
                response.failure(f"Failed to get room info: {response.text}")

    @task(2)
    def get_leaderboard(self):
        """Check leaderboard"""
        if not self.room_code:
            return
            
        with self.client.get(f"/api/v1/rooms/{self.room_code}/leaderboard",
                           catch_response=True,
                           name="Get Leaderboard") as response:
            if response.status_code != 200:
                response.failure(f"Failed to get leaderboard: {response.text}")

class QuizPlayerTasks(TaskSet):
    def on_start(self):
        """Setup for player - join a room"""
        self.player_id = f"player_{uuid.uuid4().hex[:8]}"
        self.nickname = f"Player_{self.player_id[:6]}"
        self.room_code = None
        self.ws_connected = False
        
        # Get available rooms first
        with self.client.get("/api/v1/rooms",
                           catch_response=True,
                           name="Get Active Rooms") as response:
            if response.status_code == 200:
                rooms_data = response.json()
                if rooms_data["data"]["total_rooms"] > 0:
                    # Join a random room from active ones
                    available_rooms = list(rooms_data["data"]["rooms"].keys())
                    self.room_code = random.choice(available_rooms)
                else:
                    # No rooms available, can't proceed
                    response.failure("No active rooms available")
                    return
            else:
                response.failure("Failed to get active rooms")
                return

        # Join the room
        if self.room_code:
            join_data = {"nickname": self.nickname}
            
            with self.client.post(f"/api/v1/rooms/{self.room_code}/join",
                                 json=join_data,
                                 catch_response=True,
                                 name="Join Room") as response:
                if response.status_code == 200:
                    print(f"Player {self.nickname} joined room {self.room_code}")
                    # Start WebSocket connection in background
                    self.start_websocket()
                else:
                    response.failure(f"Failed to join room: {response.text}")

    def start_websocket(self):
        """Start WebSocket connection in background thread"""
        def ws_thread():
            try:
                # Connect to WebSocket
                ws_url = f"ws://localhost:8000/ws/player/{self.room_code}?player_id={self.player_id}&nickname={self.nickname}"
                ws = create_connection(ws_url)
                self.ws_connected = True
                
                # Listen for messages
                while self.ws_connected:
                    try:
                        message = ws.recv()
                        data = json.loads(message)
                        
                        # Handle different message types
                        if data.get("type") == "question_started":
                            # Simulate answering after random delay
                            time.sleep(random.uniform(1, 5))
                            
                            question_data = data["data"]["question"]
                            if question_data["choices"]:
                                random_choice = random.choice(question_data["choices"])
                                
                                answer_data = {
                                    "type": "answer_submitted",
                                    "data": {
                                        "question_id": question_data["id"],
                                        "choice_id": random_choice["id"],
                                        "response_time": random.uniform(1, 15)
                                    }
                                }
                                ws.send(json.dumps(answer_data))
                                
                    except Exception as e:
                        print(f"WebSocket error for {self.nickname}: {e}")
                        break
                        
                ws.close()
            except Exception as e:
                print(f"Failed to connect WebSocket for {self.nickname}: {e}")

        # Start WebSocket thread
        thread = threading.Thread(target=ws_thread)
        thread.daemon = True
        thread.start()

    def on_stop(self):
        """Cleanup when player stops"""
        self.ws_connected = False

    @task(5)
    def check_leaderboard(self):
        """Check current leaderboard"""
        if not self.room_code:
            return
            
        with self.client.get(f"/api/v1/rooms/{self.room_code}/leaderboard",
                           catch_response=True,
                           name="Player Check Leaderboard") as response:
            if response.status_code != 200:
                response.failure(f"Failed to get leaderboard: {response.text}")

    @task(3)
    def get_room_players(self):
        """See who's in the room"""
        if not self.room_code:
            return
            
        with self.client.get(f"/api/v1/rooms/{self.room_code}/players",
                           catch_response=True,
                           name="Get Room Players") as response:
            if response.status_code != 200:
                response.failure(f"Failed to get players: {response.text}")

class QuizHostUser(HttpUser):
    tasks = [QuizHostTasks]
    wait_time = between(5, 15)  # Hosts act every 5-15 seconds
    weight = 1  # Fewer hosts than players

class QuizPlayerUser(HttpUser):
    tasks = [QuizPlayerTasks]
    wait_time = between(2, 8)   # Players act more frequently
    weight = 10  # More players than hosts

# Simple test for basic API endpoints
class QuickTester(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/")
    
    @task(2)
    def api_health(self):
        self.client.get("/api/v1/health")
    
    @task(1)
    def list_quizzes(self):
        self.client.get("/api/v1/quizzes")
    
    @task(1)
    def system_stats(self):
        self.client.get("/api/v1/stats")