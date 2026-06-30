import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import sio from './websocket';
import { MetroSpinner } from 'react-spinners-kit';
import Waiting from './Waiting';
import { getImageUrl } from '../config/api';

export default function RevealPrompt() {
  const { gameCode } = useParams();
  const [waitingForPlayers, setWaitingForPlayers] = useState(false);
  const [timeLeft, setTimeLeft] = useState(-1);
  
  // reference-image state
  const [referenceImage, setReferenceImage] = useState(null);
  const [isLoadingReference, setIsLoadingReference] = useState(true);
  
  // reveal-data state
  const [revealData, setRevealData] = useState([]);
  const [isLoadingData, setIsLoadingData] = useState(true);
  
  // card-display state
  const [visibleCards, setVisibleCards] = useState(new Set());
  const [isAutoProgressing, setIsAutoProgressing] = useState(false);
  const [easingOutCards, setEasingOutCards] = useState(new Set());
  const animationStartedRef = useRef(false);

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

  // get the reference image
  useEffect(() => {
    const fetchReferenceImage = async () => {
      if (!sio.id || !sio.connected) {
        setTimeout(fetchReferenceImage, 200);
        return;
      }
      
      try {
        setIsLoadingReference(true);
        const response = await axios.get(`/api/reference-image?room_id=${gameCode}&sid=${sio.id}`);
        setReferenceImage(response.data);
      } catch (error) {
        console.error('Error fetching reference image:', error);
      } finally {
        setIsLoadingReference(false);
      }
    };
    
    fetchReferenceImage();
  }, [gameCode]);

  // get reveal data
  useEffect(() => {
    const fetchRevealData = async () => {
      if (!sio.id || !sio.connected) {
        setTimeout(fetchRevealData, 200);
        return;
      }
      
      try {
        setIsLoadingData(true);
        // reset state
        setVisibleCards(new Set());
        setIsAutoProgressing(false);
        setEasingOutCards(new Set());
        animationStartedRef.current = false;
        
        const response = await axios.get(`/api/reveal-data?room_id=${gameCode}&sid=${sio.id}`);
        const data = response.data.data || [];
        console.log('🎯 Fetched reveal data:', data.length, 'items', data);
        setRevealData(data);
      } catch (error) {
        console.error('Error fetching reveal data:', error);
      } finally {
        setIsLoadingData(false);
      }
    };
    
    fetchRevealData();
  }, [gameCode]);

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

  // handle player completion
  const handlePlayerDone = async () => {
    if (waitingForPlayers) {
      console.log('⚠️ Already waiting for players, skipping player-done');
      return;
    }
    
    console.log('📤 RevealPrompt: Sending player-done event', {
      gameCode,
      socketId: sio.id,
      socketConnected: sio.connected
    });
    
    try {
      await sio.emit('player-done', {
        room_id: gameCode,
        sid: sio.id,
      });
      console.log('✅ RevealPrompt: player-done event sent successfully');
    } catch (error) {
      console.error('❌ RevealPrompt: Error sending player-done event:', error);
    }
    
    setWaitingForPlayers(true);
  };

  // automatic card fade-in and progress control
  useEffect(() => {
    console.log('🔍 Effect triggered:', {
      revealDataLength: revealData.length,
      isLoadingData,
      animationStarted: animationStartedRef.current
    });
    
    if (revealData.length === 0) {
      console.log('⏸️ No data yet, waiting...');
      return;
    }
    
    if (isLoadingData) {
      console.log('⏸️ Still loading data, waiting...');
      return;
    }
    
    if (animationStartedRef.current) {
      console.log('⏸️ Animation already started, skipping...');
      return;
    }
    
    console.log('🎭 Starting reveal animation for', revealData.length, 'cards');
    animationStartedRef.current = true;
    setIsAutoProgressing(true);
    
    const timers = [];
    
    // set a fade-in timer for each card (starting after 1s, 1000ms apart)
    revealData.forEach((_, index) => {
      const delay = 1000 + (index * 1000); // 1s initial delay + 1s between cards
      console.log(`⏰ Setting timer for card ${index + 1} with delay ${delay}ms`);

      const timer = setTimeout(() => {
        console.log(`📱 Showing card ${index + 1}`);
        setVisibleCards(prev => {
          const newSet = new Set(prev);
          newSet.add(index);
          console.log(`🎯 Updated visible cards:`, Array.from(newSet));
          return newSet;
        });
      }, delay);

      timers.push(timer);
    });

    // compute the animation end time and set up hold and ease-out logic
    const animationCompleteTime = 1000 + (revealData.length * 1000);
    const displayDuration = 5000; // hold for 5s after all cards are shown (more viewing time)
    const easeOutInterval = 800; // 800ms between each card's ease-out
    const easeOutAnimationDuration = 1000; // each card's ease-out animation lasts 1s
    
    const totalTime = animationCompleteTime + displayDuration + (revealData.length * easeOutInterval) + easeOutAnimationDuration;
    console.log(`🎭 Animation timeline: fade-in ${animationCompleteTime/1000}s → display ${displayDuration/1000}s → ease-out ${((revealData.length * easeOutInterval) + easeOutAnimationDuration)/1000}s → total ${totalTime/1000}s`);
    
    // set a timer to start easing out after the hold
    const easeOutStartTime = animationCompleteTime + displayDuration;
    
    // set an ease-out timer for each card
    revealData.forEach((_, index) => {
      const easeOutDelay = easeOutStartTime + (index * easeOutInterval);
      console.log(`⏰ Setting ease out timer for card ${index + 1} with delay ${easeOutDelay}ms`);
      
      const easeOutTimer = setTimeout(() => {
        console.log(`🌊 Easing out card ${index + 1}`);
        setEasingOutCards(prev => {
          const newSet = new Set(prev);
          newSet.add(index);
          return newSet;
        });
      }, easeOutDelay);
      
      timers.push(easeOutTimer);
    });
    
    // call handlePlayerDone after all cards finish easing out
    const allEaseOutCompleteTime = easeOutStartTime + (revealData.length * easeOutInterval) + easeOutAnimationDuration;
    const finalTimer = setTimeout(() => {
      console.log('✅ All ease out complete, calling handlePlayerDone');
      handlePlayerDone();
    }, allEaseOutCompleteTime);
    
    timers.push(finalTimer);
    
    // return a cleanup function to clear the timers
    return () => {
      console.log('🧹 Cleaning up timers');
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [revealData.length, isLoadingData]);



  return (
    <>
      {waitingForPlayers && <Waiting />}
      
          
      
      {/* layout: reference image on the left + results area on the right */}
      <div className="flex h-full w-full px-8 gap-6">
        {/* left-side reference-image area */}
        <div className="w-1/4 flex flex-col">
          <h3 className="text-lg font-inter font-medium mb-3 text-center">Reference Image</h3>
          <div className="flex-1 border border-gray-300 rounded-2xl p-4 bg-gray-50 flex flex-col items-center justify-start">
            {isLoadingReference ? (
              <div className="flex flex-col items-center">
                <MetroSpinner loading={true} color="#111111" size={50} />
                <p className="mt-2 text-gray-600">Loading reference...</p>
              </div>
            ) : referenceImage ? (
              <div className="flex flex-col items-center">
                <img
                  src={getImageUrl(referenceImage.image_path)}
                  alt={referenceImage.description}
                  className="max-w-full max-h-full rounded-xl object-contain mb-3"
                  onError={(e) => {
                    console.error('Failed to load image:', e.target.src);
                    e.target.style.display = 'none';
                  }}
                />
                <div className="text-center">
                  {/* <p className="font-medium text-gray-800">{referenceImage.content}</p> */}
                  <p className="font-medium text-gray-800">{"Original Image"}</p>
                  <p className="text-sm text-gray-600 mt-1">{referenceImage.description}</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No reference image available</p>
            )}
          </div>
        </div>
        
        {/* right-side results area */}
        <div className="w-2/3 flex flex-col">
          <h3 className="text-lg font-inter font-medium mb-3 text-center">
            Prompts Revealed!
          </h3>
          
          {isLoadingData ? (
            <div className="flex-1 flex flex-col items-center justify-center">
              <MetroSpinner loading={true} color="#111111" size={50} />
              <p className="mt-2 text-gray-600">Loading results...</p>
            </div>
          ) : revealData.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="text-6xl mb-4">🎨</div>
              <p className="text-lg text-gray-600 text-center">
                No creations to display
              </p>
            </div>
          ) : (
            <div className="flex-1 overflow-auto p-4">
              {/* two-column grid layout */}
              <div className="grid grid-cols-2 gap-6">
                {revealData.map((item, index) => {
                  const isVisible = visibleCards.has(index);
                  const isEasingOut = easingOutCards.has(index);
                  
                  return (
                    <div 
                      key={item.creator_sid}
                      className={`border-2 border-gray-300 rounded-2xl p-4 bg-white shadow-sm hover:shadow-lg transition-all duration-700 ease-out transform ${
                        isEasingOut
                          ? 'opacity-0 scale-95 translate-y-8 -translate-x-4'
                          : isVisible
                          ? 'opacity-100 scale-100 translate-y-0' 
                          : 'opacity-0 scale-95 translate-y-4'
                      }`}
                      style={{
                        animationDelay: `${index * 0.2}s`
                      }}
                    >
                      {/* Image */}
                      <div className={`mb-4 transition-all duration-500 ${
                        isEasingOut
                          ? 'opacity-0 transform translate-y-4 scale-95'
                          : isVisible
                          ? 'opacity-100 transform translate-y-0' 
                          : 'opacity-0 transform translate-y-2'
                      }`}
                      style={{ transitionDelay: `${index * 0.2 + 0.1}s` }}>
                        <img
                          src={getImageUrl(item.image_url)}
                          alt={`Creation by ${item.creator_name}`}
                          className="w-full h-full rounded-xl object-cover shadow-lg"
                          onError={(e) => {
                            console.error('Failed to load image:', e.target.src);
                            e.target.style.display = 'none';
                          }}
                        />
                      </div>
                      
                      {/* creator and prompt */}
                      <div className={`mb-3 transition-all duration-500 ${
                        isEasingOut
                          ? 'opacity-0 transform translate-y-4 scale-95'
                          : isVisible
                          ? 'opacity-100 transform translate-y-0' 
                          : 'opacity-0 transform translate-y-2'
                      }`}
                      style={{ transitionDelay: `${index * 0.2 + 0.2}s` }}>
                        {/* <p className="font-bold text-lg text-gray-800 mb-2">
                          {item.creator_name}
                        </p> */}
                        <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-3 rounded-lg border border-gray-200">
                          <p className="text-sm font-medium text-gray-700 mb-1">Prompt:</p>
                          <p className="text-sm text-gray-600 italic">
                            "{highlightMatchingWords(item.prompt, referenceImage?.description)}"
                          </p>
                        </div>
                      </div>
                      
                      {/* Voter */}
                      <div className={`transition-all duration-500 ${
                        isEasingOut
                          ? 'opacity-0 transform translate-y-4 scale-95'
                          : isVisible
                          ? 'opacity-100 transform translate-y-0' 
                          : 'opacity-0 transform translate-y-2'
                      }`}
                      style={{ transitionDelay: `${index * 0.2 + 0.3}s` }}>
                        {/* <p className="text-sm font-medium text-gray-700 mb-2">
                          Voted by ({item.vote_count}):
                        </p> */}
                        {item.voter_names.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {item.voter_names.map((voterName, voterIndex) => (
                              <span 
                                key={voterIndex}
                                className="inline-block bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 px-3 py-1 rounded-full text-sm shadow-sm hover:shadow-md transition-shadow duration-300"
                              >
                                ❤️ {voterName}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-2">
                            {/* <span className="text-gray-400 text-sm">No votes received</span> */}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
} 