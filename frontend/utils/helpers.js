export const formatPrice = (price, currency = 'USD') => {
    if (!price) return '';
    const numPrice = parseFloat(price);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency
    }).format(numPrice);
  };
  
  export const formatDate = (date) => {
    if (!date) return '';
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };
  
  export const validatePrice = (price) => {
    if (!price) return false;
    const numPrice = parseFloat(price);
    return !isNaN(numPrice) && numPrice >= 0;
  };
  
  export const createQueryString = (params) => {
    return Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== '')
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&');
  };