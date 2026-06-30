import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Home from './pages/Home';
import JoinGame from './pages/JoinGame';
import StartGame from './pages/StartGame';
import HowToPlay from './pages/HowToPlay';
import PlayGame from './pages/PlayGame';
import GameResult from './pages/GameResult';
import Image from './pages/Image';
import Tutorial from './pages/Tutorial';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/join" element={<JoinGame />} />
        <Route path="/start" element={<StartGame />} />
        <Route path="/how-to-play" element={<HowToPlay />} />
        <Route path="/play/:gameCode" element={<PlayGame />} />
        <Route path="/results" element={<GameResult />} />
        <Route path="/image" element={<Image />} />
        <Route path="/tutorial" element={<Tutorial />} />
        <Route path="/admin" element={<AdminLogin />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
