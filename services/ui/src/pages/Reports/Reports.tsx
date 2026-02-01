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
  Tabs,
  Tab,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { Download as DownloadIcon, Assessment as AssessmentIcon } from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import dayjs, { Dayjs } from 'dayjs';
import { apiService } from '../../services/api';

interface InventoryReport {
  generated_at: string;
  by_parent_item_type: Array<{
    item_type: {
      id: string;
      name: string;
      category: string;
    };
    parent_items_count: number;
  }>;
  by_child_item_type: Array<{
    item_type: {
      id: string;
      name: string;
      category: string;
    };
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
  parent_items_detail: Array<{
    id: string;
    sku: string;
    parent_item_type: string;
    location_name: string;
    location_type: string;
  }>;
  child_items_detail: Array<{
    id: string;
    sku: string;
    child_item_type: string;
    parent_item_sku: string;
    parent_item_type: string;
    location_name: string;
    location_type: string;
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
  const [locationTypes, setLocationTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Filters
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedLocationType, setSelectedLocationType] = useState('');
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs().subtract(30, 'day'));
  const [endDate, setEndDate] = useState<Dayjs | null>(null);

  useEffect(() => {
    fetchMetadata();
  }, []);

  const fetchMetadata = async () => {
    try {
      const [locationsResponse, locationTypesResponse] = await Promise.all([
        apiService.get('/api/v1/locations/locations'),
        apiService.get('/api/v1/locations/types'),
      ]);

      setLocations(locationsResponse.data);
      setLocationTypes(locationTypesResponse.data);
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
      if (selectedLocationType) params.append('location_type_ids', selectedLocationType);

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

  const exportReportAsJSON = () => {
    if (!inventoryReport) return;
    
    const data = {
      parent_items_detail: inventoryReport.parent_items_detail,
      child_items_detail: inventoryReport.child_items_detail,
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inventory-report-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const exportReportAsCSV = () => {
    if (!inventoryReport) return;
    
    // Export parent items as CSV
    const parentHeaders = ['Parent Item SKU', 'Item Type', 'Location', 'Location Type'];
    const parentRows = inventoryReport.parent_items_detail.map(item => [
      item.sku,
      item.parent_item_type,
      item.location_name,
      item.location_type,
    ]);
    
    const parentCSV = [
      parentHeaders.join(','),
      ...parentRows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');
    
    // Export child items as CSV
    const childHeaders = ['Child Item SKU', 'Child Item Type', 'Parent Item SKU', 'Parent Item Type', 'Location', 'Location Type'];
    const childRows = inventoryReport.child_items_detail.map(item => [
      item.sku,
      item.child_item_type,
      item.parent_item_sku,
      item.parent_item_type,
      item.location_name,
      item.location_type,
    ]);
    
    const childCSV = [
      childHeaders.join(','),
      ...childRows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');
    
    // Combine both CSVs with section headers
    const combinedCSV = `Parent Items\n${parentCSV}\n\nChild Items\n${childCSV}`;
    
    const blob = new Blob([combinedCSV], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inventory-report-${new Date().toISOString()}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#ff7c7c'];

  // Transform data for stacked bar charts - Parent Items by Location
  const transformParentItemsData = () => {
    if (!inventoryReport?.by_location_and_type) return [];
    
    const locationMap = new Map<string, any>();
    
    inventoryReport.by_location_and_type.forEach((item) => {
      if (!locationMap.has(item.location.name)) {
        locationMap.set(item.location.name, { location: item.location.name });
      }
      const locationData = locationMap.get(item.location.name);
      locationData[item.item_type.name] = item.parent_items_count;
    });
    
    return Array.from(locationMap.values());
  };

  // Transform data for stacked bar charts - Child Items by Location
  const transformChildItemsData = () => {
    if (!inventoryReport?.child_items_detail) return [];
    
    const locationMap = new Map<string, any>();
    
    // Group child items by location and child item type
    inventoryReport.child_items_detail.forEach((item) => {
      if (!locationMap.has(item.location_name)) {
        locationMap.set(item.location_name, { location: item.location_name });
      }
      const locationData = locationMap.get(item.location_name);
      // Count child items by their child item type
      locationData[item.child_item_type] = (locationData[item.child_item_type] || 0) + 1;
    });
    
    return Array.from(locationMap.values());
  };

  // Get unique parent item types for legend
  const getParentItemTypes = () => {
    if (!inventoryReport?.by_location_and_type) return [];
    const types = new Set<string>();
    inventoryReport.by_location_and_type.forEach((item) => types.add(item.item_type.name));
    return Array.from(types);
  };

  // Get unique child item types for legend
  const getChildItemTypes = () => {
    if (!inventoryReport?.child_items_detail) return [];
    const types = new Set<string>();
    inventoryReport.child_items_detail.forEach((item) => types.add(item.child_item_type));
    return Array.from(types);
  };

  const parentItemsChartData = transformParentItemsData();
  const childItemsChartData = transformChildItemsData();
  const parentItemTypes = getParentItemTypes();
  const childItemTypes = getChildItemTypes();

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4">Reports & Analytics</Typography>
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={exportReportAsJSON}
              disabled={loading || !inventoryReport}
            >
              Export as JSON
            </Button>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={exportReportAsCSV}
              disabled={loading || !inventoryReport}
            >
              Export as CSV
            </Button>
          </Box>
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
                            {location.location_type?.name} - {location.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Location Type</InputLabel>
                      <Select
                        value={selectedLocationType}
                        onChange={(e) => setSelectedLocationType(e.target.value)}
                      >
                        <MenuItem value="">All Location Types</MenuItem>
                        {locationTypes.map((type) => (
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
            {inventoryReport && parentItemsChartData.length > 0 && (
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Parent Items by Location
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Stacked by item type
                      </Typography>
                      <Box sx={{ height: 400, mt: 2 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={parentItemsChartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="location" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            {parentItemTypes.map((itemType, index) => (
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
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Child Items by Location
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Stacked by child item type
                      </Typography>
                      <Box sx={{ height: 400, mt: 2 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={childItemsChartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="location" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            {childItemTypes.map((itemType, index) => (
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

            {/* Inventory Tables - Parent and Child Items Detail */}
            {inventoryReport && (
              <Grid container spacing={3}>
                {/* Parent Items Detail Table */}
                {inventoryReport.parent_items_detail && inventoryReport.parent_items_detail.length > 0 && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Detailed Inventory Report - Parent Items
                        </Typography>
                        <TableContainer>
                          <Table>
                            <TableHead>
                              <TableRow>
                                <TableCell>Parent Item SKU</TableCell>
                                <TableCell>Item Type</TableCell>
                                <TableCell>Location</TableCell>
                                <TableCell>Location Type</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {inventoryReport.parent_items_detail.map((item) => (
                                <TableRow key={item.id}>
                                  <TableCell>{item.sku}</TableCell>
                                  <TableCell>{item.parent_item_type}</TableCell>
                                  <TableCell>{item.location_name}</TableCell>
                                  <TableCell>{item.location_type}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {/* Child Items Detail Table */}
                {inventoryReport.child_items_detail && inventoryReport.child_items_detail.length > 0 && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Detailed Inventory Report - Child Items
                        </Typography>
                        <TableContainer>
                          <Table>
                            <TableHead>
                              <TableRow>
                                <TableCell>Child Item SKU</TableCell>
                                <TableCell>Child Item Type</TableCell>
                                <TableCell>Parent Item SKU</TableCell>
                                <TableCell>Parent Item Type</TableCell>
                                <TableCell>Location</TableCell>
                                <TableCell>Location Type</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {inventoryReport.child_items_detail.map((item) => (
                                <TableRow key={item.id}>
                                  <TableCell>{item.sku}</TableCell>
                                  <TableCell>{item.child_item_type}</TableCell>
                                  <TableCell>{item.parent_item_sku}</TableCell>
                                  <TableCell>{item.parent_item_type}</TableCell>
                                  <TableCell>{item.location_name}</TableCell>
                                  <TableCell>{item.location_type}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>
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
                            {location.location_type?.name} - {location.name}
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