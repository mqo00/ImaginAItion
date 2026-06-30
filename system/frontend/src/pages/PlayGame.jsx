import '../App.css';
import TopBar from '../common/TopBar';
import Timer from '../common/Timer';
import Container from '../common/Container';
import GameInstruction from '../common/GameInstruction';
import PlayerContainer from '../common/Players';
import { useState } from 'react';
import Generate from '../common/Generate';
import Voting from '../common/Voting';
import RevealPrompt from '../common/RevealPrompt';
import Result from '../common/Result';
import ReferenceImage from '../common/ReferenceImage';
import QuickDraws from '../common/QuickDraws';
import sio from '../common/websocket';
import { useEffect } from 'react';
import { StageSpinner } from 'react-spinners-kit';
import GameResult from './GameResult';
import axios from 'axios';
import { useParams, useLocation } from 'react-router-dom';

export default function PlayGame() {
  const [currentTurn, setCurrentTurn] = useState(0);
  const [showModal, setShowModal] = useState(true);
  const [gameOver, setGameOver] = useState(false);  // game-over state
  const { gameCode } = useParams();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const playerName = searchParams.get('player');
  const [round, setRound] = useState(0);
  const [hasGenerated, setHasGenerated] = useState(false);  // track whether the user has generated an image
  const [isGenerating, setIsGenerating] = useState(false);  // track whether an image is being generated
  const [showExitConfirm, setShowExitConfirm] = useState(false);  // emergency-exit confirmation dialog
  const [reconnecting, setReconnecting] = useState(false);  // track the reconnection state
  const [gameStarted, setGameStarted] = useState(false);  // track whether the game has actually started

  // Handle reconnection on every socket connect (including transport upgrades)
  useEffect(() => {
    const attemptReconnect = async () => {
      // Get session token using gameCode and playerName from URL
      const sessionKey = playerName ? `session_${gameCode}_${playerName}` : 'session_token';
      const sessionToken = localStorage.getItem(sessionKey);

      if (sessionToken && sio.id) {
        console.log(`🔍 Attempting reconnection with key: ${sessionKey}, SID: ${sio.id}`);
        setReconnecting(true);
        try {
          const response = await axios.post('/api/reconnect', {
            session_token: sessionToken,
            sid: sio.id,
          });

          if (response.data.success) {
            console.log('🔄 Successfully reconnected:', response.data);
            // Verify we're in the right room
            if (response.data.room_id === gameCode) {
              console.log('✅ Reconnection successful, staying in game');

              // Trigger Socket.IO events to refresh game state
              sio.emit('get-players', { room_id: gameCode });

              // If room data is available, restore state immediately
              if (response.data.room && response.data.room.game_state) {
                const gameState = response.data.room.game_state;
                console.log('📊 Restoring game state:', {
                  round: gameState.current_round,
                  turn: gameState.current_turn,
                  started_at: gameState.started_at
                });

                // Check if game has actually started (not just waiting for players)
                if (gameState.started_at) {
                  console.log(`🎮 Game has started at: ${gameState.started_at}`);
                  setGameStarted(true);
                } else {
                  console.log(`⏳ Game not yet started, still waiting for players`);
                  setGameStarted(false);
                }

                // Immediately sync the current turn to match backend state
                if (gameState.current_turn !== undefined) {
                  console.log(`🔄 Syncing currentTurn from backend: ${gameState.current_turn}`);
                  setCurrentTurn(gameState.current_turn);
                }

                // Sync round if available
                if (gameState.current_round !== undefined) {
                  console.log(`🔄 Syncing round from backend: ${gameState.current_round}`);
                  setRound(gameState.current_round);
                }
              }
            } else {
              console.warn('⚠️ Reconnected to different room, redirecting...');
              // Could redirect to correct room here if needed
            }
          } else {
            console.log('❌ Reconnection failed, might be a new session');
          }
        } catch (error) {
          console.error('❌ Reconnection error:', error);
        } finally {
          setReconnecting(false);
        }
      }
    };

    // Listen for every socket connect event (including transport upgrades)
    const handleConnect = () => {
      console.log('🔌 Socket connected, attempting reconnect...');
      // Small delay to ensure socket.id is available
      setTimeout(attemptReconnect, 100);
    };

    // Initial connection attempt
    if (sio.connected) {
      attemptReconnect();
    }

    // Listen for all future connect events (including transport upgrades)
    sio.on('connect', handleConnect);

    return () => {
      sio.off('connect', handleConnect);
    };
  }, [gameCode, playerName]);

  useEffect(() => {
    axios.get(`/api/round-info?room_id=${gameCode}`).then((response) => {
      setRound(response.data.round);
    });
  }, [gameCode]);

  // handle emergency exit
  const handleEmergencyExit = async () => {
    try {
      // call the backend API to force-end the game
      await axios.post(`/api/force-game-end`, {
        room_id: gameCode,
        sid: sio.id
      });
      
      // set the game-over state directly
      setGameOver(true);
      setShowExitConfirm(false);
    } catch (error) {
      console.error('Error forcing game end:', error);
      // navigate to the results page even if the API call fails
      setGameOver(true);
      setShowExitConfirm(false);
    }
  };


  // check if all players are done
  useEffect(() => {
    const handleAllPlayersDone = (data) => {
      if (data.moving_to_next_turn) {
        console.log(`🔄 Turn update: backend sent global_turn ${data.current_turn} (round: ${data.current_round}, round_turn: ${data.round_turn || 'N/A'})`);
        // Use the exact turn value from backend instead of incrementing
        setCurrentTurn(prevTurn => {
          if (prevTurn !== data.current_turn) {
            console.log(`✅ Updating currentTurn: ${prevTurn} -> ${data.current_turn}`);
            // reset hasGenerated and isGenerating when entering a new generation round
            if (data.current_turn % 4 === 0) {
              setHasGenerated(false);
              setIsGenerating(false);
            }
            return data.current_turn;
          } else {
            console.log(`⚠️ Ignoring duplicate turn update: ${prevTurn}`);
            return prevTurn;
          }
        });
      }
    };

    sio.on('next-turn-ready', handleAllPlayersDone);

    return () => {
      sio.off('next-turn-ready', handleAllPlayersDone);
    };
  }, []);

  // Debug: watch the actual changes of currentTurn
  useEffect(() => {
    console.log(`🎮 Frontend currentTurn changed to: ${currentTurn}`);
  }, [currentTurn]);

  useEffect(() => {
    const handleNumPlayers = (data) => {
      if (data.num_players > 2) {
        setShowModal(false);
      }
    };
    
    // listen for the game-start event to ensure the modal is hidden
    const handleGameStarted = (data) => {
      console.log('Game started in PlayGame!', data);
      setShowModal(false);
      setGameStarted(true);  // Mark game as truly started
    };

    // listen for the game-over event
    const handleGameOver = (data) => {
      console.log('🏁 Game over event received:', data);
      setGameOver(true);
    };
    
    sio.on('num_players', handleNumPlayers);
    sio.on('game-started', handleGameStarted);
    sio.on('game_over', handleGameOver);
    
    return () => {
      sio.off('num_players', handleNumPlayers);
      sio.off('game-started', handleGameStarted);
      sio.off('game_over', handleGameOver);
    };
  }, []);

  // removed the frontend's manual timer start; fully managed by the backend
  // useEffect(() => {
  //   if (!isTutorial && currentTurn === 0 && round === 1) {
  //     sio.emit('start-turn-timer');
  //   }
  // }, [round]);

  return (
    <>
      {/* Reconnecting indicator */}
      {reconnecting && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-[60] bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <StageSpinner size={20} color="#ffffff" />
          <span>Reconnecting...</span>
        </div>
      )}

      {/* emergency-exit button - subtle but accessible in all phases, including while waiting for players */}
      {!gameOver && (
        <button
          onClick={() => setShowExitConfirm(true)}
          className="fixed top-4 right-4 z-[60] w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full text-sm opacity-30 hover:opacity-100 transition-opacity duration-200 flex items-center justify-center"
          title="Emergency Exit"
        >
          ⚠️
        </button>
      )}

      {/* emergency-exit confirmation dialog */}
      {showExitConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70]">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-4 border-2 border-red-500">
            <div className="text-center">
              <div className="text-4xl mb-4">⚠️</div>
              <h3 className="text-lg font-bold mb-2 text-red-600">Emergency Exit</h3>
              <p className="text-gray-700 mb-6">
                This will immediately end the game for all players and jump to the final scoreboard. 
                This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => setShowExitConfirm(false)}
                  className="px-4 py-2 bg-gray-300 hover:bg-gray-400 rounded transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEmergencyExit}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded transition-colors"
                >
                  End Game Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <div className="font-semibold font-inter fixed inset-0 flex items-center justify-center ">
          <div className="bg-white p-6 rounded shadow-md justify-items-center text-xl border-black border-[2px]">
            <StageSpinner loading={true} color="#111111" />
            <p>Waiting for other players to join...</p>
          </div>
        </div>
      )}
                      {gameOver || currentTurn === 24 ? (
        <GameResult />
      ) : (
        <>
          <div className="grid grid-cols-4">
            <TopBar />
            <div className="col-start-4">
              {currentTurn % 4 !== 2 && currentTurn % 4 !== 1 && !(currentTurn % 4 === 0 && !hasGenerated && !isGenerating) && <Timer />}
            </div>
            <div className="mt-7 ml-8 grid grid-cols-1 content-between h-full">
              <PlayerContainer />
              {currentTurn % 4 === 3 && (
                <div className="mt-2 h-full flex flex-col">
                  <QuickDraws />
                </div>
              )}
            </div>
            <div className="col-start-2 col-span-full m-7 h-full">
              {currentTurn % 4 === 3 ? (
                // Result component gets full height and relative positioning
                <div className="h-full relative">
                  <Result />
                </div>
              ) : (
                <Container>
                  <GameInstruction currentTurn={currentTurn}></GameInstruction>
                  <div className="mt-7">
                    {/* new 4-phase flow: Generate -> Voting -> Reveal -> Result */}
                    {currentTurn % 4 === 0 ? (
                      <Generate currentTurn={currentTurn} gameStarted={gameStarted} onHasGeneratedChange={setHasGenerated} onIsGeneratingChange={setIsGenerating} />
                    ) : currentTurn % 4 === 1 ? (
                      <Voting />
                    ) : currentTurn % 4 === 2 ? (
                      <RevealPrompt />
                    ) : null}
                  </div>
                </Container>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
