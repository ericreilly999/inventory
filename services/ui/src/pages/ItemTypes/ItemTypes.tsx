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
  Alert,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { apiService } from '../../services/api';

interface ItemType {
  id: string;
  name: string;
  description: string;
  category: string;
  created_at: string;
}

const ItemTypes: React.FC = () => {
  const [itemTypes, setItemTypes] = useState<ItemType[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItemType, setEditingItemType] = useState<ItemType | null>(null);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
  });

  const categories = ['parent', 'child'];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await apiService.get('/api/v1/items/types');
      setItemTypes(response.data);
    } catch (error) {
      setError('Failed to fetch item types data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItemType = () => {
    setEditingItemType(null);
    setFormData({
      name: '',
      description: '',
      category: '',
    });
    setDialogOpen(true);
  };

  const handleEditItemType = (itemType: ItemType) => {
    setEditingItemType(itemType);
    setFormData({
      name: itemType.name,
      description: itemType.description,
      category: itemType.category,
    });
    setDialogOpen(true);
  };

  const handleSaveItemType = async () => {
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        category: formData.category,
      };

      if (editingItemType) {
        await apiService.put(`/api/v1/items/types/${editingItemType.id}`, data);
      } else {
        await apiService.post('/api/v1/items/types', data);
      }

      setDialogOpen(false);
      fetchData();
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to save item type');
    }
  };

  const handleDeleteItemType = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this item type?')) return;

    try {
      await apiService.delete(`/api/v1/items/types/${id}`);
      fetchData();
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to delete item type');
    }
  };

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'description', headerName: 'Description', width: 300 },
    { field: 'category', headerName: 'Category', width: 150 },
    { field: 'created_at', headerName: 'Created', width: 150, type: 'dateTime' },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEditItemType(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteItemType(params.row.id)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Item Types</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddItemType}
        >
          Add Item Type
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={itemTypes}
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
          {editingItemType ? 'Edit Item Type' : 'Add Item Type'}
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
            <InputLabel>Category</InputLabel>
            <Select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            >
              {categories.map((category) => (
                <MenuItem key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveItemType} variant="contained">
            {editingItemType ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ItemTypes;