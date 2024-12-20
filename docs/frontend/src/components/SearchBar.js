
import React, { useState } from 'react'; import axios from 'axios';

const SearchBar = ({ onSearch }) => { const [query, setQuery] = useState(''); const [platform, setPlatform] = useState('ebay'); const [maxItems, setMaxItems] = useState(50);

javascript
Copy code
const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query) return;

    try {
        const response = await axios.post('/scrape', {
            query,
            platform,
            max_items: maxItems
        });
        onSearch(response.data.job_id);
    } catch (error) {
        console.error('Error initiating scrape:', error);
    }
};

return (
    <form onSubmit={handleSubmit} className="flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-4 p-4 bg-white shadow rounded">
        <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for jewelry..."
            className="flex-1 px-4 py-2 border rounded"
            required
        />
        <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="px-4 py-2 border rounded"
        >
            <option value="ebay">eBay</option>
            <option value="amazon">Amazon</option>
        </select>
        <input
            type="number"
            value={maxItems}
            onChange={(e) => setMaxItems(e.target.value)}
            placeholder="Max Items"
            className="w-24 px-4 py-2 border rounded"
            min="1"
            max="1000"
        />
        <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Search
        </button>
    </form>
);
};

export default SearchBar; 
