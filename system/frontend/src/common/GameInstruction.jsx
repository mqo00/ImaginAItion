import '../App.css';
import PropTypes from 'prop-types';
import GenerateIcon from '../assets/GenerateIcon';
import VotingIcon from '../assets/VotingIcon';
import RevealIcon from '../assets/RevealIcon';

export default function GameInstruction({ currentTurn }) {
  return (
    <div className="grid w-full bg-[#D7E5FF] p-5 rounded-t-[1.25rem] gap-2 border-b-black border-b-[0.063rem]">
      <div className="block flex justify-center gap-2 items-center">
        {/* new 4-phase flow: Generate(0) -> Voting(1) -> Reveal(2) -> Result(3) */}
        {currentTurn % 4 === 0 ? (
          <GenerateIcon />
        ) : currentTurn % 4 === 1 ? (
          <VotingIcon />
        ) : currentTurn % 4 === 2 ? (
          <RevealIcon />
        ) : null}
        {currentTurn % 4 === 0 ? (
          <p className="font-medium text-[1.5rem] font-gooper">
            Generate an Image
          </p>
        ) : currentTurn % 4 === 1 ? (
          <p className="font-medium text-[1.5rem] font-gooper">
            Vote for Best Image
          </p>
        ) : currentTurn % 4 === 2 ? (
          <p className="font-medium text-[1.5rem] font-gooper">
            Reveal
          </p>
        ) : (
          <p className="font-medium text-[1.5rem]">
                        {`Round ${Math.floor(currentTurn / 4)+1} Results`}
          </p>
        )}
      </div>
      {/* updated to the new 4-phase instructions copy */}
      {currentTurn % 4 === 0 ? (
        <p className="justify-self-center text-[#4E4E4E] font-inter">
          Generate an image that best recreates the given image with as few as possible words in prompt.
        </p>
      ) : currentTurn % 4 === 1 ? (
        <p className="justify-self-center text-[#4E4E4E] font-inter">
          Select the image that best matches the original.
        </p>
      ) : currentTurn % 4 === 2 ? (
        <p className="justify-self-center text-[#4E4E4E] font-inter">
          See who got the most points and used the shortest prompt
        </p>
      ) : null}
    </div>
  );
}

GameInstruction.propTypes = {
  currentTurn: PropTypes.number,
};
