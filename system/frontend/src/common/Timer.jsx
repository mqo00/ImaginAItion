import '../App.css';
import socket from './websocket';
import { useEffect, useState } from 'react';

export default function Timer() {
  const [timeLeft, setTimeLeft] = useState(-1);

  useEffect(() => {
    // Listen for backend updates on the timer
    const handleTimerUpdate = (data) => {
      setTimeLeft(data.time_left);
    };

    socket.on('update_timer', handleTimerUpdate);

    return () => {
      socket.off('update_timer', handleTimerUpdate);
    };
  }, []);
  // useEffect(() => {
  //   if (timeLeft === 0) {
  //     alert("Time's up! Please submit your answer.");
  //   }
  // }, [timeLeft]);

  return (
    <div className="flex font-inter mt-8 mr-8 text-center place-self-end bg-black text-white rounded-[0.5rem] border-black border-[0.063rem] gap-x-2 pt-2 pb-2 pl-4 pr-4 text-[1.25rem] font-semibold items-center whitespace-nowrap">
      <i className="fa-regular fa-clock"></i>
      {timeLeft < 0 ? <p>No Time Limit</p> : <p>{`${timeLeft}s left`}</p>}
    </div>
  );
}
