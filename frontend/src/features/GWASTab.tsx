import React, { useEffect, useState, useMemo } from 'react';
import { Box, Typography, Card, CardContent, Chip } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { ResponsiveContainer, Scatter, CartesianGrid, XAxis, YAxis } from 'recharts';
import { fetchGWAS } from '../api';
import SearchFilterBar from '../components/SearchFilterBar';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'snp_id', headerName: 'SNP ID', width: 150 },
  { field: 'chromosome', headerName: 'Chromosome', width: 120 },
  { field: 'position', headerName: 'Position', width: 120 },
  { field: 'p_value', headerName: 'P-Value', width: 120, type: 'number' },
  { field: 'effect_size', headerName: 'Effect Size', width: 130, type: 'number' },
  { field: 'maf', headerName: 'MAF', width: 100, type: 'number' },
  { 
    field: 'significance', 
    headerName: 'Significance', 
    width: 130,
    renderCell: (params) => (
      <Chip 
        label={params.value} 
        color={params.value === 'Genome-wide' ? 'error' : params.value === 'Suggestive' ? 'warning' : 'default'}
        size="small"
      />
    )
  },
  { field: 'trait', headerName: 'Trait', width: 150 },
];

export default function GWASTab() {
  const [gwasData, setGwasData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchGWAS()
      .then((data) => {
        setGwasData(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Filter and search GWAS data
  const filteredGWAS = useMemo(() => {
    let filtered = gwasData;

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(snp =>
        snp.snp_id?.toLowerCase().includes(query) ||
        snp.trait?.toLowerCase().includes(query) ||
        snp.significance?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(snp => snp[key] === value);
      }
    });

    return filtered;
  }, [gwasData, searchQuery, filters]);

  // Filter options
  const filterOptions = {
    significance: [
      { label: 'Genome-wide Significant', value: 'Genome-wide' },
      { label: 'Suggestive', value: 'Suggestive' },
      { label: 'Not Significant', value: 'Not Significant' },
    ],
    chromosome: [
      { label: 'Chromosome 1', value: '1' },
      { label: 'Chromosome 2', value: '2' },
      { label: 'Chromosome X', value: 'X' },
    ],
  };

  // Summary statistics
  const totalSNPs = filteredGWAS.length;
  const genomeWideSignificant = filteredGWAS.filter(s => s.significance === 'Genome-wide').length;
  const suggestive = filteredGWAS.filter(s => s.significance === 'Suggestive').length;
  const avgEffectSize = filteredGWAS.length > 0 
    ? (filteredGWAS.reduce((sum, s) => sum + Math.abs(s.effect_size || 0), 0) / filteredGWAS.length).toFixed(3)
    : 0;

  // Manhattan plot data (simulated)
  const manhattanData = filteredGWAS.slice(0, 100).map((snp, index) => ({
    position: snp.position || index * 1000000,
    pValue: -Math.log10(snp.p_value || 0.05),
    chromosome: snp.chromosome || '1',
    significant: snp.significance === 'Genome-wide',
  }));

  // Q-Q plot data (simulated)
  const qqData = Array.from({ length: 100 }, (_, i) => ({
    expected: -Math.log10((i + 1) / 100),
    observed: -Math.log10(Math.random() * 0.1 + 0.001),
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
      ['ID', 'SNP ID', 'Chromosome', 'Position', 'P-Value', 'Effect Size', 'MAF', 'Significance', 'Trait'],
      ...filteredGWAS.map(s => [
        s.id,
        s.snp_id,
        s.chromosome,
        s.position,
        s.p_value,
        s.effect_size,
        s.maf,
        s.significance,
        s.trait,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'gwas_export.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>GWAS Enhancer</Typography>
      
      {/* Search and Filter Bar */}
      <SearchFilterBar
        onSearch={handleSearch}
        onFilter={handleFilter}
        onExport={handleExport}
        searchPlaceholder="Search SNPs by ID, trait, or significance..."
        filterOptions={filterOptions}
      />
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="primary">Total SNPs</Typography>
            <Typography variant="h4">{totalSNPs}</Typography>
            {(searchQuery || Object.keys(filters).length > 0) && (
              <Typography variant="body2" color="text.secondary">
                (Filtered from {gwasData.length} total)
              </Typography>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="error.main">Genome-wide Significant</Typography>
            <Typography variant="h4">{genomeWideSignificant}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="warning.main">Suggestive</Typography>
            <Typography variant="h4">{suggestive}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary">Avg Effect Size</Typography>
            <Typography variant="h4">{avgEffectSize}</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Manhattan Plot</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <Scatter data={manhattanData}>
                <CartesianGrid />
                <XAxis type="number" dataKey="position" name="Position" />
                <YAxis type="number" dataKey="pValue" name="-log10(P-value)" />
                
                <Scatter dataKey="pValue" fill="#8884d8" />
              </Scatter>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Q-Q Plot</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <Scatter data={qqData}>
                <CartesianGrid />
                <XAxis type="number" dataKey="expected" name="Expected -log10(P)" />
                <YAxis type="number" dataKey="observed" name="Observed -log10(P)" />
                
                <Scatter dataKey="observed" fill="#82ca9d" />
              </Scatter>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>GWAS Results</Typography>
          <DataGrid
            rows={filteredGWAS}
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
