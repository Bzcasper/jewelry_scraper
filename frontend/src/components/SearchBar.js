import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Search, AlertCircle, RefreshCw, Settings, Check } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import debounce from 'lodash/debounce';

const SearchBar = () => {
  // Form state
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('ebay');
  const [maxItems, setMaxItems] = useState(50);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Status state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [lastResults, setLastResults] = useState(null);

  // Advanced options state
  const [advancedOptions, setAdvancedOptions] = useState({
    priceMin: '',
    priceMax: '',
    condition: 'any',
    sortBy: 'relevance',
    category: 'all',
    sellerRating: 0,
    location: '',
  });

  // Handle job status polling
  const pollJobStatus = useCallback(async (currentJobId) => {
    try {
      const response = await axios.get(`http://localhost:5000/scrape/status/${currentJobId}`);
      const { status, progress, results, error: jobError } = response.data;

      setProgress(progress);

      if (status === 'completed') {
        setLoading(false);
        setLastResults(results);
        return true;
      } else if (status === 'failed') {
        setError(jobError || 'Scraping failed');
        setLoading(false);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Error polling job status:', error);
      setError('Failed to check job status');
      setLoading(false);
      return true;
    }
  }, []);

  // Start polling when job is initiated
  const startPolling = useCallback(async (newJobId) => {
    while (!await pollJobStatus(newJobId)) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }, [pollJobStatus]);

  const handleScrape = async () => {
    if (!query.trim()) {
      setError('Please enter a search query.');
      return;
    }

    setLoading(true);
    setError('');
    setProgress(0);

    try {
      const response = await axios.post('http://localhost:5000/scrape', {
        query,
        platform,
        max_items: maxItems,
        options: {
          ...advancedOptions,
          priceMin: advancedOptions.priceMin ? parseFloat(advancedOptions.priceMin) : null,
          priceMax: advancedOptions.priceMax ? parseFloat(advancedOptions.priceMax) : null,
        }
      });

      setJobId(response.data.job_id);
      startPolling(response.data.job_id);
    } catch (error) {
      console.error('Error initiating scrape:', error);
      setError(error.response?.data?.error || 'Failed to start scraping');
      setLoading(false);
    }
  };

  // Debounced query change handler
  const debouncedQueryChange = debounce((value) => {
    setQuery(value);
  }, 300);

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Success Alert */}
      {lastResults && !error && !loading && (
        <Alert variant="success">
          <Check className="h-4 w-4" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>
            Found {lastResults.length} items matching your search
          </AlertDescription>
        </Alert>
      )}

      {/* Main Search Controls */}
      <div className="flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            defaultValue={query}
            onChange={(e) => debouncedQueryChange(e.target.value)}
            placeholder="Search for jewelry..."
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={handleScrape}
          disabled={loading}
          className={`px-6 py-2 rounded-lg bg-blue-600 text-white flex items-center gap-2 ${
            loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
          }`}
        >
          {loading ? (
            <>
              <RefreshCw className="h-5 w-5 animate-spin" />
              Scraping... {progress}%
            </>
          ) : (
            <>
              <Search className="h-5 w-5" />
              Search
            </>
          )}
        </button>
      </div>

      {/* Platform and Basic Controls */}
      <div className="flex items-center gap-4">
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="ebay">eBay</option>
          <option value="amazon">Amazon</option>
        </select>

        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
        >
          <Settings className="h-4 w-4" />
          Advanced Options
        </button>
      </div>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="p-4 bg-gray-50 rounded-lg space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Price Range
              </label>
              <div className="flex gap-4 mt-1">
                <input
                  type="number"
                  value={advancedOptions.priceMin}
                  onChange={(e) => setAdvancedOptions({
                    ...advancedOptions,
                    priceMin: e.target.value
                  })}
                  placeholder="Min"
                  className="px-3 py-2 border rounded-lg w-full"
                />
                <input
                  type="number"
                  value={advancedOptions.priceMax}
                  onChange={(e) => setAdvancedOptions({
                    ...advancedOptions,
                    priceMax: e.target.value
                  })}
                  placeholder="Max"
                  className="px-3 py-2 border rounded-lg w-full"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Item Condition
              </label>
              <select
                value={advancedOptions.condition}
                onChange={(e) => setAdvancedOptions({
                  ...advancedOptions,
                  condition: e.target.value
                })}
                className="mt-1 px-3 py-2 border rounded-lg w-full"
              >
                <option value="any">Any</option>
                <option value="new">New</option>
                <option value="used">Used</option>
                <option value="refurbished">Refurbished</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Sort By
              </label>
              <select
                value={advancedOptions.sortBy}
                onChange={(e) => setAdvancedOptions({
                  ...advancedOptions,
                  sortBy: e.target.value
                })}
                className="mt-1 px-3 py-2 border rounded-lg w-full"
              >
                <option value="relevance">Relevance</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="newest">Newest First</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Maximum Items
              </label>
              <input
                type="number"
                value={maxItems}
                onChange={(e) => setMaxItems(parseInt(e.target.value))}
                min="1"
                max="200"
                className="mt-1 px-3 py-2 border rounded-lg w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Progress Bar (when loading) */}
      {loading && (
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      )}
    </div>
  );
};

export default SearchBar;