import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import sio from './websocket';
import { getImageUrl } from '../config/api';

export default function QuickDraws() {
  const { gameCode } = useParams();
  const [quickDrawPrompt, setQuickDrawPrompt] = useState('');
  const [quickDrawImages, setQuickDrawImages] = useState([]);
  const [isGeneratingQuickDraw, setIsGeneratingQuickDraw] = useState(false);
  const [attemptsLeft, setAttemptsLeft] = useState(2);
  const [allPlayersResults, setAllPlayersResults] = useState([]);
  const [selectedPlayerId, setSelectedPlayerId] = useState(null);
  const [displayedResults, setDisplayedResults] = useState([]);
  const [currentPlayerName, setCurrentPlayerName] = useState(null);

  // get the current username
  const fetchCurrentPlayerName = async () => {
    try {
      const response = await axios.get(`/api/current-player/${gameCode}/${sio.id}`);
      if (response.data.player_name) {
        setCurrentPlayerName(response.data.player_name);
        return response.data.player_name;
      }
    } catch (error) {
      console.error('Error fetching current player name:', error);
    }
    return null;
  };

  // get the Quick Draw results for all players
  const fetchAllPlayersResults = async () => {
    try {
      const response = await axios.get(`/api/quick-draw-results/${gameCode}`);
      if (response.data.players) {
        setAllPlayersResults(response.data.players);
        
        // no default selection here; it is handled in initializeData
      }
    } catch (error) {
      console.error('Error fetching players results:', error);
    }
  };

  // switch which player's results are shown
  const switchToPlayer = (playerName) => {
    setSelectedPlayerId(playerName);
    if (playerName === currentPlayerName) {
      // show our own results (live quickDrawImages)
      setDisplayedResults(quickDrawImages);
    } else {
      // show another player's results
      const playerData = allPlayersResults.find(p => p.player_name === playerName);
      if (playerData) {
        setDisplayedResults(playerData.quick_draws.map(qd => ({
          prompt: qd.prompt,
          imageUrl: qd.image_url,
          timestamp: qd.timestamp * 1000
        })));
      } else {
        setDisplayedResults([]);
      }
    }
  };

  // get the current player ID (based on the socket connection)
  const getCurrentPlayerId = () => {
    // if no player is selected yet and player data exists, select the first player by default
    if (allPlayersResults.length > 0) {
      return allPlayersResults[0]?.player_id;
    }
    return null;
  };

  // on mount, fetch the current username and all players' results
  useEffect(() => {
    const initializeData = async () => {
      const playerName = await fetchCurrentPlayerName();
      fetchAllPlayersResults();
      
      // select the current user by default
      if (playerName && !selectedPlayerId) {
        setSelectedPlayerId(playerName);
        setDisplayedResults(quickDrawImages);
      }
    };
    initializeData();
    
    // listen for real-time quick draw updates
    const handleQuickDrawUpdate = (data) => {
      console.log('🔊 Received quick_draw_update:', data);
      const { player_name, quick_draw } = data;
      
      // update allPlayersResults
      setAllPlayersResults(prev => {
        const updated = prev.map(player => {
          if (player.player_name === player_name) {
            return {
              ...player,
              quick_draws: [...player.quick_draws, quick_draw]
            };
          }
          return player;
        });
        
        // if it is a new player, add it to the list
        if (!updated.find(p => p.player_name === player_name)) {
          updated.push({
            player_name: player_name,
            quick_draws: [quick_draw]
          });
        }
        
        return updated;
      });
      
      // do not update displayedResults here; let the toggle logic and useEffect handle it
      // this avoids the stale-closure problem
    };
    
    sio.on('quick_draw_update', handleQuickDrawUpdate);
    
    // removed polling; rely entirely on real-time WebSocket updates
    // const interval = setInterval(fetchAllPlayersResults, 10000);
    
    return () => {
      sio.off('quick_draw_update', handleQuickDrawUpdate);
      // clearInterval(interval);
    };
  }, [gameCode]);

  // when our own quickDrawImages update, refresh the view if viewing our own results  
  useEffect(() => {
    if (!selectedPlayerId || selectedPlayerId === currentPlayerName) {
      setDisplayedResults(quickDrawImages);
    }
  }, [quickDrawImages, selectedPlayerId, currentPlayerName]);

  // when allPlayersResults updates, refresh the view if currently viewing another player
  useEffect(() => {
    if (selectedPlayerId && selectedPlayerId !== currentPlayerName) {
      const playerData = allPlayersResults.find(p => p.player_name === selectedPlayerId);
      if (playerData) {
        setDisplayedResults(playerData.quick_draws.map(qd => ({
          prompt: qd.prompt,
          imageUrl: qd.image_url,
          timestamp: qd.timestamp * 1000
        })));
      }
    }
  }, [allPlayersResults, selectedPlayerId, currentPlayerName]);

  // handle Quick Draw generation
  const handleQuickDraw = async () => {
    if (!quickDrawPrompt.trim() || attemptsLeft <= 0 || isGeneratingQuickDraw) return;
    
    setIsGeneratingQuickDraw(true);
    try {
      const response = await axios.post('/api/generate-quick-draw', {
        prompt: quickDrawPrompt.trim(),
        room_id: gameCode,
        sid: sio.id
      });
      
      if (response.data.image_url) {
        const newImage = {
          prompt: quickDrawPrompt.trim(),
          imageUrl: response.data.image_url,
          timestamp: Date.now()
        };
        setQuickDrawImages(prev => [...prev, newImage]);
        
        // if currently viewing our own results, refresh the view too
        // note: WebSocket events handle other users' updates; this only handles our own
        if (!selectedPlayerId || selectedPlayerId === currentPlayerName) {
          setDisplayedResults(prev => [...prev, newImage]);
        }
        
        setAttemptsLeft(prev => prev - 1);
        setQuickDrawPrompt('');
      }
    } catch (error) {
      console.error('Error generating quick draw:', error);
    } finally {
      setIsGeneratingQuickDraw(false);
    }
  };

  // handle Enter-key submission
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleQuickDraw();
    }
  };

  return (
    <div className="rounded-[1rem] border-black border-[0.063rem] h-full flex flex-col overflow-hidden">
      <div className="bg-[#D7E5FF] p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">⚡</span>
          <h3 className="font-gooper font-bold text-lg">Quick Draws!</h3>
        </div>
        <p className="text-sm text-gray-700">Any prompt you wanna try really quick?</p>
      </div>
      
      <div className="bg-white p-4 flex flex-col flex-1">
        {/* player toggle buttons - shows all players with the current player first */}
        <div className="flex justify-center gap-2 mb-3">
          {/* prefer showing the current player's name if known */}
          {currentPlayerName && (
            <button
              onClick={() => switchToPlayer(currentPlayerName)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                selectedPlayerId === currentPlayerName || !selectedPlayerId
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {currentPlayerName} (Me)
            </button>
          )}
          
          {/* show other players */}
          {allPlayersResults
            .filter(player => player.player_name !== currentPlayerName)
            .map((player) => (
              <button
                key={player.player_name}
                onClick={() => switchToPlayer(player.player_name)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                  selectedPlayerId === player.player_name
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {player.player_name}
              </button>
            ))}
          
          {/* show the loading state if there is no player data */}
          {!currentPlayerName && allPlayersResults.length === 0 && (
            <div className="text-gray-500 text-xs">Loading players...</div>
          )}
        </div>

        {/* show 'attempts left' only when viewing our own results */}
        {(!selectedPlayerId || selectedPlayerId === currentPlayerName) && (
          <div className="bg-black text-white rounded-lg px-3 py-2 text-center font-medium mb-4">
            {attemptsLeft} attempts left
          </div>
        )}
        
        {/* generated-image display area - uses flex-1 to fill remaining space */}
        <div className="flex-1 mb-4 overflow-y-auto min-h-0 max-h-80">
          <div className="space-y-3">
            {displayedResults.map((item, index) => (
              <div key={item.timestamp} className="border border-gray-300 rounded-lg p-3 bg-white">
                <img
                  src={getImageUrl(item.imageUrl)}
                  alt={`Quick draw ${index + 1}`}
                  className="w-full h-auto rounded-lg mb-2"
                  onError={(e) => {
                    console.error('Failed to load image:', e.target.src);
                    e.target.style.display = 'none';
                  }}
                />
                <p className="text-xs text-gray-600 font-medium text-center">"{item.prompt}"</p>
              </div>
            ))}
            
            {displayedResults.length === 0 && (
              <div className="bg-gray-200 rounded-lg border-2 border-dashed border-gray-300 flex flex-col items-center justify-center p-8">
                <div className="text-4xl mb-2 text-gray-400">🖼️</div>
                <p className="text-sm text-gray-500 text-center">No image generated yet</p>
                <p className="text-xs text-gray-400 text-center">You have two chances to test your prompt below.</p>
              </div>
            )}
          </div>
        </div>
        
        {/* input area - at the bottom, single-row layout */}
        <div className="flex gap-2">
          <input
            type="text"
            value={quickDrawPrompt}
            onChange={(e) => setQuickDrawPrompt(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Try your prompts here!"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            disabled={attemptsLeft <= 0 || isGeneratingQuickDraw}
          />
          <button
            onClick={handleQuickDraw}
            disabled={!quickDrawPrompt.trim() || attemptsLeft <= 0 || isGeneratingQuickDraw}
            className="w-12 h-12 bg-black text-white rounded-lg hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isGeneratingQuickDraw ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}