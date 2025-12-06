import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Trophy, Home, RotateCcw, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { RoomsService } from "@/api/client";

interface PlayerScore {
  player_id: string;
  nickname: string;
  total_score: number;
  rank: number;
  is_connected: boolean;
}

const Results = () => {
  const navigate = useNavigate();
  const [finalScore] = useState(parseInt(localStorage.getItem("finalScore") || "0"));
  const [leaderboard, setLeaderboard] = useState<PlayerScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const roomCode = localStorage.getItem("roomCode");
        const playerName = localStorage.getItem("playerName") || "You";
        const playerId = localStorage.getItem("playerId") || `player_${Date.now()}`;

        if (!roomCode) {
          // If no room code, create a mock leaderboard with current player
          setLeaderboard([
            {
              player_id: playerId,
              nickname: playerName,
              total_score: finalScore,
              rank: 1,
              is_connected: true
            }
          ]);
          setLoading(false);
          return;
        }

        console.log("Fetching leaderboard for room:", roomCode);
        const response = await RoomsService.getRoomLeaderboard(roomCode);
        console.log("Leaderboard API response:", response);

        // FIXED: Handle LeaderboardResponse type correctly
        if (response && response.players) {
          // Direct LeaderboardResponse - already has players array
          const sortedPlayers = response.players
            .sort((a: PlayerScore, b: PlayerScore) => b.total_score - a.total_score)
            .map((player: PlayerScore, index: number) => ({
              ...player,
              rank: index + 1
            }));
          
          setLeaderboard(sortedPlayers);
        } else {
          throw new Error("Invalid leaderboard response format");
        }
      } catch (error: any) {
        console.error("Failed to fetch leaderboard:", error);
        setError(error.message || "Could not load leaderboard");
        
        // Fallback: create mock data with current player
        const playerName = localStorage.getItem("playerName") || "You";
        const playerId = localStorage.getItem("playerId") || `player_${Date.now()}`;
        setLeaderboard([
          {
            player_id: playerId,
            nickname: playerName,
            total_score: finalScore,
            rank: 1,
            is_connected: true
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, [finalScore]);

  const topPlayer = leaderboard[0] || { 
    nickname: localStorage.getItem("playerName") || "You", 
    total_score: finalScore 
  };

  const podiumColors = ["#FFD700", "#C0C0C0", "#CD7F32"];

  if (loading) {
    return (
      <div className="min-h-screen gradient-hero relative overflow-hidden flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 text-white animate-spin mx-auto mb-4" />
          <p className="text-white text-xl">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  if (error && leaderboard.length === 0) {
    return (
      <div className="min-h-screen gradient-hero relative overflow-hidden flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-300 text-xl mb-4">{error}</p>
          <Button onClick={() => navigate("/")}>Return to Home</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-hero relative overflow-hidden py-12 px-4">
      {/* Background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-primary/20 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative z-10 max-w-4xl mx-auto">
        {/* Winner Announcement */}
        <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="inline-flex items-center justify-center w-24 h-24 mb-6 rounded-full bg-white/20 backdrop-blur-sm shadow-2xl animate-bounce">
            <Trophy className="w-12 h-12 text-yellow-400" />
          </div>
          <h1 className="text-5xl md:text-7xl font-black text-white mb-4">
            Game Over!
          </h1>
          <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 inline-block">
            <p className="text-2xl text-white/80 mb-2">Winner</p>
            <p className="text-6xl font-black text-white mb-2">{topPlayer.nickname}</p>
            <p className="text-4xl font-bold text-yellow-400">{topPlayer.total_score} points</p>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 mb-8">
          <h2 className="text-3xl font-bold text-white mb-6 text-center">Final Leaderboard</h2>
          <div className="space-y-4">
            {leaderboard.map((player, index) => {
              const currentPlayerName = localStorage.getItem("playerName") || "You";
              const isCurrentPlayer = player.nickname === currentPlayerName || 
                                    player.player_id === localStorage.getItem("playerId");
              
              return (
                <div
                  key={player.player_id}
                  className={`bg-white/10 backdrop-blur-sm rounded-2xl p-6 border-2 transition-smooth hover:scale-105 animate-in fade-in slide-in-from-bottom-4 ${
                    isCurrentPlayer
                      ? "border-accent shadow-lg"
                      : "border-white/20"
                  }`}
                  style={{
                    animationDelay: `${index * 100}ms`,
                    borderColor: index < 3 ? podiumColors[index] : undefined,
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center text-2xl font-black text-white"
                        style={{
                          background: index < 3 ? podiumColors[index] : "hsl(var(--primary))",
                        }}
                      >
                        {player.rank}
                      </div>
                      <div>
                        <p className="text-xl font-bold text-white">{player.nickname}</p>
                        {isCurrentPlayer && (
                          <p className="text-sm text-accent font-medium">You</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-black text-white">{player.total_score}</p>
                      <p className="text-sm text-white/60">points</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            variant="default"
            size="xl"
            onClick={() => {
              localStorage.removeItem("currentQuiz");
              localStorage.removeItem("finalScore");
              localStorage.removeItem("roomCode");
              localStorage.removeItem("playerId");
              navigate("/");
            }}
          >
            <Home className="mr-2 h-5 w-5" />
            Back to Home
          </Button>
          <Button
            variant="outline"
            size="xl"
            onClick={() => {
              localStorage.removeItem("finalScore");
              navigate("/play");
            }}
          >
            <RotateCcw className="mr-2 h-5 w-5" />
            Play Again
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Results;