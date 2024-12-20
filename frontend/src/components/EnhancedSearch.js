import React, { useState, useCallback, useEffect } from 'react';
import { 
  AlertCircle, Search, RefreshCw, Database, Settings, 
  Filter, Clock, Check, X 
} from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import debounce from 'lodash/debounce';
import axios from 'axios';

const EnhancedSearch = () => {
  // Basic search state
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('ebay');
  const [maxItems, setMaxItems] = useState(50);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeJob, setActiveJob] = useState(null);
  const [progress, setProgress] = useState(0);
  const [searchHistory, setSearchHistory] = useState([]);
  
  // Advanced filters
  const [filters, setFilters] = useState({
    priceRange: { min: '', max: '' },
    condition: 'any',
    sortBy: 'relevance',
    category: 'all',
    minRating: 0,
    location: '',
    sellerScore: '',
    shippingOptions: [],
    excludeKeywords: []
  });

  // Stats and metadata
  const [searchStats, setSearchStats] = useState({
    lastScraped: null,
    totalResults: 0,
    avgPrice: 0,
    searchTime: 0
  });

  // Job polling
  useEffect(() => {
    let pollInterval;
    
    const pollJobStatus = async () => {
      if (!activeJob) return;
      
      try {
        const response = await axios.get(`http://localhost:5000/scrape/status/${activeJob.id}`);
        const { status, progress: jobProgress, results, error: jobError } = response.data;

        setProgress(jobProgress);

        if (status === 'completed') {
          setLoading(false);
          setSearchStats(prev => ({
            ...prev,
            lastScraped: new Date(),
            totalResults: results.length,
            avgPrice: calculateAveragePrice(results),
            searchTime: (new Date() - activeJob.startTime) / 1000
          }));
          setActiveJob(null);
          addToSearchHistory(query, results.length);
        } else if (status === 'failed') {
          setError(jobError || 'Search failed');
          setLoading(false);
          setActiveJob(null);
        }
      } catch (err) {
        setError('Failed to check search status');
        setLoading(false);
        setActiveJob(null);
      }
    };

    if (activeJob) {
      pollInterval = setInterval(pollJobStatus, 1000);
    }

    return () => clearInterval(pollInterval);
  }, [activeJob]);

  // Handle search
  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    setProgress(0);

    try {
      const response = await axios.post('http://localhost:5000/scrape', {
        query: query.trim(),
        platform,
        max_items: maxItems,
        filters: {
          price_min: filters.priceRange.min || null,
          price_max: filters.priceRange.max || null,
          condition: filters.condition,
          sort_by: filters.sortBy,
          category: filters.category,
          min_rating: filters.minRating,
          location: filters.location,
          seller_score: filters.sellerScore,
          shipping_options: filters.shippingOptions,
          exclude_keywords: filters.excludeKeywords
        }
      });

      setActiveJob({
        id: response.data.job_id,
        startTime: new Date()
      });
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start search');
      setLoading(false);
    }
  };

  // Utility functions
  const calculateAveragePrice = (results) => {
    if (!results?.length) return 0;
    const prices = results.map(r => parseFloat(r.price)).filter(p => !isNaN(p));
    return prices.reduce((a, b) => a + b, 0) / prices.length;
  };

  const addToSearchHistory = (searchQuery, resultCount) => {
    setSearchHistory(prev => [{
      query: searchQuery,
      results: resultCount,
      timestamp: new Date(),
      platform
    }, ...prev].slice(0, 10));
  };

  // Debounced query handler
  const debouncedQueryChange = useCallback(
    debounce((value) => setQuery(value), 300),
    []
  );

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Alerts */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Search Bar */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <input
            type="text"
            defaultValue={query}
            onChange={(e) => debouncedQueryChange(e.target.value)}
            placeholder="Search for jewelry..."
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        
        <button
          onClick={handleSearch}
          disabled={loading}
          className={`px-6 py-2 rounded-lg bg-blue-600 text-white flex items-center gap-2 ${
            loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
          }`}
        >
          {loading ? (
            <>
              <RefreshCw className="h-5 w-5 animate-spin" />
              <span>Searching... {progress}%</span>
            </>
          ) : (
            <>
              <Search className="h-5 w-5" />
              <span>Search</span>
            </>
          )}
        </button>
      </div>

      {/* Platform and Advanced Controls */}
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
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            showAdvanced 
              ? 'bg-blue-50 text-blue-600' 
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Settings className="h-4 w-4" />
          <span>Advanced</span>
          {showAdvanced && <Check className="h-4 w-4" />}
        </button>

        {searchStats.lastScraped && (
          <div className="flex items-center gap-2 text-sm text-gray-600 ml-auto">
            <Clock className="h-4 w-4" />
            <span>Last search: {searchStats.searchTime.toFixed(1)}s</span>
          </div>
        )}
      </div>

      {/* Advanced Options Panel */}
      {showAdvanced && (
        <div className="p-6 bg-gray-50 rounded-lg space-y-6 border">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Price Range
              </label>
              <div className="flex gap-4">
                <input
                  type="number"
                  value={filters.priceRange.min}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    priceRange: { ...prev.priceRange, min: e.target.value }
                  }))}
                  placeholder="Min"
                  className="px-4 py-2 border rounded-lg w-full"
                />
                <input
                  type="number"
                  value={filters.priceRange.max}
                  onChange={(e) => setFilters(prev => ({
                    ...prev,
                    priceRange: { ...prev.priceRange, max: e.target.value }
                  }))}
                  placeholder="Max"
                  className="px-4 py-2 border rounded-lg w-full"
                />
              </div>
            </div>

            {/* Item Condition */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Item Condition
              </label>
              <select
                value={filters.condition}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  condition: e.target.value
                }))}
                className="px-4 py-2 border rounded-lg w-full"
              >
                <option value="any">Any Condition</option>
                <option value="new">New</option>
                <option value="used">Used</option>
                <option value="refurbished">Refurbished</option>
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  category: e.target.value
                }))}
                className="px-4 py-2 border rounded-lg w-full"
              >
                <option value="all">All Jewelry</option>
                <option value="necklaces">Necklaces</option>
                <option value="rings">Rings</option>
                <option value="earrings">Earrings</option>
                <option value="bracelets">Bracelets</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort Results By
              </label>
              <select
                value={filters.sortBy}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  sortBy: e.target.value
                }))}
                className="px-4 py-2 border rounded-lg w-full"
              >
                <option value="relevance">Most Relevant</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="date_desc">Newest First</option>
                <option value="rating_desc">Highest Rated</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Search Stats */}
      {searchStats.lastScraped && (
        <div className="flex items-center justify-between text-sm text-gray-600 border-t pt-4">
          <div className="flex items-center gap-4">
            <span>
              <Database className="h-4 w-4 inline mr-2" />
              {searchStats.totalResults} results
            </span>
            <span>
              Average price: ${searchStats.avgPrice.toFixed(2)}
            </span>
          </div>
          <span>
            Last scraped: {new Date(searchStats.lastScraped).toLocaleString()}
          </span>
        </div>
      )}

      {/* Progress Bar */}
      {loading && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default EnhancedSearch;