// File: /frontend/src/context/AppContext.js

import React, { createContext, useContext, useState, useCallback } from 'react';
import { scraping, products, system } from '../services/api';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // State management
  const [scrapingJobs, setScrapingJobs] = useState({});
  const [systemStatus, setSystemStatus] = useState({
    activeJobs: 0,
    lastSync: null,
    databaseSize: 0,
    errorRate: 0
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Start a new scraping job
  const startScraping = async (params) => {
    setLoading(true);
    try {
      const { job_id } = await scraping.startScraping(params);
      setScrapingJobs(prev => ({
        ...prev,
        [job_id]: { status: 'running', progress: 0, ...params }
      }));
      return job_id;
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start scraping');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Fetch products with filters
  const fetchProducts = async (params) => {
    setLoading(true);
    try {
      const data = await products.fetchProducts(params);
      return data;
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch products');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Delete products
  const deleteProducts = async (ids) => {
    setLoading(true);
    try {
      await products.deleteProducts(ids);
      return true;
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete products');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Update system status
  const updateSystemStatus = useCallback(async () => {
    try {
      const status = await system.getStatus();
      setSystemStatus(status);
    } catch (err) {
      console.error('Failed to update system status:', err);
    }
  }, []);

  // Keep system status updated
  React.useEffect(() => {
    updateSystemStatus();
    const interval = setInterval(updateSystemStatus, 30000);
    return () => clearInterval(interval);
  }, [updateSystemStatus]);

  const value = {
    scrapingJobs,
    systemStatus,
    error,
    loading,
    startScraping,
    fetchProducts,
    deleteProducts,
    clearError: () => setError(null)
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};