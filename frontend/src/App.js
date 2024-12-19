import React from 'react';
import SearchBar from './components/SearchBar';
import DataTable from './components/DataTable';
import DataDashboard from './components/DataDashboard';
import EnhancedSearch from './components/EnhancedSearch';

function App() {
  return (
    <div className="App">
      <h1>Jewelry Scraper</h1>
      <EnhancedSearch />
      <DataDashboard />
      <DataTable />
    </div>
  );
}

export default App;
