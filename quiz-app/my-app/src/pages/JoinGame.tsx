import React from 'react'; 
import { useState } from "react";
import { Button } from  "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, LogIn } from "lucide-react";
import { useToast } from  "@/hooks/use-toast";

const JoinGame = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [gamePin, setGamePin] = useState("");
  const [nickname, setNickname] = useState("");

  const joinGame = () => {
    if (!gamePin.trim() || !nickname.trim()) {
      toast({
        title: "Missing information",
        description: "Please enter both game PIN and nickname",
        variant: "destructive",
      });
      return;
    }

    // Store player info for demo
    localStorage.setItem("playerName", nickname);
    localStorage.setItem("gamePin", gamePin);
    
    // For demo, redirect to lobby if there's a quiz
    const quiz = localStorage.getItem("currentQuiz");
    if (quiz) {
      navigate("/lobby");
    } else {
      toast({
        title: "Game not found",
        description: "Please check the game PIN and try again",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen gradient-hero relative overflow-hidden flex items-center justify-center px-4">
      {/* Background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-primary/20 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative z-10 w-full max-w-md">
        <Button
          variant="outline"
          onClick={() => navigate("/")}
          className="mb-8"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Home
        </Button>

        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-2xl">
          <h1 className="text-4xl font-black text-white mb-2 text-center">Join Game</h1>
          <p className="text-white/80 text-center mb-8">Enter the game PIN to start playing</p>

          <div className="space-y-6">
            <div>
              <label className="text-white font-medium mb-2 block text-sm">Game PIN</label>
              <Input
                type="text"
                placeholder="123456"
                value={gamePin}
                onChange={(e) => setGamePin(e.target.value)}
                className="h-16 text-3xl font-bold text-center tracking-wider bg-white/90"
                maxLength={6}
              />
            </div>

            <div>
              <label className="text-white font-medium mb-2 block text-sm">Your Nickname</label>
              <Input
                type="text"
                placeholder="Enter your name..."
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                className="h-14 text-xl bg-white/90"
                maxLength={20}
              />
            </div>

            <Button
              variant="default"
              size="xl"
              onClick={joinGame}
              className="w-full"
            >
              <LogIn className="mr-2 h-5 w-5" />
              Join Game
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JoinGame;