import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
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
      startJobPolling(job_id);
      return job_id;
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start scraping');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Poll job status
  const startJobPolling = useCallback((jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await scraping.checkStatus(jobId);
        setScrapingJobs(prev => ({
          ...prev,
          [jobId]: { ...prev[jobId], ...status }
        }));

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval);
          updateSystemStatus();
        }
      } catch (err) {
        console.error(`Error polling job ${jobId}:`, err);
        clearInterval(pollInterval);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, []);

  // Update system status
  const updateSystemStatus = useCallback(async () => {
    try {
      const status = await system.getStatus();
      setSystemStatus(status);
    } catch (err) {
      console.error('Failed to update system status:', err);
    }
  }, []);

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
      updateSystemStatus();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete products');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Export products
  const exportProducts = async (filters) => {
    try {
      const blob = await products.exportProducts(filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `products_export_${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to export products');
      throw err;
    }
  };

  // Keep system status updated
  useEffect(() => {
    updateSystemStatus();
    const interval = setInterval(updateSystemStatus, 30000);
    return () => clearInterval(interval);
  }, [updateSystemStatus]);

  const value = {
    // State
    scrapingJobs,
    systemStatus,
    error,
    loading,
    // Actions
    startScraping,
    fetchProducts,
    deleteProducts,
    exportProducts,
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