import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import sio from './websocket';
import { MetroSpinner } from 'react-spinners-kit';
import Waiting from './Waiting';
import { getImageUrl } from '../config/api';

export default function Result() {
  const { gameCode } = useParams();
  const [waitingForPlayers, setWaitingForPlayers] = useState(false);
  const [timeLeft, setTimeLeft] = useState(-1);
  
  // final-results state
  const [finalResults, setFinalResults] = useState([]);
  const [isLoadingResults, setIsLoadingResults] = useState(true);
  const [round, setRound] = useState(0);
  const [totalRounds, setTotalRounds] = useState(6); // Add state to track total rounds
  const [referenceDescription, setReferenceDescription] = useState('');
  const [referenceImage, setReferenceImage] = useState(null);
  

  // listen for timer updates
  useEffect(() => {
    const handleTimerUpdate = (data) => {
      setTimeLeft(data.time_left);
    };

    sio.on('update_timer', handleTimerUpdate);

    return () => {
      sio.off('update_timer', handleTimerUpdate);
    };
  }, []);


  // get the final results
  useEffect(() => {
    const fetchFinalResults = async () => {
      if (!sio.id || !sio.connected) {
        setTimeout(fetchFinalResults, 200);
        return;
      }
      
      try {
        setIsLoadingResults(true);
        const response = await axios.get(`/api/final-results?room_id=${gameCode}&sid=${sio.id}`);
        setFinalResults(response.data.results || []);
      } catch (error) {
        console.error('Error fetching final results:', error);
      } finally {
        setIsLoadingResults(false);
      }
    };
    
    fetchFinalResults();
  }, [gameCode]);

  // get round info
  useEffect(() => {
    const fetchRound = async () => {
      try {
        const response = await axios.get(`/api/round-info?room_id=${gameCode}`);
        setRound(response.data.round);
        // Also get total rounds if available
        if (response.data.total_rounds) {
          setTotalRounds(response.data.total_rounds);
        }
      } catch (error) {
        console.error('Error fetching round:', error);
      }
    };

    fetchRound();
  }, []);

  // get the reference image and description
  useEffect(() => {
    const fetchReferenceData = async () => {
      if (!sio.id || !sio.connected) {
        setTimeout(fetchReferenceData, 200);
        return;
      }
      
      try {
        const response = await axios.get(`/api/reference-image?room_id=${gameCode}&sid=${sio.id}`);
        setReferenceDescription(response.data.description || '');
        setReferenceImage(response.data);
      } catch (error) {
        console.error('Error fetching reference data:', error);
      }
    };

    fetchReferenceData();
  }, [gameCode]);

  // handle completion
  const handlePlayerDone = async () => {
    await sio.emit('player-done', {
      room_id: gameCode,
      sid: sio.id,
    });
    setWaitingForPlayers(true);
  };


  // check for a clear winner - only when the top score is unique
  const hasWinner = () => {
    if (finalResults.length === 0) return false;
    
    const highestScore = finalResults[0]?.score_info?.total_score;
    const playersWithHighestScore = finalResults.filter(
      result => result.score_info?.total_score === highestScore
    );
    
    return playersWithHighestScore.length === 1;
  };

  // get the current username - find the entry belonging to the current user in the results
  const getCurrentUserName = () => {
    if (finalResults.length > 0) {
      // try to find the result belonging to the current socket ID
      const currentUserResult = finalResults.find(result => result.creator_sid === sio.id);
      if (currentUserResult) {
        return currentUserResult.creator_name;
      }
      // if not found, fall back to a random player name
      const randomPlayer = finalResults[Math.floor(Math.random() * finalResults.length)];
      return randomPlayer?.creator_name || 'Player';
    }
    return 'Player';
  };

  // function to highlight matching words
  const highlightMatchingWords = (prompt, referenceDescription) => {
    if (!prompt || !referenceDescription) return prompt;
    
    // convert the reference description into a lowercase word array for matching
    const referenceWords = referenceDescription.toLowerCase()
      .replace(/[^\w\s]/g, ' ') // replace punctuation with spaces
      .split(/\s+/)
      .filter(word => word.length > 0);
    
    // split the prompt into words, preserving the original format
    const words = prompt.split(/(\s+|[^\w\s]+)/);
    
    return words.map((word, index) => {
      const cleanWord = word.toLowerCase().replace(/[^\w]/g, '');
      
      // check whether it matches any word in the reference description
      const isMatch = cleanWord.length > 0 && referenceWords.includes(cleanWord);
      
      if (isMatch) {
        return (
          <span key={index} className="bg-[#D7E5FF] text-black px-1 rounded">
            {word}
          </span>
        );
      }
      return word;
    });
  };

  // highlight words in the original description that overlap with any user prompt
  const highlightOriginalPrompt = (originalDescription) => {
    if (!originalDescription || finalResults.length === 0) return originalDescription;
    
    // collect the words from all users' prompts
    const allUserWords = new Set();
    finalResults.forEach(result => {
      if (result.prompt) {
        const userWords = result.prompt.toLowerCase()
          .replace(/[^\w\s]/g, ' ')
          .split(/\s+/)
          .filter(word => word.length > 0);
        userWords.forEach(word => allUserWords.add(word));
      }
    });
    
    // split the original description into words, preserving the original format
    const words = originalDescription.split(/(\s+|[^\w\s]+)/);
    
    return words.map((word, index) => {
      const cleanWord = word.toLowerCase().replace(/[^\w]/g, '');
      
      // check whether it matches any word in the users' prompts
      const isMatch = cleanWord.length > 0 && allUserWords.has(cleanWord);
      
      if (isMatch) {
        return (
          <span key={index} className="bg-[#D7E5FF] text-black px-1 rounded">
            {word}
          </span>
        );
      }
      return word;
    });
  };

  return (
    <div className="bg-white rounded-2xl border-2 border-black shadow-lg h-full flex flex-col">
      {waitingForPlayers && <Waiting />}
      
      {/* title area */}
      <div className="rounded-t-[1.25rem] overflow-hidden">
        <div className="bg-[#D7E5FF] p-5 text-center">
          <h2 className="text-3xl font-gooper font-bold mb-3">
            Round {round} Results
          </h2>
        </div>
        <div className="bg-gray-100 text-center">
          <p className="text-lg text-gray-800 px-0 py-4">
            {finalResults.length > 0 && hasWinner() && (
              <>
                Congrats, <span className="font-medium text-black bg-white border border-gray-300 px-3 py-1 rounded-full">{finalResults[0]?.creator_name}</span> wins this round!
              </>
            )}
            {finalResults.length > 0 && !hasWinner() && (
              <>
                Great effort from all!
              </>
            )}
          </p>
        </div>
      </div>

      {/* reference-image area - now at the top for easy comparison */}
      {referenceImage && (
        <div className="px-6 py-2 border-b border-gray-200">
          <div className="flex items-center gap-8 py-2 bg-gray-200 rounded-lg px-4 py-4">
            {/* Original Image label and placeholder */}
            <div className="flex min-w-0 w-72">
              <div className="bg-white border border-gray-300 px-3 py-2 rounded-full">
                <span className="text-black font-bold text-base whitespace-nowrap">Original Image</span>
              </div>
            </div>
            
            <div className="flex items-center flex-1 gap-6">
              {/* reference image */}
              <div className="w-24 h-24">
                <img
                  src={getImageUrl(referenceImage.image_path)}
                  alt={referenceImage.description}
                  className="w-24 h-24 rounded-lg object-cover border border-gray-200"
                  onError={(e) => {
                    console.error('Failed to load image:', e.target.src);
                    e.target.style.display = 'none';
                  }}
                />
              </div>
              
              {/* Prompt info */}
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 mb-1">Prompt</p>
                <p className="text-sm font-medium">
                  {highlightOriginalPrompt(referenceImage.description)}
                </p>
              </div>
            </div>
            
            {/* Token stats */}
            <div className="text-center min-w-[120px]">
              <div className="text-xl font-bold">
                {referenceImage.description ? referenceImage.description.split(' ').length : 0}
              </div>
              <div className="text-xs text-gray-500">
                Tokens
              </div>
            </div>
            
            {/* empty placeholder to keep alignment */}
            <div className="text-center min-w-[60px]">
            </div>
          </div>
        </div>
      )}
      
      {/* results-list area */}
      <div className="flex-1 flex flex-col">
        {isLoadingResults ? (
          <div className="flex flex-col items-center justify-center h-64">
            <MetroSpinner loading={true} color="#111111" size={50} />
            <p className="mt-4 text-gray-600 text-lg">Calculating results...</p>
          </div>
        ) : finalResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64">
            <div className="text-6xl mb-4">🎯</div>
            <p className="text-xl text-gray-600 text-center">
              No results to display
            </p>
          </div>
        ) : (
          <div className="space-y-2 flex-1 overflow-auto px-6">
            {finalResults.map((item, index) => (
              <>
                <div 
                  key={item.creator_sid}
                  className="flex items-center gap-8 py-2"
                >
                  {/* player name and score */}
                  <div className="flex min-w-0 w-72">
                    <div className="bg-white border border-gray-300 px-3 py-2 rounded-full">
                      <span className="text-black font-bold text-sm whitespace-nowrap">{item.creator_name}</span>
                    </div>
                    <div className="bg-green-500 text-white px-3 py-2 rounded-full text-sm font-bold whitespace-nowrap absolute left-52">
                      + {item.score_info.total_score} points
                    </div>
                  </div>
                  
                  <div className="flex items-center flex-1 gap-6">
                    {/* generated image */}
                    <div className="w-24 h-24">
                      <img
                        src={getImageUrl(item.image_url)}
                        alt={`Creation by ${item.creator_name}`}
                        className="w-24 h-24 rounded-lg object-cover border border-gray-200"
                        onError={(e) => {
                          console.error('Failed to load image:', e.target.src);
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                    
                    {/* Prompt info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-gray-500 mb-1">Prompt</p>
                      <p className="text-sm font-medium">
                        {highlightMatchingWords(item.prompt, referenceDescription)}
                      </p>
                    </div>
                  </div>
                  
                  {/* Token stats */}
                  <div className="text-center min-w-[120px]">
                    <div className="text-xl font-bold">
                      {item.score_info.prompt_tokens}
                    </div>
                    <div className="text-xs text-gray-500">
                      Tokens
                    </div>
                    {item.score_info.penalty > 0 && (
                      <div className="text-red-500 text-xs mt-1">-1 for longest prompt</div>
                    )}
                  </div>
                  
                  {/* Votes stats */}
                  <div className="text-center min-w-[60px]">
                    <div className="text-xl font-bold">
                      {item.vote_count}
                    </div>
                    <div className="text-xs text-gray-500">
                      Votes
                    </div>
                    {item.vote_count > 0 && (
                      <div className="text-green-500 text-xs mt-1">+{item.vote_count} point{item.vote_count > 1 ? 's' : ''}</div>
                    )}
                  </div>
                </div>
                {index < finalResults.length - 1 && (
                  <div className="h-px bg-gray-200/60" />
                )}
              </>
            ))}
          </div>
        )}
      </div>
      
      {/* bottom area: reflection question and button on the same row */}
      {finalResults.length > 0 && (
        <div className="mt-6 flex items-center gap-4 p-4 border-t-2 border-gray-200">
          <div className="flex-1 flex items-center gap-2 text-gray-800 bg-gray-100 px-4 py-2 rounded-lg">
            <span className="text-base">Discuss time! Share your thoughts with other players and feel free to try two more prompts!</span>
          </div>
          <button
            className="bg-black text-white px-6 py-2 rounded-xl font-semibold hover:bg-gray-800 transition-colors"
            onClick={handlePlayerDone}
          >
            {round >= totalRounds ? 'Finish Game' : 'Next round'}
          </button>
        </div>
      )}
      
      {/* if there are no results, show only the button */}
      {finalResults.length === 0 && (
        <div className="flex justify-center mt-6">
          <button
            className="bg-black text-white px-8 py-3 rounded-xl font-semibold text-lg hover:bg-gray-800 transition-colors"
            onClick={handlePlayerDone}
          >
            {round >= totalRounds ? 'Finish Game' : 'Next round'}
          </button>
        </div>
      )}
    </div>
  );
}