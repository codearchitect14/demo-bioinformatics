import React, { useEffect, useState, useMemo } from 'react';
import { Box, Typography, Card, CardContent, Chip, LinearProgress } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { fetchVariantPrioritization } from '../api';
import SearchFilterBar from '../components/SearchFilterBar';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'variant_id', headerName: 'Variant ID', width: 150 },
  { field: 'gene', headerName: 'Gene', width: 120 },
  { field: 'disease', headerName: 'Disease', width: 150 },
  { field: 'prioritization_score', headerName: 'Priority Score', width: 140, type: 'number' },
  { field: 'clinical_significance', headerName: 'Clinical Significance', width: 150 },
  { 
    field: 'priority_level', 
    headerName: 'Priority Level', 
    width: 130,
    renderCell: (params) => (
      <Chip 
        label={params.value} 
        color={params.value === 'High' ? 'error' : params.value === 'Medium' ? 'warning' : 'success'}
        size="small"
      />
    )
  },
  { field: 'patient_id', headerName: 'Patient ID', width: 120 },
  { field: 'inheritance_pattern', headerName: 'Inheritance', width: 120 },
];

const COLORS = ['#ff0000', '#ffa500', '#00ff00', '#0000ff'];

export default function VariantPrioritizationTab() {
  const [variants, setVariants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchVariantPrioritization()
      .then((data) => {
        setVariants(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Filter and search variants
  const filteredVariants = useMemo(() => {
    let filtered = variants;

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(variant =>
        variant.gene?.toLowerCase().includes(query) ||
        variant.disease?.toLowerCase().includes(query) ||
        variant.patient_id?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(variant => variant[key] === value);
      }
    });

    return filtered;
  }, [variants, searchQuery, filters]);

  // Filter options
  const filterOptions = {
    priority_level: [
      { label: 'High Priority', value: 'High' },
      { label: 'Medium Priority', value: 'Medium' },
      { label: 'Low Priority', value: 'Low' },
    ],
    clinical_significance: [
      { label: 'Pathogenic', value: 'Pathogenic' },
      { label: 'Likely Pathogenic', value: 'Likely Pathogenic' },
      { label: 'VUS', value: 'VUS' },
      { label: 'Likely Benign', value: 'Likely Benign' },
      { label: 'Benign', value: 'Benign' },
    ],
    inheritance_pattern: [
      { label: 'Autosomal Dominant', value: 'AD' },
      { label: 'Autosomal Recessive', value: 'AR' },
      { label: 'X-linked', value: 'XL' },
    ],
  };

  // Summary statistics
  const totalVariants = filteredVariants.length;
  const highPriority = filteredVariants.filter(v => v.priority_level === 'High').length;
  const mediumPriority = filteredVariants.filter(v => v.priority_level === 'Medium').length;
  const lowPriority = filteredVariants.filter(v => v.priority_level === 'Low').length;
  
  const avgScore = filteredVariants.length > 0 
    ? (filteredVariants.reduce((sum, v) => sum + (v.prioritization_score || 0), 0) / filteredVariants.length).toFixed(2)
    : 0;

  // Chart data
  const priorityData = [
    { name: 'High Priority', value: highPriority },
    { name: 'Medium Priority', value: mediumPriority },
    { name: 'Low Priority', value: lowPriority },
  ];

  const scoreData = filteredVariants
    .sort((a, b) => (b.prioritization_score || 0) - (a.prioritization_score || 0))
    .slice(0, 10)
    .map(v => ({ 
      gene: v.gene || 'Unknown', 
      score: v.prioritization_score || 0 
    }));

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilter = (newFilters: Record<string, any>) => {
    setFilters(newFilters);
  };

  const handleExport = () => {
    // CSV export
    const csvContent = [
      ['ID', 'Variant ID', 'Gene', 'Disease', 'Priority Score', 'Clinical Significance', 'Priority Level', 'Patient ID', 'Inheritance'],
      ...filteredVariants.map(v => [
        v.id,
        v.variant_id,
        v.gene,
        v.disease,
        v.prioritization_score,
        v.clinical_significance,
        v.priority_level,
        v.patient_id,
        v.inheritance_pattern,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'variant_prioritization_export.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Variant Prioritization for Rare Disease</Typography>
      
      {/* Search and Filter Bar */}
      <SearchFilterBar
        onSearch={handleSearch}
        onFilter={handleFilter}
        onExport={handleExport}
        searchPlaceholder="Search variants by gene, disease, or patient ID..."
        filterOptions={filterOptions}
      />
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="primary">Total Variants</Typography>
            <Typography variant="h4">{totalVariants}</Typography>
            {searchQuery || Object.keys(filters).length > 0 && (
              <Typography variant="body2" color="text.secondary">
                (Filtered from {variants.length} total)
              </Typography>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="error.main">High Priority</Typography>
            <Typography variant="h4">{highPriority}</Typography>
            <LinearProgress 
              variant="determinate" 
              value={(highPriority / totalVariants) * 100} 
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="warning.main">Medium Priority</Typography>
            <Typography variant="h4">{mediumPriority}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary">Avg Priority Score</Typography>
            <Typography variant="h4">{avgScore}</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Priority Level Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Top 10 Variants by Priority Score</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreData}>
                <XAxis dataKey="gene" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                
                <Bar dataKey="score" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Variant Prioritization Results</Typography>
          <DataGrid
            rows={filteredVariants}
            columns={columns}
            autoHeight
            loading={loading}
            initialState={{
              pagination: {
                paginationModel: { page: 0, pageSize: 10 },
              },
            }}
            pageSizeOptions={[10, 25, 50]}
          />
        </CardContent>
      </Card>
    </Box>
  );
} 
