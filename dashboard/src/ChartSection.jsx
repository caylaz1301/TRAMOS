import React from 'react';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Legend, Tooltip } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import './ChartSection.css';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Legend, Tooltip);

export default function ChartSection({ categories, severity, tickets }) {
  const categoryColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'];
  const severityColors = ['#ef4444', '#f97316', '#f59e0b', '#10b981'];

  const categoryData = {
    labels: categories.map(c => c.name),
    datasets: [{
      data: categories.map(c => c.count),
      backgroundColor: categoryColors,
      borderColor: '#fff',
      borderWidth: 2
    }]
  };

  const severityData = {
    labels: severity.map(s => {
      const severityMap = { 'critical': '🔴 Critical', 'high': '🟠 High', 'medium': '🟡 Medium', 'low': '🟢 Low' };
      return severityMap[s.name] || s.name;
    }),
    datasets: [{
      label: 'Issues by Severity',
      data: severity.map(s => s.count),
      backgroundColor: severityColors,
      borderColor: '#fff',
      borderWidth: 2
    }]
  };

  const ticketData = {
    labels: tickets.by_category?.map(t => t.category) || [],
    datasets: [{
      label: 'Tickets Created',
      data: tickets.by_category?.map(t => t.count) || [],
      backgroundColor: categoryColors,
      borderColor: '#fff',
      borderWidth: 1
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          font: { size: 12 },
          padding: 16,
          usePointStyle: true
        }
      }
    }
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 1 }
      }
    }
  };

  return (
    <div className="charts-grid">
      <div className="chart-card">
        <h3>📊 Problem Categories</h3>
        {categories.length > 0 ? (
          <Pie data={categoryData} options={chartOptions} />
        ) : (
          <p className="no-data">No data available</p>
        )}
      </div>

      <div className="chart-card">
        <h3>⚠️ Issue Severity</h3>
        {severity.length > 0 ? (
          <Pie data={severityData} options={chartOptions} />
        ) : (
          <p className="no-data">No data available</p>
        )}
      </div>

      <div className="chart-card chart-full">
        <h3>🎫 Tickets by Category</h3>
        {tickets.by_category && tickets.by_category.length > 0 ? (
          <Bar data={ticketData} options={barOptions} />
        ) : (
          <p className="no-data">No ticket data available</p>
        )}
      </div>
    </div>
  );
}
