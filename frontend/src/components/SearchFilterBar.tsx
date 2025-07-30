import React, { useState } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Paper,
} from '@mui/material';
import { Search, FilterList, Clear, Download } from '@mui/icons-material';

interface FilterOption {
  label: string;
  value: string;
}

interface SearchFilterBarProps {
  onSearch: (query: string) => void;
  onFilter: (filters: Record<string, any>) => void;
  onExport: () => void;
  searchPlaceholder?: string;
  filterOptions?: {
    [key: string]: FilterOption[];
  };
  showExport?: boolean;
}

export default function SearchFilterBar({
  onSearch,
  onFilter,
  onExport,
  searchPlaceholder = "Search...",
  filterOptions = {},
  showExport = true,
}: SearchFilterBarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const query = event.target.value;
    setSearchQuery(query);
    onSearch(query);
  };

  const handleFilterChange = (filterKey: string, value: any) => {
    const newFilters = { ...filters, [filterKey]: value };
    setFilters(newFilters);
    onFilter(newFilters);
  };

  const clearFilters = () => {
    setFilters({});
    setSearchQuery('');
    onFilter({});
    onSearch('');
  };

  const hasActiveFilters = Object.keys(filters).length > 0 || searchQuery.length > 0;

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* Search Bar */}
        <TextField
          size="small"
          placeholder={searchPlaceholder}
          value={searchQuery}
          onChange={handleSearch}
          InputProps={{
            startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ minWidth: 250 }}
        />

        {/* Filter Toggle */}
        <Tooltip title="Advanced Filters">
          <IconButton
            onClick={() => setShowFilters(!showFilters)}
            color={showFilters ? 'primary' : 'default'}
          >
            <FilterList />
          </IconButton>
        </Tooltip>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <Tooltip title="Clear All Filters">
            <IconButton onClick={clearFilters} color="error">
              <Clear />
            </IconButton>
          </Tooltip>
        )}

        {/* Export Button */}
        {showExport && (
          <Tooltip title="Export Data">
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={onExport}
              size="small"
            >
              Export
            </Button>
          </Tooltip>
        )}

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {searchQuery && (
              <Chip
                label={`Search: "${searchQuery}"`}
                onDelete={() => {
                  setSearchQuery('');
                  onSearch('');
                }}
                size="small"
              />
            )}
            {Object.entries(filters).map(([key, value]) => (
              <Chip
                key={key}
                label={`${key}: ${value}`}
                onDelete={() => handleFilterChange(key, '')}
                size="small"
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Advanced Filters */}
      {showFilters && (
        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(auto-fit, minmax(200px, 1fr))' }, gap: 2 }}>
            {Object.entries(filterOptions).map(([filterKey, options]) => (
              <FormControl key={filterKey} size="small" fullWidth>
                <InputLabel>{filterKey}</InputLabel>
                <Select
                  value={filters[filterKey] || ''}
                  label={filterKey}
                  onChange={(e) => handleFilterChange(filterKey, e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  {options.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ))}
          </Box>
        </Box>
      )}
    </Paper>
  );
} 