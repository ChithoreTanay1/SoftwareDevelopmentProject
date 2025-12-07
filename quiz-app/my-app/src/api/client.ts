// File: src/api/client.ts
// Complete client with WebSocket support for answer submissions



export const API_BASE_URL = import.meta.env.VITE_APP_API_BASE_URL || "http://localhost:8003";
export const WS_BASE_URL = import.meta.env.VITE_APP_WS_BASE_URL || "ws://localhost:8003";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const opts: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  };

  const res = await fetch(url, opts);
  const text = await res.text();
  const contentType = res.headers.get("content-type") || "";

  if (!res.ok) {
    let payload: any = text;
    if (contentType.includes("application/json") && text) {
      try { payload = JSON.parse(text); } catch(e) {}
    }
    throw new Error(`API Error ${res.status}: ${JSON.stringify(payload)}`);
  }

  if (!text) return (null as unknown) as T;
  if (contentType.includes("application/json")) return JSON.parse(text) as T;

  return (text as unknown) as T;
}

// -------------------------
// WebSocket Types
// -------------------------

export type WSMessageType = 
  | "answer_submitted"
  | "question_started"
  | "question_ended"
  | "game_ended"
  | "leaderboard_update"
  | "player_joined"
  | "player_left"
  | "error"
  | "start_game"
  | "next_question"
  | "question"
  | "game_started" 
  | "end_game";

export type WSMessage<T = any> = {
  type: WSMessageType;
  data: T;
};

export type PlayerAnswerPayload = {
  question_id: string;
  choice_id: string;
  time_taken: number;
};

