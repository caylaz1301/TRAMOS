import React, { useState } from 'react';
import './DateFilter.css';

interface DateFilterProps {
  onFilterChange: (range: { startDate: string | null; endDate: string | null }) => void;
}

export default function DateFilter({ onFilterChange }: DateFilterProps) {
  const [filterType, setFilterType] = useState('all');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const formatDate = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  const handleFilterSelect = (type: string) => {
    setFilterType(type);
    setCustomStart('');
    setCustomEnd('');

    if (type === 'all') {
      onFilterChange({ startDate: null, endDate: null });
    } else if (type === 'week') {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      onFilterChange({
        startDate: formatDate(start),
        endDate: formatDate(end),
      });
    } else if (type === 'month') {
      const end = new Date();
      const start = new Date();
      start.setMonth(start.getMonth() - 1);
      onFilterChange({
        startDate: formatDate(start),
        endDate: formatDate(end),
      });
    }
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      setFilterType('custom');
      onFilterChange({
        startDate: customStart,
        endDate: customEnd,
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
