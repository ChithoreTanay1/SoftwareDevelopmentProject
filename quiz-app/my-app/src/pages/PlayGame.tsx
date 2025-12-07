import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Timer, CheckCircle2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { WebSocketManager, WSMessage } from "@/api/client";

const PlayGame = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const wsManagerRef = useRef<WebSocketManager>(new WebSocketManager());

  const playerId = localStorage.getItem("playerId");
  const roomCode = localStorage.getItem("roomCode");

  // Initialize state from localStorage
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

  // Initialize timer when quiz loads
  useEffect(() => {
    if (quiz && quiz.questions[currentQuestionIndex]) {
      setTimeLeft(quiz.questions[currentQuestionIndex].time_limit || 20);
    }
  }, [currentQuestionIndex, quiz]);

  // Redirect if missing required data
  useEffect(() => {
    if (!playerId || !roomCode) {
      console.error("Missing required data:", { playerId, roomCode });
      navigate("/");
    }
  }, [playerId, roomCode, navigate]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!roomCode || !playerId) return;

    let mounted = true;
    const manager = wsManagerRef.current;

    const initWebSocket = async () => {
      try {
        console.log("🎮 PlayGame: Connecting to WebSocket:", { roomCode, playerId });

        await manager.connect(
          roomCode,
          playerId,
          (message: WSMessage) => {
            if (!mounted) return;
            console.log("📨 PlayGame: WebSocket message:", message.type, message.data);

            switch (message.type) {
              case "game_started":
                // Server confirms the game has started
                console.log("✅ Game started by server:", message.data);
                if (message.data?.quiz) {
                  localStorage.setItem("quizData", JSON.stringify(message.data.quiz));
                  setQuiz(message.data.quiz);
                  setCurrentQuestionIndex(message.data.currentQuestionIndex || 0);
                  setScore(message.data.score || 0);
                  setGameStarted(true);
                }
                break;

              case "question":
                // Server sends the current question
                console.log("📝 Received question from server:", message.data);
                if (message.data?.questionIndex !== undefined) {
                  setCurrentQuestionIndex(message.data.questionIndex);
                  setSelectedAnswer(null);
                  setShowResult(false);
                  setTimeLeft(message.data.timeLimit || 20);
                }
                break;

              case "leaderboard_update":
                console.log("🏆 Leaderboard updated:", message.data);
                break;

              case "question_ended":
                console.log("⏱️ Question ended:", message.data);
                if (message.data?.correctAnswer !== undefined) {
                  // Show correct answer even if player didn't answer
                  setShowResult(true);
                }
                break;

                case "game_ended":
                  console.log("🏁 Game ended:", message.data);
  // Get the current player's score from the leaderboard
                  if (message.data?.final_leaderboard?.players) {
                    const currentPlayerName = localStorage.getItem("playerName") || "You";
                    const currentPlayer = message.data.final_leaderboard.players.find((p: any) => p.nickname === currentPlayerName);
                    if (currentPlayer) {
                      localStorage.setItem("finalScore", currentPlayer.total_score.toString());
                      console.log("Saved final score:", currentPlayer.total_score);
                    }
                  }
                  navigate("/results");
                  break;

              case "error":
                console.error("❌ Server error:", message.data);
                toast({
                  title: "Error",
                  description: message.data?.message || "An error occurred",
                  variant: "destructive",
                });
                break;
            }
          },
          (error) => {
            if (!mounted) return;
            console.error("❌ WebSocket error:", error);
            toast({
              title: "Connection Error",
              description: "Lost connection to game server",
              variant: "destructive",
            });
            setWsConnected(false);
          },
          (event) => {
            if (!mounted) return;
            console.log("WebSocket closed:", event);
            setWsConnected(false);
            setGameStarted(false);
          }
        );

        if (mounted) {
          setWsConnected(true);
          console.log("✅ PlayGame WebSocket connected");
        }
      } catch (error) {
        if (!mounted) return;
        console.error("❌ Failed to connect WebSocket:", error);
        toast({
          title: "Connection Failed",
          description: "Could not connect to game server",
          variant: "destructive",
        });
      }
    };

    initWebSocket();

    return () => {
      mounted = false;
      manager.disconnect();
    };
  }, [roomCode, playerId, navigate, toast]);

  // Timer effect - only runs if game has started
  useEffect(() => {
    if (!wsConnected || !gameStarted || !quiz) return;

    const currentQuestion = quiz.questions[currentQuestionIndex];
    if (!currentQuestion || selectedAnswer !== null) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          handleTimeUp();
          return currentQuestion.time_limit || 20;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentQuestionIndex, quiz, wsConnected, gameStarted, selectedAnswer]);

  const handleTimeUp = () => {
    if (selectedAnswer !== null) return;
    console.log("⏱️ Time up - auto-submitting");
    handleAnswerSelect(-1);
  };

  const handleAnswerSelect = (answerIndex: number) => {
    if (selectedAnswer !== null || showResult) return;
    if (!wsManagerRef.current.isConnected()) {
      toast({
        title: "Error",
        description: "Not connected to game server",
        variant: "destructive",
      });
      return;
    }

    if (!quiz) {
      toast({
        title: "Error",
        description: "Quiz data not loaded",
        variant: "destructive",
      });
      return;
    }

    setSelectedAnswer(answerIndex);
    setShowResult(true);

    const currentQuestion = quiz.questions[currentQuestionIndex];
    const timeTaken = currentQuestion.time_limit - timeLeft;
    const isCorrect = answerIndex !== -1 && currentQuestion.correctAnswer === answerIndex;

    try {
      // Get the choice ID from the answers array
      let choiceId = "";
      if (answerIndex >= 0 && currentQuestion.answers && currentQuestion.answers[answerIndex]) {
        const answer = currentQuestion.answers[answerIndex];
        // If answer is an object with id property, use it; otherwise use the text
        choiceId = answer.id || answer;
      }

      console.log("📤 Submitting answer:", {
        questionId: currentQuestion.id,
        choiceId: choiceId,
        timeTaken: timeTaken,
        isCorrect: isCorrect
      });

      wsManagerRef.current.submitAnswer(
        currentQuestion.id,
        choiceId,
        timeTaken
      );

      if (isCorrect) {
        const points = Math.round((timeLeft / currentQuestion.time_limit) * 1000);
        const newScore = score + points;
        setScore(newScore);
        localStorage.setItem("score", newScore.toString());

        toast({
          title: "✅ Correct!",
          description: `+${points} points!`,
          variant: "default",
        });
      } else if (answerIndex !== -1) {
        toast({
          title: "❌ Incorrect",
          description: "The correct answer was highlighted",
          variant: "destructive",
        });
      } else {
        toast({
          title: "⏱️ Time's up!",
          description: "Moving to next question",
          variant: "default",
        });
      }
    } catch (error: any) {
      console.error("❌ Failed to submit answer:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to submit answer",
        variant: "destructive",
      });
    }

    // Let the server send the next question or game_ended
  };

  // Loading states
  if (!playerId || !roomCode) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">Game data missing</h1>
          <p className="text-purple-200 mt-2">Redirecting...</p>
          <Button onClick={() => navigate("/")} className="mt-4">
            Return to Home
          </Button>
        </div>
      </div>
    );
  }

  if (!wsConnected || !gameStarted || !quiz) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-300 border-t-white mx-auto mb-4"></div>
          <h1 className="text-2xl font-bold text-white">
            {!wsConnected ? "🔌 Connecting to game..." : "⏳ Loading game..."}
          </h1>
          <p className="text-purple-200 mt-2">Please wait</p>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">Invalid question</h1>
          <p className="text-purple-200 mt-2">
            Expected question {currentQuestionIndex + 1}, but quiz only has {quiz.questions.length}
          </p>
          <Button onClick={() => navigate("/")} className="mt-4">
            Return to Home
          </Button>
        </div>
      </div>
    );
  }

  const answerColorClasses = [
    "bg-red-500 border-red-500 hover:bg-red-600",
    "bg-blue-500 border-blue-500 hover:bg-blue-600",
    "bg-yellow-500 border-yellow-500 hover:bg-yellow-600",
    "bg-green-500 border-green-500 hover:bg-green-600",
  ];
  const answerShapes = ["◆", "●", "▲", "■"];
  const timeProgress = (timeLeft / (currentQuestion.time_limit || 20)) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header with timer and score */}
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-6 mb-6 shadow-lg border-2 border-white/20">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-2xl font-bold text-white">
                <Timer className={`h-6 w-6 ${timeLeft <= 5 ? "text-red-500 animate-pulse" : "text-purple-300"}`} />
                <span className={timeLeft <= 5 ? "text-red-500 animate-pulse" : "text-white"}>
                  {timeLeft}s
                </span>
              </div>
              <div className="text-sm text-purple-200">
                Question {currentQuestionIndex + 1} of {quiz.questions.length}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-purple-200">Your Score</div>
              <div className="text-3xl font-black text-white">{score}</div>
            </div>
          </div>
          <Progress value={timeProgress} className="h-3 bg-purple-900" />
        </div>

        {/* Question */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl p-8 md:p-12 mb-8 shadow-2xl text-center animate-in fade-in slide-in-from-bottom-4">
          <h2 className="text-3xl md:text-5xl font-black text-white">{currentQuestion.question_text}</h2>
        </div>

        {/* Answer Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {currentQuestion.answers.map((answer: any, index: number) => {
            const answerText = typeof answer === "string" ? answer : answer.text;
            const isSelected = selectedAnswer === index;
            const isCorrect = currentQuestion.correctAnswer === index;
            const showCorrect = showResult && isCorrect;
            const showIncorrect = showResult && isSelected && !isCorrect;

            return (
              <Button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                disabled={selectedAnswer !== null}
                className={`h-auto min-h-32 p-8 rounded-3xl text-2xl font-bold transition-all border-4 relative overflow-hidden group ${
                  showCorrect
                    ? "bg-green-500 border-green-600 text-white scale-105"
                    : showIncorrect
                    ? "bg-red-500 border-red-600 text-white opacity-50"
                    : `${answerColorClasses[index % 4]} text-white`
                }`}
              >
                <span className="text-4xl mr-4">{answerShapes[index % 4]}</span>
                <span className="flex-1 text-left">{answerText}</span>
                {showCorrect && <CheckCircle2 className="absolute right-4 h-12 w-12 animate-in zoom-in" />}
              </Button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PlayGame;