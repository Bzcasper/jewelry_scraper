import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Error Boundary Component
const ErrorBoundary = ({ children }) => {
  const [hasError, setHasError] = React.useState(false);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const handleError = (error) => {
      setHasError(true);
      setError(error);
      // Log error to your error tracking service here
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (hasError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold text-red-600 mb-4">
            Something went wrong
          </h2>
          <p className="text-gray-600 mb-4">
            The application encountered an error. Please try refreshing the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Refresh Page
          </button>
          {error && (
            <pre className="mt-4 p-4 bg-gray-100 rounded text-sm overflow-auto">
              {error.toString()}
            </pre>
          )}
        </div>
      </div>
    );
  }

  return children;
};

// Root Layout Component
const RootLayout = ({ children }) => {
  React.useEffect(() => {
    // Add meta theme color for mobile browsers
    const metaThemeColor = document.createElement('meta');
    metaThemeColor.name = 'theme-color';
    metaThemeColor.content = '#ffffff';
    document.head.appendChild(metaThemeColor);

    // Clean up
    return () => {
      document.head.removeChild(metaThemeColor);
    };
  }, []);

  return (
    <div className="app-root">
      {children}
      <div id="portal-root" /> {/* For modals and popovers */}
    </div>
  );
};

// Initialize root and render app
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <RootLayout>
        <App />
      </RootLayout>
    </ErrorBoundary>
  </React.StrictMode>
);

// Performance monitoring
const reportWebVitals = (metric) => {
  // Implement your analytics service here
  console.log(metric);
};

// Handle service worker registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('SW registered:', registration);
      })
      .catch((error) => {
        console.log('SW registration failed:', error);
      });
  });
}

// Handle offline capabilities
window.addEventListener('online', () => {
  document.body.classList.remove('offline');
});

window.addEventListener('offline', () => {
  document.body.classList.add('offline');
});

// Export for metric reporting
export default reportWebVitals;