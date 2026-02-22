import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Button,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { apiService } from '../../services/api';
import DataGridFilters, { FilterConfig, FilterValue } from '../../components/DataGridFilters';

interface LocationType {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

const LocationTypes: React.FC = () => {
  const [locationTypes, setLocationTypes] = useState<LocationType[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLocationType, setEditingLocationType] = useState<LocationType | null>(null);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<FilterValue[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const filterConfigs: FilterConfig[] = useMemo(() => [
    { field: 'name', label: 'Name', type: 'text' },
  ], []);

  const filteredLocationTypes = useMemo(() => {
    if (filters.length === 0) return locationTypes;

    return locationTypes.filter((locationType) => {
      return filters.every((filter) => {
        if (filter.field === 'name') {
          return locationType.name.toLowerCase().includes(filter.value.toLowerCase());
        }
        return true;
      });
    });
  }, [locationTypes, filters]);

  const fetchData = async () => {
    try {
      const response = await apiService.get('/api/v1/locations/types');
      setLocationTypes(response.data);
    } catch (error) {
      setError('Failed to fetch location types data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLocationType = () => {
    setEditingLocationType(null);
    setFormData({
      name: '',
      description: '',
    });
    setDialogOpen(true);
  };

  const handleEditLocationType = (locationType: LocationType) => {
    setEditingLocationType(locationType);
    setFormData({
      name: locationType.name,
      description: locationType.description,
    });
    setDialogOpen(true);
  };

  const handleSaveLocationType = async () => {
    try {
      const data = {
        name: formData.name,
        description: formData.description,
      };

      if (editingLocationType) {
        await apiService.put(`/api/v1/locations/types/${editingLocationType.id}`, data);
      } else {
        await apiService.post('/api/v1/locations/types', data);
      }

      setDialogOpen(false);
      fetchData();
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to save location type');
    }
  };

  const handleDeleteLocationType = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this location type?')) return;

    try {
      await apiService.delete(`/api/v1/locations/types/${id}`);
      fetchData();
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to delete location type');
    }
  };

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'description', headerName: 'Description', width: 400 },
    { 
      field: 'created_at', 
      headerName: 'Created', 
      width: 150, 
      type: 'dateTime',
      valueGetter: (params) => params.row.created_at ? new Date(params.row.created_at) : null,
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEditLocationType(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteLocationType(params.row.id)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Location Types</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddLocationType}
        >
          Add Location Type
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <DataGridFilters
        filters={filterConfigs}
        activeFilters={filters}
        onFilterChange={setFilters}
      />

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={filteredLocationTypes}
          columns={columns}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
        />
      </Box>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingLocationType ? 'Edit Location Type' : 'Add Location Type'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveLocationType} variant="contained">
            {editingLocationType ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LocationTypes;