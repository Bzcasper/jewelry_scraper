// File: /frontend/src/components/DataDashboard.js

import React, { useState, useEffect } from 'react';
import { LineChart, XAxis, YAxis, CartesianGrid, Line, Tooltip, ResponsiveContainer } from 'recharts';
import { PieChart, BarChart as BarChartIcon } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useApp } from '../context/AppContext';
import { useDataFetching } from '../hooks/useDataFetching';

const DataDashboard = () => {
  // State and hooks
  const [view, setView] = useState('table');
  const [selectedPlatform, setPlatform] = useState('all');
  const { systemStatus } = useApp();
  
  const { data: products, loading, error, setParams } = useDataFetching({
    platform: selectedPlatform !== 'all' ? selectedPlatform : undefined,
    sort: 'date_scraped',
    limit: 100
  });

  // Calculate stats from products
  const stats = React.useMemo(() => {
    if (!products?.length) return null;
    
    return {
      totalProducts: products.length,
      avgPrice: products.reduce((sum, p) => sum + p.price, 0) / products.length,
      platforms: products.reduce((acc, p) => {
        acc[p.platform] = (acc[p.platform] || 0) + 1;
        return acc;
      }, {}),
      categories: products.reduce((acc, p) => {
        acc[p.category] = (acc[p.category] || 0) + 1;
        return acc;
      }, {})
    };
  }, [products]);

  // Price trend data for chart
  const priceData = React.useMemo(() => {
    if (!products?.length) return [];
    
    // Group by date and calculate average price
    const grouped = products.reduce((acc, p) => {
      const date = new Date(p.date_scraped).toLocaleDateString();
      if (!acc[date]) {
        acc[date] = { prices: [], count: 0 };
      }
      acc[date].prices.push(p.price);
      acc[date].count++;
      return acc;
    }, {});

    return Object.entries(grouped).map(([date, data]) => ({
      date,
      avgPrice: data.prices.reduce((a, b) => a + b, 0) / data.count
    }));
  }, [products]);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <BarChartIcon className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );

  if (error) return (
    <Alert variant="destructive">
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{error}</AlertDescription>
    </Alert>
  );

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="flex justify-between items-center">
        <div className="flex gap-4">
          <select
            value={selectedPlatform}
            onChange={(e) => setPlatform(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All Platforms</option>
            <option value="ebay">eBay</option>
            <option value="amazon">Amazon</option>
          </select>

          <div className="flex gap-2">
            <button
              onClick={() => setView('table')}
              className={`px-4 py-2 rounded-lg ${
                view === 'table' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'
              }`}
            >
              Table View
            </button>
            <button
              onClick={() => setView('chart')}
              className={`px-4 py-2 rounded-lg ${
                view === 'chart' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'
              }`}
            >
              Price Trends
            </button>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Overview</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Total Products:</span>
                <span className="font-medium">{stats.totalProducts}</span>
              </div>
              <div className="flex justify-between">
                <span>Average Price:</span>
                <span className="font-medium">
                  ${stats.avgPrice.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Active Jobs:</span>
                <span className="font-medium">{systemStatus.activeJobs}</span>
              </div>
            </div>
          </div>

          {/* Platform Distribution */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Platforms</h3>
            <div className="space-y-2">
              {Object.entries(stats.platforms).map(([platform, count]) => (
                <div key={platform} className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-blue-600 rounded-full h-2"
                      style={{
                        width: `${(count / stats.totalProducts) * 100}%`
                      }}
                    />
                  </div>
                  <span className="text-sm w-20 text-right">
                    {platform}: {count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Category Distribution */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Categories</h3>
            <div className="space-y-2">
              {Object.entries(stats.categories).map(([category, count]) => (
                <div key={category} className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-green-600 rounded-full h-2"
                      style={{
                        width: `${(count / stats.totalProducts) * 100}%`
                      }}
                    />
                  </div>
                  <span className="text-sm w-20 text-right">
                    {category}: {count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Price Trends Chart */}
      {view === 'chart' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Price Trends</h3>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                <Line
                  type="monotone"
                  dataKey="avgPrice"
                  stroke="#2563eb"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataDashboard;