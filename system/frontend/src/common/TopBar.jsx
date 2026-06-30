import '../App.css';
import { Link } from 'react-router-dom';

export default function TopBar() {
  return (
    <div className="pt-8 pl-8 text-left place-self-start">
      <Link to="/">
        {/* need to replace font */}
        <h1 className="text-white font-extrabold text-[2rem] drop-shadow-[3px_3px_0px_rgba(0,0,0,1)] font-gooper [-webkit-text-stroke:0.63px_black]">
          ImaginAItion
        </h1>
      </Link>
    </div>
  );
}
