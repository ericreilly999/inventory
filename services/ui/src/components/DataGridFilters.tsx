import React from 'react';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip,
  Paper,
} from '@mui/material';
import { Clear as ClearIcon, FilterList as FilterIcon } from '@mui/icons-material';

export interface FilterConfig {
  field: string;
  label: string;
  type: 'text' | 'select' | 'boolean' | 'date';
  options?: { value: string; label: string }[];
}

export interface FilterValue {
  field: string;
  value: any;
}

interface DataGridFiltersProps {
  filters: FilterConfig[];
  activeFilters: FilterValue[];
  onFilterChange: (filters: FilterValue[]) => void;
}

const DataGridFilters: React.FC<DataGridFiltersProps> = ({
  filters,
  activeFilters,
  onFilterChange,
}) => {
  const handleFilterUpdate = (field: string, value: any) => {
    const existingFilterIndex = activeFilters.findIndex((f) => f.field === field);
    
    if (value === '' || value === null || value === undefined) {
      // Remove filter if value is empty
      if (existingFilterIndex !== -1) {
        const newFilters = [...activeFilters];
        newFilters.splice(existingFilterIndex, 1);
        onFilterChange(newFilters);
      }
    } else {
      // Add or update filter
      const newFilters = [...activeFilters];
      if (existingFilterIndex !== -1) {
        newFilters[existingFilterIndex] = { field, value };
      } else {
        newFilters.push({ field, value });
      }
      onFilterChange(newFilters);
    }
  };

  const handleClearAll = () => {
    onFilterChange([]);
  };

  const getFilterValue = (field: string) => {
    const filter = activeFilters.find((f) => f.field === field);
    return filter ? filter.value : '';
  };

  const renderFilter = (config: FilterConfig) => {
    const value = getFilterValue(config.field);

    switch (config.type) {
      case 'select':
        return (
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{config.label}</InputLabel>
            <Select
              value={value}
              label={config.label}
              onChange={(e) => handleFilterUpdate(config.field, e.target.value)}
            >
              <MenuItem value="">
                <em>All</em>
              </MenuItem>
              {config.options?.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'boolean':
        return (
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{config.label}</InputLabel>
            <Select
              value={value}
              label={config.label}
              onChange={(e) => handleFilterUpdate(config.field, e.target.value)}
            >
              <MenuItem value="">
                <em>All</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        );

      case 'text':
      default:
        return (
          <TextField
            size="small"
            label={config.label}
            value={value}
            onChange={(e) => handleFilterUpdate(config.field, e.target.value)}
            sx={{ minWidth: 150 }}
          />
        );
    }
  };

  return (
    <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
      <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
        <Box display="flex" alignItems="center" gap={1}>
          <FilterIcon color="action" />
          <strong>Filters:</strong>
        </Box>
        
        {filters.map((config) => (
          <Box key={config.field}>{renderFilter(config)}</Box>
        ))}

        {activeFilters.length > 0 && (
          <IconButton
            size="small"
            onClick={handleClearAll}
            title="Clear all filters"
            color="primary"
          >
            <ClearIcon />
          </IconButton>
        )}
      </Box>

      {activeFilters.length > 0 && (
        <Box display="flex" gap={1} mt={2} flexWrap="wrap">
          {activeFilters.map((filter) => {
            const config = filters.find((f) => f.field === filter.field);
            if (!config) return null;

            let displayValue = filter.value;
            if (config.type === 'select') {
              const option = config.options?.find((o) => o.value === filter.value);
              displayValue = option?.label || filter.value;
            } else if (config.type === 'boolean') {
              displayValue = filter.value === 'true' ? 'Yes' : 'No';
            }

            return (
              <Chip
                key={filter.field}
                label={`${config.label}: ${displayValue}`}
                onDelete={() => handleFilterUpdate(filter.field, '')}
                size="small"
                color="primary"
                variant="outlined"
              />
            );
          })}
        </Box>
      )}
    </Paper>
  );
};

export default DataGridFilters;
