

import React, { useEffect, useState } from 'react'; import { Bar, Pie } from 'react-chartjs-2'; import axios from 'axios';

const DataDashboard = () => { const [productData, setProductData] = useState([]);

javascript
useEffect(() => {
    fetchProductData();
}, []);

const fetchProductData = async () => {
    try {
        const response = await axios.get('/products');
        setProductData(response.data);
    } catch (error) {
        console.error('Error fetching product data:', error);
    }
};

const getCategoryDistribution = () => {
    const categories = {};
    productData.forEach(product => {
        categories[product.category] = (categories[product.category] || 0) + 1;
    });
    return {
        labels: Object.keys(categories),
        datasets: [
            {
                data: Object.values(categories),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
            },
        ],
    };
};

const getPriceDistribution = () => {
    const prices = productData.map(product => product.price);
    return {
        labels: ['0-100', '100-200', '200-300', '300+'],
        datasets: [
            {
                label: 'Price Distribution',
                data: [
                    prices.filter(price => price < 100).length,
                    prices.filter(price => price >= 100 && price < 200).length,
                    prices.filter(price => price >= 200 && price < 300).length,
                    prices.filter(price => price >= 300).length,
                ],
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
            },
        ],
    };
};

return (
    <div className="p-4">
        <h2 className="text-2xl font-bold mb-4">Data Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white shadow rounded p-4">
                <h3 className="text-xl font-semibold mb-2">Category Distribution</h3>
                <Pie data={getCategoryDistribution()} />
            </div>
            <div className="bg-white shadow rounded p-4">
                <h3 className="text-xl font-semibold mb-2">Price Distribution</h3>
                <Bar data={getPriceDistribution()} />
            </div>
        </div>
    </div>
);
}; 

export default DataDashboard; 
