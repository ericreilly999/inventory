import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import dayjs, { Dayjs } from 'dayjs';
import { apiService } from '../../services/api';

interface DashboardData {
  inventory_by_location: Array<{
    location_name: string;
    item_type_name: string;
    count: number;
  }>;
  inbound_throughput: Array<{
    location_name: string;
    item_type_name: string;
    count: number;
  }>;
  outbound_throughput: Array<{
    location_name: string;
    item_type_name: string;
    count: number;
  }>;
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [locationTypes, setLocationTypes] = useState<any[]>([]);
  const [selectedLocationType, setSelectedLocationType] = useState('');
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs().subtract(30, 'day'));
  const [endDate, setEndDate] = useState<Dayjs | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLocationTypes();
  }, []);

  useEffect(() => {
    if (selectedLocationType) {
      fetchDashboardData();
    }
  }, [selectedLocationType, startDate, endDate]);

  const fetchLocationTypes = async () => {
    try {
      const response = await apiService.get('/api/v1/locations/types');
      setLocationTypes(response.data);
      // Auto-select first location type if available
      if (response.data.length > 0) {
        setSelectedLocationType(response.data[0].id);
      }
    } catch (error) {
      setError('Failed to fetch location types');
    }
  };

  const fetchDashboardData = async () => {
    if (!selectedLocationType) return;

    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      params.append('location_type_id', selectedLocationType);
      if (startDate) params.append('start_date', startDate.format('YYYY-MM-DD'));
      if (endDate) params.append('end_date', endDate.format('YYYY-MM-DD'));

      const response = await apiService.get(`/api/v1/reports/dashboard?${params}`);
      setDashboardData(response.data);
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Transform data for stacked bar charts
  const transformDataForChart = (data: Array<{ location_name: string; item_type_name: string; count: number }>) => {
    const locationMap = new Map<string, any>();

    data.forEach((item) => {
      if (!locationMap.has(item.location_name)) {
        locationMap.set(item.location_name, { location: item.location_name });
      }
      const locationData = locationMap.get(item.location_name);
      locationData[item.item_type_name] = item.count;
    });

    return Array.from(locationMap.values());
  };

  // Get unique item types for legend
  const getItemTypes = (data: Array<{ location_name: string; item_type_name: string; count: number }>) => {
    const types = new Set<string>();
    data.forEach((item) => types.add(item.item_type_name));
    return Array.from(types);
  };

  // Colors for different item types
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#ff7c7c'];

  const inventoryChartData = dashboardData ? transformDataForChart(dashboardData.inventory_by_location) : [];
  const inboundChartData = dashboardData ? transformDataForChart(dashboardData.inbound_throughput) : [];
  const outboundChartData = dashboardData ? transformDataForChart(dashboardData.outbound_throughput) : [];

  const inventoryItemTypes = dashboardData ? getItemTypes(dashboardData.inventory_by_location) : [];
  const throughputItemTypes = dashboardData
    ? getItemTypes([...dashboardData.inbound_throughput, ...dashboardData.outbound_throughput])
    : [];

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Filters
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <FormControl fullWidth required>
                  <InputLabel>Location Type</InputLabel>
                  <Select
                    value={selectedLocationType}
                    onChange={(e) => setSelectedLocationType(e.target.value)}
                    label="Location Type"
                  >
                    {locationTypes.map((type) => (
                      <MenuItem key={type.id} value={type.id}>
                        {type.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <DatePicker
                  label="Start Date (Throughput)"
                  value={startDate}
                  onChange={(newValue) => setStartDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <DatePicker
                  label="End Date (Throughput)"
                  value={endDate}
                  onChange={(newValue) => setEndDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {loading && (
          <Box display="flex" justifyContent="center" p={3}>
            <Typography>Loading dashboard data...</Typography>
          </Box>
        )}

        {!loading && dashboardData && (
          <Grid container spacing={3}>
            {/* Inventory by Location */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Inventory by Location
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Parent items count by location and item type
                  </Typography>
                  <Box sx={{ height: 400, mt: 2 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={inventoryChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="location" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {inventoryItemTypes.map((itemType, index) => (
                          <Bar
                            key={itemType}
                            dataKey={itemType}
                            stackId="a"
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Inbound Throughput */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Inbound Throughput by Location
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Items moved TO locations, split by item type
                  </Typography>
                  <Box sx={{ height: 400, mt: 2 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={inboundChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="location" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {throughputItemTypes.map((itemType, index) => (
                          <Bar
                            key={itemType}
                            dataKey={itemType}
                            stackId="a"
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Outbound Throughput */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Outbound Throughput by Location
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Items moved FROM locations, split by item type
                  </Typography>
                  <Box sx={{ height: 400, mt: 2 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={outboundChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="location" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {throughputItemTypes.map((itemType, index) => (
                          <Bar
                            key={itemType}
                            dataKey={itemType}
                            stackId="a"
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {!loading && !dashboardData && selectedLocationType && (
          <Box display="flex" justifyContent="center" p={3}>
            <Typography color="text.secondary">No data available for the selected filters</Typography>
          </Box>
        )}
      </Box>
    </LocalizationProvider>
  );
};

export default Dashboard;
