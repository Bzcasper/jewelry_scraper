import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { 
  Trash2, Filter, Download, RefreshCw, ChevronUp, ChevronDown, 
  ArrowUpDown, Edit, MoreHorizontal, AlertCircle 
} from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const DataTable = () => {
  // Data state
  const [products, setProducts] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [totalItems, setTotalItems] = useState(0);
  
  // Sorting state
  const [sortField, setSortField] = useState('date_scraped');
  const [sortDirection, setSortDirection] = useState('desc');
  
  // Filter state
  const [filters, setFilters] = useState({
    priceMin: '',
    priceMax: '',
    platform: 'all',
    category: 'all',
    dateFrom: '',
    dateTo: '',
    searchTerm: ''
  });
  
  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [isEditing, setIsEditing] = useState(null);
  const [editData, setEditData] = useState({});

  // Fetch data with filters, sorting, and pagination
  const fetchProducts = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const response = await axios.get('http://localhost:5000/products', {
        params: {
          page,
          per_page: perPage,
          sort_by: sortField,
          sort_direction: sortDirection,
          ...filters
        }
      });
      setProducts(response.data.products);
      setTotalItems(response.data.total);
      setError(null);
    } catch (err) {
      setError('Failed to fetch products: ' + err.message);
      console.error('Error fetching products:', err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  // Setup auto-refresh
  useEffect(() => {
    fetchProducts();
    const interval = setInterval(() => fetchProducts(true), refreshInterval);
    return () => clearInterval(interval);
  }, [page, perPage, sortField, sortDirection, filters, refreshInterval]);

  // Handle sorting
  const handleSort = (field) => {
    if (field === sortField) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Handle bulk actions
  const handleDelete = async () => {
    if (!selectedItems.length) return;
    
    if (window.confirm(`Delete ${selectedItems.length} selected items?`)) {
      try {
        await axios.delete('http://localhost:5000/products', {
          data: { ids: selectedItems }
        });
        setSelectedItems([]);
        fetchProducts();
      } catch (err) {
        setError('Failed to delete items: ' + err.message);
      }
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get('http://localhost:5000/products/export', {
        params: { ids: selectedItems },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `products_export_${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to export data: ' + err.message);
    }
  };

  // Handle item editing
  const handleEdit = (id) => {
    setIsEditing(id);
    setEditData(products.find(p => p.id === id));
  };

  const handleSaveEdit = async () => {
    try {
      await axios.put(`http://localhost:5000/products/${isEditing}`, editData);
      setIsEditing(null);
      fetchProducts();
    } catch (err) {
      setError('Failed to save changes: ' + err.message);
    }
  };

  // Computed properties
  const totalPages = Math.ceil(totalItems / perPage);
  const pageRange = useMemo(() => {
    const range = [];
    const maxButtons = 5;
    const start = Math.max(1, Math.min(page - Math.floor(maxButtons / 2), totalPages - maxButtons + 1));
    const end = Math.min(totalPages, start + maxButtons - 1);
    
    for (let i = start; i <= end; i++) {
      range.push(i);
    }
    return range;
  }, [page, totalPages]);

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Table Controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
              showFilters ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>

          <select
            value={perPage}
            onChange={(e) => setPerPage(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="10">10 per page</option>
            <option value="25">25 per page</option>
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
          </select>
        </div>

        <div className="flex items-center space-x-4">
          {selectedItems.length > 0 && (
            <>
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Export ({selectedItems.length})
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete ({selectedItems.length})
              </button>
            </>
          )}
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="p-4 bg-gray-50 rounded-lg border grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price Range
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Min"
                value={filters.priceMin}
                onChange={(e) => setFilters(prev => ({ ...prev, priceMin: e.target.value }))}
                className="px-3 py-2 border rounded-lg w-full"
              />
              <input
                type="number"
                placeholder="Max"
                value={filters.priceMax}
                onChange={(e) => setFilters(prev => ({ ...prev, priceMax: e.target.value }))}
                className="px-3 py-2 border rounded-lg w-full"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Platform
            </label>
            <select
              value={filters.platform}
              onChange={(e) => setFilters(prev => ({ ...prev, platform: e.target.value }))}
              className="px-3 py-2 border rounded-lg w-full"
            >
              <option value="all">All Platforms</option>
              <option value="ebay">eBay</option>
              <option value="amazon">Amazon</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filters.category}
              onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
              className="px-3 py-2 border rounded-lg w-full"
            >
              <option value="all">All Categories</option>
              <option value="rings">Rings</option>
              <option value="necklaces">Necklaces</option>
              <option value="bracelets">Bracelets</option>
              <option value="earrings">Earrings</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search products..."
              value={filters.searchTerm}
              onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
              className="px-3 py-2 border rounded-lg w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date Range
            </label>
            <div className="flex gap-2">
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                className="px-3 py-2 border rounded-lg w-full"
              />
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                className="px-3 py-2 border rounded-lg w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="overflow-x-auto rounded-lg border">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-8 px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedItems.length === products.length && products.length > 0}
                  onChange={(e) => 
                    setSelectedItems(
                      e.target.checked 
                        ? products.map(p => p.id)
                        : []
                    )
                  }
                  className="rounded"
                />
              </th>
              {['Title', 'Price', 'Platform', 'Category', 'Date Scraped'].map(header => (
                <th
                  key={header}
                  className="px-4 py-3 text-left text-sm font-medium text-gray-700 cursor-pointer"
                  onClick={() => handleSort(header.toLowerCase())}
                >
                  <div className="flex items-center gap-2">
                    {header}
                    <ArrowUpDown className="h-4 w-4" />
                  </div>
                </th>
              ))}
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {loading ? (
              <tr>
                <td colSpan="7" className="text-center py-4">
                  <RefreshCw className="h-6 w-6 animate-spin mx-auto text-gray-400" />
                </td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center py-4 text-gray-500">
                  No products found
                </td>
              </tr>
            ) : (
              products.map(product => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(product.id)}
                      onChange={() => toggleSelect(product.id)}
                      className="rounded"
                    />
                  </td>
                  <td className="px-4 py-3">
                    {isEditing === product.id ? (
                      <input
                        type="text"
                        value={editData.title}
                        onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                        className="px-2 py-1 border rounded w-full"
                      />
                    ) : (
                      product.title
                    )}
                  </td>
                  <td className="px-4 py-3">{product.price}</td>
                  <td className="px-4 py-3 capitalize">{product.platform}</td>
                  <td className="px-4 py-3 capitalize">{product.category}</td>
                  <td className="px-4 py-3">
                    {new Date(product.date_scraped).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      {isEditing === product.id ? (
                        <>
                          <button
                            onClick={handleSaveEdit}
                            className="text-green-600 hover:text-green-700"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setIsEditing(null)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => handleEdit(product.id)}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <a
                            href={product.product_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700"
                          >
                            View
                          </a>
                        </>
                      )}
                    </div>
                    </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700">
          Showing {Math.min((page - 1) * perPage + 1, totalItems)} to{' '}
          {Math.min(page * perPage, totalItems)} of {totalItems} results
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(1)}
            disabled={page === 1}
            className={`px-3 py-2 rounded-lg ${
              page === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            First
          </button>

          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className={`px-3 py-2 rounded-lg ${
              page === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <ChevronUp className="h-4 w-4 rotate-90" />
          </button>

          {pageRange.map(pageNum => (
            <button
              key={pageNum}
              onClick={() => setPage(pageNum)}
              className={`px-3 py-2 rounded-lg ${
                page === pageNum
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {pageNum}
            </button>
          ))}

          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className={`px-3 py-2 rounded-lg ${
              page === totalPages
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <ChevronDown className="h-4 w-4 rotate-90" />
          </button>

          <button
            onClick={() => setPage(totalPages)}
            disabled={page === totalPages}
            className={`px-3 py-2 rounded-lg ${
              page === totalPages
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Last
          </button>

          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="ml-4 px-3 py-2 border rounded-lg"
          >
            <option value={0}>Manual refresh</option>
            <option value={10000}>10 seconds</option>
            <option value={30000}>30 seconds</option>
            <option value={60000}>1 minute</option>
            <option value={300000}>5 minutes</option>
          </select>
        </div>
      </div>

      {/* Bulk Action Modal */}
      {selectedItems.length > 0 && (
        <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4">
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {selectedItems.length} items selected
            </span>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
            <button
              onClick={() => setSelectedItems([])}
              className="text-gray-600 hover:text-gray-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;