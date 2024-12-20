import axios from 'axios';

// Configure base API instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Transform product data from backend to frontend format
const transformProduct = (product) => ({
  id: product.id,
  title: product.title,
  price: {
    amount: parseFloat(product.price_amount),
    currency: product.price_currency
  },
  description: product.description,
  product_url: product.product_url,
  platform: product.platform,
  category: product.category,
  brand: product.brand,
  specifications: product.specifications || {},
  images: product.images?.map(img => img.url) || [],
  seller_info: product.seller_info,
  date_scraped: product.date_scraped,
  last_updated: product.last_updated
});

// API service functions
export const scraping = {
  startScraping: async (params) => {
    const { data } = await api.post('/scrape', params);
    return data;
  },

  checkStatus: async (jobId) => {
    const { data } = await api.get(`/scrape/status/${jobId}`);
    return data;
  },

  cancelJob: async (jobId) => {
    const { data } = await api.post(`/scrape/cancel/${jobId}`);
    return data;
  }
};

export const products = {
  fetchProducts: async (params) => {
    const { data } = await api.get('/products', { params });
    return {
      items: data.products.map(transformProduct),
      total: data.total,
      page: params.page || 1,
      per_page: params.per_page || 50
    };
  },

  deleteProducts: async (ids) => {
    return api.delete('/products', { data: { ids } });
  },

  exportProducts: async (filters) => {
    const { data } = await api.get('/products/export', {
      params: filters,
      responseType: 'blob'
    });
    return data;
  }
};

export const system = {
  getStatus: async () => {
    const { data } = await api.get('/system/status');
    return data;
  },

  getMetrics: async () => {
    const { data } = await api.get('/system/metrics');
    return data;
  }
};