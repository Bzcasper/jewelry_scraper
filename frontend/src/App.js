import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from './context/AppContext';
import { 
  Search, Settings, Sun, Moon, Database, AlertCircle, 
  BarChart2, Layout, RefreshCw, ChevronLeft, Users, 
  HardDrive, Shield
} from 'lucide-react';
import DataDashboard from './components/DataDashboard';
import EnhancedSearch from './components/EnhancedSearch';
import DataTable from './components/DataTable';
import SystemStats from './components/SystemStats';
import Analytics from './components/Analytics';
import SettingsPanel from './components/SettingsPanel';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const REFRESH_INTERVALS = {
  FAST: 5000,
  NORMAL: 30000,
  SLOW: 60000
};

const App = () => {
  // State Management
  const { systemStatus, error, clearError } = useApp();
  const [darkMode, setDarkMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard');
  const [refreshInterval, setRefreshInterval] = useState(REFRESH_INTERVALS.NORMAL);
  const [isMobile, setIsMobile] = useState(false);

  // Navigation Configuration
  const navigation = [
    { 
      name: 'Dashboard', 
      icon: Layout, 
      view: 'dashboard',
      badge: systemStatus?.activeJobs || 0 
    },
    { 
      name: 'Search', 
      icon: Search, 
      view: 'search' 
    },
    { 
      name: 'Data', 
      icon: Database, 
      view: 'data',
      badge: systemStatus?.totalProducts || 0
    },
    { 
      name: 'Analytics', 
      icon: BarChart2, 
      view: 'analytics' 
    },
    { 
      name: 'Users', 
      icon: Users, 
      view: 'users',
      requiresAdmin: true
    },
    { 
      name: 'Storage', 
      icon: HardDrive, 
      view: 'storage' 
    },
    { 
      name: 'Security', 
      icon: Shield, 
      view: 'security',
      requiresAdmin: true
    }
  ];

  // Handle Dark Mode
  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(savedMode ? savedMode === 'true' : prefersDark);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  // Handle Mobile Detection
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) setSidebarOpen(false);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // System Status Polling
  const fetchSystemStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5000/system/status');
      if (!response.ok) throw new Error('Failed to fetch system status');
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error fetching system status:', err);
      return null;
    }
  }, []);

  useEffect(() => {
    const pollStatus = async () => {
      const status = await fetchSystemStatus();
      if (status) {
        // Update system status through context
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, fetchSystemStatus]);

  // View Components Mapping
  const viewComponents = {
    dashboard: <DataDashboard />,
    search: <EnhancedSearch />,
    data: <DataTable />,
    analytics: <Analytics />,
    settings: <SettingsPanel 
      refreshInterval={refreshInterval}
      setRefreshInterval={setRefreshInterval}
    />,
    users: <div>Users Management</div>,
    storage: <div>Storage Management</div>,
    security: <div>Security Settings</div>
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Sidebar */}
      <div 
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 transform 
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          transition-transform duration-200 ease-in-out border-r dark:border-gray-700
          ${isMobile ? 'shadow-lg' : ''}`}
      >
        {/* Sidebar Content */}
        <div className="flex flex-col h-full">
          {/* Logo Section */}
          <div className="flex items-center justify-between px-4 h-16 border-b dark:border-gray-700">
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">
              Jewelry Scraper
            </span>
            {isMobile && (
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              !item.requiresAdmin && (
                <button
                  key={item.name}
                  onClick={() => {
                    setCurrentView(item.view);
                    if (isMobile) setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center px-4 py-2 rounded-lg transition-colors
                    ${currentView === item.view
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                      : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  <span>{item.name}</span>
                  {item.badge > 0 && (
                    <span className="ml-auto px-2 py-0.5 text-xs font-medium rounded-full 
                      bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100"
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            ))}
          </nav>

          {/* Sidebar Footer */}
          <div className="p-4 border-t dark:border-gray-700">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {darkMode ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
              <button
                onClick={() => setCurrentView('settings')}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-200 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
        {/* Header */}
        <header className="sticky top-0 z-40 bg-white dark:bg-gray-800 shadow-sm">
          <div className="flex items-center justify-between px-4 py-4">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            <SystemStats />
          </div>
        </header>

        {/* Main Content Area */}
        <main className="p-4">
          {/* Error Alert */}
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                {error}
                <button
                  onClick={clearError}
                  className="ml-2 text-sm underline"
                >
                  Dismiss
                </button>
              </AlertDescription>
            </Alert>
          )}

          {/* Active View */}
          <div className="max-w-7xl mx-auto">
            {viewComponents[currentView]}
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-white dark:bg-gray-800 shadow-md mt-8">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <SystemStats detailed />
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;