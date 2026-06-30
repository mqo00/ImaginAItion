import '../App.css';
import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';
import TopBar from '../common/TopBar';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { getImageUrl } from '../config/api';

export function Player({ rank, name, round1, round2, round3, round4, round5, round6, totalPoints }) {
  return (
    <div className="bg-white rounded-b-[0.75rem] gap-[0.625rem] text-center py-[1.5268rem] px-[1.9rem] text-[1.875rem] grid grid-cols-9 font-inter border-white border-[0.5rem]">
      <div className="flex col-start-1 col-span-1 gap-x-[2.8rem]">
        <span className="font-semibold">{rank}</span>
        <div className="flex gap-x-[1.145rem] font-normal">
          <div>{name}</div>
        </div>
      </div>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {round1} pts
      </span>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {round2} pts
      </span>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {round3} pts
      </span>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {round4} pts
      </span>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {round5} pts
      </span>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {round6} pts
      </span>
      <span className="text-[#4E4E4E] text-[1.527rem] self-center">
        {totalPoints} pts
      </span>
    </div>
  );
}

export default function GameResult() {
  const [playerState, setPlayerState] = useState({});
  const [sidToPlayer, setSidToPlayer] = useState({});
  const [currentRound, setCurrentRound] = useState(1);
  const [roundDetails, setRoundDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const { gameCode } = useParams();

  useEffect(() => {
    const fetchPlayerState = async () => {
      try {
        const response = await axios.get(
          `/api/game-results?room_id=${gameCode}`
        );
        console.log('Game results response:', response.data);
        setPlayerState(response.data.player_state);
      } catch (error) {
        console.error('Error fetching game results:', error);
      }
    };

    fetchPlayerState();
  }, [gameCode]);

  useEffect(() => {
    const fetchSidToPlayers = async () => {
      try {
        const response = await axios.get(
          `/api/sid-to-players?room_id=${gameCode}`
        );
        console.log('Sid to players response:', response.data);
        setSidToPlayer(response.data);
      } catch (error) {
        console.error('Error fetching sid to players:', error);
      }
    };

    fetchSidToPlayers();
    fetchRoundDetails(1); // Load round 1 details by default
  }, [gameCode]);

  const fetchRoundDetails = async (roundNum) => {
    setLoading(true);
    try {
      const response = await axios.get(
        `/api/round-details?room_id=${gameCode}&round_num=${roundNum}`
      );
      console.log(`Round ${roundNum} details:`, response.data);
      
      if (response.data.error) {
        console.warn(`Round ${roundNum} error:`, response.data.error);
        setRoundDetails({ error: response.data.error });
      } else {
        setRoundDetails(response.data);
      }
    } catch (error) {
      console.error(`Error fetching round ${roundNum} details:`, error);
      setRoundDetails({ error: 'Failed to load round details' });
    } finally {
      setLoading(false);
    }
  };

  const handleRoundChange = (direction) => {
    const newRound = direction === 'next' 
      ? Math.min(currentRound + 1, 6) 
      : Math.max(currentRound - 1, 1);
    
    if (newRound !== currentRound) {
      setCurrentRound(newRound);
      fetchRoundDetails(newRound);
    }
  };

  return (
    <div className="h-svh justify-items-center">
      {/* <div className="absolute">
        <TopBar />
      </div> */}
      <div className="h-full content-center w-3/4 rounded-b-[0.75rem] text-center">
        <div className="font-gooper [-webkit-text-stroke:3px_black] bg-white inline-block text-transparent bg-clip-text font-semibold text-[4rem] mb-6">
          Game Ended
        </div>
        <div className="bg-black rounded-t-[0.75rem] text-white gap-[0.625rem] text-center py-[1.5268rem] px-[1.9rem] text-[1.875rem] grid grid-cols-9 font-gooper font-medium">
          <div className="flex col-start-1 col-span-1 gap-x-[2.8rem]">
            <span>#</span>
            <span>Name</span>
          </div>
          <span>Round 1</span>
          <span>Round 2</span>
          <span>Round 3</span>
          <span>Round 4</span>
          <span>Round 5</span>
          <span>Round 6</span>
          <span>Total</span>
        </div>
        <div className="bg-white h-auto rounded-b-[0.75rem]">
          {Object.entries(playerState).length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              Loading player results...
            </div>
          ) : (
            Object.entries(playerState)
              .map(([sid, data]) => {
                console.log('Processing player data:', { sid, data, playerName: sidToPlayer[sid] });
                
                // get the single-round score using the new scoring logic (no guess stage)
                const getRoundScore = (roundNum) => {
                  try {
                    const round = data.round && data.round[roundNum];
                    if (!round) {
                      console.warn(`Round ${roundNum} data missing for player ${sid}`);
                      return 0;
                    }
                    // use the backend-computed total field, or fall back to choose+prompt
                    return round.total || ((round.choose || 0) + (round.prompt || 0));
                  } catch (error) {
                    console.error(`Error getting round ${roundNum} score for ${sid}:`, error);
                    return 0;
                  }
                };

                return {
                  sid,
                  name: sidToPlayer[sid] || `Player ${sid}`,
                  round1: getRoundScore(1),
                  round2: getRoundScore(2),
                  round3: getRoundScore(3),
                  round4: getRoundScore(4),
                  round5: getRoundScore(5),
                  round6: getRoundScore(6),
                  totalPoints: data.score || 0,
                };
              })
              .sort((a, b) => b.totalPoints - a.totalPoints)
              .map((player, index, sortedPlayers) => {
                // Calculate proper ranking with tied positions
                // Find the first occurrence of this score to get the correct rank
                let rank = 1;
                for (let i = 0; i < sortedPlayers.length; i++) {
                  if (sortedPlayers[i].totalPoints === player.totalPoints) {
                    rank = i + 1;
                    break;
                  }
                }

                return (
                  <Player
                    key={player.sid}
                    rank={rank}
                    name={player.name}
                    round1={player.round1}
                    round2={player.round2}
                    round3={player.round3}
                    round4={player.round4}
                    round5={player.round5}
                    round6={player.round6}
                    totalPoints={player.totalPoints}
                  />
                );
              })
          )}
        </div>
        
        {/* Round Details Section */}
        <div className="mt-[3rem]">
          {/* Round Navigation - with black background */}
          <div className="bg-black rounded-t-[0.75rem] text-white p-[1.5rem]">
            <div className="flex items-center justify-center gap-[2rem]">
              <button 
                onClick={() => handleRoundChange('prev')}
                disabled={currentRound === 1}
                className={`flex items-center justify-center w-[3rem] h-[3rem] rounded-full ${
                  currentRound === 1 
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                    : 'bg-white text-black hover:bg-gray-200'
                }`}
              >
                <span className="text-[1.5rem] font-bold">‹</span>
              </button>
              
              <h2 className="font-gooper font-medium text-[2rem]">
                Round {currentRound} Results
              </h2>
              
              <button 
                onClick={() => handleRoundChange('next')}
                disabled={currentRound === 6}
                className={`flex items-center justify-center w-[3rem] h-[3rem] rounded-full ${
                  currentRound === 6 
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                    : 'bg-white text-black hover:bg-gray-200'
                }`}
              >
                <span className="text-[1.5rem] font-bold">›</span>
              </button>
            </div>
          </div>
          
          {/* Round Content - without black background */}
          {loading ? (
            <div className="text-center py-[3rem] text-gray-600">
              Loading round details...
            </div>
          ) : roundDetails && roundDetails.error ? (
            <div className="text-center py-[3rem] text-red-500">
              Error: {roundDetails.error}
            </div>
          ) : roundDetails && roundDetails.player_results ? (
            <div className="grid grid-cols-2 gap-0 rounded-b-[0.75rem] overflow-hidden">
              {/* Reference Image Container */}
              {roundDetails.reference_image && (
                <div className="flex items-center gap-4 py-6 bg-gray-100 px-4">
                  {/* Name Section */}
                  <div className="w-32 flex-shrink-0 flex justify-center">
                    <div className="bg-white border border-gray-300 px-3 py-2 rounded-full">
                      <span className="text-black font-bold text-sm whitespace-nowrap">Original Image</span>
                    </div>
                  </div>
                  
                  {/* Image Section */}
                  <div className="w-20 h-20">
                    {roundDetails.reference_image.image_path ? (
                      <img
                        src={getImageUrl(roundDetails.reference_image.image_path)}
                        alt={roundDetails.reference_image.description}
                        className="w-20 h-20 rounded-lg object-cover border border-gray-200"
                        onError={(e) => {
                          console.log('Reference image failed to load:', e.target.src);
                          e.target.style.display = 'none';
                          e.target.parentNode.innerHTML = '<div class="w-20 h-20 bg-gray-500 rounded-lg flex items-center justify-center text-gray-300 text-xs">No Image</div>';
                        }}
                      />
                    ) : (
                      <div className="w-20 h-20 bg-gray-500 rounded-lg flex items-center justify-center text-gray-300 text-xs">
                        No Image
                      </div>
                    )}
                  </div>
                  
                  {/* Prompt Section */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 mb-1">Prompt</p>
                    <p className="text-sm font-medium text-black truncate">
                      {roundDetails.reference_image.description || 'Unknown'}
                    </p>
                  </div>
                  
                  {/* Tokens Section */}
                  <div className="text-center min-w-[60px]">
                    <div className="text-lg font-bold text-blue-400">
                      {roundDetails.reference_image.description ? roundDetails.reference_image.description.split(' ').length : 0}
                    </div>
                    <div className="text-sm text-gray-300">Tokens</div>
                  </div>
                </div>
              )}

              {/* Player Results Containers */}
              {roundDetails.player_results.map((player, index) => (
                <div key={player.sid} className="flex items-center gap-4 py-6 bg-white px-4 border border-gray-200">
                  {/* Name Section */}
                  <div className="w-32 flex-shrink-0 flex justify-center">
                    <div className="bg-white border border-gray-300 px-3 py-2 rounded-full">
                      <span className="text-black font-bold text-sm whitespace-nowrap">{player.name}</span>
                    </div>
                  </div>
                  
                  {/* Image Section */}
                  <div className="w-20 h-20">
                    {player.generated_image && (player.generated_image.image_url || player.generated_image.url) ? (
                      <img
                        src={player.generated_image.image_url || player.generated_image.url}
                        alt={`Creation by ${player.name}`}
                        className="w-20 h-20 rounded-lg object-cover border border-gray-200"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentNode.innerHTML = '<div class="w-20 h-20 bg-gray-300 rounded-lg flex items-center justify-center text-gray-500 text-sm">Failed</div>';
                        }}
                      />
                    ) : (
                      <div className="w-20 h-20 bg-gray-300 rounded-lg flex items-center justify-center text-gray-500 text-sm">
                        No Image
                      </div>
                    )}
                  </div>
                  
                  {/* Prompt Section */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-500 mb-1">Prompt</p>
                    <p className="text-sm font-medium text-black truncate">
                      {player.prompt || 'No prompt'}
                    </p>
                  </div>
                  
                  {/* Tokens Section */}
                  <div className="text-center min-w-[50px]">
                    <div className="text-lg font-bold text-blue-600">
                      {player.tokens}
                    </div>
                    <div className="text-sm text-gray-500">Tokens</div>
                  </div>
                  
                  {/* Votes Section */}
                  <div className="text-center min-w-[50px]">
                    <div className="text-lg font-bold text-green-600">
                      {player.votes}
                    </div>
                    <div className="text-sm text-gray-500">Vote{player.votes !== 1 ? 's' : ''}</div>
                    {player.score > 0 && (
                      <div className="text-green-600 text-sm font-bold">+{player.score}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-[3rem] text-gray-600">
              No round details available
            </div>
          )}
        </div>
        
        <Link to="/">
          <button className="py-[0.75rem] px-[4rem] rounded-[0.5rem] font-gooper bg-black text-white gap-[0.625rem] text-[1.5rem] mt-[3rem]">
            Leave
          </button>
        </Link>
      </div>
    </div>
  );
}

Player.propTypes = {
  rank: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  round1: PropTypes.number.isRequired,
  round2: PropTypes.number.isRequired,
  round3: PropTypes.number.isRequired,
  round4: PropTypes.number.isRequired,
  round5: PropTypes.number.isRequired,
  round6: PropTypes.number.isRequired,
  totalPoints: PropTypes.number.isRequired,
};
