import React from 'react'; 
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Timer, CheckCircle2 } from "lucide-react";
import { Progress } from  "@/components/ui/progress";

const PlayGame = () => {
  const navigate = useNavigate();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(20);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [showResult, setShowResult] = useState(false);

  // Load quiz data
  const quizData = localStorage.getItem("currentQuiz");
  const quiz = quizData ? JSON.parse(quizData) : null;

  useEffect(() => {
    if (!quiz) {
      navigate("/");
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          handleNextQuestion();
          return quiz.questions[currentQuestionIndex]?.timeLimit || 20;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentQuestionIndex, quiz]);

  const handleAnswerSelect = (answerIndex: number) => {
    if (selectedAnswer !== null || showResult) return;

    setSelectedAnswer(answerIndex);
    setShowResult(true);

    const isCorrect =
      quiz.questions[currentQuestionIndex].correctAnswer === answerIndex;
    
    if (isCorrect) {
      const points = Math.round((timeLeft / quiz.questions[currentQuestionIndex].timeLimit) * 1000);
      setScore(score + points);
    }

    setTimeout(() => {
      handleNextQuestion();
    }, 2000);
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setSelectedAnswer(null);
      setShowResult(false);
      setTimeLeft(quiz.questions[currentQuestionIndex + 1].timeLimit);
    } else {
      // Game over - go to results
      localStorage.setItem("finalScore", score.toString());
      navigate("/results");
    }
  };

  if (!quiz) return null;

  const currentQuestion = quiz.questions[currentQuestionIndex];
  
  // FIXED: Use actual Tailwind color classes
  const answerColorClasses = [
    "bg-red-500 border-red-500 hover:bg-red-600",    // Answer 1
    "bg-blue-500 border-blue-500 hover:bg-blue-600",  // Answer 2  
    "bg-yellow-500 border-yellow-500 hover:bg-yellow-600", // Answer 3
    "bg-green-500 border-green-500 hover:bg-green-600" // Answer 4
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
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Score</div>
              <div className="text-3xl font-black text-gradient">{score}</div>
            </div>
          </div>
          <Progress value={timeProgress} className="h-3" />
        </div>

        {/* Question */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl p-8 md:p-12 mb-8 shadow-2xl text-center animate-in fade-in slide-in-from-bottom-4">
          <div className="text-white/80 text-lg mb-4">
            Question {currentQuestionIndex + 1} of {quiz.questions.length}
          </div>
          <h2 className="text-3xl md:text-5xl font-black text-white">
            {currentQuestion.question}
          </h2>
        </div>

        {/* Answers */}
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
                {showCorrect && (
                  <CheckCircle2 className="absolute right-4 h-12 w-12 animate-in zoom-in" />
                )}
              </Button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PlayGame;