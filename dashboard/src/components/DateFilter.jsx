import React, { useState } from 'react';
import './DateFilter.css';

export default function DateFilter({ onFilterChange }) {
  const [filterType, setFilterType] = useState('all');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const handleFilterSelect = (type) => {
    setFilterType(type);
    
    if (type === 'all') {
      onFilterChange({ startDate: null, endDate: null });
    } else if (type === 'week') {
      const start = new Date();
      start.setDate(start.getDate() - 7);
      onFilterChange({ 
        startDate: start.toISOString(), 
        endDate: new Date().toISOString() 
      });
    } else if (type === 'month') {
      const start = new Date();
      start.setMonth(start.getMonth() - 1);
      onFilterChange({ 
        startDate: start.toISOString(), 
        endDate: new Date().toISOString() 
      });
    }
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      setFilterType('custom');
      
      // We convert to ISO strings, ensuring full day coverage for the end date
      const start = new Date(customStart);
      start.setHours(0, 0, 0, 0);
      
      const end = new Date(customEnd);
      end.setHours(23, 59, 59, 999);
      
      onFilterChange({ 
        startDate: start.toISOString(), 
        endDate: end.toISOString() 
      });
    }
  };

  return (
    <div className="date-filter-container">
      <div className="filter-presets">
        <button 
          className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => handleFilterSelect('all')}
        >
          Semua Waktu
        </button>
        <button 
          className={`filter-btn ${filterType === 'week' ? 'active' : ''}`}
          onClick={() => handleFilterSelect('week')}
        >
          7 Hari Terakhir
        </button>
        <button 
          className={`filter-btn ${filterType === 'month' ? 'active' : ''}`}
          onClick={() => handleFilterSelect('month')}
        >
          Bulan Ini
        </button>
      </div>
      
      <div className="custom-range-container">
        <span className="custom-label">Atau Kustom:</span>
        <input 
          type="date" 
          className="date-input" 
          value={customStart}
          onChange={(e) => setCustomStart(e.target.value)}
        />
        <span className="range-separator">-</span>
        <input 
          type="date" 
          className="date-input" 
          value={customEnd}
          onChange={(e) => setCustomEnd(e.target.value)}
        />
        <button 
          className={`apply-btn ${filterType === 'custom' ? 'active' : ''}`}
          onClick={handleCustomApply}
          disabled={!customStart || !customEnd}
        >
          Terapkan
        </button>
      </div>
    </div>
  );
}
