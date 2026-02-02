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
  Alert,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Paper,
  Grid,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { apiService } from '../../services/api';
import { getErrorMessage } from '../../utils/errorHandler';

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Record<string, boolean>;
  created_at: string;
}

interface PermissionGroup {
  service: string;
  label: string;
  permissions: {
    key: string;
    label: string;
  }[];
}

const permissionGroups: PermissionGroup[] = [
  {
    service: 'inventory',
    label: 'Inventory Service',
    permissions: [
      { key: 'inventory:read', label: 'Read' },
      { key: 'inventory:write', label: 'Write' },
      { key: 'inventory:delete', label: 'Delete' },
    ],
  },
  {
    service: 'location',
    label: 'Location Service',
    permissions: [
      { key: 'location:read', label: 'Read' },
      { key: 'location:write', label: 'Write' },
      { key: 'location:delete', label: 'Delete' },
    ],
  },
  {
    service: 'reporting',
    label: 'Reporting Service',
    permissions: [
      { key: 'reporting:read', label: 'Read' },
    ],
  },
  {
    service: 'user',
    label: 'User Management',
    permissions: [
      { key: 'user:read', label: 'Read' },
      { key: 'user:write', label: 'Write' },
      { key: 'user:delete', label: 'Delete' },
      { key: 'user:admin', label: 'Admin' },
    ],
  },
  {
    service: 'role',
    label: 'Role Management',
    permissions: [
      { key: 'role:admin', label: 'Admin' },
    ],
  },
];

const Roles: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: {} as Record<string, boolean>,
  });

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      const response = await apiService.get('/api/v1/roles');
      setRoles(response.data);
      setError('');
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to fetch roles'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddRole = () => {
    setEditingRole(null);
    const defaultPermissions: Record<string, boolean> = {};
    permissionGroups.forEach(group => {
      group.permissions.forEach(perm => {
        defaultPermissions[perm.key] = false;
      });
    });
    setFormData({
      name: '',
      description: '',
      permissions: defaultPermissions,
    });
    setDialogOpen(true);
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
    const permissions: Record<string, boolean> = {};
    permissionGroups.forEach(group => {
      group.permissions.forEach(perm => {
        permissions[perm.key] = role.permissions[perm.key] || false;
      });
    });
    setFormData({
      name: role.name,
      description: role.description || '',
      permissions: permissions,
    });
    setDialogOpen(true);
  };

  const handleSaveRole = async () => {
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        permissions: formData.permissions,
      };

      if (editingRole) {
        await apiService.put(`/api/v1/roles/${editingRole.id}`, data);
      } else {
        await apiService.post('/api/v1/roles', data);
      }

      setDialogOpen(false);
      fetchRoles();
      setError('');
    } catch (error: any) {
      setError(getErrorMessage(error, 'Failed to save role'));
    }
  };

  const handleDeleteRole = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this role?')) return;

    try {
      await apiService.delete(`/api/v1/roles/${id}`);
      fetchRoles();
      setError('');
    } catch (error: any) {
      setError(getErrorMessage(error, 'Failed to delete role'));
    }
  };

  const handlePermissionChange = (key: string, checked: boolean) => {
    setFormData({
      ...formData,
      permissions: {
        ...formData.permissions,
        [key]: checked,
      },
    });
  };

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'Role Name', width: 200 },
    { field: 'description', headerName: 'Description', width: 300 },
    {
      field: 'permissions',
      headerName: 'Permissions',
      width: 300,
      valueGetter: (params) => {
        const perms = params.row.permissions;
        if (perms['*']) return 'Full Access';
        const activePerms = Object.entries(perms)
          .filter(([_, value]) => value === true)
          .map(([key, _]) => key);
        return activePerms.length > 0 ? `${activePerms.length} permissions` : 'No permissions';
      },
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
          onClick={() => handleEditRole(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteRole(params.row.id)}
          disabled={params.row.name === 'admin'}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Role Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddRole}
        >
          Add Role
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={roles}
          columns={columns}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
        />
      </Box>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingRole ? 'Edit Role' : 'Add Role'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Role Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            disabled={editingRole?.name === 'admin'}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            variant="outlined"
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
            Permissions
          </Typography>

          <Grid container spacing={2}>
            {permissionGroups.map((group) => (
              <Grid item xs={12} sm={6} key={group.service}>
                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    {group.label}
                  </Typography>
                  <FormGroup>
                    {group.permissions.map((perm) => (
                      <FormControlLabel
                        key={perm.key}
                        control={
                          <Checkbox
                            checked={formData.permissions[perm.key] || false}
                            onChange={(e) => handlePermissionChange(perm.key, e.target.checked)}
                          />
                        }
                        label={perm.label}
                      />
                    ))}
                  </FormGroup>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveRole} variant="contained">
            {editingRole ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Roles;
