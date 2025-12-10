import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { Timer, CheckCircle2, Trophy, Users } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { WebSocketManager, WSMessage } from "@/api/client";

const PlayGame = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  
  // Two managers: One for Player logic, one for Host logic
  const wsManagerRef = useRef<WebSocketManager>(new WebSocketManager());
  const hostWsRef = useRef<WebSocket | null>(null);

  const playerId = localStorage.getItem("playerId");
  const roomCode = localStorage.getItem("roomCode");
  const hostId = localStorage.getItem("hostId"); // Get Host ID
  
  // Check if current user is Host
  const isHost = location.state?.isHost || localStorage.getItem("isHost") === "true";

  const [quiz, setQuiz] = useState<any>(() => {
    const stored = localStorage.getItem("quizData");
    return stored ? JSON.parse(stored) : null;
  });
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(() => {
    return parseInt(localStorage.getItem("currentQuestionIndex") || "0");
  });
  const [score, setScore] = useState(() => {
    return parseInt(localStorage.getItem("score") || "0");
  });

  const [timeLeft, setTimeLeft] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [gameStarted, setGameStarted] = useState(!!quiz);
  
  const [leaderboardData, setLeaderboardData] = useState<any>(null);
  const [showLeaderboard, setShowLeaderboard] = useState(false);

  // Initialize timer
  useEffect(() => {
    if (quiz && quiz.questions && quiz.questions[currentQuestionIndex]) {
      setTimeLeft(quiz.questions[currentQuestionIndex].time_limit || 20);
    }
  }, [currentQuestionIndex, quiz]);

  // Redirect if missing data
  useEffect(() => {
    if (!playerId || !roomCode) {
      navigate("/");
    }
  }, [playerId, roomCode, navigate]);

  // --- 1. PLAYER CONNECTION (Standard) ---
  useEffect(() => {
    if (!roomCode || !playerId) return;

    let mounted = true;
    const manager = wsManagerRef.current;

    const initWebSocket = async () => {
      try {
        await manager.connect(
          roomCode,
          playerId,
          (message: WSMessage) => {
            if (!mounted) return;
            handleGameMessage(message); // Unified handler
          },
          (error) => console.error(error),
          () => setWsConnected(false)
        );
        if (mounted) setWsConnected(true);
      } catch (error) {
        console.error("Player WS failed:", error);
      }
    };

    initWebSocket();
    return () => { mounted = false; manager.disconnect(); };
  }, [roomCode, playerId]);

  // --- 2. HOST CONNECTION (Special Teacher Channel) ---
  useEffect(() => {
    if (!isHost || !hostId || !roomCode) return;

    const apiBase = import.meta.env.VITE_APP_API_BASE_URL || "http://localhost:8003";
    const wsProtocol = apiBase.startsWith("https") ? "wss" : "ws";
    // Connect to the SPECIAL Host endpoint
    const wsUrl = `${wsProtocol}://${apiBase.replace(/^https?:\/\//, "")}/api/v1/ws/host/${roomCode}/${hostId}`;

    console.log("🔗 Connecting Host WS:", wsUrl);
    const hostWs = new WebSocket(wsUrl);

    hostWs.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleGameMessage(message); // Reuse same handler
      } catch (e) { console.error("Host WS parse error", e); }
    };

    hostWsRef.current = hostWs;

    return () => { hostWs.close(); };
  }, [isHost, hostId, roomCode]);


  // --- UNIFIED MESSAGE HANDLER ---
  const handleGameMessage = (message: WSMessage) => {
    console.log("📨 Msg:", message.type);

    switch (message.type) {
      case "game_started":
        if (message.data?.quiz) {
          setQuiz(message.data.quiz);
          setGameStarted(true);
          setShowLeaderboard(false);
        }
        break;

      case "question":
        if (message.data?.questionIndex !== undefined) {
          setCurrentQuestionIndex(message.data.questionIndex);
          setSelectedAnswer(null);
          setShowResult(false);
          setShowLeaderboard(false);
          setLeaderboardData(null);
          setTimeLeft(message.data.timeLimit || 20);
        }
        break;

      case "leaderboard_update":
        console.log("🏆 Leaderboard received!");
        setLeaderboardData(message.data);
        setShowLeaderboard(true);
        break;

      case "question_ended":
        if (message.data?.correctAnswer !== undefined) {
          setShowResult(true);
        }
        break;

      case "game_ended":
        console.log("🏁 Game ended - Redirecting!");
        // Force navigation for everyone
        window.location.href = "/results"; 
        break;
    }
  };

  // Timer Logic
  useEffect(() => {
    if (!gameStarted || !quiz || showLeaderboard) return;
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
            if (!isHost) handleTimeUp(); 
            return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [quiz, gameStarted, showLeaderboard, isHost]);

  const handleTimeUp = () => {
    if (selectedAnswer !== null) return;
    handleAnswerSelect(-1);
  };

  const handleAnswerSelect = (answerIndex: number) => {
    if (isHost) return;
    if (selectedAnswer !== null || showResult) return;
    
    setSelectedAnswer(answerIndex);
    setShowResult(true);

    const currentQuestion = quiz.questions[currentQuestionIndex];
    const timeTaken = (currentQuestion.time_limit || 20) - timeLeft;
    
    let choiceId = "";
    if (answerIndex >= 0 && currentQuestion.answers[answerIndex]) {
        const answer = currentQuestion.answers[answerIndex];
        choiceId = answer.id || answer;
    }

    wsManagerRef.current.submitAnswer(currentQuestion.id, choiceId, timeTaken);
    
    if (answerIndex !== -1 && currentQuestion.correctAnswer === answerIndex) {
        const points = Math.round((timeLeft / currentQuestion.time_limit) * 1000);
        setScore(score + points);
    }
  };

  // --- HOST VIEW ---
  if (isHost) {
     if (!quiz || !quiz.questions) return <div className="text-white text-center p-10">Loading Quiz...</div>;
     const currentQ = quiz.questions[currentQuestionIndex];

     return (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 py-8 px-4 flex flex-col items-center">
           <div className="w-full max-w-6xl flex justify-between items-center mb-8 bg-white/10 p-4 rounded-2xl backdrop-blur-md">
              <div className="text-white font-bold text-xl">Room: {roomCode}</div>
              <div className="text-purple-200">Question {currentQuestionIndex + 1} / {quiz.questions.length}</div>
              <div className="text-white font-bold flex items-center gap-2"><Users className="h-5 w-5"/> Host View</div>
           </div>

           {showLeaderboard && leaderboardData ? (
              <div className="w-full max-w-4xl animate-in zoom-in duration-500">
                 <div className="text-center mb-8">
                    <Trophy className="h-20 w-20 text-yellow-400 mx-auto mb-4 animate-bounce" />
                    <h1 className="text-5xl font-black text-white drop-shadow-lg">Leaderboard</h1>
                 </div>
                 <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 space-y-4">
                    {leaderboardData.players && leaderboardData.players.map((player: any, index: number) => (
                       <div key={index} className="flex items-center justify-between bg-white/20 p-6 rounded-2xl transition-all hover:scale-105 border border-white/10">
                          <div className="flex items-center gap-6">
                             <div className="w-12 h-12 rounded-full flex items-center justify-center text-2xl font-bold text-white bg-purple-600">#{index + 1}</div>
                             <span className="text-2xl font-bold text-white">{player.nickname}</span>
                          </div>
                          <span className="text-3xl font-black text-white">{player.score} pts</span>
                       </div>
                    ))}
                 </div>
                 <div className="text-center mt-8 text-white/50 animate-pulse">Waiting for next question...</div>
              </div>
           ) : (
              <div className="w-full max-w-5xl text-center space-y-12 mt-10">
                 <div className="bg-white/10 backdrop-blur-md rounded-full px-12 py-6 inline-block mb-8">
                    <span className="text-8xl font-black text-white">{timeLeft}</span>
                 </div>
                 <h1 className="text-5xl md:text-6xl font-black text-white leading-tight drop-shadow-xl">{currentQ.question_text}</h1>
              </div>
           )}
        </div>
     );
  }

  // --- PLAYER VIEW ---
  if (!playerId || !roomCode) return null;
  if (!quiz || !quiz.questions) return <div className="text-white text-center p-20">Loading...</div>;

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const timeProgress = (timeLeft / (currentQuestion.time_limit || 20)) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-6 mb-6 shadow-lg border-2 border-white/20">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Timer className="h-6 w-6 text-purple-300" />
              <span className="text-white">{timeLeft}s</span>
            </div>
            <div className="text-right">
              <div className="text-sm text-purple-200">Your Score</div>
              <div className="text-3xl font-black text-white">{score}</div>
            </div>
          </div>
          <Progress value={timeProgress} className="h-3 bg-purple-900" />
        </div>
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl p-8 md:p-12 mb-8 shadow-2xl text-center">
          <h2 className="text-3xl md:text-5xl font-black text-white">{currentQuestion.question_text}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {currentQuestion.answers.map((answer: any, index: number) => (
              <Button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                disabled={selectedAnswer !== null}
                className={`h-auto min-h-32 p-8 rounded-3xl text-2xl font-bold transition-all border-4 ${
                  selectedAnswer === index ? "bg-purple-600 border-purple-400" : "bg-white/10 border-white/20 hover:bg-white/20"
                }`}
              >
                {typeof answer === "string" ? answer : answer.text}
              </Button>
            ))}
        </div>
      </div>
    </div>
  );
};

export default PlayGame;