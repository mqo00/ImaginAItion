import '../App.css';
import TopBar from '../common/TopBar';
import Container from '../common/Container';
import BackButton from '../common/BackButton';
import socket from '../common/websocket';
import { useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function JoinGame() {
  const gameCodeRef = useRef();
  const playerNameRef = useRef();
  const navigate = useNavigate();
  const joinGame = async () => {
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

    if (!socket.id) {
      alert('Socket not connected. Please refresh the page.');
      return;
    }

    const response = await axios.post('/api/join-room', {
      sid: socket.id,
      room_id: gameCodeRef.current.value,
      player_name: playerNameRef.current.value,
    });
    console.log(gameCodeRef.current.value);
    console.log(response);

    if (!response.data.room) {
      alert('Game not found');
      return;
    }

    // Store session token for reconnection with unique key per player
    const gameCode = gameCodeRef.current.value;
    const playerName = playerNameRef.current.value;
    if (response.data.session_token) {
      const sessionKey = `session_${gameCode}_${playerName}`;
      localStorage.setItem(sessionKey, response.data.session_token);
      console.log(`🔑 Session token stored: ${sessionKey}`);
    }

    socket.emit('get-players', { room_id: gameCode });

    // Navigate with player name in URL for multi-tab support
    navigate(`/play/${gameCode}?player=${encodeURIComponent(playerName)}`);

    console.log(response.data.room);
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
              <div className="col-start-1 col-span-full font-medium text-[2.5rem] mb-8 font-gooper">
                Join a Game
              </div>
              <div className="col-start-2 col-span-2 mb-16 justify-self-start w-full">
                <div className="mb-3">
                  <label
                    htmlFor="game-code"
                    className="mb-2 text-xl font-semibold"
                  >
                    Game code
                  </label>
                </div>
                <input
                  type="text"
                  id="game-code"
                  ref={gameCodeRef}
                  name="game-code"
                  className="rounded-xl border border-[#D3D3D3] w-full bg-[#FAFAFA] pt-[1rem] pb-[1rem] pl-[1.25rem] pr-[1.25rem] text-[1.5rem] mb-3"
                  placeholder="Enter game code"
                ></input>
                <div className="mb-3">
                  <label
                    htmlFor="player-name"
                    className="mb-2 mt-5 text-xl font-semibold"
                  >
                    Name
                  </label>
                </div>
                <input
                  type="text"
                  id="player-name"
                  ref={playerNameRef}
                  name="player-name"
                  className="rounded-xl border border-[#D3D3D3] w-full bg-[#FAFAFA] pt-[1rem] pb-[1rem] pl-[1.25rem] pr-[1.25rem] text-[1.5rem] text-[1.5rem]"
                  placeholder="Enter your (or your team's) name"
                ></input>
              </div>
              {/* TODO: Add a link to the button */}
              <button
                onClick={() => {
                  console.log(gameCodeRef.current.value);
                  joinGame();
                }}
                className="font-medium border border-black rounded-xl text-[2rem] text-[#FFFFFF] pl-8 pr-8 pb-3 pt-3 bg-[#111111] col-start-2 col-span-2 justify-self-center font-gooper"
              >
                Join Game
              </button>
            </div>
          </Container>
        </div>
      </div>
    </div>
  );
}
