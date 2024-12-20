import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { EnhancedSearch } from '../../../src/components/EnhancedSearch';
import { DataTable } from '../../../src/components/DataTable';
import { DataDashboard } from '../../../src/components/DataDashboard';
import { AppProvider } from '../../../src/context/AppContext';

// Mock API calls
jest.mock('../../../src/services/api', () => ({
  scraping: {
    startJob: jest.fn(() => Promise.resolve({ job_id: 'test-job' })),
    getStatus: jest.fn(() => Promise.resolve({ status: 'completed' }))
  },
  products: {
    fetch: jest.fn(() => Promise.resolve({
      items: [],
      total: 0
    }))
  }
}));

describe('EnhancedSearch Component', () => {
  it('should handle search submission', async () => {
    const { getByPlaceholderText, getByText } = render(
      <AppProvider>
        <EnhancedSearch />
      </AppProvider>
    );

    const input = getByPlaceholderText('Search for jewelry...');
    fireEvent.change(input, { target: { value: 'gold ring' } });

    const searchButton = getByText('Search');
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Searching...')).toBeInTheDocument();
    });
  });

  it('should handle filter changes', () => {
    const { getByLabelText } = render(
      <AppProvider>
        <EnhancedSearch />
      </AppProvider>
    );

    const priceMin = getByLabelText('Min Price');
    fireEvent.change(priceMin, { target: { value: '100' } });

    const priceMax = getByLabelText('Max Price');
    fireEvent.change(priceMax, { target: { value: '1000' } });

    expect(priceMin.value).toBe('100');
    expect(priceMax.value).toBe('1000');
  });
});

describe('DataTable Component', () => {
  const mockProducts = [
    {
      id: 1,
      title: 'Test Ring',
      price: { amount: 99.99, currency: 'USD' },
      platform: 'ebay'
    }
  ];

  it('should render products correctly', () => {
    const { getByText } = render(
      <AppProvider>
        <DataTable products={mockProducts} />
      </AppProvider>
    );

    expect(getByText('Test Ring')).toBeInTheDocument();
    expect(getByText('$99.99')).toBeInTheDocument();
  });

  it('should handle sorting', () => {
    const { getByText } = render(
      <AppProvider>
        <DataTable products={mockProducts} />
      </AppProvider>
    );

    const titleHeader = getByText('Title');
    fireEvent.click(titleHeader);

    // Check sort indicator
    expect(titleHeader).toHaveAttribute('aria-sort', 'ascending');
  });
});

describe('DataDashboard Component', () => {
  it('should render system stats', async () => {
    const { getByText } = render(
      <AppProvider>
        <DataDashboard />
      </AppProvider>
    );

    await waitFor(() => {
      expect(getByText('Active Jobs')).toBeInTheDocument();
      expect(getByText('Total Products')).toBeInTheDocument();
    });
  });

  it('should update periodically', async () => {
    jest.useFakeTimers();

    render(
      <AppProvider>
        <DataDashboard />
      </AppProvider>
    );

    jest.advanceTimersByTime(30000); // 30 seconds

    await waitFor(() => {
      expect(mockApi.getSystemStatus).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});