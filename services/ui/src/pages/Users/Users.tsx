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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { apiService } from '../../services/api';
import { getErrorMessage } from '../../utils/errorHandler';
import DataGridFilters, { FilterConfig, FilterValue } from '../../components/DataGridFilters';

interface User {
  id: string;
  username: string;
  email: string;
  role: { id: string; name: string };
  active: boolean;
  created_at: string;
}

interface Role {
  id: string;
  name: string;
}

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<FilterValue[]>([]);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role_id: '',
    active: true,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const filterConfigs: FilterConfig[] = useMemo(() => [
    { field: 'username', label: 'Username', type: 'text' },
    { field: 'email', label: 'Email', type: 'text' },
    {
      field: 'role',
      label: 'Role',
      type: 'select',
      options: roles.map((role) => ({ value: role.name, label: role.name })),
    },
    { field: 'active', label: 'Active', type: 'boolean' },
  ], [roles]);

  const filteredUsers = useMemo(() => {
    if (filters.length === 0) return users;

    return users.filter((user) => {
      return filters.every((filter) => {
        switch (filter.field) {
          case 'username':
            return user.username.toLowerCase().includes(filter.value.toLowerCase());
          case 'email':
            return user.email.toLowerCase().includes(filter.value.toLowerCase());
          case 'role':
            return user.role?.name === filter.value;
          case 'active':
            return user.active === (filter.value === 'true');
          default:
            return true;
        }
      });
    });
  }, [users, filters]);

  const fetchData = async () => {
    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        apiService.get('/api/v1/users'),
        apiService.get('/api/v1/roles'),
      ]);

      setUsers(usersResponse.data);
      setRoles(rolesResponse.data);
      setError('');
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to fetch users data'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      role_id: '',
      active: true,
    });
    setDialogOpen(true);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      role_id: user.role?.id || '',
      active: user.active,
    });
    setDialogOpen(true);
  };

  const handleSaveUser = async () => {
    try {
      // Validate required fields
      if (!formData.username || !formData.email || !formData.role_id) {
        setError('Please fill in all required fields');
        return;
      }

      if (!editingUser && !formData.password) {
        setError('Password is required for new users');
        return;
      }

      const data: any = {
        username: formData.username,
        email: formData.email,
        role_id: formData.role_id,
        active: formData.active,
      };

      if (formData.password) {
        data.password = formData.password;
      }

      if (editingUser) {
        await apiService.put(`/api/v1/users/${editingUser.id}`, data);
      } else {
        await apiService.post('/api/v1/users', data);
      }

      setDialogOpen(false);
      setError('');
      fetchData();
    } catch (error: any) {
      setError(getErrorMessage(error, 'Failed to save user'));
    }
  };

  const handleDeleteUser = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;

    try {
      await apiService.delete(`/api/v1/users/${id}`);
      setError('');
      fetchData();
    } catch (error: any) {
      setError(getErrorMessage(error, 'Failed to delete user'));
    }
  };

  const columns: GridColDef[] = [
    { field: 'username', headerName: 'Username', width: 150 },
    { field: 'email', headerName: 'Email', width: 200 },
    { 
      field: 'role', 
      headerName: 'Role', 
      width: 150,
      valueGetter: (params) => params.row.role?.name || '',
    },
    { 
      field: 'active', 
      headerName: 'Active', 
      width: 100,
      type: 'boolean',
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
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEditUser(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteUser(params.row.id)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddUser}
        >
          Add User
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
          rows={filteredUsers}
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
          {editingUser ? 'Edit User' : 'Add User'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Username"
            fullWidth
            variant="outlined"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            variant="outlined"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <TextField
            margin="dense"
            label={editingUser ? 'New Password (leave blank to keep current)' : 'Password'}
            type="password"
            fullWidth
            variant="outlined"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required={!editingUser}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Role</InputLabel>
            <Select
              value={formData.role_id}
              onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
            >
              {roles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={formData.active}
                onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveUser} variant="contained">
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Users;