# TRAMOS Analytics Dashboard

Modern React-based analytics dashboard for the TRAMOS WhatsApp AI Support System.

## Features

✅ **Authentication**
- JWT-based login system
- Session management
- Secure access control

✅ **Real-time Metrics**
- Total sessions and tickets
- Success rates
- Active conversations
- Message statistics

✅ **Advanced Analytics**
- Problem category distribution
- Severity level analysis
- Session quality metrics
- Ticket creation tracking

✅ **Interactive Charts**
- Pie charts for category/severity distribution
- Bar charts for ticket analysis
- Responsive design

✅ **Auto-refresh**
- Automatic data refresh every 5 seconds
- Real-time dashboard updates
- Live session monitoring

✅ **Recent Sessions Table**
- Latest session details
- Driver information
- Problem tracking
- Ticket references

## Prerequisites

- Node.js 16+ (for development)
- npm or yarn
- Backend API running on `http://localhost:8000`

## Installation

### Backend Setup

First, ensure the backend API is running with PyJWT installed:

```bash
cd /Users/vdr/Documents/TRAMOS
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to dashboard directory
cd /Users/vdr/Documents/TRAMOS/dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Quick Start

1. **Install Backend Dependencies**
   ```bash
   pip install pyjwt==2.8.1
   ```

2. **Start Backend Server**
   ```bash
   cd /Users/vdr/Documents/TRAMOS
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd /Users/vdr/Documents/TRAMOS/dashboard
   npm install
   ```

4. **Start Dashboard**
   ```bash
   npm run dev
   ```

5. **Login**
   - Default username: `admin`
   - Default password: `admin123`
   - (Change in environment variables)

## Configuration

### Backend Auth (.env)

```env
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=admin123
JWT_SECRET_KEY=tramos_dashboard_secret_key_change_me
```

## Build for Production

```bash
cd /Users/vdr/Documents/TRAMOS/dashboard
npm run build
```

This creates a `dist` folder with optimized production files.

## Architecture

### Frontend Components

- **Login.jsx** - Authentication page
- **Dashboard.jsx** - Main dashboard with state management
- **MetricCard.jsx** - Individual metric display
- **ChartSection.jsx** - Chart visualizations
- **RecentSessions.jsx** - Session table view

### API Endpoints

- `POST /api/auth/login` - User authentication
- `GET /api/analytics/dashboard` - Complete dashboard data
- `GET /api/analytics/stats/overview` - Overview statistics
- `GET /api/analytics/stats/categories` - Problem categories
- `GET /api/analytics/stats/severity` - Severity distribution
- `GET /api/analytics/stats/quality` - Quality metrics
- `GET /api/analytics/data/recent-sessions` - Recent session data

## Metrics Displayed

### Key Metrics
- Total Sessions
- Tickets Created
- Success Rate
- Active Sessions
- Total Messages
- Avg Messages per Session

### Quality Metrics
- Completion Rate
- Average Duration
- Average Messages per Session
- Abandoned Sessions

### Analytics
- Problem Categories (Pie Chart)
- Issue Severity (Pie Chart)
- Tickets by Category (Bar Chart)

### Recent Data
- Session timestamp
- Driver phone and name
- Problem description
- Category and severity
- Current state
- Linked ticket ID

## Troubleshooting

### Connection Refused
Ensure backend is running on port 8000:
```bash
curl http://localhost:8000/health
```

### Login Failed
- Check credentials (default: admin/admin123)
- Verify DASHBOARD_USERNAME and DASHBOARD_PASSWORD in .env

### No Data Showing
- Confirm backend analytics endpoints are accessible
- Check browser console for API errors
- Verify database has session data

### CORS Issues
Backend should have CORS enabled for `http://localhost:5173`

## Performance

- **Auto-refresh**: 5 seconds
- **Chart.js**: Lightweight charting
- **Responsive**: Mobile-friendly design
- **Real-time**: Live data updates

## Security Notes

⚠️ **Production Recommendations**
1. Change default admin credentials
2. Use strong JWT_SECRET_KEY
3. Enable HTTPS
4. Add rate limiting
5. Implement proper user management
6. Use environment-based configuration

## Browser Support

| Browser | Support |
|---------|---------|
| Chrome  | ✅ Latest |
| Firefox | ✅ Latest |
| Safari  | ✅ Latest |
| Edge    | ✅ Latest |

## License

Part of TRAMOS AI Support System © 2026

## Support

For issues or feature requests, contact the development team.
