import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, CartesianGrid, Line, Tooltip, ResponsiveContainer } from 'recharts';
import { PieChart, BarChart as BarChartIcon } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import axios from 'axios';

const DataDashboard = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [view, setView] = useState('table'); # table, chart, stats
  const [filters, setFilters] = useState({
    priceMin: '',
    priceMax: '',
    platform: 'all',
    category: 'all'
  });
  const [selectedItems, setSelectedItems] = useState([]);
  const [stats, setStats] = useState({
    totalProducts: 0,
    avgPrice: 0,
    platforms: {},
    categories: {}
  });

  # Price trend data for chart
  const [priceData, setPriceData] = useState([]);

  const calculateStats = (data) => {
    const stats = {
      totalProducts: data.length,
      avgPrice: 0,
      platforms: {},
      categories: {}
    };

    data.forEach(item => {
      # Calculate average price
      const price = parseFloat(item.price?.replace(/[^0-9.]/g, '') || 0);
      stats.avgPrice += price;

      # Count by platform
      stats.platforms[item.platform] = (stats.platforms[item.platform] || 0) + 1;

      # Count by category
      stats.categories[item.category] = (stats.categories[item.category] || 0) + 1;
    });

    stats.avgPrice = data.length ? stats.avgPrice / data.length : 0;
    return stats;
  };

  const handleExport = () => {
    const csvContent = "data:text/csv;charset=utf-8," + 
      "Title,Price,Platform,Category,URL\n" +
      products.map(p => 
        "","","","",""
      ).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "scraped_products.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDelete = async () => {
    if (!selectedItems.length) return;
    
    if (window.confirm(Delete  selected items?)) {
      # Implement delete logic here, e.g., send DELETE requests to backend
      # For now, we'll just clear the selection
      setSelectedItems([]);
      alert('Selected items deleted (implement backend logic).');
    }
  };

  const toggleSelect = (id) => {
    setSelectedItems(prev => 
      prev.includes(id)
        ? prev.filter(item => item !== id)
        : [...prev, id]
    );
  };

  const filteredProducts = products.filter(product => {
    const price = parseFloat(product.price?.replace(/[^0-9.]/g, '') || 0);
    return (
      (!filters.priceMin || price >= parseFloat(filters.priceMin)) &&
      (!filters.priceMax || price <= parseFloat(filters.priceMax)) &&
      (filters.platform === 'all' || product.platform === filters.platform) &&
      (filters.category === 'all' || product.category === filters.category)
    );
  });

  useEffect(() => {
    # Fetch products from backend
    const fetchProducts = async () => {
      try {
        const response = await axios.get('http://localhost:5000/products');
        setProducts(response.data);
        setStats(calculateStats(response.data));
        # Optionally, prepare priceData for charts
        # For simplicity, this example does not implement historical price trends
      } catch (err) {
        setError('Failed to fetch products.');
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      # Controls
      <div className="flex justify-between items-center">
        <div className="flex gap-4">
          <button
            onClick={() => setView('table')}
            className={px-4 py-2 rounded-lg }
          >
            Table View
          </button>
          <button
            onClick={() => setView('chart')}
            className={px-4 py-2 rounded-lg flex items-center gap-2 }
          >
            <BarChartIcon className="h-4 w-4" />
            Price Trends
          </button>
          <button
            onClick={() => setView('stats')}
            className={px-4 py-2 rounded-lg flex items-center gap-2 }
          >
            <PieChart className="h-4 w-4" />
            Statistics
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="px-4 py-2 rounded-lg bg-green-600 text-white flex items-center gap-2"
          >
            Export
          </button>
          {selectedItems.length > 0 && (
            <button
              onClick={handleDelete}
              className="px-4 py-2 rounded-lg bg-red-600 text-white flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete ({selectedItems.length})
            </button>
          )}
        </div>
      </div>

      # Filters
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Price Range
            </label>
            <div className="flex gap-2 mt-1">
              <input
                type="number"
                placeholder="Min"
                value={filters.priceMin}
                onChange={(e) => setFilters({...filters, priceMin: e.target.value})}
                className="px-3 py-2 border rounded-lg w-24"
              />
              <span className="self-center">-</span>
              <input
                type="number"
                placeholder="Max"
                value={filters.priceMax}
                onChange={(e) => setFilters({...filters, priceMax: e.target.value})}
                className="px-3 py-2 border rounded-lg w-24"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Platform
            </label>
            <select
              value={filters.platform}
              onChange={(e) => setFilters({...filters, platform: e.target.value})}
              className="mt-1 px-3 py-2 border rounded-lg"
            >
              <option value="all">All Platforms</option>
              <option value="ebay">eBay</option>
              <option value="amazon">Amazon</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Category
            </label>
            <select
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value})}
              className="mt-1 px-3 py-2 border rounded-lg"
            >
              <option value="all">All Categories</option>
              <option value="rings">Rings</option>
              <option value="necklaces">Necklaces</option>
              <option value="bracelets">Bracelets</option>
            </select>
          </div>
        </div>
      </div>

      # Content
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : error ? (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : (
        <div>
          {view === 'table' && (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="w-8 px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedItems.length === filteredProducts.length && filteredProducts.length > 0}
                        onChange={(e) => 
                          setSelectedItems(
                            e.target.checked 
                              ? filteredProducts.map(p => p.id)
                              : []
                          )
                        }
                        className="rounded"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                      Title
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                      Price
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                      Platform
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                      Category
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                      Date Scraped
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                      URL
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredProducts.map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedItems.includes(product.id)}
                          onChange={() => toggleSelect(product.id)}
                          className="rounded"
                        />
                      </td>
                      <td className="px-4 py-3">{product.title}</td>
                      <td className="px-4 py-3"></td>
                      <td className="px-4 py-3 capitalize">{product.platform}</td>
                      <td className="px-4 py-3 capitalize">{product.category}</td>
                      <td className="px-4 py-3">{new Date(product.date_scraped).toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <a
                          href={product.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          View
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {view === 'chart' && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium mb-4">Price Trends</h3>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={priceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="avgPrice" stroke="#2563eb" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {view === 'stats' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium mb-4">Overview</h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-gray-600">Total Products:</span>
                    <span className="ml-2 font-medium">{stats.totalProducts}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Average Price:</span>
                    <span className="ml-2 font-medium">
                      
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium mb-4">Platform Distribution</h3>
                <div className="space-y-2">
                  {Object.entries(stats.platforms).map(([platform, count]) => (
                    <div key={platform} className="flex items-center">
                      <span className="text-gray-600 capitalize">{platform}:</span>
                      <div className="ml-2 flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 rounded-full h-2"
                          style={{
                            width: ${(count / stats.totalProducts) * 100}%
                          }}
                        ></div>
                      </div>
                      <span className="ml-2 text-sm">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium mb-4">Category Distribution</h3>
                <div className="space-y-2">
                  {Object.entries(stats.categories).map(([category, count]) => (
                    <div key={category} className="flex items-center">
                      <span className="text-gray-600 capitalize">{category}:</span>
                      <div className="ml-2 flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 rounded-full h-2"
                          style={{
                            width: ${(count / stats.totalProducts) * 100}%
                          }}
                        ></div>
                      </div>
                      <span className="ml-2 text-sm">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataDashboard;
