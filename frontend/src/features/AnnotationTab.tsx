import React, { useEffect, useState, useMemo } from 'react';
import { Box, Typography, Card, CardContent, Chip, LinearProgress } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { fetchAnnotations } from '../api';
import SearchFilterBar from '../components/SearchFilterBar';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'gene_id', headerName: 'Gene ID', width: 150 },
  { field: 'gene_name', headerName: 'Gene Name', width: 150 },
  { field: 'chromosome', headerName: 'Chromosome', width: 120 },
  { field: 'start_position', headerName: 'Start', width: 100, type: 'number' },
  { field: 'end_position', headerName: 'End', width: 100, type: 'number' },
  { field: 'strand', headerName: 'Strand', width: 80 },
  { 
    field: 'annotation_quality', 
    headerName: 'Quality', 
    width: 120,
    renderCell: (params) => (
      <Chip 
        label={params.value} 
        color={params.value === 'High' ? 'success' : params.value === 'Medium' ? 'warning' : 'error'}
        size="small"
      />
    )
  },
  { field: 'functional_prediction', headerName: 'Function', width: 200 },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function AnnotationTab() {
  const [annotations, setAnnotations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchAnnotations()
      .then((data) => {
        setAnnotations(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Filter and search annotations
  const filteredAnnotations = useMemo(() => {
    let filtered = annotations;

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(annotation =>
        annotation.gene_name?.toLowerCase().includes(query) ||
        annotation.chromosome?.toLowerCase().includes(query) ||
        annotation.annotation_quality?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(annotation => annotation[key] === value);
      }
    });

    return filtered;
  }, [annotations, searchQuery, filters]);

  // Filter options
  const filterOptions = {
    annotation_quality: [
      { label: 'High Quality', value: 'High' },
      { label: 'Medium Quality', value: 'Medium' },
      { label: 'Low Quality', value: 'Low' },
    ],
    chromosome: [
      { label: 'Chromosome 1', value: '1' },
      { label: 'Chromosome 2', value: '2' },
      { label: 'Chromosome X', value: 'X' },
    ],
  };

  // Summary statistics
  const totalGenes = filteredAnnotations.length;
  const highQuality = filteredAnnotations.filter(a => a.annotation_quality === 'High').length;
  const mediumQuality = filteredAnnotations.filter(a => a.annotation_quality === 'Medium').length;
  const lowQuality = filteredAnnotations.filter(a => a.annotation_quality === 'Low').length;
  
  const avgLength = filteredAnnotations.length > 0 
    ? (filteredAnnotations.reduce((sum, a) => sum + ((a.end_position || 0) - (a.start_position || 0)), 0) / filteredAnnotations.length).toFixed(0)
    : 0;

  // Chromosome distribution
  const chromosomeData = filteredAnnotations.reduce((acc: Record<string, number>, gene) => {
    const chr = gene.chromosome || 'Unknown';
    acc[chr] = (acc[chr] || 0) + 1;
    return acc;
  }, {});

  const chrChartData = Object.entries(chromosomeData)
    .map(([chr, count]) => ({ chromosome: chr, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  // Quality distribution
  const qualityData = [
    { quality: 'High', count: highQuality },
    { quality: 'Medium', count: mediumQuality },
    { quality: 'Low', count: lowQuality },
  ];

  // Functional categories (simulated)
  const functionalCategories = [
    { category: 'Protein Coding', count: Math.floor(totalGenes * 0.6) },
    { category: 'Regulatory', count: Math.floor(totalGenes * 0.2) },
    { category: 'Non-coding RNA', count: Math.floor(totalGenes * 0.15) },
    { category: 'Pseudogene', count: Math.floor(totalGenes * 0.05) },
  ];

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilter = (newFilters: Record<string, any>) => {
    setFilters(newFilters);
  };

  const handleExport = () => {
    // CSV export
    const csvContent = [
      ['ID', 'Gene ID', 'Gene Name', 'Chromosome', 'Start', 'End', 'Strand', 'Quality', 'Function'],
      ...filteredAnnotations.map(a => [
        a.id,
        a.gene_id,
        a.gene_name,
        a.chromosome,
        a.start_position,
        a.end_position,
        a.strand,
        a.annotation_quality,
        a.functional_prediction,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'annotations_export.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Genome Annotation AI</Typography>
      
      {/* Search and Filter Bar */}
      <SearchFilterBar
        onSearch={handleSearch}
        onFilter={handleFilter}
        onExport={handleExport}
        searchPlaceholder="Search annotations by gene name, chromosome, or quality..."
        filterOptions={filterOptions}
      />
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="primary">Total Genes</Typography>
            <Typography variant="h4">{totalGenes}</Typography>
            {(searchQuery || Object.keys(filters).length > 0) && (
              <Typography variant="body2" color="text.secondary">
                (Filtered from {annotations.length} total)
              </Typography>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="success.main">High Quality</Typography>
            <Typography variant="h4">{highQuality}</Typography>
            <LinearProgress 
              variant="determinate" 
              value={(highQuality / totalGenes) * 100} 
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="warning.main">Medium Quality</Typography>
            <Typography variant="h4">{mediumQuality}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary">Avg Gene Length</Typography>
            <Typography variant="h4">{avgLength} bp</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Annotation Quality Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={qualityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ quality, percent }) => `${quality} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {qualityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                {/*  */}
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Functional Categories</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={functionalCategories}>
                <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                {/*  */}
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Chromosome Distribution */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Gene Distribution by Chromosome</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chrChartData}>
              <XAxis dataKey="chromosome" />
              <YAxis />
              {/*  */}
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Gene Annotations</Typography>
          <DataGrid
            rows={filteredAnnotations}
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
