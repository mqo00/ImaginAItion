import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Container from '../common/Container';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(API_ENDPOINTS.ADMIN_LOGIN, {
        username,
        password
      });

      if (response.data.success) {
        // Store the token in localStorage
        localStorage.setItem('adminToken', response.data.token);
        localStorage.setItem('adminTokenExpires', response.data.expires_at);
        
        // Navigate to admin dashboard
        navigate('/admin/dashboard');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-svh flex flex-col font-inter">
      <div className="main-container h-full mt-20">
        <Container>
          <div className="h-full flex flex-col items-center justify-center">
            {/* Header */}
            <div className="text-center mb-12">
              <Link to="/" className="font-gooper [-webkit-text-stroke:1.5px_black] bg-gradient-to-r from-[#5FB1E0] to-[#FAF8E0] inline-block text-transparent bg-clip-text font-semibold text-[3rem] drop-shadow-[5px_5px_0px_rgba(0,0,0,1)] mb-4">
                ImaginAItion Admin
              </Link>
              <div className="font-inter text-[20px] text-[#5A5A5A]">
                Game Logs Management System
              </div>
            </div>

            {/* Login Form */}
            <div className="bg-white border-2 border-black rounded-xl p-8 shadow-[4px_4px_0px_rgba(0,0,0,1)] max-w-md w-full">
              <h2 className="font-gooper font-semibold text-[1.5rem] text-center mb-6">Admin Login</h2>
              
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block font-inter font-medium text-[14px] text-[#5A5A5A] mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-3 py-2 border-2 border-black rounded-lg font-inter text-[16px] focus:outline-none focus:border-[#5FB1E0]"
                    placeholder="Enter username"
                    required
                  />
                </div>

                <div>
                  <label className="block font-inter font-medium text-[14px] text-[#5A5A5A] mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 border-2 border-black rounded-lg font-inter text-[16px] focus:outline-none focus:border-[#5FB1E0]"
                    placeholder="Enter password"
                    required
                  />
                </div>

                {error && (
                  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className={`w-full font-gooper font-medium border-2 border-black rounded-xl text-[1.2rem] py-3 mt-6 ${
                    loading 
                      ? 'bg-gray-300 cursor-not-allowed' 
                      : 'bg-[#D7E5FF] hover:bg-[#C1D9FF] active:translate-y-1'
                  } transition-all`}
                >
                  {loading ? 'Logging in...' : 'Login'}
                </button>
              </form>

              <div className="text-center mt-4">
                <Link 
                  to="/" 
                  className="font-inter text-[14px] text-[#5A5A5A] hover:text-[#5FB1E0]"
                >
                  Back to Home
                </Link>
              </div>
            </div>

          </div>
        </Container>
      </div>
    </div>
  );
}