import React, { useState, useMemo } from 'react';
import { DataGrid, GridColDef, GridFilterModel, GridSortModel } from '@mui/x-data-grid';
import { Box, Typography, Button, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import { Download, FilterList, Search, Sort } from '@mui/icons-material';
import { exportData } from '../utils/exportUtils';

interface AdvancedDataGridProps {
  rows: any[];
  columns: GridColDef[];
  loading?: boolean;
  title?: string;
  searchable?: boolean;
  filterable?: boolean;
  exportable?: boolean;
  searchFields?: string[];
  filterOptions?: {
    [key: string]: { label: string; value: string }[];
  };
}

export default function AdvancedDataGrid({
  rows,
  columns,
  loading = false,
  title,
  searchable = true,
  filterable = true,
  exportable = true,
  searchFields = [],
  filterOptions = {},
}: AdvancedDataGridProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [filterModel, setFilterModel] = useState<GridFilterModel>({ items: [] });
  const [sortModel, setSortModel] = useState<GridSortModel>([]);
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);

  // Filter and search data
  const filteredRows = useMemo(() => {
    let filtered = rows;

    // Apply search
    if (searchQuery && searchFields.length > 0) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(row =>
        searchFields.some(field => {
          const value = row[field];
          return value && value.toString().toLowerCase().includes(query);
        })
      );
    }

    // Apply custom filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(row => row[key] === value);
      }
    });

    return filtered;
  }, [rows, searchQuery, filters, searchFields]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilter = (newFilters: Record<string, any>) => {
    setFilters(newFilters);
  };

  const handleExport = (format: 'csv' | 'json' | 'excel') => {
    const filename = title ? `${title.toLowerCase().replace(/\s+/g, '_')}_export` : 'data_export';
    exportData(filteredRows, { filename, format });
    setExportAnchorEl(null);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setFilters({});
    setFilterModel({ items: [] });
  };

  const hasActiveFilters = searchQuery || Object.keys(filters).length > 0 || filterModel.items.length > 0;

  return (
    <Box>
      {/* Header with title and actions */}
      {(title || searchable || filterable || exportable) && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          {title && <Typography variant="h6">{title}</Typography>}
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            {/* Search */}
            {searchable && (
              <Button
                size="small"
                startIcon={<Search />}
                onClick={() => {/* Toggle search */}}
                variant={searchQuery ? 'contained' : 'outlined'}
              >
                Search
              </Button>
            )}

            {/* Filters */}
            {filterable && (
              <Button
                size="small"
                startIcon={<FilterList />}
                onClick={() => {/* Toggle filters */}}
                variant={hasActiveFilters ? 'contained' : 'outlined'}
              >
                Filters
              </Button>
            )}

            {/* Export */}
            {exportable && (
              <>
                <Button
                  size="small"
                  startIcon={<Download />}
                  onClick={(e) => setExportAnchorEl(e.currentTarget)}
                  variant="outlined"
                >
                  Export
                </Button>
                <Menu
                  anchorEl={exportAnchorEl}
                  open={Boolean(exportAnchorEl)}
                  onClose={() => setExportAnchorEl(null)}
                >
                  <MenuItem onClick={() => handleExport('csv')}>
                    <ListItemIcon><Download fontSize="small" /></ListItemIcon>
                    <ListItemText>Export as CSV</ListItemText>
                  </MenuItem>
                  <MenuItem onClick={() => handleExport('excel')}>
                    <ListItemIcon><Download fontSize="small" /></ListItemIcon>
                    <ListItemText>Export as Excel</ListItemText>
                  </MenuItem>
                  <MenuItem onClick={() => handleExport('json')}>
                    <ListItemIcon><Download fontSize="small" /></ListItemIcon>
                    <ListItemText>Export as JSON</ListItemText>
                  </MenuItem>
                </Menu>
              </>
            )}

            {/* Clear filters */}
            {hasActiveFilters && (
              <Button
                size="small"
                onClick={clearFilters}
                variant="outlined"
                color="error"
              >
                Clear All
              </Button>
            )}
          </Box>
        </Box>
      )}

      {/* DataGrid */}
      <DataGrid
        rows={filteredRows}
        columns={columns}
        autoHeight
        loading={loading}
        filterModel={filterModel}
        onFilterModelChange={setFilterModel}
        sortModel={sortModel}
        onSortModelChange={setSortModel}
        initialState={{
          pagination: {
            paginationModel: { page: 0, pageSize: 10 },
          },
        }}
        pageSizeOptions={[10, 25, 50, 100]}
        disableRowSelectionOnClick
        sx={{
          '& .MuiDataGrid-cell:focus': {
            outline: 'none',
          },
        }}
      />

      {/* Results summary */}
      <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredRows.length} of {rows.length} records
          {hasActiveFilters && ' (filtered)'}
        </Typography>
      </Box>
    </Box>
  );
} 