// -------------------------
// WebSocket Manager
// -------------------------

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private messageHandlers: Map<WSMessageType, (data: any) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private roomCode = '';
  private playerId = '';
  private onMessageCallback: ((message: WSMessage) => void) | null = null;
  private onErrorCallback: ((error: Event) => void) | null = null;
  private onCloseCallback: ((event: CloseEvent) => void) | null = null;

  connect(
    roomCode: string,
    playerId: string,
    onMessage?: (message: WSMessage) => void,
    onError?: (error: Event) => void,
    onClose?: (event: CloseEvent) => void
  ): Promise<void> {
    this.roomCode = roomCode;
    this.playerId = playerId;
    this.onMessageCallback = onMessage || null;
    this.onErrorCallback = onError || null;
    this.onCloseCallback = onClose || null;

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_BASE_URL}/api/v1/ws/${encodeURIComponent(roomCode)}/${encodeURIComponent(playerId)}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("WebSocket connected");
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.onMessageCallback?.(message);
            
            const handler = this.messageHandlers.get(message.type);
            if (handler) {
              handler(message.data);
            }
          } catch (e) {
            console.error("Failed to parse WebSocket message:", e);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.onErrorCallback?.(error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log("WebSocket closed");
          this.onCloseCallback?.(event);
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect(
          this.roomCode,
          this.playerId,
          this.onMessageCallback || undefined,
          this.onErrorCallback || undefined,
          this.onCloseCallback || undefined
        ).catch(err => {
          console.error("Reconnect failed:", err);
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(message: WSMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error("WebSocket is not connected");
    }
  }

  submitAnswer(questionId: string, choiceId: string, timeTaken: number): void {
    this.send({
      type: 'answer_submitted',
      data: {
        question_id: questionId,
        choice_id: choiceId,
        time_taken: timeTaken,
      }
    });
  }

  registerHandler(type: WSMessageType, handler: (data: any) => void): void {
    this.messageHandlers.set(type, handler);
  }

  disconnect(): void {
    if (!this.ws) return;
  
    if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CLOSING) {
      this.ws.close();
    }
  
    this.ws = null;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// -------------------------
// Types (from OpenAPI components.schemas)
// -------------------------

export type APIResponse<TData = any> = {
  success: boolean;
  message: string;
  data: TData | null;
  error_code?: string | null;
};

export type ChoiceCreate = {
  choice_text: string;
  order_index: number;
  is_correct?: boolean;
};

export type ChoiceResponse = {
  choice_text: string;
  order_index: number;
  id: string;
};

export type GameStatus = "waiting" | "active" | "completed" | "cancelled";

export type LeaderboardResponse = {
  players: PlayerScore[];
  total_players: number;
  last_updated: string;
};

export type PlayerResponse = {
  nickname: string;
  id: string;
  player_id: string;
  joined_at: string;
  is_connected: boolean;
  total_score: number;
};

export type PlayerScore = {
  player_id: string;
  nickname: string;
  total_score: number;
  rank: number;
  is_connected: boolean;
};

export type QuestionType = "multiple_choice" | "true_false";

export type QuestionCreate = {
  question_text: string;
  question_type?: QuestionType;
  time_limit?: number;
  points?: number;
  order_index: number;
  choices: ChoiceCreate[];
};

export type QuestionResponse = {
  question_text: string;
  question_type: QuestionType;
  time_limit: number;
  points: number;
  order_index: number;
  id: string;
  choices: ChoiceResponse[];
};

export type QuizCreate = {
  title: string;
  description?: string | null;
  created_by: string;
  questions: QuestionCreate[];
};

export type QuizResponse = {
  title: string;
  description?: string | null;
  id: string;
  created_by: string;
  created_at: string;
  is_active: boolean;
  questions: QuestionResponse[];
};

export type QuizSummary = {
  title: string;
  description?: string | null;
  id: string;
  created_by: string;
  created_at: string;
  is_active: boolean;
  question_count: number;
};

export type RoomCreate = {
  quiz_id?: string;
  host_name: string;
  max_players?: number;
};

export type RoomJoin = {
  nickname: string;
};

export type RoomResponse = {
  id: string;
  room_code: string;
  quiz_id: string;
  host_id: string;
  host_name: string;
  status: GameStatus;
  current_question: number;
  created_at: string;
  started_at?: string | null;
  ended_at?: string | null;
  max_players: number;
  player_count: number;
};

// -------------------------
// Services / Endpoint wrappers
// -------------------------

export const QuizzesService = {
  async createQuiz(payload: QuizCreate): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>("/api/v1/quizzes", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async listQuizzes(limit?: number): Promise<QuizSummary[]> {
    const q = limit ? `?limit=${encodeURIComponent(limit)}` : "";
    return apiFetch<QuizSummary[]>(`/api/v1/quizzes${q}`);
  },

  async getQuiz(quiz_id: string): Promise<QuizResponse> {
    return apiFetch<QuizResponse>(`/api/v1/quizzes/${encodeURIComponent(quiz_id)}`);
  },
};

// Function to check if backend is available

export class MockQuizzesService {
  static async createQuiz(data: any): Promise<APIResponse> {
    console.log('🎭 Using MockQuizzesService.createQuiz');
    console.log('📤 Mock Request Data:', data);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Return mock response
    return {
      success: true,
      message: "Quiz created successfully (MOCK)",
      data: {
        id: `mock_quiz_${Date.now()}`,
        quiz_id: `mock_quiz_${Date.now()}`,
        title: data.title,
        created_by: data.created_by,
        created_at: new Date().toISOString(),
        is_active: true,
        question_count: data.questions.length
      }
    };
  }
}



export class MockRoomsService {
  static async createRoom(data: { quiz_id: string; host_name: string; max_players: number }): Promise<APIResponse> {
    console.log('🎭 Using MockRoomsService.createRoom');
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Generate a random 6-digit room code
    const roomCode = Math.floor(100000 + Math.random() * 900000).toString();
    const hostId = `host_${Date.now()}`;
    
    return {
      success: true,
      message: "Room created successfully (MOCK)",
      data: {
        room_code: roomCode,
        quiz_id: data.quiz_id,
        host_name: data.host_name,
        host_id: hostId,
        max_players: data.max_players,
        status: "waiting"
      }
    };
  }

  

  static async getLeaderboard(roomCode: string): Promise<APIResponse<LeaderboardResponse>> {
    console.log('🎭 Using MockRoomsService.getLeaderboard');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Get the player's score from localStorage
    const finalScore = parseInt(localStorage.getItem("finalScore") || "0");
    const playerName = localStorage.getItem("playerName") || "You";
    const playerId = localStorage.getItem("playerId") || `player_${Date.now()}`;
    
    const mockPlayers: PlayerScore[] = [
      {
        player_id: playerId,
        nickname: playerName,
        total_score: finalScore,
        rank: 1,
        is_connected: true
      },
      {
        player_id: "player_2",
        nickname: "Alex",
        total_score: Math.max(0, finalScore - 500),
        rank: 2,
        is_connected: false
      },
      {
        player_id: "player_3",
        nickname: "Jordan",
        total_score: Math.max(0, finalScore - 1200),
        rank: 3,
        is_connected: true
      },
      {
        player_id: "player_4",
        nickname: "Sam",
        total_score: Math.max(0, finalScore - 1800),
        rank: 4,
        is_connected: false
      },
      {
        player_id: "player_5",
        nickname: "Taylor",
        total_score: Math.max(0, finalScore - 2500),
        rank: 5,
        is_connected: true
      }
    ];
    
    // Sort by score
    const sortedPlayers = mockPlayers.sort((a, b) => b.total_score - a.total_score)
      .map((player, index) => ({ ...player, rank: index + 1 }));
    
    return {
      success: true,
      message: "Leaderboard fetched successfully (MOCK)",
      data: {
        players: sortedPlayers,
        total_players: sortedPlayers.length,
        last_updated: new Date().toISOString()
      }
    };
  }

  static async joinRoom(roomCode: string, data: { nickname: string }): Promise<APIResponse> {
    console.log('🎭 Using MockRoomsService.joinRoom');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // If the player is the host, use host_ prefix
    const isHost = data.nickname === "Host" || data.nickname === localStorage.getItem("playerName");
    const playerId = isHost ? `host_${Date.now()}` : `player_${Date.now()}`;
    
    return {
      success: true,
      message: "Joined room successfully (MOCK)",
      data: {
        player_id: playerId,
        room_code: roomCode,
        nickname: data.nickname
      }
    };
  }

  static async startGame(roomCode: string): Promise<APIResponse> {
    console.log('🎭 Using MockRoomsService.startGame');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      success: true,
      message: "Game started successfully (MOCK)",
      data: {
        room_code: roomCode,
        status: "active"
      }
    };
  }
}

export const RoomsService = {
  async listActiveRooms(): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms`);
  },

  async getCurrentQuestion(room_code: string): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms/${encodeURIComponent(room_code)}/current-question`);
  },

  async getQuestionResults(room_code: string, question_index: number): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms/${encodeURIComponent(room_code)}/question/${question_index}/results`);
  },

  async createRoom(payload: RoomCreate): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms`, { 
      method: "POST", 
      body: JSON.stringify(payload) 
    });
  },

  async getRoomInfo(room_code: string): Promise<RoomResponse> {
    return apiFetch<RoomResponse>(`/api/v1/rooms/${encodeURIComponent(room_code)}`);
  },

  async joinRoom(room_code: string, payload: RoomJoin): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms/${encodeURIComponent(room_code)}/join`, { 
      method: "POST", 
      body: JSON.stringify(payload) 
    });
  },

  async getRoomPlayers(room_code: string): Promise<PlayerResponse[]> {
    return apiFetch<PlayerResponse[]>(`/api/v1/rooms/${encodeURIComponent(room_code)}/players`);
  },

  async getRoomLeaderboard(room_code: string): Promise<LeaderboardResponse> {
    return apiFetch<LeaderboardResponse>(`/api/v1/rooms/${encodeURIComponent(room_code)}/leaderboard`);
  },

  async startGame(room_code: string): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms/${encodeURIComponent(room_code)}/start`, { 
      method: "POST" 
    });
  },

  async nextQuestion(room_code: string): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms/${encodeURIComponent(room_code)}/next-question`, { 
      method: "POST" 
    });
  },

  async endGame(room_code: string): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/rooms/${encodeURIComponent(room_code)}/end`, { 
      method: "POST" 
    });
  },
};

export const DevService = {
  async createSampleQuiz(): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/dev/create-sample-quiz`, { 
      method: "POST" 
    });
  },
};

export const SystemService = {
  async healthCheck(): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/health`);
  },

  async getSystemStats(): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/api/v1/stats`);
  },

  async root(): Promise<APIResponse<any>> {
    return apiFetch<APIResponse<any>>(`/`);
  },
};