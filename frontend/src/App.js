import React, { useState, useEffect } from 'react';
import { AlertCircle, Settings, Moon, Sun, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import SearchBar from './components/SearchBar';
import DataTable from './components/DataTable';
import DataDashboard from './components/DataDashboard';
import EnhancedSearch from './components/EnhancedSearch';

const App = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedView, setSelectedView] = useState('dashboard');
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
  const [systemStatus, setSystemStatus] = useState({
    lastSync: null,
    activeJobs: 0,
    databaseSize: 0,
    errorRate: 0
  });

  // Theme management
  useEffect(() => {
    const isDark = localStorage.getItem('darkMode') === 'true';
    setDarkMode(isDark);
    document.documentElement.classList.toggle('dark', isDark);
  }, []);

  const toggleTheme = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', newMode.toString());
    document.documentElement.classList.toggle('dark', newMode);
  };

  // System status polling
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const response = await fetch('http://localhost:5000/system/status');
        if (!response.ok) throw new Error('Failed to fetch system status');
        const data = await response.json();
        setSystemStatus(data);
      } catch (err) {
        setError('System status check failed');
        console.error('Error fetching system status:', err);
      }
    };

    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900 text-white' : 'bg-gray-50'}`}>
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                Jewelry Scraper
              </h1>
              
              {/* System Status Indicators */}
              <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-300">
                <span className="flex items-center">
                  <RefreshCw
                    className={`h-4 w-4 mr-1 ${
                      systemStatus.activeJobs > 0 ? 'animate-spin text-green-500' : ''
                    }`}
                  />
                  {systemStatus.activeJobs} Active Jobs
                </span>
                <span>
                  Last Sync: {
                    systemStatus.lastSync 
                      ? new Date(systemStatus.lastSync).toLocaleTimeString()
                      : 'Never'
                  }
                </span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {darkMode ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>

              <button
                onClick={() => setSelectedView('settings')}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* View Navigation */}
        <div className="mb-6">
          <nav className="flex space-x-4">
            <button
              onClick={() => setSelectedView('dashboard')}
              className={`px-4 py-2 rounded-lg ${
                selectedView === 'dashboard'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setSelectedView('search')}
              className={`px-4 py-2 rounded-lg ${
                selectedView === 'search'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Search
            </button>
            <button
              onClick={() => setSelectedView('data')}
              className={`px-4 py-2 rounded-lg ${
                selectedView === 'data'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Data Table
            </button>
          </nav>
        </div>

        {/* View Content */}
        <div className="space-y-6">
          {selectedView === 'dashboard' && <DataDashboard />}
          {selectedView === 'search' && <EnhancedSearch />}
          {selectedView === 'data' && <DataTable />}
          {selectedView === 'settings' && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Settings</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Auto-refresh Interval (ms)
                  </label>
                  <input
                    type="number"
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(Number(e.target.value))}
                    className="px-3 py-2 border rounded-lg w-full dark:bg-gray-700 dark:border-gray-600"
                    min="5000"
                    step="1000"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 shadow-md mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center text-sm text-gray-600 dark:text-gray-300">
            <span>Database Size: {(systemStatus.databaseSize / 1024 / 1024).toFixed(2)} MB</span>
            <span>Error Rate: {(systemStatus.errorRate * 100).toFixed(2)}%</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;