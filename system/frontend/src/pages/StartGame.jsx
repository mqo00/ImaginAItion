import '../App.css';
import TopBar from '../common/TopBar';
import Container from '../common/Container';
import BackButton from '../common/BackButton';
import GameConfigModal from '../common/GameConfigModal';
import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import socket from '../common/websocket';

export default function JoinGame() {
  const [randomNumber] = useState(Math.floor(Math.random() * 100000));
  const gameCode = randomNumber.toString();
  const playerNameRef = useRef();
  const navigate = useNavigate();
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [gameConfig, setGameConfig] = useState({
    selectedCategories: ['cultural', 'demographic', 'biological', 'co-occurrence', 'realism', 'number & spatial'],
    apiKey: ''
  });
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKeyError, setApiKeyError] = useState('');

  // Compute API key validity without causing re-renders
  const isApiKeyValid = apiKey && apiKey.trim() !== '' && apiKey.startsWith('sk-') && apiKey.length >= 20;

  const validateApiKey = (key) => {
    if (!key || key.trim() === '') {
      setApiKeyError('OpenAI API key is required');
      return false;
    }
    if (!key.startsWith('sk-')) {
      setApiKeyError('API key must start with "sk-"');
      return false;
    }
    if (key.length < 20) {
      setApiKeyError('API key appears to be too short');
      return false;
    }
    setApiKeyError('');
    return true;
  };

  const handleStartGame = async () => {
    if (!validateApiKey(apiKey)) {
      return;
    }

    // Wait for socket connection if not connected
    if (!socket.connected) {
      console.log('⏳ Waiting for Socket.IO connection...');
      await new Promise((resolve) => {
        if (socket.connected) {
          resolve();
        } else {
          socket.once('connect', resolve);
          // Timeout after 5 seconds
          setTimeout(() => {
            if (!socket.connected) {
              alert('Failed to connect to server. Please refresh the page.');
            }
            resolve();
          }, 5000);
        }
      });
    }

    if (!socket.id || !gameCode) {
      alert('Missing socket ID or game code!');
      return;
    }

    axios
      .post('/api/create-room', {
        sid: socket.id,
        room_id: gameCode.toString(),
        player_name: playerNameRef.current.value,
        tutorial: false,
        categories: gameConfig.selectedCategories,
        api_key: apiKey,
      }) // Sending correct JSON
      .then((response) => {
        if (response.status !== 200) {
          console.error('❌ Axios error:', response);
          return;
        }
        // Store session token for reconnection with unique key per player
        const playerName = playerNameRef.current.value;
        if (response.data.session_token) {
          const sessionKey = `session_${gameCode}_${playerName}`;
          localStorage.setItem(sessionKey, response.data.session_token);
          console.log(`🔑 Session token stored: ${sessionKey}`);
        }
        // Navigate with player name in URL for multi-tab support
        navigate(`/play/${gameCode}?player=${encodeURIComponent(playerName)}`);
      })
      .catch((error) => {
        console.error(
          '❌ Axios error:',
          error.response ? error.response.data : error
        );

        // Check if it's an API key related error
        if (error.response?.status === 401 ||
            (error.response?.data && error.response.data.toString().includes('API key'))) {
          setApiKeyError('Invalid API key. Please check your OpenAI API key.');
        } else {
          alert('Failed to create room. Please try again.');
        }
      });
  };
  return (
    <div className="h-svh flex flex-col">
      <div className="-z-10">
        <TopBar />
      </div>
      <div className="h-full items-center flex">
        <div className="main-container font-inter w-full">
          <Container>
            <BackButton />
            <div className="grid grid-cols-4 justify-items-center pb-12">
              <div className="col-start-1 col-span-full font-medium text-[2.5rem] mb-8 font-gooper flex items-center justify-center gap-4">
                Start a Game
                <button
                  onClick={() => setIsConfigModalOpen(true)}
                  className="text-lg bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded-lg border"
                  title="Game Configuration"
                >
                  ⚙️ Config
                </button>
              </div>
              <div className="col-start-2 col-span-2 mb-16 justify-self-start w-full">
                <div className="text-[1.408rem] mb-20">
                  <div className="font-semibold flex gap-2">
                    Link:{' '}
                    <p className="font-normal">imaginaition.com/{gameCode}</p>
                  </div>
                  <div className="font-semibold flex gap-2">
                    Game code: <p className="font-normal">{gameCode}</p>
                  </div>
                  <div className="font-semibold flex gap-2 mt-4">
                    Config: <p className="font-normal">{gameConfig.selectedCategories.length} rounds, {gameConfig.selectedCategories.length} categories</p>
                  </div>
                </div>

                {/* OpenAI API Key Section */}
                <div className="mb-6">
                  <label
                    htmlFor="api-key"
                    className="mb-2 text-xl font-semibold block"
                  >
                    OpenAI API Key (Required)
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => {
                        const value = e.target.value;
                        setApiKey(value);

                        // Update error message based on current value
                        if (!value || value.trim() === '') {
                          setApiKeyError('OpenAI API key is required');
                        } else if (!value.startsWith('sk-')) {
                          setApiKeyError('API key must start with "sk-"');
                        } else if (value.length < 20) {
                          setApiKeyError('API key appears to be too short');
                        } else {
                          setApiKeyError('');
                        }
                      }}
                      id="api-key"
                      name="api-key"
                      className={`rounded-xl border w-full bg-[#FAFAFA] pt-[1rem] pb-[1rem] pl-[1.25rem] pr-[3rem] text-[1.5rem] ${
                        apiKeyError ? 'border-red-500' : 'border-[#D3D3D3]'
                      }`}
                      placeholder="sk-..."
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 text-xl"
                    >
                      {showApiKey ? "🙈" : "👁️"}
                    </button>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Your API key will NOT be stored and is only used for this game session.
                  </p>
                  {apiKeyError && (
                    <p className="text-sm text-red-600 mt-1">{apiKeyError}</p>
                  )}
                </div>

                <div className="mb-3">
                  <label
                    htmlFor="player-name"
                    className="mb-2 mt-5 text-xl font-semibold"
                  >
                    Your name?
                  </label>
                </div>
                <input
                  type="text"
                  ref={playerNameRef}
                  id="player-name"
                  name="player-name"
                  className="rounded-xl border border-[#D3D3D3] w-full bg-[#FAFAFA] pt-[1rem] pb-[1rem] pl-[1.25rem] pr-[1.25rem] text-[1.5rem] text-[1.5rem]"
                  placeholder="Enter your (or your team's) name"
                ></input>
              </div>
              <button
                onClick={() => {
                  console.log(playerNameRef.current.value);
                  handleStartGame();
                }}
                disabled={!isApiKeyValid}
                className={`font-medium border rounded-xl text-[2rem] py-[0.75rem] px-[2rem] col-start-2 col-span-2 justify-self-center font-gooper transition-colors ${
                  !isApiKeyValid
                    ? 'border-gray-400 text-gray-400 bg-gray-200 cursor-not-allowed'
                    : 'border-black text-[#FFFFFF] bg-[#111111] hover:bg-gray-800'
                }`}
              >
                Start Game
              </button>
            </div>
          </Container>
        </div>
      </div>
      
      <GameConfigModal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        onSave={setGameConfig}
        initialConfig={gameConfig}
      />
    </div>
  );
}
