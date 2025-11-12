import React from 'react'; 
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Plus, Trash2, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

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

  const startQuiz = () => {
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

    // Store quiz data in localStorage for demo purposes
    localStorage.setItem("currentQuiz", JSON.stringify({ title: quizTitle, questions }));
    navigate("/lobby");
  };

  // FIXED: Use actual Tailwind classes instead of dynamic strings
  const getAnswerColorClass = (index: number, isCorrect: boolean) => {
    const baseClasses = "border-0 h-20 text-lg font-medium ";
    const colorClasses = [
      "bg-red-100 hover:bg-red-200",    // Answer 1 - red
      "bg-blue-100 hover:bg-blue-200",  // Answer 2 - blue  
      "bg-yellow-100 hover:bg-yellow-200", // Answer 3 - yellow
      "bg-green-100 hover:bg-green-200" // Answer 4 - green
    ];
    return baseClasses + colorClasses[index];
  };

  const getCorrectButtonClass = (index: number, isCorrect: boolean) => {
    const colorClasses = [
      "bg-red-500 text-white",    // Answer 1 - red
      "bg-blue-500 text-white",   // Answer 2 - blue  
      "bg-yellow-500 text-white", // Answer 3 - yellow
      "bg-green-500 text-white"  // Answer 4 - green
    ];
    return isCorrect ? colorClasses[index] : "bg-gray-300";
  };

  const getBorderClass = (index: number, isCorrect: boolean) => {
    const colorClasses = [
      "border-red-500",    // Answer 1 - red
      "border-blue-500",   // Answer 2 - blue  
      "border-yellow-500", // Answer 3 - yellow
      "border-green-500"  // Answer 4 - green
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
          >
            <Plus className="mr-2 h-5 w-5" />
            Add Question
          </Button>
          <Button
            variant="default" /* CHANGED from "hero" to "default" */
            size="lg"
            onClick={startQuiz}
            className="flex-1"
          >
            <Play className="mr-2 h-5 w-5" />
            Start Quiz
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CreateQuiz;