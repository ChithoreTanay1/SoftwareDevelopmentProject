import React from 'react';
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Plus, Trash2, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  QuizzesService, 
  RoomsService, 
  QuestionType,
  checkBackendAvailability,
  MockQuizzesService,
  
  MockRoomsService,
  
} from "@/api/client";

interface Question {
  id: string;
  question: string;
  answers: string[];
  correctAnswer: number;
  timeLimit: number;
}

const CreateQuiz = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [quizTitle, setQuizTitle] = useState("");
  const [questions, setQuestions] = useState<Question[]>([
    {
      id: "1",
      question: "",
      answers: ["", "", "", ""],
      correctAnswer: 0,
      timeLimit: 20,
    },
  ]);
  const [isCreating, setIsCreating] = useState(false);
  const [usingMockServices, setUsingMockServices] = useState(false);

  useEffect(() => {
    // Check backend availability on component mount
    const checkBackend = async () => {
      const isBackendAvailable = await checkBackendAvailability();
      setUsingMockServices(!isBackendAvailable);
      
      if (!isBackendAvailable) {
        toast({
          title: "Using offline mode",
          description: "Backend server not available. Using mock services.",
          variant: "default",
        });
      }
    };
    
    checkBackend();
  }, [toast]);

  const addQuestion = () => {
    const newQuestion: Question = {
      id: Date.now().toString(),
      question: "",
      answers: ["", "", "", ""],
      correctAnswer: 0,
      timeLimit: 20,
    };
    setQuestions([...questions, newQuestion]);
  };

  const removeQuestion = (id: string) => {
    if (questions.length > 1) {
      setQuestions(questions.filter((q) => q.id !== id));
    }
  };

  const updateQuestion = (id: string, field: keyof Question, value: any) => {
    setQuestions(
      questions.map((q) => (q.id === id ? { ...q, [field]: value } : q))
    );
  };

  const updateAnswer = (questionId: string, answerIndex: number, value: string) => {
    setQuestions(
      questions.map((q) => {
        if (q.id === questionId) {
          const newAnswers = [...q.answers];
          newAnswers[answerIndex] = value;
          return { ...q, answers: newAnswers };
        }
        return q;
      })
    );
  };

  const startQuiz = async () => {
    if (!quizTitle.trim()) {
      toast({
        title: "Quiz title required",
        description: "Please enter a title for your quiz",
        variant: "destructive",
      });
      return;
    }

    const hasEmptyQuestions = questions.some(
      (q) => !q.question.trim() || q.answers.some((a) => !a.trim())
    );

    if (hasEmptyQuestions) {
      toast({
        title: "Incomplete questions",
        description: "Please fill in all questions and answers",
        variant: "destructive",
      });
      return;
    }

    setIsCreating(true);

    try {
      // Use appropriate service based on backend availability
      const QuizService = usingMockServices ? MockQuizzesService : QuizzesService;
      const RoomService = usingMockServices ? MockRoomsService : RoomsService;

      // Convert to API format
      const quizPayload = {
        title: quizTitle,
        created_by: localStorage.getItem("playerName") || "QuizMaster User",
        questions: questions.map((q, index) => ({
          question_text: q.question,
          question_type: "multiple_choice" as QuestionType,
          time_limit: q.timeLimit,
          points: 1000,
          order_index: index,
          choices: q.answers.map((answer, aIndex) => ({
            choice_text: answer,
            order_index: aIndex,
            is_correct: aIndex === q.correctAnswer
          }))
        }))
      };

      console.log("📤 Sending quiz payload:", quizPayload);
      console.log("🔧 Using service:", usingMockServices ? "Mock" : "Real");

      // Create quiz on server
      const quizResponse = await QuizService.createQuiz(quizPayload);
      console.log("📥 Full quiz creation response:", quizResponse);

      let quizId;
      
      if (quizResponse.success) {
        // Try multiple possible locations for the quiz ID
        const data = quizResponse.data || quizResponse;
        
        // Look for ID in common locations
        quizId = data.id || 
                data.quiz_id || 
                data.quizId || 
                data._id ||
                (data.data && (data.data.id || data.data.quiz_id));
        
        console.log("🔍 Found quiz ID:", quizId);
        
        if (!quizId && !usingMockServices) {
          // For real API, we need the ID
          console.error("❌ Could not find quiz ID in response:", data);
          throw new Error("Quiz created but ID not found in response. Check server response format.");
        } else if (!quizId && usingMockServices) {
          // For mock, generate one
          quizId = `mock_quiz_${Date.now()}`;
          console.log("🎭 Generated mock quiz ID:", quizId);
        }
      } else {
        throw new Error(quizResponse.message || "Quiz creation failed on server");
      }

      // Create room for this quiz
      const roomPayload = {
        quiz_id: quizId,
        host_name: localStorage.getItem("playerName") || "Host",
        max_players: 10
      };

      console.log("📤 Sending room payload:", roomPayload);
      
      const roomResponse = await RoomService.createRoom(roomPayload);
      console.log("📥 Room creation response:", roomResponse);
      
      let roomCode;
      if (roomResponse.success && (roomResponse.data || roomResponse)) {
        // Try multiple possible locations for room code
        const roomData = roomResponse.data || roomResponse;
        roomCode = roomData.room_code || 
                  roomData.code || 
                  roomData.roomCode ||
                  (roomData.data && roomData.data.room_code);
        
        console.log("🔍 Found room code:", roomCode);
        
        if (!roomCode) {
          // Generate a mock room code
          roomCode = Math.floor(100000 + Math.random() * 900000).toString();
          console.warn("⚠️ Using generated room code:", roomCode);
        }
      } else {
        throw new Error(roomResponse.message || "Room creation failed");
      }

      // FIXED: Host needs to join their own room
      console.log("👤 Host joining room:", roomCode);
      const joinResponse = await RoomService.joinRoom(roomCode, {
        nickname: localStorage.getItem("playerName") || "Host"
      });
      
      console.log("📥 Host join response:", joinResponse);
      
      let playerId;
      if (joinResponse.success && (joinResponse.data || joinResponse)) {
        const joinData = joinResponse.data || joinResponse;
        playerId = joinData.player_id || 
                  joinData.id ||
                  joinData.data?.player_id;
        
        console.log("🔍 Host player ID:", playerId);
      }

      if (!playerId) {
        // Generate a player ID if not provided by server
        playerId = `host_${Date.now()}`;
        console.warn("⚠️ Using generated host player ID:", playerId);
      }

      // Save everything to localStorage
      localStorage.setItem("currentQuiz", JSON.stringify({ 
        title: quizTitle, 
        questions,
        quizId: quizId 
      }));
      localStorage.setItem("roomCode", roomCode);
      localStorage.setItem("isHost", "true");
      localStorage.setItem("playerId", playerId);
      localStorage.setItem("playerName", localStorage.getItem("playerName") || "Host");
      localStorage.setItem("finalScore", "0"); // Initialize score
      
      toast({
        title: "🎉 Quiz created successfully!",
        description: `Room code: ${roomCode} (${usingMockServices ? 'Offline Mode' : 'Online Mode'})`,
        variant: "default",
      });
      
      navigate("/lobby");
      
    } catch (error: any) {
      console.error("❌ Full error details:", error);
      toast({
        title: "Failed to create quiz",
        description: error.message || "Please check your connection and try again",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  const getAnswerColorClass = (index: number, isCorrect: boolean) => {
    const baseClasses = "border-0 h-20 text-lg font-medium ";
    const colorClasses = [
      "bg-red-100 hover:bg-red-200",
      "bg-blue-100 hover:bg-blue-200", 
      "bg-yellow-100 hover:bg-yellow-200",
      "bg-green-100 hover:bg-green-200"
    ];
    return baseClasses + colorClasses[index];
  };

  const getCorrectButtonClass = (index: number, isCorrect: boolean) => {
    const colorClasses = [
      "bg-red-500 text-white",
      "bg-blue-500 text-white", 
      "bg-yellow-500 text-white",
      "bg-green-500 text-white"
    ];
    return isCorrect ? colorClasses[index] : "bg-gray-300";
  };

  const getBorderClass = (index: number, isCorrect: boolean) => {
    const colorClasses = [
      "border-red-500",
      "border-blue-500", 
      "border-yellow-500",
      "border-green-500"
    ];
    return isCorrect ? `border-4 ${colorClasses[index]} shadow-md` : "border-2 border-gray-300";
  };

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-6"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Home
        </Button>

        {usingMockServices && (
          <div className="mb-4 p-4 bg-yellow-100 border border-yellow-400 rounded-lg">
            <p className="text-yellow-800 font-medium">
              ⚠️ Working in offline mode. Data will be saved locally only.
            </p>
          </div>
        )}

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gradient mb-4">Create Your Quiz</h1>
          <Input
            placeholder="Enter quiz title..."
            value={quizTitle}
            onChange={(e) => setQuizTitle(e.target.value)}
            className="text-2xl font-bold h-14 border-2"
          />
        </div>

        <div className="space-y-6 mb-8">
          {questions.map((question, qIndex) => (
            <Card key={question.id} className="p-6 border-2 transition-smooth hover:shadow-lg">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-bold text-primary">Question {qIndex + 1}</h3>
                {questions.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeQuestion(question.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <Input
                placeholder="Enter your question..."
                value={question.question}
                onChange={(e) =>
                  updateQuestion(question.id, "question", e.target.value)
                }
                className="mb-4 text-lg font-medium"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {question.answers.map((answer, aIndex) => (
                  <div
                    key={aIndex}
                    className={`relative rounded-xl overflow-hidden transition-smooth ${getBorderClass(aIndex, question.correctAnswer === aIndex)}`}
                  >
                    <Input
                      placeholder={`Answer ${aIndex + 1}`}
                      value={answer}
                      onChange={(e) =>
                        updateAnswer(question.id, aIndex, e.target.value)
                      }
                      className={getAnswerColorClass(aIndex, question.correctAnswer === aIndex)}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        updateQuestion(question.id, "correctAnswer", aIndex)
                      }
                      className={`absolute top-2 right-2 h-8 w-8 p-0 rounded-full ${getCorrectButtonClass(aIndex, question.correctAnswer === aIndex)}`}
                    >
                      ✓
                    </Button>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-4">
                <label className="text-sm font-medium">Time Limit:</label>
                <Input
                  type="number"
                  min="5"
                  max="120"
                  value={question.timeLimit}
                  onChange={(e) =>
                    updateQuestion(
                      question.id,
                      "timeLimit",
                      parseInt(e.target.value) || 20
                    )
                  }
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">seconds</span>
              </div>
            </Card>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button
            variant="outline"
            size="lg"
            onClick={addQuestion}
            className="flex-1"
            disabled={isCreating}
          >
            <Plus className="mr-2 h-5 w-5" />
            Add Question
          </Button>
          <Button
            variant="default"
            size="lg"
            onClick={startQuiz}
            className="flex-1"
            disabled={isCreating}
          >
            {isCreating ? (
              <>
                <div className="h-5 w-5 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                {usingMockServices ? "Creating (Offline)..." : "Creating..."}
              </>
            ) : (
              <>
                <Play className="mr-2 h-5 w-5" />
                {usingMockServices ? "Start Quiz (Offline)" : "Start Quiz"}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CreateQuiz;