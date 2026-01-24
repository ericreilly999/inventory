import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, MoveUp as MoveIcon } from '@mui/icons-material';
import { apiService } from '../../services/api';
import ErrorDetails from '../../components/ErrorDetails';
import { useApiError } from '../../hooks/useApiError';

interface ParentItem {
  id: string;
  name: string;
  description: string;
  item_type: { name: string };
  current_location: { name: string };
  created_at: string;
}

interface ChildItem {
  id: string;
  name: string;
  description: string;
  item_type: { name: string };
  parent_item: { name: string } | null;
  created_at: string;
}

interface ItemType {
  id: string;
  name: string;
}

interface Location {
  id: string;
  name: string;
}

const Inventory: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [parentItems, setParentItems] = useState<ParentItem[]>([]);
  const [childItems, setChildItems] = useState<ChildItem[]>([]);
  const [itemTypes, setItemTypes] = useState<ItemType[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [moveDialogOpen, setMoveDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [movingItem, setMovingItem] = useState<any>(null);
  const { errorState, setError, clearError } = useApiError();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    item_type_id: '',
    current_location_id: '',
    parent_item_id: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [parentResponse, childResponse, typesResponse, locationsResponse] = await Promise.all([
        apiService.get('/api/v1/items/parent'),
        apiService.get('/api/v1/items/child'),
        apiService.get('/api/v1/items/types'),
        apiService.get('/api/v1/locations/locations'),
      ]);

      setParentItems(parentResponse.data);
      setChildItems(childResponse.data);
      setItemTypes(typesResponse.data);
      setLocations(locationsResponse.data);
    } catch (error: any) {
      setError(error, {
        method: 'GET',
        endpoint: 'Multiple endpoints (parent, child, types, locations)',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    setEditingItem(null);
    setFormData({
      name: '',
      description: '',
      item_type_id: '',
      current_location_id: '',
      parent_item_id: '',
    });
    setDialogOpen(true);
  };

  const handleEditItem = (item: any) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      description: item.description,
      item_type_id: item.item_type?.id || '',
      current_location_id: item.current_location?.id || '',
      parent_item_id: item.parent_item?.id || '',
    });
    setDialogOpen(true);
  };

  const handleMoveItem = (item: ParentItem) => {
    setMovingItem(item);
    setMoveDialogOpen(true);
  };

  const handleSaveItem = async () => {
    try {
      const endpoint = tabValue === 0 ? '/api/v1/items/parent' : '/api/v1/items/child';
      const data = tabValue === 0 
        ? {
            name: formData.name,
            description: formData.description,
            item_type_id: formData.item_type_id,
            current_location_id: formData.current_location_id,
          }
        : {
            name: formData.name,
            description: formData.description,
            item_type_id: formData.item_type_id,
            parent_item_id: formData.parent_item_id,
          };

      if (editingItem) {
        await apiService.put(`${endpoint}/${editingItem.id}`, data);
      } else {
        await apiService.post(endpoint, data);
      }

      setDialogOpen(false);
      fetchData();
    } catch (error: any) {
      setError(error, {
        method: editingItem ? 'PUT' : 'POST',
        endpoint: editingItem ? `${endpoint}/${editingItem.id}` : endpoint,
        requestPayload: data,
      });
    }
  };

  const handleMoveItemSubmit = async () => {
    const payload = {
      item_id: movingItem.id,
      to_location_id: formData.current_location_id,
      notes: 'Moved via UI',
    };
    
    try {
      await apiService.post(`/api/v1/movements/move`, payload);

      setMoveDialogOpen(false);
      fetchData();
    } catch (error: any) {
      setError(error, {
        method: 'POST',
        endpoint: '/api/v1/movements/move',
        requestPayload: payload,
      });
    }
  };

  const handleDeleteItem = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;

    try {
      const endpoint = tabValue === 0 ? '/api/v1/items/parent' : '/api/v1/items/child';
      await apiService.delete(`${endpoint}/${id}`);
      fetchData();
    } catch (error: any) {
      setError(error, {
        method: 'DELETE',
        endpoint: `${tabValue === 0 ? '/api/v1/items/parent' : '/api/v1/items/child'}/${id}`,
      });
    }
  };

  const parentColumns: GridColDef[] = [
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'description', headerName: 'Description', width: 250 },
    { 
      field: 'item_type', 
      headerName: 'Type', 
      width: 150,
      valueGetter: (params) => params.row.item_type?.name || '',
    },
    { 
      field: 'current_location', 
      headerName: 'Location', 
      width: 150,
      valueGetter: (params) => params.row.current_location?.name || '',
    },
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
      width: 150,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEditItem(params.row)}
        />,
        <GridActionsCellItem
          icon={<MoveIcon />}
          label="Move"
          onClick={() => handleMoveItem(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteItem(params.row.id)}
        />,
      ],
    },
  ];

  const childColumns: GridColDef[] = [
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'description', headerName: 'Description', width: 250 },
    { 
      field: 'item_type', 
      headerName: 'Type', 
      width: 150,
      valueGetter: (params) => params.row.item_type?.name || '',
    },
    { 
      field: 'parent_item', 
      headerName: 'Parent Item', 
      width: 150,
      valueGetter: (params) => params.row.parent_item?.name || 'Unassigned',
    },
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
      width: 100,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEditItem(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteItem(params.row.id)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Inventory Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddItem}
        >
          Add {tabValue === 0 ? 'Parent' : 'Child'} Item
        </Button>
      </Box>

      {errorState && (
        <ErrorDetails
          error={errorState.error}
          requestPayload={errorState.requestPayload}
          endpoint={errorState.endpoint}
          method={errorState.method}
          onClose={clearError}
        />
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
        <Tab label="Parent Items" />
        <Tab label="Child Items" />
      </Tabs>

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={tabValue === 0 ? parentItems : childItems}
          columns={tabValue === 0 ? parentColumns : childColumns}
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
          {editingItem ? 'Edit' : 'Add'} {tabValue === 0 ? 'Parent' : 'Child'} Item
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
          <FormControl fullWidth margin="dense">
            <InputLabel>Item Type</InputLabel>
            <Select
              value={formData.item_type_id}
              onChange={(e) => setFormData({ ...formData, item_type_id: e.target.value })}
            >
              {itemTypes.map((type) => (
                <MenuItem key={type.id} value={type.id}>
                  {type.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {tabValue === 0 ? (
            <FormControl fullWidth margin="dense">
              <InputLabel>Location</InputLabel>
              <Select
                value={formData.current_location_id}
                onChange={(e) => setFormData({ ...formData, current_location_id: e.target.value })}
              >
                {locations.map((location) => (
                  <MenuItem key={location.id} value={location.id}>
                    {location.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : (
            <FormControl fullWidth margin="dense">
              <InputLabel>Parent Item</InputLabel>
              <Select
                value={formData.parent_item_id}
                onChange={(e) => setFormData({ ...formData, parent_item_id: e.target.value })}
              >
                <MenuItem value="">Unassigned</MenuItem>
                {parentItems.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveItem} variant="contained">
            {editingItem ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Move Dialog */}
      <Dialog open={moveDialogOpen} onClose={() => setMoveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Move Item: {movingItem?.name}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>New Location</InputLabel>
            <Select
              value={formData.current_location_id}
              onChange={(e) => setFormData({ ...formData, current_location_id: e.target.value })}
            >
              {locations.map((location) => (
                <MenuItem key={location.id} value={location.id}>
                  {location.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMoveDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleMoveItemSubmit} variant="contained">
            Move Item
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Inventory;