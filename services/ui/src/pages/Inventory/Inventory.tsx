import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
import DataGridFilters, { FilterConfig, FilterValue } from '../../components/DataGridFilters';

interface ParentItem {
  id: string;
  sku: string;
  description: string;
  item_type: { id: string; name: string };
  current_location: { id: string; name: string; location_type: { name: string } };
  created_at: string;
}

interface ChildItem {
  id: string;
  sku: string;
  description: string;
  item_type: { name: string };
  parent_item: { id: string; sku: string; item_type: { name: string } } | null;
  created_at: string;
}

interface ItemType {
  id: string;
  name: string;
}

interface ItemTypes {
  parent: ItemType[];
  child: ItemType[];
}

interface Location {
  id: string;
  name: string;
  location_type?: { name: string };
}

const Inventory: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [parentItems, setParentItems] = useState<ParentItem[]>([]);
  const [childItems, setChildItems] = useState<ChildItem[]>([]);
  const [itemTypes, setItemTypes] = useState<ItemTypes>({ parent: [], child: [] });
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [moveDialogOpen, setMoveDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [movingItem, setMovingItem] = useState<any>(null);
  const [movingChildItem, setMovingChildItem] = useState<any>(null);
  const { errorState, setError, clearError } = useApiError();
  const [parentFilters, setParentFilters] = useState<FilterValue[]>([]);
  const [childFilters, setChildFilters] = useState<FilterValue[]>([]);
  const [formData, setFormData] = useState({
    sku: '',
    description: '',
    item_type_id: '',
    current_location_id: '',
    parent_item_id: '',
  });

  const fetchData = useCallback(async () => {
    try {
      const [parentResponse, childResponse, parentTypesResponse, childTypesResponse, locationsResponse] = await Promise.all([
        apiService.get('/api/v1/items/parent'),
        apiService.get('/api/v1/items/child'),
        apiService.get('/api/v1/items/types?category=parent'),
        apiService.get('/api/v1/items/types?category=child'),
        apiService.get('/api/v1/locations/locations'),
      ]);

      setParentItems(parentResponse.data);
      setChildItems(childResponse.data);
      // Store both parent and child types separately
      setItemTypes({
        parent: parentTypesResponse.data,
        child: childTypesResponse.data,
      });
      setLocations(locationsResponse.data);
    } catch (error: any) {
      setError(error, {
        method: 'GET',
        endpoint: 'Multiple endpoints (parent, child, types, locations)',
      });
    } finally {
      setLoading(false);
    }
  }, [setError]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter configurations
  const parentFilterConfigs: FilterConfig[] = useMemo(() => [
    { field: 'sku', label: 'SKU', type: 'text' },
    {
      field: 'item_type',
      label: 'Item Type',
      type: 'select',
      options: itemTypes.parent.map((type) => ({ value: type.name, label: type.name })),
    },
    {
      field: 'location_type',
      label: 'Location Type',
      type: 'select',
      options: Array.from(new Set(locations.map((loc) => loc.location_type?.name).filter(Boolean)))
        .map((name) => ({ value: name!, label: name! })),
    },
    {
      field: 'location',
      label: 'Location',
      type: 'select',
      options: locations.map((loc) => ({ value: loc.name, label: loc.name })),
    },
  ], [itemTypes.parent, locations]);

  const childFilterConfigs: FilterConfig[] = useMemo(() => [
    { field: 'sku', label: 'SKU', type: 'text' },
    {
      field: 'item_type',
      label: 'Item Type',
      type: 'select',
      options: itemTypes.child.map((type) => ({ value: type.name, label: type.name })),
    },
    {
      field: 'parent_item_type',
      label: 'Parent Item Type',
      type: 'select',
      options: itemTypes.parent.map((type) => ({ value: type.name, label: type.name })),
    },
    {
      field: 'parent_item',
      label: 'Parent Item',
      type: 'select',
      options: parentItems.map((item) => ({ value: item.sku, label: item.sku })),
    },
  ], [itemTypes.child, itemTypes.parent, parentItems]);

  // Apply filters to data
  const filteredParentItems = useMemo(() => {
    if (parentFilters.length === 0) return parentItems;

    return parentItems.filter((item) => {
      return parentFilters.every((filter) => {
        const value = filter.value.toLowerCase();
        
        switch (filter.field) {
          case 'sku':
            return item.sku.toLowerCase().includes(value);
          case 'item_type':
            return item.item_type?.name === filter.value;
          case 'location_type':
            return item.current_location?.location_type?.name === filter.value;
          case 'location':
            return item.current_location?.name === filter.value;
          default:
            return true;
        }
      });
    });
  }, [parentItems, parentFilters]);

  const filteredChildItems = useMemo(() => {
    if (childFilters.length === 0) return childItems;

    return childItems.filter((item) => {
      return childFilters.every((filter) => {
        const value = filter.value.toLowerCase();
        
        switch (filter.field) {
          case 'sku':
            return item.sku.toLowerCase().includes(value);
          case 'item_type':
            return item.item_type?.name === filter.value;
          case 'parent_item_type':
            return item.parent_item?.item_type?.name === filter.value;
          case 'parent_item':
            return item.parent_item?.sku === filter.value;
          default:
            return true;
        }
      });
    });
  }, [childItems, childFilters]);

  const handleAddItem = () => {
    setEditingItem(null);
    setFormData({
      sku: '',
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
      sku: item.sku,
      description: item.description,
      item_type_id: item.item_type?.id || '',
      current_location_id: item.current_location?.id || '',
      parent_item_id: item.parent_item?.id || '',
    });
    setDialogOpen(true);
  };

  const handleMoveItem = (item: ParentItem) => {
    setMovingItem(item);
    setMovingChildItem(null);
    setFormData({ ...formData, current_location_id: '', parent_item_id: '' });
    setMoveDialogOpen(true);
  };

  const handleMoveChildItem = (item: ChildItem) => {
    setMovingChildItem(item);
    setMovingItem(null);
    setFormData({ ...formData, current_location_id: '', parent_item_id: '' });
    setMoveDialogOpen(true);
  };

  const handleSaveItem = async () => {
    const endpoint = tabValue === 0 ? '/api/v1/items/parent' : '/api/v1/items/child';
    const data = tabValue === 0 
      ? {
          sku: formData.sku,
          description: formData.description,
          item_type_id: formData.item_type_id,
          current_location_id: formData.current_location_id,
        }
      : {
          sku: formData.sku,
          description: formData.description,
          item_type_id: formData.item_type_id,
          parent_item_id: formData.parent_item_id,
        };

    try {
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
    try {
      if (movingItem) {
        // Moving a parent item to a new location
        const payload = {
          item_id: movingItem.id,
          to_location_id: formData.current_location_id,
          notes: 'Moved via UI',
        };
        await apiService.post(`/api/v1/movements/move`, payload);
      } else if (movingChildItem) {
        // Moving a child item to a new parent (which changes its location)
        await apiService.post(
          `/api/v1/items/child/${movingChildItem.id}/move?new_parent_id=${formData.parent_item_id}&notes=Moved via UI`
        );
      }

      setMoveDialogOpen(false);
      fetchData();
    } catch (error: any) {
      setError(error, {
        method: 'POST',
        endpoint: movingItem ? '/api/v1/movements/move' : `/api/v1/items/child/${movingChildItem?.id}/move`,
        requestPayload: movingItem ? {
          item_id: movingItem.id,
          to_location_id: formData.current_location_id,
          notes: 'Moved via UI',
        } : { new_parent_id: formData.parent_item_id },
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
    { field: 'sku', headerName: 'SKU', width: 200 },
    { 
      field: 'item_type', 
      headerName: 'Type', 
      width: 150,
      valueGetter: (params) => params.row.item_type?.name || '',
    },
    { 
      field: 'location_type', 
      headerName: 'Location Type', 
      width: 150,
      valueGetter: (params) => params.row.current_location?.location_type?.name || '',
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
    { field: 'sku', headerName: 'SKU', width: 200 },
    { 
      field: 'item_type', 
      headerName: 'Type', 
      width: 150,
      valueGetter: (params) => params.row.item_type?.name || '',
    },
    { 
      field: 'parent_item_type', 
      headerName: 'Parent Item Type', 
      width: 150,
      valueGetter: (params) => params.row.parent_item?.item_type?.name || 'N/A',
    },
    { 
      field: 'parent_item', 
      headerName: 'Parent Item', 
      width: 150,
      valueGetter: (params) => params.row.parent_item?.sku || 'Unassigned',
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
          onClick={() => handleMoveChildItem(params.row)}
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
          message={errorState.message}
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

      {tabValue === 0 ? (
        <DataGridFilters
          filters={parentFilterConfigs}
          activeFilters={parentFilters}
          onFilterChange={setParentFilters}
        />
      ) : (
        <DataGridFilters
          filters={childFilterConfigs}
          activeFilters={childFilters}
          onFilterChange={setChildFilters}
        />
      )}

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={tabValue === 0 ? filteredParentItems : filteredChildItems}
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
            label="SKU"
            fullWidth
            variant="outlined"
            value={formData.sku}
            onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
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
              {(tabValue === 0 ? itemTypes.parent : itemTypes.child).map((type) => (
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
                    {item.item_type.name} - {item.sku}
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
        <DialogTitle>
          {movingItem ? `Move Parent Item: ${movingItem?.sku}` : `Move Child Item: ${movingChildItem?.sku}`}
        </DialogTitle>
        <DialogContent>
          {movingItem ? (
            <FormControl fullWidth margin="dense">
              <InputLabel>New Location</InputLabel>
              <Select
                value={formData.current_location_id}
                onChange={(e) => setFormData({ ...formData, current_location_id: e.target.value })}
              >
                {locations.map((location) => (
                  <MenuItem key={location.id} value={location.id}>
                    {location.location_type?.name} - {location.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Moving a child item will reassign it to a different parent item, which changes its location.
              </Typography>
              <FormControl fullWidth margin="dense">
                <InputLabel>New Parent Item</InputLabel>
                <Select
                  value={formData.parent_item_id}
                  onChange={(e) => setFormData({ ...formData, parent_item_id: e.target.value })}
                >
                  {parentItems
                    .filter(item => item.id !== movingChildItem?.parent_item?.id)
                    .map((item) => (
                      <MenuItem key={item.id} value={item.id}>
                        {item.item_type.name} - {item.sku} (at {item.current_location.name})
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </>
          )}
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