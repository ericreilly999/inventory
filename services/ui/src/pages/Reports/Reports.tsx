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
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { Download as DownloadIcon, Assessment as AssessmentIcon } from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import dayjs, { Dayjs } from 'dayjs';
import { apiService } from '../../services/api';

interface InventoryReport {
  generated_at: string;
  by_item_type: Array<{
    item_type: {
      id: string;
      name: string;
      category: string;
    };
    parent_items_count: number;
    child_items_count: number;
  }>;
  by_location_and_type: Array<{
    location: {
      id: string;
      name: string;
      location_type: string;
    };
    item_type: {
      id: string;
      name: string;
      category: string;
    };
    parent_items_count: number;
    child_items_count: number;
  }>;
}

interface MovementReport {
  generated_at: string;
  date_range_start: string | null;
  date_range_end: string | null;
  total_movements: number;
  movements: Array<{
    id: string;
    parent_item_name: string;
    from_location: {
      name: string;
    } | null;
    to_location: {
      name: string;
    };
    moved_at: string;
    moved_by: {
      username: string;
    };
    notes: string | null;
  }>;
}

const Reports: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [inventoryReport, setInventoryReport] = useState<InventoryReport | null>(null);
  const [movementReport, setMovementReport] = useState<MovementReport | null>(null);
  const [locations, setLocations] = useState<any[]>([]);
  const [itemTypes, setItemTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Filters
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedItemType, setSelectedItemType] = useState('');
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs().subtract(30, 'day'));
  const [endDate, setEndDate] = useState<Dayjs | null>(dayjs());

  useEffect(() => {
    fetchMetadata();
  }, []);

  const fetchMetadata = async () => {
    try {
      const [locationsResponse, itemTypesResponse] = await Promise.all([
        apiService.get('/api/v1/locations/locations'),
        apiService.get('/api/v1/items/types'),
      ]);

      setLocations(locationsResponse.data);
      setItemTypes(itemTypesResponse.data);
    } catch (error) {
      setError('Failed to fetch metadata');
    }
  };

  const generateInventoryReport = async () => {
    setLoading(true);
    setError('');
    
    try {
      const params = new URLSearchParams();
      if (selectedLocation) params.append('location_ids', selectedLocation);
      if (selectedItemType) params.append('item_type_ids', selectedItemType);

      const response = await apiService.get(`/api/v1/reports/inventory/counts?${params}`);
      setInventoryReport(response.data);
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to generate inventory report');
    } finally {
      setLoading(false);
    }
  };

  const generateMovementReport = async () => {
    setLoading(true);
    setError('');
    
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate.format('YYYY-MM-DD'));
      if (endDate) params.append('end_date', endDate.format('YYYY-MM-DD'));
      if (selectedLocation) params.append('location_ids', selectedLocation);

      const response = await apiService.get(`/api/v1/reports/movements/history?${params}`);
      setMovementReport(response.data);
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to generate movement report');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async () => {
    try {
      // Only inventory export is available
      const endpoint = '/api/v1/reports/export/inventory';
      const params = new URLSearchParams();
      
      if (selectedLocation) params.append('location_ids', selectedLocation);
      
      const response = await apiService.get(`${endpoint}?${params}`);
      
      // Create and download file
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${tabValue === 0 ? 'inventory' : 'movement'}-report-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to export report');
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  // Transform data for charts
  const inventoryChartData = inventoryReport?.by_location_and_type.reduce((acc: any[], item) => {
    const existing = acc.find(x => x.name === item.location.name);
    const count = item.parent_items_count + item.child_items_count;
    if (existing) {
      existing.value += count;
    } else {
      acc.push({ name: item.location.name, value: count });
    }
    return acc;
  }, []) || [];

  const itemTypeChartData = inventoryReport?.by_item_type.map(item => ({
    name: item.item_type.name,
    value: item.parent_items_count + item.child_items_count,
  })) || [];

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4">Reports & Analytics</Typography>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={exportReport}
            disabled={loading || (tabValue === 0 ? !inventoryReport : !movementReport)}
          >
            Export Report
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
          <Tab label="Inventory Reports" />
          <Tab label="Movement Reports" />
        </Tabs>

        {tabValue === 0 && (
          <Box>
            {/* Inventory Report Filters */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Inventory Report Filters
                </Typography>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Location</InputLabel>
                      <Select
                        value={selectedLocation}
                        onChange={(e) => setSelectedLocation(e.target.value)}
                      >
                        <MenuItem value="">All Locations</MenuItem>
                        {locations.map((location) => (
                          <MenuItem key={location.id} value={location.id}>
                            {location.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Item Type</InputLabel>
                      <Select
                        value={selectedItemType}
                        onChange={(e) => setSelectedItemType(e.target.value)}
                      >
                        <MenuItem value="">All Item Types</MenuItem>
                        {itemTypes.map((type) => (
                          <MenuItem key={type.id} value={type.id}>
                            {type.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Button
                      variant="contained"
                      startIcon={<AssessmentIcon />}
                      onClick={generateInventoryReport}
                      disabled={loading}
                      fullWidth
                    >
                      Generate Report
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Inventory Charts */}
            {inventoryReport && inventoryChartData.length > 0 && (
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Items by Location
                      </Typography>
                      <Box sx={{ height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={inventoryChartData}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {inventoryChartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Items by Type
                      </Typography>
                      <Box sx={{ height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={itemTypeChartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="value" fill="#1976d2" />
                          </BarChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}

            {/* Inventory Table */}
            {inventoryReport && inventoryReport.by_location_and_type.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Detailed Inventory Report
                  </Typography>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Location</TableCell>
                          <TableCell>Location Type</TableCell>
                          <TableCell>Item Type</TableCell>
                          <TableCell align="right">Parent Items</TableCell>
                          <TableCell align="right">Child Items</TableCell>
                          <TableCell align="right">Total Items</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {inventoryReport.by_location_and_type.map((item, index) => (
                          <TableRow key={index}>
                            <TableCell>{item.location.name}</TableCell>
                            <TableCell>{item.location.location_type}</TableCell>
                            <TableCell>{item.item_type.name}</TableCell>
                            <TableCell align="right">{item.parent_items_count}</TableCell>
                            <TableCell align="right">{item.child_items_count}</TableCell>
                            <TableCell align="right">{item.parent_items_count + item.child_items_count}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            )}
          </Box>
        )}

        {tabValue === 1 && (
          <Box>
            {/* Movement Report Filters */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Movement Report Filters
                </Typography>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={3}>
                    <DatePicker
                      label="Start Date"
                      value={startDate}
                      onChange={(newValue) => setStartDate(newValue)}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <DatePicker
                      label="End Date"
                      value={endDate}
                      onChange={(newValue) => setEndDate(newValue)}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Location</InputLabel>
                      <Select
                        value={selectedLocation}
                        onChange={(e) => setSelectedLocation(e.target.value)}
                      >
                        <MenuItem value="">All Locations</MenuItem>
                        {locations.map((location) => (
                          <MenuItem key={location.id} value={location.id}>
                            {location.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Button
                      variant="contained"
                      startIcon={<AssessmentIcon />}
                      onClick={generateMovementReport}
                      disabled={loading}
                      fullWidth
                    >
                      Generate Report
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Movement Table */}
            {movementReport && movementReport.movements.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Movement History Report ({movementReport.total_movements} movements)
                  </Typography>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Item</TableCell>
                          <TableCell>From Location</TableCell>
                          <TableCell>To Location</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell>Moved By</TableCell>
                          <TableCell>Notes</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {movementReport.movements.map((movement) => (
                          <TableRow key={movement.id}>
                            <TableCell>{movement.parent_item_name}</TableCell>
                            <TableCell>{movement.from_location?.name || 'N/A'}</TableCell>
                            <TableCell>{movement.to_location.name}</TableCell>
                            <TableCell>
                              {dayjs(movement.moved_at).format('YYYY-MM-DD HH:mm')}
                            </TableCell>
                            <TableCell>{movement.moved_by.username}</TableCell>
                            <TableCell>{movement.notes || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            )}
          </Box>
        )}
      </Box>
    </LocalizationProvider>
  );
};

export default Reports;