// components/host/QuizCreator.jsx
import React, { useState } from 'react';
import '../../styles/QuizCreator.css';

const QuizCreator = ({ onQuizCreated }) => {
  const [quiz, setQuiz] = useState({
    title: '',
    description: '',
    questions: [
      {
        question_text: '',
        question_type: 'multiple_choice',
        time_limit: 30,
        points: 100,
        order_index: 0,
        choices: [
          { choice_text: '', is_correct: false, order_index: 0 },
          { choice_text: '', is_correct: false, order_index: 1 },
          { choice_text: '', is_correct: false, order_index: 2 },
          { choice_text: '', is_correct: false, order_index: 3 },
        ]
      }
    ]
  });

  const addQuestion = () => {
    setQuiz(prev => ({
      ...prev,
      questions: [
        ...prev.questions,
        {
          question_text: '',
          question_type: 'multiple_choice',
          time_limit: 30,
          points: 100,
          order_index: prev.questions.length,
          choices: [
            { choice_text: '', is_correct: false, order_index: 0 },
            { choice_text: '', is_correct: false, order_index: 1 },
            { choice_text: '', is_correct: false, order_index: 2 },
            { choice_text: '', is_correct: false, order_index: 3 },
          ]
        }
      ]
    }));
  };

  const updateQuestion = (index, field, value) => {
    setQuiz(prev => ({
      ...prev,
      questions: prev.questions.map((q, i) => 
        i === index ? { ...q, [field]: value } : q
      )
    }));
  };

  const updateChoice = (qIndex, cIndex, field, value) => {
    setQuiz(prev => ({
      ...prev,
      questions: prev.questions.map((q, i) => 
        i === qIndex ? {
          ...q,
          choices: q.choices.map((choice, j) =>
            j === cIndex ? { ...choice, [field]: value } : choice
          )
        } : q
      )
    }));
  };

  const setCorrectAnswer = (qIndex, cIndex) => {
    setQuiz(prev => ({
      ...prev,
      questions: prev.questions.map((q, i) => 
        i === qIndex ? {
          ...q,
          choices: q.choices.map((choice, j) => ({
            ...choice,
            is_correct: j === cIndex
          }))
        } : q
      )
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onQuizCreated(quiz);
  };

  return (
    <form onSubmit={handleSubmit} className="quiz-creator">
      <div className="quiz-basic-info">
        <input
          type="text"
          placeholder="Quiz Title"
          value={quiz.title}
          onChange={(e) => setQuiz(prev => ({ ...prev, title: e.target.value }))}
          className="quiz-title-input"
          required
        />
        <textarea
          placeholder="Quiz Description (optional)"
          value={quiz.description}
          onChange={(e) => setQuiz(prev => ({ ...prev, description: e.target.value }))}
          className="quiz-description-input"
        />
      </div>

      <div className="questions-list">
        {quiz.questions.map((question, qIndex) => (
          <div key={qIndex} className="question-card">
            <div className="question-header">
              <h3>Question {qIndex + 1}</h3>
              {quiz.questions.length > 1 && (
                <button
                  type="button"
                  onClick={() => setQuiz(prev => ({
                    ...prev,
                    questions: prev.questions.filter((_, i) => i !== qIndex)
                  }))}
                  className="delete-question-btn"
                >
                  Delete
                </button>
              )}
            </div>

            <input
              type="text"
              placeholder="Enter your question"
              value={question.question_text}
              onChange={(e) => updateQuestion(qIndex, 'question_text', e.target.value)}
              className="question-text-input"
              required
            />

            <div className="question-settings">
              <label>
                Time Limit (seconds):
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={question.time_limit}
                  onChange={(e) => updateQuestion(qIndex, 'time_limit', parseInt(e.target.value))}
                />
              </label>
              <label>
                Points:
                <input
                  type="number"
                  min="10"
                  max="1000"
                  value={question.points}
                  onChange={(e) => updateQuestion(qIndex, 'points', parseInt(e.target.value))}
                />
              </label>
            </div>

            <div className="choices-list">
              <h4>Answer Choices</h4>
              {question.choices.map((choice, cIndex) => (
                <div key={cIndex} className="choice-item">
                  <button
                    type="button"
                    onClick={() => setCorrectAnswer(qIndex, cIndex)}
                    className={`correct-toggle ${choice.is_correct ? 'correct' : ''}`}
                  >
                    {choice.is_correct ? '✓' : '○'}
                  </button>
                  <input
                    type="text"
                    placeholder={`Choice ${cIndex + 1}`}
                    value={choice.choice_text}
                    onChange={(e) => updateChoice(qIndex, cIndex, 'choice_text', e.target.value)}
                    className="choice-input"
                    required
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="quiz-actions">
        <button type="button" onClick={addQuestion} className="add-question-btn">
          + Add Question
        </button>
        <button type="submit" className="create-quiz-btn">
          Create Quiz & Start Game
        </button>
      </div>
    </form>
  );
};

export default QuizCreator;