import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  LocationOn as LocationIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../../services/api';

interface DashboardStats {
  totalItems: number;
  totalLocations: number;
  recentMovements: number;
  activeUsers: number;
}

interface LocationData {
  name: string;
  itemCount: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalItems: 0,
    totalLocations: 0,
    recentMovements: 0,
    activeUsers: 0,
  });
  const [locationData, setLocationData] = useState<LocationData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch dashboard statistics
        const [itemsResponse, locationsResponse, movementsResponse, usersResponse] = await Promise.all([
          apiService.get('/api/v1/items/parent'),
          apiService.get('/api/v1/locations'),
          apiService.get('/api/v1/movements/history?limit=100'),
          apiService.get('/api/v1/users'),
        ]);

        setStats({
          totalItems: itemsResponse.data.length || 0,
          totalLocations: locationsResponse.data.length || 0,
          recentMovements: movementsResponse.data.length || 0,
          activeUsers: usersResponse.data.filter((user: any) => user.active).length || 0,
        });

        // Fetch location-based inventory data for chart
        const reportResponse = await apiService.get('/api/v1/reports/inventory/status');
        const chartData = reportResponse.data.locations?.map((loc: any) => ({
          name: loc.location.name,
          itemCount: loc.parent_items_count + loc.child_items_count,
        })) || [];
        setLocationData(chartData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const StatCard: React.FC<{
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, icon, color }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="h2">
              {loading ? '...' : value}
            </Typography>
          </Box>
          <Box sx={{ color, fontSize: 40 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Items"
            value={stats.totalItems}
            icon={<InventoryIcon />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Locations"
            value={stats.totalLocations}
            icon={<LocationIcon />}
            color="#388e3c"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Recent Movements"
            value={stats.recentMovements}
            icon={<TrendingUpIcon />}
            color="#f57c00"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Users"
            value={stats.activeUsers}
            icon={<PeopleIcon />}
            color="#7b1fa2"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Inventory by Location
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={locationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="itemCount" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2" color="textSecondary">
                • Add new inventory items
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • Move items between locations
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • Generate inventory reports
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • Manage user access
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;