import React, { useState } from 'react';
import { 
  ExternalLink, Star, Image as ImageIcon, Edit2, Trash2, 
  Info, ShoppingCart, Share2 
} from 'lucide-react';

const ProductCard = ({ 
  product, 
  onEdit, 
  onDelete, 
  onSave,
  className = '' 
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [currentImage, setCurrentImage] = useState(0);
  const [loading, setLoading] = useState(false);

  // Format price with currency
  const formatPrice = (price) => {
    if (!price?.amount) return 'Price unavailable';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: price.currency || 'USD',
      minimumFractionDigits: 2
    }).format(price.amount);
  };

  // Format date for display
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleAction = async (action) => {
    setLoading(true);
    try {
      await action(product);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className} ${loading ? 'opacity-70' : ''}`}>
      {/* Image Gallery */}
      <div className="relative aspect-square bg-gray-50">
        {product.images?.length > 0 ? (
          <>
            <img
              src={product.images[currentImage]}
              alt={product.title}
              className="w-full h-full object-contain"
              loading="lazy"
            />
            {product.images.length > 1 && (
              <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
                {product.images.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentImage(idx)}
                    className={`w-2 h-2 rounded-full transition-colors
                      ${currentImage === idx ? 'bg-blue-600' : 'bg-gray-300'}`}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageIcon className="h-12 w-12 text-gray-400" />
          </div>
        )}
        
        {/* Platform Badge */}
        <div className="absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-medium
          ${product.platform === 'ebay' ? 'bg-blue-100 text-blue-800' : 'bg-orange-100 text-orange-800'}">
          {product.platform}
        </div>
      </div>

      {/* Product Info */}
      <div className="p-4 space-y-3">
        <div className="flex justify-between items-start gap-2">
          <h3 className="font-medium text-gray-900 leading-tight line-clamp-2">
            {product.title}
          </h3>
          <span className="text-lg font-bold text-blue-600 whitespace-nowrap">
            {formatPrice(product.price)}
          </span>
        </div>

        {/* Seller Info & Rating */}
        {product.seller_info && (
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1">
              <span className="text-gray-600">
                {product.seller_info.name}
              </span>
              {product.seller_info.rating && (
                <div className="flex items-center">
                  <Star className="h-4 w-4 text-yellow-400 fill-current" />
                  <span className="ml-1">{product.seller_info.rating}</span>
                </div>
              )}
            </div>
            <span className="text-gray-500 text-xs">
              {formatDate(product.date_scraped)}
            </span>
          </div>
        )}

        {/* Expandable Details */}
        <div className={`transition-all duration-300 ${showDetails ? 'max-h-96' : 'max-h-0'} overflow-hidden`}>
          {product.specifications && (
            <div className="mt-3 border-t pt-3 space-y-2">
              {Object.entries(product.specifications).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-gray-600">{key}:</span>
                  <span className="text-gray-900">{value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-3 border-t">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-gray-600 hover:text-gray-900 flex items-center gap-1 text-sm"
          >
            <Info className="h-4 w-4" />
            {showDetails ? 'Less Info' : 'More Info'}
          </button>
          
          <div className="flex items-center gap-2">
            {onSave && (
              <button
                onClick={() => handleAction(onSave)}
                className="p-1 rounded-full hover:bg-gray-100"
                title="Save Product"
              >
                <ShoppingCart className="h-4 w-4 text-gray-600" />
              </button>
            )}
            {onEdit && (
              <button
                onClick={() => handleAction(onEdit)}
                className="p-1 rounded-full hover:bg-gray-100"
                title="Edit Product"
              >
                <Edit2 className="h-4 w-4 text-gray-600" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => handleAction(onDelete)}
                className="p-1 rounded-full hover:bg-gray-100"
                title="Delete Product"
              >
                <Trash2 className="h-4 w-4 text-red-600" />
              </button>
            )}
            <a
              href={product.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 rounded-full hover:bg-gray-100"
              title="View on Platform"
            >
              <ExternalLink className="h-4 w-4 text-gray-600" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;