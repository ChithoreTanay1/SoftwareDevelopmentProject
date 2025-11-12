import React from 'react'; 
import { Button } from  "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Gamepad2, Plus, Trophy } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen gradient-hero relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-primary/20 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        {/* Logo/Title */}
        <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="inline-flex items-center justify-center w-20 h-20 mb-6 rounded-2xl bg-white/20 backdrop-blur-sm shadow-lg">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-6xl md:text-8xl font-black text-white mb-4 drop-shadow-lg">
            QuizMaster
          </h1>
          <p className="text-xl md:text-2xl text-white/90 font-medium">
            Create. Play. Learn. Win.
          </p>
        </div>

        {/* Main Actions */}
        <div className="flex flex-col sm:flex-row gap-6 mb-16 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
          <Button
            variant="default"
            size="xl"
            onClick={() => navigate("/create")}
            className="group"
          >
            <Plus className="mr-2 h-6 w-6 transition-transform group-hover:rotate-90" />
            Create Quiz
          </Button>
          <Button
            variant="outline"
            size="xl"
            onClick={() => navigate("/join")}
            className="group"
          >
            <Gamepad2 className="mr-2 h-6 w-6 transition-transform group-hover:scale-110" />
            Join Game
          </Button>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full animate-in fade-in slide-in-from-bottom-12 duration-700 delay-300">
          <FeatureCard
            icon="🎯"
            title="Interactive Quizzes"
            description="Create engaging quizzes with multiple choice questions"
          />
          <FeatureCard
            icon="⚡"
            title="Real-time Play"
            description="Compete with others in live quiz sessions"
          />
          <FeatureCard
            icon="🏆"
            title="Leaderboards"
            description="Track scores and see who comes out on top"
          />
        </div>
      </div>
    </div>
  );
};

const FeatureCard = ({ icon, title, description }: { icon: string; title: string; description: string }) => (
  <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 transition-smooth hover:bg-white/20 hover:scale-105 hover:shadow-2xl">
    <div className="text-4xl mb-3">{icon}</div>
    <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
    <p className="text-white/80">{description}</p>
  </div>
);

export default Index;