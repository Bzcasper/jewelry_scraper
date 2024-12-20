import { useState, useEffect, useCallback } from 'react';
import { productsApi } from '../src/services/api';

export const useDataFetching = (initialParams = {}) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [params, setParams] = useState(initialParams);

  const fetchData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const response = await productsApi.fetch(params);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    setParams,
    refetch: fetchData
  };
};

export const useJobPolling = (jobId, interval = 1000) => {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    const pollJob = async () => {
      try {
        const response = await scrapingApi.getStatus(jobId);
        const { status, progress, results, error } = response.data;

        setStatus(status);
        setProgress(progress);
        
        if (status === 'completed') {
          setResult(results);
        } else if (status === 'failed') {
          setError(error);
        }
        
        return status === 'completed' || status === 'failed';
      } catch (err) {
        setError(err.message);
        return true;
      }
    };

    const poll = setInterval(async () => {
      const shouldStop = await pollJob();
      if (shouldStop) clearInterval(poll);
    }, interval);

    return () => clearInterval(poll);
  }, [jobId, interval]);

  return { status, progress, result, error };
};