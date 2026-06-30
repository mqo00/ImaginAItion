import '../App.css';
import Container from '../common/Container';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="h-svh flex flex-col font-inter">
      <div className="main-container h-full mt-20">
        <Container>
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="font-gooper [-webkit-text-stroke:1.5px_black] bg-gradient-to-r from-[#5FB1E0] to-[#FAF8E0] inline-block text-transparent bg-clip-text font-semibold text-[4rem] drop-shadow-[5px_5px_0px_rgba(0,0,0,1)] mb-6">
              ImaginAItion
            </div>
            <div className="font-inter text-[32px] text-[#5A5A5A] mb-20">
              A generative AI drawing and guessing game
            </div>
            <div className="flex justify-center mb-8">
              {/* Add links to the Start Game, Join Game, and How to Play pages. */}
              <Link to="/start">
                <button className="font-gooper font-medium border border-black rounded-xl text-[2rem] pl-8 pr-8 pb-3 pt-3 mr-5 bg-[#D7E5FF]">
                  Start Game
                </button>
              </Link>
              <Link to="/join">
                <button className="font-gooper font-medium border border-black rounded-xl text-[2rem] pl-8 pr-8 pb-3 pt-3 ml-5 bg-[#D7E5FF]">
                  Join Game
                </button>
              </Link>
            </div>
            <div className="flex flex-col items-center gap-4">
              <Link to="/how-to-play">
                <button className="font-gooper font-medium border border-black rounded-xl text-[2rem] pl-8 pr-8 pb-3 pt-3 bg-[#EAEAEA]">
                  How to Play
                </button>
              </Link>
              <Link to="/tutorial">
                <button className="font-gooper font-medium border border-black rounded-xl text-[2rem] pl-8 pr-8 pb-3 pt-3 bg-[#EAEAEA]">
                  Game Tutorial
                </button>
              </Link>
            </div>
          </div>
        </Container>
      </div>
    </div>
  );
}
