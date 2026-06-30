import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Container from '../common/Container';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

export default function AdminDashboard() {
  const [logs, setLogs] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exportLoading, setExportLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const navigate = useNavigate();

  // Check authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem('adminToken');
    const expires = localStorage.getItem('adminTokenExpires');
    
    if (!token || !expires || new Date() > new Date(expires)) {
      localStorage.removeItem('adminToken');
      localStorage.removeItem('adminTokenExpires');
      navigate('/admin');
      return;
    }

    // Verify token with backend
    verifyToken(token);
    loadLogs(token);
  }, [navigate]);

  // Auto-refresh logs every 30 seconds
  useEffect(() => {
    const token = localStorage.getItem('adminToken');
    if (!token) return;

    const interval = setInterval(() => {
      const currentToken = localStorage.getItem('adminToken');
      const expires = localStorage.getItem('adminTokenExpires');
      
      if (currentToken && expires && new Date() < new Date(expires)) {
        loadLogs(currentToken);
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const verifyToken = async (token) => {
    try {
      await axios.get(`${API_ENDPOINTS.ADMIN_VERIFY}?token=${token}`);
    } catch (err) {
      console.error('Token verification failed:', err);
      localStorage.removeItem('adminToken');
      localStorage.removeItem('adminTokenExpires');
      navigate('/admin');
    }
  };

  const loadLogs = async (token) => {
    try {
      const response = await axios.get(`${API_ENDPOINTS.ADMIN_LIST_LOGS}?token=${token}`);
      setLogs(response.data.game_logs || []);
      setLastUpdated(new Date());
      setError(''); // Clear any previous errors
    } catch (err) {
      console.error('Error loading logs:', err);
      setError('Failed to load game logs');
    } finally {
      setLoading(false);
    }
  };

  const refreshLogs = async () => {
    const token = localStorage.getItem('adminToken');
    if (token) {
      setLoading(true);
      await loadLogs(token);
    }
  };

  const loadLogDetail = async (gameId) => {
    const token = localStorage.getItem('adminToken');
    try {
      const response = await axios.get(`${API_ENDPOINTS.ADMIN_GET_LOG(gameId)}?token=${token}`);
      setSelectedLog(response.data);
    } catch (err) {
      console.error('Error loading log detail:', err);
      setError('Failed to load log details');
    }
  };

  const exportLogs = async () => {
    const token = localStorage.getItem('adminToken');
    setExportLoading(true);
    try {
      const response = await axios.get(`${API_ENDPOINTS.ADMIN_EXPORT_LOGS}?token=${token}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `imaginaition_logs_${new Date().toISOString().slice(0, 10)}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting logs:', err);
      setError('Failed to export logs');
    } finally {
      setExportLoading(false);
    }
  };

  const exportGameData = async (gameId) => {
    const token = localStorage.getItem('adminToken');
    setExportLoading(true);
    try {
      const response = await axios.get(`/api/export-game/${gameId}?token=${token}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `game_${gameId}_export.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting game data:', err);
      setError('Failed to export game data');
    } finally {
      setExportLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminTokenExpires');
    navigate('/admin');
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
      // Handle ISO timestamp format (e.g., "2025-08-15T16:15:23.123456Z")
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      return date.toLocaleString();
    } catch (error) {
      console.error('Error formatting timestamp:', timestamp, error);
      return 'Invalid Date';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  const formatDuration = (start, end) => {
    if (!start || !end) return 'N/A';
    const duration = new Date(end) - new Date(start);
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  if (loading) {
    return (
      <div className="h-svh flex items-center justify-center">
        <div className="text-[1.5rem] font-gooper">Loading logs...</div>
      </div>
    );
  }

  return (
    <div className="h-svh flex flex-col font-inter">
      <div className="main-container h-full">
        <Container>
          <div className="h-full flex flex-col py-8">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <Link to="/" className="font-gooper [-webkit-text-stroke:1px_black] bg-gradient-to-r from-[#5FB1E0] to-[#FAF8E0] inline-block text-transparent bg-clip-text font-semibold text-[2rem] drop-shadow-[3px_3px_0px_rgba(0,0,0,1)]">
                  ImaginAItion Admin
                </Link>
                <div className="font-inter text-[16px] text-[#5A5A5A] mt-2">
                  Game Logs Dashboard
                  {lastUpdated && (
                    <div className="text-[12px] text-[#8A8A8A] mt-1">
                      Last updated: {lastUpdated.toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={refreshLogs}
                  disabled={loading}
                  className={`font-gooper font-medium border-2 border-black rounded-xl text-[14px] px-4 py-2 ${
                    loading ? 'bg-gray-300' : 'bg-[#D7E5FF] hover:bg-[#C1D9FF]'
                  }`}
                >
                  {loading ? 'Refreshing...' : 'Refresh Logs'}
                </button>
                <button
                  onClick={exportLogs}
                  disabled={exportLoading}
                  className={`font-gooper font-medium border-2 border-black rounded-xl text-[14px] px-4 py-2 ${
                    exportLoading ? 'bg-gray-300' : 'bg-[#FFE5B4] hover:bg-[#FFD700]'
                  }`}
                >
                  {exportLoading ? 'Exporting...' : 'Export All Logs'}
                </button>
                <button
                  onClick={logout}
                  className="font-gooper font-medium border-2 border-black rounded-xl text-[14px] px-4 py-2 bg-[#FFCCCC] hover:bg-[#FFAAAA]"
                >
                  Logout
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            <div className="flex-1 flex gap-6 overflow-hidden">
              {/* Logs List */}
              <div className="w-1/2 border-2 border-black rounded-xl bg-white shadow-[4px_4px_0px_rgba(0,0,0,1)] overflow-hidden">
                <div className="bg-[#F0F0F0] border-b-2 border-black p-4">
                  <h2 className="font-gooper font-semibold text-[1.2rem]">Game Logs ({logs.length})</h2>
                </div>
                <div className="overflow-y-auto h-full p-4 space-y-3">
                  {logs.length === 0 ? (
                    <div className="text-center text-[#5A5A5A] py-8">
                      No game logs found
                    </div>
                  ) : (
                    logs.map((log, index) => (
                      <div
                        key={index}
                        onClick={() => loadLogDetail(log.game_id)}
                        className={`p-4 border-2 border-black rounded-lg cursor-pointer transition-all ${
                          selectedLog?.game_id === log.game_id
                            ? 'bg-[#D7E5FF]'
                            : 'bg-white hover:bg-[#F5F5F5]'
                        }`}
                      >
                        <div className="font-gooper font-medium text-[16px] mb-2">
                          Game {log.game_id}
                        </div>
                        <div className="text-[12px] text-[#5A5A5A] space-y-1">
                          <div>Started: {formatTimestamp(log.start_timestamp)}</div>
                          {/* <div>Size: {formatFileSize(log.file_size)}</div>
                          <div>Players: {Object.keys(log.players || {}).length}</div> */}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Log Details */}
              <div className="w-1/2 border-2 border-black rounded-xl bg-white shadow-[4px_4px_0px_rgba(0,0,0,1)] overflow-hidden">
                <div className="bg-[#F0F0F0] border-b-2 border-black p-4">
                  <div className="flex justify-between items-center">
                    <h2 className="font-gooper font-semibold text-[1.2rem]">
                      {selectedLog ? `Game ${selectedLog.game_id} Details` : 'Select a Log'}
                    </h2>
                    {selectedLog && (
                      <button
                        onClick={() => exportGameData(selectedLog.game_id)}
                        disabled={exportLoading}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                          exportLoading 
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                            : 'bg-green-500 text-white hover:bg-green-600'
                        }`}
                      >
                        {exportLoading ? 'Exporting...' : '📦 Export Game + Images'}
                      </button>
                    )}
                  </div>
                </div>
                <div className="overflow-y-auto h-full p-4">
                  {selectedLog ? (
                    <div className="space-y-6">
                      {/* Game Summary */}
                      <div className="bg-[#E8F4FD] p-4 rounded-lg border border-[#B3D9FF]">
                        <h3 className="font-gooper font-medium text-[16px] mb-3">Game Summary</h3>
                        <div className="text-[14px] space-y-1">
                          <div><strong>Game ID:</strong> {selectedLog.game_id}</div>
                          <div><strong>Started:</strong> {formatTimestamp(selectedLog.start_timestamp)}</div>
                          <div><strong>Ended:</strong> {formatTimestamp(selectedLog.end_timestamp)}</div>
                          <div><strong>Duration:</strong> {formatDuration(selectedLog.start_timestamp, selectedLog.end_timestamp)}</div>
                          <div><strong>Rounds:</strong> {selectedLog.total_rounds}</div>
                          <div><strong>Completed:</strong> {selectedLog.game_completed ? 'Yes' : 'No'}</div>
                        </div>
                      </div>

                      {/* Players & Scores */}
                      <div className="bg-[#FFF3CD] p-4 rounded-lg border border-[#FFE69C]">
                        <h3 className="font-gooper font-medium text-[16px] mb-3">Final Scores</h3>
                        <div className="space-y-2">
                          {selectedLog.final_scores && Object.entries(selectedLog.final_scores)
                            .sort(([,a], [,b]) => (b.total_score || 0) - (a.total_score || 0))
                            .map(([sid, player]) => (
                              <div key={sid} className="flex justify-between text-[14px]">
                                <span><strong>{player.player_name}</strong></span>
                                <span>{player.total_score} points</span>
                              </div>
                            ))
                          }
                        </div>
                      </div>

                      {/* Round Results */}
                      {selectedLog.round_results && (
                        <div className="bg-[#D1ECF1] p-4 rounded-lg border border-[#B3E5FC]">
                          <h3 className="font-gooper font-medium text-[16px] mb-3">Round Results</h3>
                          <div className="space-y-3">
                            {selectedLog.round_results.map((round, index) => (
                              <div key={index} className="bg-white p-3 rounded border">
                                <div className="font-medium text-[14px] mb-2">Round {round.round_num}</div>
                                <div className="text-[12px] text-[#5A5A5A] mb-2">
                                  Reference: {round.reference_image?.description}
                                </div>
                                <div className="space-y-1">
                                  {round.player_results?.map((result, i) => (
                                    <div key={i} className="text-[12px] flex justify-between">
                                      <span>{result.player_name}: "{result.prompt}"</span>
                                      <span>{result.votes_received} votes, {result.score} pts</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Player Actions Summary */}
                      {selectedLog.player_actions && (
                        <div className="bg-[#F8F9FA] p-4 rounded-lg border border-[#DEE2E6]">
                          <h3 className="font-gooper font-medium text-[16px] mb-3">Actions Summary</h3>
                          <div className="text-[12px] text-[#5A5A5A]">
                            Total actions: {selectedLog.player_actions.length}
                          </div>
                          <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                            {selectedLog.player_actions.slice(0, 20).map((action, index) => (
                              <div key={index} className="text-[11px] bg-white p-2 rounded border">
                                {new Date(action.timestamp).toLocaleTimeString()}: {action.player_name} - {action.action_type}
                                {action.action_type === 'vote' && ` for ${action.voted_for_name}`}
                              </div>
                            ))}
                            {selectedLog.player_actions.length > 20 && (
                              <div className="text-[11px] text-[#5A5A5A] text-center py-2">
                                ... and {selectedLog.player_actions.length - 20} more actions
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center text-[#5A5A5A] py-12">
                      Click on a game log to view details
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Container>
      </div>
    </div>
  );
}