import React, { useState } from 'react';
import { AlertCircle, Search, RefreshCw, Database, Settings } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import axios from 'axios';

const EnhancedSearch = () => {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('ebay');
  const [maxItems, setMaxItems] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [priceRange, setPriceRange] = useState({ min: 0, max: 1000 });
  const [sortBy, setSortBy] = useState('relevance');
  const [lastScraped, setLastScraped] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:5000/scrape', {
        query,
        platform,
        max_items: maxItems
      });
      setLastScraped(new Date().toLocaleString());
      alert('Scraping completed successfully!');
    } catch (err) {
      setError('Failed to scrape data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for jewelry..."
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className={px-6 py-2 rounded-lg bg-blue-600 text-white flex items-center gap-2 }
          >
            {loading ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <Search className="h-5 w-5" />
            )}
            {loading ? 'Scraping...' : 'Search'}
          </button>
        </div>

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

        {showAdvanced && (
          <div className="p-4 bg-gray-50 rounded-lg space-y-4">
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
                className="mt-1 px-4 py-2 border rounded-lg w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Price Range
              </label>
              <div className="flex gap-4">
                <input
                  type="number"
                  value={priceRange.min}
                  onChange={(e) =>
                    setPriceRange({ ...priceRange, min: parseInt(e.target.value) })
                  }
                  placeholder="Min"
                  className="mt-1 px-4 py-2 border rounded-lg w-full"
                />
                <input
                  type="number"
                  value={priceRange.max}
                  onChange={(e) =>
                    setPriceRange({ ...priceRange, max: parseInt(e.target.value) })
                  }
                  placeholder="Max"
                  className="mt-1 px-4 py-2 border rounded-lg w-full"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="mt-1 px-4 py-2 border rounded-lg w-full"
              >
                <option value="relevance">Relevance</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="newest">Newest First</option>
              </select>
            </div>
          </div>
        )}

        {lastScraped && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Database className="h-4 w-4" />
            Last scraped: {lastScraped}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedSearch;
