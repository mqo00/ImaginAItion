import '../App.css';
import PropTypes from 'prop-types';
import socket from './websocket';
import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

export function Player({ rank, name, points }) {
  return (
    <div className="flex justify-between pt-4 pb-4 pr-5 pl-5 font-inter items-center">
      <div className="flex gap-5">
        <p className="font-semibold text-[1.25rem]">#{rank}</p>
        <div></div>
        <p className="text-[1.25rem]">{name}</p>
      </div>
      <p className="text-[#4E4E4E]">{points} points</p>
    </div>
  );
}

export default function PlayerContainer() {
  const [players, setPlayers] = useState([]);
  const [playerScores, setPlayerScores] = useState({});
  const [playerToSid, setPlayerToSid] = useState({});
  const [currentTurn, setCurrentTurn] = useState(0);
  const { gameCode } = useParams();

  useEffect(() => {
    axios
      .get(`/api/player-to-sid?room_id=${gameCode}`)
      .then((response) => setPlayerToSid(response.data))
      .catch((error) => {
        console.error('Error fetching words:', error);
      });
  }, [players]);

  useEffect(() => {
    const handlePlayerScores = (data) => {
      setPlayerScores(data.player_state);
    };

    socket.on('player-state', handlePlayerScores);
    
    // Also fetch updated scores using the new API initially
    const fetchUpdatedScores = async () => {
      try {
        const response = await axios.get(`/api/game-results?room_id=${gameCode}`);
        if (response.data && response.data.player_state) {
          setPlayerScores(response.data.player_state);
        }
      } catch (error) {
        console.error('Error fetching updated scores:', error);
      }
    };

    fetchUpdatedScores();
    
    // Listen for game events that should trigger score updates
    const handleNextTurn = () => {
      fetchUpdatedScores();
    };
    
    socket.on('next-turn-ready', handleNextTurn);
    
    return () => {
      socket.off('next-turn-ready', handleNextTurn);
    };
  }, [gameCode]);

  useEffect(() => {
    const handleNextTurnReady = (data) => {
      if (data.moving_to_next_turn && data.current_turn !== undefined) {
        setCurrentTurn(data.current_turn);
      }
      
      // Fetch updated scores when turn changes
      const fetchScoresOnTurnChange = async () => {
        try {
          const response = await axios.get(`/api/game-results?room_id=${gameCode}`);
          if (response.data && response.data.player_state) {
            setPlayerScores(response.data.player_state);
          }
        } catch (error) {
          console.error('Error fetching scores on turn change:', error);
        }
      };
      
      fetchScoresOnTurnChange();
    };
    
    socket.on('next-turn-ready', handleNextTurnReady);
    
    return () => {
      socket.off('next-turn-ready', handleNextTurnReady);
    };
  }, [gameCode]);

  useEffect(() => {
    const handlePlayerJoined = (data) => {
      // Ensure data is an array before updating state
      if (Array.isArray(data.players)) {
        setPlayers(data.players);
      } else {
        console.error('Expected an array but received:', data);
      }
    };
    socket.on('players', handlePlayerJoined);
  }, []);
  useEffect(() => {
    socket.emit('get-players', { room_id: gameCode });
  }, [gameCode]);
  useEffect(() => {
    socket.emit('get-player-state');
  }, []);

  return (
    <div className="bg-white rounded-[1rem] border-black border-[0.063rem]">
      <div className="p-[0.625rem] bg-black rounded-t-[0.75rem] text-white gap-[0.625rem] text-center font-medium text-[1.25rem] font-gooper">
        <div>{`Round ${Math.floor(currentTurn / 4) + 1} of 6`}</div>
        {/* {currentTurn < 4 && (
          <div className="font-inter text-[1rem] font-normal text-[#D9D9D9]">
            Points earned during the tutorial won't count toward your gameplay
            score.
          </div>
        )} */}
      </div>
      {players
        .map((player) => {
          const sid = playerToSid[player];
          // If round === 0 -> use .tutorial_score, else -> use .score
          // If it doesn't exist, default to 0
          const points = playerScores[sid]?.score ?? 0;

          return {
            name: player,
            points: points,
          };
        })
        .sort((a, b) => b.points - a.points)
        .map((player, index) => (
          <Player
            key={player.name}
            rank={index + 1}
            name={player.name}
            points={player.points}
          />
        ))}
    </div>
  );
}

Player.propTypes = {
  rank: PropTypes.number,
  name: PropTypes.string,
  points: PropTypes.number,
};
