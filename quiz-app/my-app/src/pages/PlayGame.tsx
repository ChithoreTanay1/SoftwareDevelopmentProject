// File: src/pages/PlayGame.tsx
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

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(20);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [gameStarted, setGameStarted] = useState(false); // Track if server confirmed game start
  const [quiz, setQuiz] = useState<any>(null);

  const playerId = localStorage.getItem("playerId");
  const roomCode = localStorage.getItem("roomCode");

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
        console.log("Connecting to WebSocket:", { roomCode, playerId });

        await manager.connect(
          roomCode,
          playerId,
          (message: WSMessage) => {
            if (!mounted) return;
            console.log("WebSocket message:", message);

            switch (message.type) {
              case "game_started":
                // Server confirms the game has started
                console.log("Game started by server:", message.data);
                if (message.data?.quiz) {
                  setQuiz(message.data.quiz);
                  setCurrentQuestionIndex(message.data.currentQuestionIndex || 0);
                  setScore(message.data.score || 0);
                  setGameStarted(true);
                }
                break;

              case "question":
                // Server sends the current question
                console.log("Received question from server:", message.data);
                if (message.data?.questionIndex !== undefined) {
                  setCurrentQuestionIndex(message.data.questionIndex);
                  setSelectedAnswer(null);
                  setShowResult(false);
                  setTimeLeft(message.data.timeLimit || 20);
                }
                break;

              case "leaderboard_update":
                console.log("Leaderboard updated:", message.data);
                break;

              case "question_ended":
                console.log("Question ended:", message.data);
                break;

              case "game_ended":
                console.log("Game ended:", message.data);
                if (message.data?.finalScore) {
                  localStorage.setItem("finalScore", message.data.finalScore.toString());
                }
                navigate("/results");
                break;

              case "error":
                console.error("Server error:", message.data);
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
            console.error("WebSocket error:", error);
            toast({
              title: "Connection Error",
              description: "Lost connection to game server",
              variant: "destructive",
            });
          },
          (event) => {
            if (!mounted) return;
            console.log("WebSocket closed:", event);
            setWsConnected(false);
            setGameStarted(false);
          }
        );

        if (mounted) setWsConnected(true);
      } catch (error) {
        if (!mounted) return;
        console.error("Failed to connect WebSocket:", error);
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
    if (!currentQuestion) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          handleTimeUp();
          return currentQuestion.timeLimit || 20;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentQuestionIndex, quiz, wsConnected, gameStarted]);

  const handleTimeUp = () => {
    if (selectedAnswer !== null) return;
    console.log("Time up - auto-submitting");
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
    const timeTaken = currentQuestion.timeLimit - timeLeft;
    const isCorrect = answerIndex !== -1 && currentQuestion.correctAnswer === answerIndex;

    try {
      wsManagerRef.current.submitAnswer(
        currentQuestion.id,
        answerIndex >= 0 ? currentQuestion.answers[answerIndex] : "",
        timeTaken
      );

      if (isCorrect) {
        const points = Math.round((timeLeft / currentQuestion.timeLimit) * 1000);
        const newScore = score + points;
        setScore(newScore);

        toast({
          title: "Correct!",
          description: `+${points} points!`,
          variant: "default",
        });
      } else if (answerIndex !== -1) {
        toast({
          title: "Incorrect",
          description: "The correct answer was highlighted",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error("Failed to submit answer:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to submit answer",
        variant: "destructive",
      });
    }

    // Let the server send the next question or game_ended
    // setTimeout(handleNextQuestion, 2000);
  };

  if (!playerId || !roomCode) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-destructive">Game data missing</h1>
          <p className="text-muted-foreground mt-2">Redirecting...</p>
          <Button onClick={() => navigate("/")} className="mt-4">
            Return to Home
          </Button>
        </div>
      </div>
    );
  }

  if (!wsConnected || !gameStarted || !quiz) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">
            {!wsConnected ? "Connecting to game..." : "Waiting for game to start..."}
          </h1>
          <p className="text-muted-foreground mt-2">Please wait</p>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];
  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Invalid question index</h1>
          <p className="text-muted-foreground mt-2">
            Expected question {currentQuestionIndex}, but quiz only has {quiz.questions.length}
          </p>
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
  const timeProgress = (timeLeft / currentQuestion.timeLimit) * 100;

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="bg-card rounded-3xl p-6 mb-6 shadow-lg border-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-2xl font-bold">
                <Timer className="h-6 w-6 text-primary" />
                <span className={timeLeft <= 5 ? "text-red-500 animate-pulse" : ""}>
                  {timeLeft}s
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                Question {currentQuestionIndex + 1} of {quiz.questions.length}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Your Score</div>
              <div className="text-3xl font-black text-gradient">{score}</div>
            </div>
          </div>
          <Progress value={timeProgress} className="h-3" />
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl p-8 md:p-12 mb-8 shadow-2xl text-center animate-in fade-in slide-in-from-bottom-4">
          <h2 className="text-3xl md:text-5xl font-black text-white">{currentQuestion.question}</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {currentQuestion.answers.map((answer: string, index: number) => {
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
                    : `${answerColorClasses[index]} text-white`
                }`}
              >
                <span className="text-4xl mr-4">{answerShapes[index]}</span>
                <span className="flex-1 text-left">{answer}</span>
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