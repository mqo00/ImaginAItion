import '../App.css';
import { Link } from 'react-router-dom';

export default function BackButton() {
  return (
    <div className="mb-3 mt-10 ml-10">
      <Link to="/">
        <i className="fa-solid fa-chevron-left"></i>
        <span className="font-medium text-xl ml-2 font-gooper"> Back</span>
      </Link>
    </div>
  );
}
