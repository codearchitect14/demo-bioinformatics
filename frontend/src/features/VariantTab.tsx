import React, { useEffect, useState, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  TextField, 
  Grid, 
  Alert, 
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { fetchVariants, predictVariantPathogenicity } from '../api';
import SearchFilterBar from '../components/SearchFilterBar';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'chromosome', headerName: 'Chromosome', width: 120 },
  { field: 'position', headerName: 'Position', width: 120 },
  { field: 'ref_allele', headerName: 'Ref', width: 100 },
  { field: 'alt_allele', headerName: 'Alt', width: 100 },
  { field: 'impact', headerName: 'Impact', width: 120 },
  { field: 'gene', headerName: 'Gene', width: 120 },
];

interface PredictionResult {
  variant_id: string;
  pathogenicity_score: number;
  clinical_significance: string;
  confidence_level: string;
  model_accuracy: number;
}

export default function VariantTab() {
  const [variants, setVariants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});
  
  // ML Prediction states
  const [predictionDialogOpen, setPredictionDialogOpen] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  
  // Prediction form data
  const [predictionForm, setPredictionForm] = useState({
    chromosome: '',
    position: '',
    reference_allele: '',
    alternate_allele: '',
    quality_score: 50,
    allele_frequency: 0.0
  });

  useEffect(() => {
    fetchVariants()
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
        variant.chromosome?.toLowerCase().includes(query) ||
        variant.impact?.toLowerCase().includes(query)
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
    chromosome: [
      { label: 'Chromosome 1', value: '1' },
      { label: 'Chromosome 2', value: '2' },
      { label: 'Chromosome X', value: 'X' },
      { label: 'Chromosome Y', value: 'Y' },
    ],
    impact: [
      { label: 'High', value: 'HIGH' },
      { label: 'Moderate', value: 'MODERATE' },
      { label: 'Low', value: 'LOW' },
      { label: 'Modifier', value: 'MODIFIER' },
    ],
  };

  // Summary statistics
  const totalVariants = filteredVariants.length;
  const impactCounts = filteredVariants.reduce((acc: any, v: any) => {
    acc[v.impact] = (acc[v.impact] || 0) + 1;
    return acc;
  }, {});
  const chartData = Object.entries(impactCounts).map(([impact, count]) => ({ impact, count }));

  // Compute layman summary
  const summary = useMemo(() => {
    if (!variants || variants.length === 0) return 'No variant data available.';
    const total = variants.length;
    const chromCounts: Record<string, number> = {};
    const significanceCounts: Record<string, number> = {};
    variants.forEach(v => {
      if (v.chromosome) chromCounts[v.chromosome] = (chromCounts[v.chromosome] || 0) + 1;
      if (v.impact) significanceCounts[v.impact] = (significanceCounts[v.impact] || 0) + 1;
    });
    const topChroms = Object.entries(chromCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([chrom, count]) => `${chrom} (${count})`)
      .join(', ');
    const sigSorted = Object.entries(significanceCounts).sort((a, b) => b[1] - a[1]);
    const sigSummary = sigSorted.map(([sig, count]) => `${count} ${sig}`).join(', ');
    let focus = '';
    const pathogenicCount = significanceCounts['pathogenic'] ?? significanceCounts['Pathogenic'];
    if (typeof pathogenicCount === 'number' && pathogenicCount > 0) {
      focus = `Focus on the ${pathogenicCount} pathogenic variants for further investigation.`;
    }
    return `We analyzed ${total} genetic variants. Most are found on chromosomes: ${topChroms}. Clinical significance: ${sigSummary}. ${focus}`;
  }, [variants]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilter = (newFilters: Record<string, any>) => {
    setFilters(newFilters);
  };

  const handleExport = () => {
    // Simple CSV export
    const csvContent = [
      ['ID', 'Chromosome', 'Position', 'Ref', 'Alt', 'Impact', 'Gene'],
      ...filteredVariants.map(v => [
        v.id,
        v.chromosome,
        v.position,
        v.ref_allele,
        v.alt_allele,
        v.impact,
        v.gene,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'variants_export.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handlePredictVariant = async () => {
    setPredictionLoading(true);
    setPredictionError(null);
    setPredictionResult(null);

    try {
      const result = await predictVariantPathogenicity({
        chromosome: predictionForm.chromosome,
        position: parseInt(predictionForm.position),
        reference_allele: predictionForm.reference_allele,
        alternate_allele: predictionForm.alternate_allele,
        quality_score: predictionForm.quality_score,
        allele_frequency: predictionForm.allele_frequency
      });
      
      setPredictionResult(result);
    } catch (error: any) {
      setPredictionError(error.response?.data?.detail || 'Prediction failed. Please try again.');
    } finally {
      setPredictionLoading(false);
    }
  };

  const getSignificanceColor = (significance: string) => {
    switch (significance.toLowerCase()) {
      case 'pathogenic':
        return 'error';
      case 'likely pathogenic':
        return 'warning';
      case 'vus':
        return 'info';
      case 'likely benign':
        return 'success';
      case 'benign':
        return 'success';
      default:
        return 'default';
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence.toLowerCase()) {
      case 'high':
        return 'success';
      case 'medium':
        return 'warning';
      case 'low':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Layman summary card */}
      <Box sx={{ mb: 2 }}>
        <Card>
          <CardContent>
            <Typography variant="h6">Summary for Non-Experts</Typography>
            <Typography variant="body1">{summary}</Typography>
          </CardContent>
        </Card>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Variant Interpretation</Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => setPredictionDialogOpen(true)}
        >
          🧬 Predict Variant Pathogenicity
        </Button>
      </Box>
      
      {/* Search and Filter Bar */}
      <SearchFilterBar
        onSearch={handleSearch}
        onFilter={handleFilter}
        onExport={handleExport}
        searchPlaceholder="Search variants by gene, chromosome, or impact..."
        filterOptions={filterOptions}
      />
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 2fr' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6">Total Variants</Typography>
            <Typography variant="h4">{totalVariants}</Typography>
            {(searchQuery || Object.keys(filters).length > 0) && (
              <Typography variant="body2" color="text.secondary">
                (Filtered from {variants.length} total)
              </Typography>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">Impact Distribution</Typography>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <XAxis dataKey="impact" />
                <YAxis allowDecimals={false} />
                <Bar dataKey="count" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Variant Data</Typography>
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

      {/* ML Prediction Dialog */}
      <Dialog 
        open={predictionDialogOpen} 
        onClose={() => setPredictionDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>🧬 Variant Pathogenicity Prediction</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Chromosome"
              value={predictionForm.chromosome}
              onChange={(e) => setPredictionForm({...predictionForm, chromosome: e.target.value})}
              placeholder="e.g., 7"
            />
            <TextField
              fullWidth
              label="Position"
              value={predictionForm.position}
              onChange={(e) => setPredictionForm({...predictionForm, position: e.target.value})}
              placeholder="e.g., 117199644"
            />
            <TextField
              fullWidth
              label="Reference Allele"
              value={predictionForm.reference_allele}
              onChange={(e) => setPredictionForm({...predictionForm, reference_allele: e.target.value})}
              placeholder="e.g., G"
            />
            <TextField
              fullWidth
              label="Alternate Allele"
              value={predictionForm.alternate_allele}
              onChange={(e) => setPredictionForm({...predictionForm, alternate_allele: e.target.value})}
              placeholder="e.g., A"
            />
            <TextField
              fullWidth
              label="Quality Score"
              type="number"
              value={predictionForm.quality_score}
              onChange={(e) => setPredictionForm({...predictionForm, quality_score: parseFloat(e.target.value)})}
              inputProps={{ min: 0, max: 100 }}
            />
            <TextField
              fullWidth
              label="Allele Frequency"
              type="number"
              value={predictionForm.allele_frequency}
              onChange={(e) => setPredictionForm({...predictionForm, allele_frequency: parseFloat(e.target.value)})}
              inputProps={{ min: 0, max: 1, step: 0.0001 }}
            />
          </Box>

          {predictionError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {predictionError}
            </Alert>
          )}

          {predictionResult && (
            <Card sx={{ mt: 2, p: 2 }}>
              <Typography variant="h6" gutterBottom>Prediction Results</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Variant ID</Typography>
                  <Typography variant="body1">{predictionResult.variant_id}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Pathogenicity Score</Typography>
                  <Typography variant="h6" color="primary">
                    {(predictionResult.pathogenicity_score * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Clinical Significance</Typography>
                  <Chip 
                    label={predictionResult.clinical_significance}
                    color={getSignificanceColor(predictionResult.clinical_significance) as any}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Confidence Level</Typography>
                  <Chip 
                    label={predictionResult.confidence_level}
                    color={getConfidenceColor(predictionResult.confidence_level) as any}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
                  <Typography variant="body2" color="text.secondary">Model Accuracy</Typography>
                  <Typography variant="body1">
                    {(predictionResult.model_accuracy * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </Card>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPredictionDialogOpen(false)}>Close</Button>
          <Button 
            onClick={handlePredictVariant}
            variant="contained"
            disabled={predictionLoading || !predictionForm.chromosome || !predictionForm.position}
          >
            {predictionLoading ? <CircularProgress size={20} /> : 'Predict'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 
