
import React, { useEffect, useState } from 'react'; import axios from 'axios';

const DataTable = () => { const [products, setProducts] = useState([]); const [filters, setFilters] = useState({ platform: '', category: '', priceMin: '', priceMax: '', condition: '' });

javascript
Copy code
useEffect(() => {
    fetchProducts();
}, [filters]);

const fetchProducts = async () => {
    try {
        const params = {};
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params[key] = filters[key];
            }
        });
        const response = await axios.get('/products', { params });
        setProducts(response.data);
    } catch (error) {
        console.error('Error fetching products:', error);
    }
};

const handleFilterChange = (e) => {
    setFilters({
        ...filters,
        [e.target.name]: e.target.value
    });
};

return (
    <div className="p-4">
        <h2 className="text-2xl font-bold mb-4">Scraped Products</h2>
        <div className="flex space-x-4 mb-4">
            <select name="platform" onChange={handleFilterChange} className="px-4 py-2 border rounded">
                <option value="">All Platforms</option>
                <option value="ebay">eBay</option>
                <option value="amazon">Amazon</option>
            </select>
            <select name="category" onChange={handleFilterChange} className="px-4 py-2 border rounded">
                <option value="">All Categories</option>
                <option value="Rings">Rings</option>
                <option value="Necklaces">Necklaces</option>
                <option value="Bracelets">Bracelets</option>
                <option value="Earrings">Earrings</option>
            </select>
            <input
                type="number"
                name="priceMin"
                placeholder="Min Price"
                onChange={handleFilterChange}
                className="px-4 py-2 border rounded w-24"
            />
            <input
                type="number"
                name="priceMax"
                placeholder="Max Price"
                onChange={handleFilterChange}
                className="px-4 py-2 border rounded w-24"
            />
            <select name="condition" onChange={handleFilterChange} className="px-4 py-2 border rounded">
                <option value="">All Conditions</option>
                <option value="New">New</option>
                <option value="Used">Used</option>
            </select>
        </div>
        <table className="min-w-full bg-white shadow rounded">
            <thead>
                <tr>
                    <th className="py-2 px-4 border-b">Title</th>
                    <th className="py-2 px-4 border-b">Price</th>
                    <th className="py-2 px-4 border-b">Platform</th>
                    <th className="py-2 px-4 border-b">Category</th>
                    <th className="py-2 px-4 border-b">Condition</th>
                    <th className="py-2 px-4 border-b">Date Scraped</th>
                </tr>
            </thead>
            <tbody>
                {products.map(product => (
                    <tr key={product.id}>
                        <td className="py-2 px-4 border-b">{product.title}</td>
                        <td className="py-2 px-4 border-b">${product.price}</td>
                        <td className="py-2 px-4 border-b capitalize">{product.platform}</td>
                        <td className="py-2 px-4 border-b">{product.category}</td>
                        <td className="py-2 px-4 border-b">{product.condition}</td>
                        <td className="py-2 px-4 border-b">{new Date(product.date_scraped).toLocaleString()}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);
};

export default DataTable; 
