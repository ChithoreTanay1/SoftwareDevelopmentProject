import React from "react"; 
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Users, Play, Copy, Check } from "lucide-react";
import { useToast } from  "@/hooks/use-toast";

const GameLobby = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [gamePin] = useState(Math.floor(100000 + Math.random() * 900000).toString());
  const [copied, setCopied] = useState(false);
  const [players, setPlayers] = useState<string[]>([]);

  useEffect(() => {
    // Simulate players joining for demo
    const playerName = localStorage.getItem("playerName");
    if (playerName) {
      setPlayers([playerName]);
    }

    // Simulate more players joining
    const interval = setInterval(() => {
      const demoNames = ["Alex", "Jordan", "Sam", "Taylor", "Casey", "Morgan"];
      const randomName = demoNames[Math.floor(Math.random() * demoNames.length)];
      setPlayers((prev) => {
        if (prev.length < 8 && !prev.includes(randomName)) {
          return [...prev, randomName];
        }
        return prev;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const copyGamePin = () => {
    navigator.clipboard.writeText(gamePin);
    setCopied(true);
    toast({
      title: "Game PIN copied!",
      description: "Share it with your players",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const startGame = () => {
    if (players.length === 0) {
      toast({
        title: "No players",
        description: "Wait for players to join before starting",
        variant: "destructive",
      });
      return;
    }
    navigate("/play");
  };

  return (
    <div className="min-h-screen gradient-hero relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-primary/20 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        <div className="max-w-4xl w-full">
          {/* Game PIN Section */}
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-white/80 mb-4">Game PIN</h2>
            <div className="inline-flex items-center gap-4 bg-white/20 backdrop-blur-xl rounded-3xl px-8 py-6 border-4 border-white/30">
              <span className="text-6xl md:text-8xl font-black text-white tracking-wider">
                {gamePin}
              </span>
              <Button
                variant="outline"
                size="icon"
                onClick={copyGamePin}
                className="h-14 w-14"
              >
                {copied ? <Check className="h-6 w-6" /> : <Copy className="h-6 w-6" />}
              </Button>
            </div>
            <p className="text-white/80 mt-4 text-lg">
              Share this PIN with players to join the game
            </p>
          </div>

          {/* Players Section */}
          <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                <Users className="h-7 w-7" />
                Players ({players.length})
              </h3>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {players.map((player, index) => (
                <div
                  key={index}
                  className="bg-white/20 rounded-2xl p-4 text-center backdrop-blur-sm border border-white/20 transition-smooth hover:bg-white/30 hover:scale-105 animate-in fade-in slide-in-from-bottom-4"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="w-12 h-12 rounded-full bg-gradient-primary mx-auto mb-3 flex items-center justify-center text-2xl font-bold text-white">
                    {player[0].toUpperCase()}
                  </div>
                  <p className="text-white font-medium truncate">{player}</p>
                </div>
              ))}
            </div>

            {players.length === 0 && (
              <div className="text-center py-12">
                <div className="animate-pulse-slow inline-block">
                  <Users className="h-16 w-16 text-white/40 mx-auto mb-4" />
                </div>
                <p className="text-white/60 text-lg">Waiting for players to join...</p>
              </div>
            )}
          </div>

          {/* Start Button */}
          <div className="text-center">
            <Button
              variant="default"
              size="xl"
              onClick={startGame}
              disabled={players.length === 0}
              className="group"
            >
              <Play className="mr-2 h-6 w-6 transition-transform group-hover:scale-110" />
              Start Game
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameLobby;