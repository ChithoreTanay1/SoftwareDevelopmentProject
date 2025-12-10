import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Users, Play, Copy, Check, Wifi, WifiOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { RoomsService, WebSocketManager, WSMessage } from "@/api/client";

interface Player {
  id: string;
  nickname: string;
  is_connected: boolean;
}

const GameLobby = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const wsManagerRef = useRef<WebSocketManager>(new WebSocketManager());
  const hostWsRef = useRef<WebSocket | null>(null);

  const [players, setPlayers] = useState<Player[]>([]);
  const [copied, setCopied] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [hostWsConnected, setHostWsConnected] = useState(false);
  const [quizTitle, setQuizTitle] = useState("");

  const roomCode = localStorage.getItem("roomCode") || "";
  const playerId = localStorage.getItem("playerId") || "";
  const hostId = localStorage.getItem("hostId") || "";
  const isHost = localStorage.getItem("isHost") === "true";
  const playerName = localStorage.getItem("playerName") || "Player";

  // Initialize WebSocket and fetch players
  useEffect(() => {
    if (!roomCode || !playerId) {
      console.error("Missing required data");
      navigate("/");
      return;
    }

    let mounted = true;
    const manager = wsManagerRef.current;

    const initWebSocket = async () => {
      try {
        console.log("🎮 Lobby: Connecting to WebSocket:", { roomCode, playerId, isHost });

        // Connect as player
        await manager.connect(
          roomCode,
          playerId,
          (message: WSMessage) => {
            if (!mounted) return;
            console.log("📨 Lobby: WebSocket message:", message.type);

            switch (message.type) {
              case "player_joined":
                console.log("👤 Player joined:", message.data.nickname);
                fetchPlayers();
                break;

              case "player_left":
                console.log("👤 Player left:", message.data.nickname);
                fetchPlayers();
                break;

              case "game_started":
                console.log("✅ Game started message received");
                // Store quiz data before navigating
                if (message.data?.quiz) {
                  localStorage.setItem("quizData", JSON.stringify(message.data.quiz));
                  localStorage.setItem("currentQuestionIndex", message.data.currentQuestionIndex || "0");
                  localStorage.setItem("score", message.data.score || "0");
                }
                // Navigation will happen from host WS or this will trigger it
                if (mounted) {
                  navigate("/play", { state: { isHost: isHost } });
                }
                break;

              case "error":
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
            setWsConnected(false);
          },
          (event) => {
            if (!mounted) return;
            console.log("WebSocket closed");
            setWsConnected(false);
          }
        );

        if (mounted) {
          setWsConnected(true);
          console.log("✅ Player WebSocket connected");
        }

        // If host, also connect to host WebSocket endpoint
        if (isHost && hostId) {
          console.log("🎬 Connecting host WebSocket:", { roomCode, hostId });
          connectHostWebSocket(roomCode, hostId);
        }
      } catch (error) {
        if (!mounted) return;
        console.error("Failed to connect WebSocket:", error);
        toast({
          title: "Connection Error",
          description: "Could not connect to room. Retrying...",
          variant: "destructive",
        });
      }
    };

    initWebSocket();

    return () => {
      mounted = false;
      manager.disconnect();
      if (hostWsRef.current) {
        hostWsRef.current.close();
      }
    };
  }, [roomCode, playerId, hostId, isHost, navigate, toast]);

  // Connect host to host-specific WebSocket
  const connectHostWebSocket = (room: string, host: string) => {
    try {
      const apiBase = import.meta.env.VITE_APP_API_BASE_URL || "http://localhost:8003";
      const wsProtocol = apiBase.startsWith("https") ? "wss" : "ws";
      const wsUrl = `${wsProtocol}://${apiBase.replace(/^https?:\/\//, "")}/api/v1/ws/host/${room}/${host}`;

      console.log("🔗 Host WebSocket URL:", wsUrl);

      const hostWs = new WebSocket(wsUrl);

      hostWs.onopen = () => {
        console.log("✅ Host WebSocket connected");
        setHostWsConnected(true);
      };

      hostWs.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log("📨 Host WS message:", message.type, message);

          switch (message.type) {
            case "game_started":
              console.log("✅ Host received game_started confirmation");
              // Store quiz data before navigating
              if (message.data?.quiz) {
                localStorage.setItem("quizData", JSON.stringify(message.data.quiz));
                localStorage.setItem("currentQuestionIndex", message.data.currentQuestionIndex || "0");
                localStorage.setItem("score", message.data.score || "0");
              }
              navigate("/play", { state: { isHost: true } });
              break;
            case "error":
              console.error("Host WS error:", message.data);
              toast({
                title: "Error",
                description: message.data?.message || "An error occurred",
                variant: "destructive",
              });
              break;
          }
        } catch (e) {
          console.error("Failed to parse host WS message:", e);
        }
      };

      hostWs.onerror = (error) => {
        console.error("Host WebSocket error:", error);
        setHostWsConnected(false);
      };

      hostWs.onclose = () => {
        console.log("Host WebSocket closed");
        setHostWsConnected(false);
      };

      hostWsRef.current = hostWs;
    } catch (error) {
      console.error("Failed to connect host WebSocket:", error);
    }
  };

  // Fetch players from server
  const fetchPlayers = async () => {
    if (!roomCode) return;
    try {
      const playersData = await RoomsService.getRoomPlayers(roomCode);
      console.log("📋 Fetched players:", playersData);

      if (Array.isArray(playersData)) {
        setPlayers(
          playersData.map((p: any) => ({
            id: p.id || p.player_id,
            nickname: p.nickname,
            is_connected: p.is_connected ?? true,
          }))
        );
      }
    } catch (error) {
      console.error("Failed to fetch players:", error);
    }
  };

  // Fetch players on mount and periodically
  useEffect(() => {
    if (!wsConnected || !roomCode) return;

    fetchPlayers();

    // Poll every 2 seconds for player updates
    const interval = setInterval(fetchPlayers, 2000);
    return () => clearInterval(interval);
  }, [roomCode, wsConnected]);

  // Fetch quiz title
  useEffect(() => {
    const quiz = localStorage.getItem("currentQuiz");
    if (quiz) {
      try {
        const quizData = JSON.parse(quiz);
        setQuizTitle(quizData.title);
      } catch (e) {
        console.error("Failed to parse quiz:", e);
      }
    }
  }, []);

  const copyGamePin = () => {
    navigator.clipboard.writeText(roomCode);
    setCopied(true);
    toast({
      title: "✅ Game PIN copied!",
      description: "Share it with your players",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const startGame = async () => {
    if (players.length === 0) {
      toast({
        title: "No players",
        description: "Wait for players to join before starting",
        variant: "destructive",
      });
      return;
    }

    if (!isHost) {
      toast({
        title: "Error",
        description: "Only the host can start the game",
        variant: "destructive",
      });
      return;
    }

    setIsStarting(true);

    try {
      console.log("🎬 Host starting game for room:", roomCode);
      console.log("📍 Host WS Connected:", hostWsConnected);

      // Call the start game API endpoint
      const response = await RoomsService.startGame(roomCode);
      console.log("📡 Start game response:", response);

      if (!response.success) {
        throw new Error(response.message || "Failed to start game");
      }

      toast({
        title: "🎮 Game Started!",
        description: "Starting quiz for all players...",
        variant: "default",
      });

      // Wait for game_started message from WebSocket
      // The listener above will handle navigation
    } catch (error: any) {
      console.error("❌ Failed to start game:", error);
      console.error("📋 Error details:", {
        message: error.message,
        status: error.status,
        response: error.response,
      });
      toast({
        title: "Failed to start game",
        description: error.message || "Please try again",
        variant: "destructive",
      });
      setIsStarting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-900 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: "1s" }}></div>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        <div className="max-w-4xl w-full">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-5xl font-black text-white mb-2">{quizTitle}</h1>
            <div className="flex items-center justify-center gap-4 text-purple-200">
              <div className="flex items-center gap-2">
                {wsConnected ? (
                  <>
                    <Wifi className="h-4 w-4 text-green-400" />
                    <span>Player WS</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-4 w-4 text-red-400 animate-pulse" />
                    <span>Connecting...</span>
                  </>
                )}
              </div>
              {isHost && (
                <div className="flex items-center gap-2">
                  {hostWsConnected ? (
                    <>
                      <Wifi className="h-4 w-4 text-green-400" />
                      <span>Host WS</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-4 w-4 text-orange-400 animate-pulse" />
                      <span>Host Connecting...</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Game PIN Section */}
          <div className="text-center mb-12">
            <h2 className="text-xl font-bold text-white/80 mb-4">Game PIN</h2>
            <div className="inline-flex items-center gap-4 bg-white/10 backdrop-blur-xl rounded-3xl px-8 py-6 border-4 border-white/30">
              <span className="text-6xl md:text-8xl font-black text-white tracking-widest">
                {roomCode}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={copyGamePin}
                className="h-14 w-14 hover:bg-white/20"
              >
                {copied ? (
                  <Check className="h-6 w-6 text-green-400" />
                ) : (
                  <Copy className="h-6 w-6 text-white" />
                )}
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
              {isHost && (
                <span className="text-xs bg-purple-600 text-white px-3 py-1 rounded-full font-semibold">
                  HOST
                </span>
              )}
            </div>

            {players.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {players.map((player, index) => (
                  <div
                    key={player.id}
                    className="bg-white/20 rounded-2xl p-4 text-center backdrop-blur-sm border border-white/20 transition-smooth hover:bg-white/30 hover:scale-105 animate-in fade-in slide-in-from-bottom-4"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="relative">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 mx-auto mb-3 flex items-center justify-center text-2xl font-bold text-white">
                        {player.nickname[0].toUpperCase()}
                      </div>
                      {player.is_connected ? (
                        <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></div>
                      ) : (
                        <div className="absolute bottom-0 right-0 w-4 h-4 bg-gray-400 rounded-full border-2 border-white"></div>
                      )}
                    </div>
                    <p className="text-white font-medium text-sm truncate">
                      {player.nickname}
                    </p>
                    {player.id === playerId && (
                      <p className="text-purple-200 text-xs mt-1">(You)</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="animate-pulse inline-block">
                  <Users className="h-16 w-16 text-white/40 mx-auto mb-4" />
                </div>
                <p className="text-white/60 text-lg">
                  {wsConnected ? "Waiting for players to join..." : "Connecting to room..."}
                </p>
              </div>
            )}
          </div>

          {/* Status and Action */}
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 mb-8">
            {isHost ? (
              <div>
                <p className="text-white/80 text-sm mb-4">
                  You are the host. Click below to start the game when ready.
                </p>
                <Button
                  size="lg"
                  onClick={startGame}
                  disabled={isStarting || players.length === 0 || !wsConnected || !hostWsConnected}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold text-lg h-14"
                >
                  {isStarting ? (
                    <>
                      <div className="h-5 w-5 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                      Starting Game...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-5 w-5" />
                      Start Game ({players.length} player{players.length !== 1 ? "s" : ""})
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-lg font-semibold text-purple-300 mb-2">
                  Waiting for host to start...
                </p>
                <p className="text-white/60">
                  You're in the room. The host will start the game shortly.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameLobby;