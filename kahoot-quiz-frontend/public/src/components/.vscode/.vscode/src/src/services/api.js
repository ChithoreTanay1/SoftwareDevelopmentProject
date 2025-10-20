import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const quizApi = {
  createQuiz: (quizData) => api.post('/quizzes', quizData),
  getQuiz: (quizId) => api.get(`/quizzes/${quizId}`),
  listQuizzes: () => api.get('/quizzes'),
};

export const roomApi = {
  createRoom: (roomData) => api.post('/rooms', roomData),
  getRoom: (roomCode) => api.get(`/rooms/${roomCode}`),
  joinRoom: (roomCode, joinData) => api.post(`/rooms/${roomCode}/join`, joinData),
  getPlayers: (roomCode) => api.get(`/rooms/${roomCode}/players`),
  getLeaderboard: (roomCode) => api.get(`/rooms/${roomCode}/leaderboard`),
  startGame: (roomCode) => api.post(`/rooms/${roomCode}/start`),
  nextQuestion: (roomCode) => api.post(`/rooms/${roomCode}/next-question`),
  endGame: (roomCode) => api.post(`/rooms/${roomCode}/end`),
};

export const systemApi = {
  healthCheck: () => api.get('/health'),
  getStats: () => api.get('/stats'),
};

export default api;