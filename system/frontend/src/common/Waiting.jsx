import { StageSpinner } from 'react-spinners-kit';
import { useEffect, useState } from 'react';
import socket from './websocket';
import axios from 'axios';
import { useParams } from 'react-router-dom';

export default function Waiting({ message = "Waiting for other players...", showGenerationProgress = false }) {
  const [playerState, setPlayerState] = useState({});
  const [sidToPlayer, setSidToPlayer] = useState({});
  const { gameCode } = useParams();
  const [currentTurn, setCurrentTurn] = useState(0);
  const [generationProgress, setGenerationProgress] = useState("");

  useEffect(() => {
    const fetchSidToPlayers = async () => {
      try {
        const response = await axios.get(
          `/api/sid-to-players?room_id=${gameCode}`
        );
        console.log(response.data);
        setSidToPlayer(response.data);
      } catch (error) {
        console.error('Error fetching player states:', error);
      }
    };

    fetchSidToPlayers();
  }, []);

  useEffect(() => {
    socket.emit('get-player-state');
    const handlePlayerScores = (data) => {
      if (!data.player_state || !data.player_state[socket.id]) {
        console.warn('⚠️ player_state not available or current player not found:', data.player_state);
        return;
      }
      setPlayerState(data.player_state);
      setCurrentTurn(data.player_state[socket.id].current_turn);
      console.log(data.player_state[socket.id].current_turn);
      console.log(data.player_state);
    };

    const handleGenerationProgress = (data) => {
      if (showGenerationProgress) {
        setGenerationProgress(data.message);
      }
    };

    socket.on('player-state', handlePlayerScores);
    socket.on('generation_progress', handleGenerationProgress);

    return () => {
      socket.off('player-state', handlePlayerScores);
      socket.off('generation_progress', handleGenerationProgress);
    };
  }, [showGenerationProgress]);

  return (
    <div className="font-semibold font-inter fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white rounded shadow-md justify-items-center text-xl rounded-[1.25rem] py-12 px-20">
        <StageSpinner loading={true} color="#111111" />
        <div className="font-gooper font-medium text-[2.5rem] flex gap-x-3 mb-10">
          {message}
        </div>
        {showGenerationProgress && generationProgress && (
          <div className="text-lg text-gray-600 mb-4">
            {generationProgress}
          </div>
        )}
        <div className="flex flex-col gap-4 mt-4 w-full">
          {Object.entries(playerState).map(([sid, player]) => (
            <div key={sid} className="w-full">
              <div className="flex justify-between items-center pb-2 font-inter font-normal">
                <div className="text-[1.25rem]">{sidToPlayer[sid]}</div>
                {playerState[sid].current_turn === currentTurn ? (
                  <div className="gap-x-[0.625rem] py-[0.5rem] px-[0.75rem] rounded-[4.625rem] bg-[#009416] text-white flex items-center">
                    <i className="fa-solid fa-check"></i>
                    <div>Complete</div>
                  </div>
                ) : (
                  <div className="gap-x-[0.625rem] py-[0.5rem] px-[0.75rem] rounded-[4.625rem] bg-[#BA940F] text-white flex items-center">
                    <i className="fa-regular fa-clock"></i>
                    <div>In Progress</div>
                  </div>
                )}
              </div>
              <hr className="my-4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
