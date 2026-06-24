/**
 * Skeleton Loading Components for TRAMOS Dashboard
 * Provides shimmer loading states for better UX
 */

import React from 'react';

export const SkeletonLine = ({ width = '100%', height = 16 }: { width?: string; height?: number }) => (
  <div
    className="skeleton-line"
    style={{
      width,
      height: `${height}px`,
    }}
  />
);

export const SkeletonBox = ({
  width = '100%',
  height = 100,
}: {
  width?: string;
  height?: number;
}) => (
  <div
    className="skeleton-box"
    style={{ width, height: `${height}px` }}
  />
);

export const SkeletonAvatar = ({ size = 40 }: { size?: number }) => (
  <div
    className="skeleton-avatar"
    style={{
      width: `${size}px`,
      height: `${size}px`,
    }}
  />
);

// KPI Card Skeleton
export const SkeletonKPICard = () => (
  <div className="skeleton-kpi-card">
    <div className="skeleton-kpi-header">
      <SkeletonAvatar size={40} />
      <SkeletonLine width="60px" height={14} />
    </div>
    <SkeletonLine width="80px" height={28} />
    <SkeletonLine width="120px" height={12} />
  </div>
);

// KPI Grid Skeleton
export const SkeletonKPIGrid = ({ count = 4 }: { count?: number }) => (
  <div className="skeleton-kpi-grid">
    {[...Array(count)].map((_, i) => (
      <SkeletonKPICard key={i} />
    ))}
  </div>
);

// Chart Skeleton
export const SkeletonChart = ({ height = 260 }: { height?: number }) => (
  <div className="skeleton-chart" style={{ height: `${height}px` }}>
    <div className="skeleton-chart-header">
      <SkeletonLine width="150px" height={18} />
      <SkeletonLine width="60px" height={20} />
    </div>
    <div className="skeleton-chart-area">
      <SkeletonBox height={height - 60} />
    </div>
  </div>
);

// Table Row Skeleton
export const SkeletonTableRow = () => (
  <div className="skeleton-table-row">
    <div className="skeleton-cell skeleton-cell-user">
      <SkeletonAvatar size={32} />
      <div className="skeleton-cell-text">
        <SkeletonLine width="100px" height={13} />
        <SkeletonLine width="70px" height={11} />
      </div>
    </div>
    <SkeletonLine width="150px" height={13} />
    <SkeletonLine width="80px" height={20} />
    <SkeletonLine width="60px" height={20} />
    <SkeletonLine width="40px" height={13} />
    <SkeletonLine width="60px" height={13} />
  </div>
);

// Table Skeleton
export const SkeletonTable = ({ rows = 5 }: { rows?: number }) => (
  <div className="skeleton-table">
    <div className="skeleton-table-header">
      {[120, 160, 80, 70, 45, 65].map((width, i) => (
        <SkeletonLine key={i} width={`${width}px`} height={14} />
      ))}
    </div>
    {[...Array(rows)].map((_, i) => (
      <SkeletonTableRow key={i} />
    ))}
  </div>
);

// Card Skeleton
export const SkeletonCard = ({
  header = true,
  contentHeight = 200,
}: {
  header?: boolean;
  contentHeight?: number;
}) => (
  <div className="skeleton-card">
    {header && (
      <div className="skeleton-card-header">
        <SkeletonLine width="150px" height={18} />
        <SkeletonLine width="50px" height={20} />
      </div>
    )}
    <div className="skeleton-card-content" style={{ height: `${contentHeight}px` }} />
  </div>
);

// Activity Item Skeleton
export const SkeletonActivityItem = () => (
  <div className="skeleton-activity-item">
    <SkeletonAvatar size={32} />
    <div className="skeleton-activity-content">
      <SkeletonLine width="80%" height={13} />
      <SkeletonLine width="60%" height={11} />
    </div>
  </div>
);

// Activity List Skeleton
export const SkeletonActivityList = ({ count = 6 }: { count?: number }) => (
  <div className="skeleton-activity-list">
    {[...Array(count)].map((_, i) => (
      <SkeletonActivityItem key={i} />
    ))}
  </div>
);

// Stats Grid Skeleton
export const SkeletonStatsGrid = ({ count = 6 }: { count?: number }) => (
  <div className="skeleton-stats-grid">
    {[...Array(count)].map((_, i) => (
      <div key={i} className="skeleton-stat-item">
        <SkeletonLine width="80px" height={24} />
        <SkeletonLine width="60px" height={12} />
      </div>
    ))}
  </div>
);

// Full Page Skeleton
export const SkeletonDashboard = () => (
  <div className="skeleton-page">
    <SkeletonKPIGrid count={4} />
    <SkeletonChart height={280} />
    <div className="skeleton-charts-row">
      <SkeletonChart height={260} />
      <SkeletonChart height={260} />
      <SkeletonCard contentHeight={260} />
    </div>
    <SkeletonCard header={true} contentHeight={300} />
    <SkeletonTable rows={8} />
  </div>
);

// Category Item Skeleton
export const SkeletonCategoryItem = () => (
  <div className="skeleton-category-item">
    <SkeletonLine width="30px" height={14} />
    <SkeletonLine width="100px" height={14} />
    <div className="skeleton-bar" />
    <SkeletonLine width="30px" height={14} />
  </div>
);

// Category List Skeleton
export const SkeletonCategoryList = ({ count = 5 }: { count?: number }) => (
  <div className="skeleton-category-list">
    {[...Array(count)].map((_, i) => (
      <SkeletonCategoryItem key={i} />
    ))}
  </div>
);
