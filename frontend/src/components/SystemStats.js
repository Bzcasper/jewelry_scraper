import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './SystemStats.css'; // Optional, if you want to style it separately

const SystemStats = () => {
  const [stats, setStats] = useState({
    cpuUsage: null,
    memoryUsage: null,
    diskSpace: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Function to fetch system stats
    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/system-stats'); // Adjust API endpoint as needed
        setStats(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load system stats.');
        setLoading(false);
      }
    };

    fetchStats();

    // Optionally, refresh stats every 10 seconds
    const interval = setInterval(fetchStats, 10000);

    return () => clearInterval(interval); // Cleanup interval on component unmount
  }, []);

  if (loading) return <p>Loading system stats...</p>;
  if (error) return <p>{error}</p>;

  return (
    <div className="system-stats">
      <h2>System Statistics</h2>
      <div className="stats-container">
        <div className="stat">
          <h3>CPU Usage</h3>
          <p>{stats.cpuUsage ? `${stats.cpuUsage}%` : 'N/A'}</p>
        </div>
        <div className="stat">
          <h3>Memory Usage</h3>
          <p>{stats.memoryUsage ? `${stats.memoryUsage} MB` : 'N/A'}</p>
        </div>
        <div className="stat">
          <h3>Disk Space</h3>
          <p>{stats.diskSpace ? `${stats.diskSpace} GB` : 'N/A'}</p>
        </div>
      </div>
    </div>
  );
};

export default SystemStats;
