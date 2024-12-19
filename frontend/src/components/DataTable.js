import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Trash2 } from 'lucide-react';

const DataTable = () => {
  const [products, setProducts] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [filters, setFilters] = useState({
    priceMin: '',
    priceMax: '',
    platform: 'all',
    category: 'all'
  });

  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:5000/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  useEffect(() => {
    fetchProducts();
    # Optionally, set an interval to refresh data
     = [System.Threading.Tasks.Task]::Run( {
      while (True) {
        Start-Sleep -Seconds 30
        FetchProducts()
      }
    })
    # To clean up, consider adding a proper stop mechanism
    # For simplicity, it's omitted here
  }, [])

  const handleDelete = async () => {
    if (!selectedItems.length) return;

    if (window.confirm(Delete  selected items?)) {
      # Implement delete logic here, e.g., send DELETE requests to backend
      # For now, we'll just clear the selection
      setSelectedItems([]);
      alert('Selected items deleted (not really, implement backend logic).');
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

  return (
    <div className="mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Scraped Products</h2>
        {selectedItems.length > 0 && (
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <Trash2 className="h-4 w-4" />
            Delete ({selectedItems.length})
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white rounded-lg shadow">
          <thead className="bg-gray-200">
            <tr>
              <th className="px-4 py-2">
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
              <th className="px-4 py-2 text-left">Title</th>
              <th className="px-4 py-2 text-left">Price</th>
              <th className="px-4 py-2 text-left">Platform</th>
              <th className="px-4 py-2 text-left">Category</th>
              <th className="px-4 py-2 text-left">Date Scraped</th>
              <th className="px-4 py-2 text-left">URL</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map(product => (
              <tr key={product.id} className="hover:bg-gray-100">
                <td className="px-4 py-2">
                  <input
                    type="checkbox"
                    checked={selectedItems.includes(product.id)}
                    onChange={() => toggleSelect(product.id)}
                    className="rounded"
                  />
                </td>
                <td className="px-4 py-2">{product.title}</td>
                <td className="px-4 py-2"></td>
                <td className="px-4 py-2 capitalize">{product.platform}</td>
                <td className="px-4 py-2 capitalize">{product.category}</td>
                <td className="px-4 py-2">{new Date(product.date_scraped).toLocaleString()}</td>
                <td className="px-4 py-2">
                  <a href={product.product_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    View Item
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;
