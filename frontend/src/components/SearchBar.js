import React, { useState } from 'react';
import axios from 'axios';

const SearchBar = () => {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('ebay');
  const [maxItems, setMaxItems] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleScrape = async () => {
    if (!query.trim()) {
      setError('Please enter a search query.');
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
      console.log('Scraped Data:', response.data.data);
      alert('Scraping completed successfully!');
    } catch (error) {
      console.error('Error scraping data:', error);
      setError('Scraping failed. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}
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
          onClick={handleScrape}
          disabled={loading}
          className={px-6 py-2 rounded-lg bg-blue-600 text-white flex items-center gap-2 }
        >
          {loading ? (
            <span className="animate-spin">⏳</span>
          ) : (
            <span>Scrape</span>
          )}
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

        <input
          type="number"
          value={maxItems}
          onChange={(e) => setMaxItems(parseInt(e.target.value))}
          placeholder="Max Items"
          min="1"
          className="px-4 py-2 border rounded-lg w-24"
        />
      </div>
    </div>
  );
};

export default SearchBar;
