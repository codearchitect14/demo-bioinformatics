import React, { useEffect, useState, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Chip, 
  LinearProgress, 
  Button, 
  TextField, 
  Grid, 
  Alert, 
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
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Scatter, CartesianGrid } from 'recharts';
import { fetchGeneExpression, predictBiomarker } from '../api';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'gene_symbol', headerName: 'Gene Symbol', width: 130 },
  { field: 'expression_level', headerName: 'Expression Level', width: 140, type: 'number' },
  { field: 'fold_change', headerName: 'Fold Change', width: 130, type: 'number' },
  { field: 'p_value', headerName: 'P-Value', width: 120, type: 'number' },
  { 
    field: 'significance', 
    headerName: 'Significance', 
    width: 130,
    renderCell: (params) => (
      <Chip 
        label={params.value} 
        color={params.value === 'High' ? 'success' : params.value === 'Medium' ? 'warning' : 'default'}
        size="small"
      />
    )
  },
  { field: 'biomarker_score', headerName: 'Biomarker Score', width: 140, type: 'number' },
];

interface BiomarkerPredictionResult {
  gene_name: string;
  biomarker_score: number;
  clinical_relevance: string;
  significance_level: string;
}

export default function BiomarkerTab() {
  const [geneExpression, setGeneExpression] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // ML Prediction states
  const [predictionDialogOpen, setPredictionDialogOpen] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState<BiomarkerPredictionResult | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  
  // Prediction form data
  const [predictionForm, setPredictionForm] = useState({
    gene_name: '',
    expression_value: 5.0,
    sample_type: 'tumor'
  });

  useEffect(() => {
    fetchGeneExpression()
      .then((data) => {
        setGeneExpression(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Summary statistics
  const totalGenes = geneExpression.length;
  const significantGenes = geneExpression.filter(g => g.p_value < 0.05).length;
  const highExpression = geneExpression.filter(g => g.expression_level > 5).length;
  const avgFoldChange = geneExpression.length > 0 
    ? (geneExpression.reduce((sum, g) => sum + Math.abs(g.fold_change || 0), 0) / geneExpression.length).toFixed(2)
    : 0;

  // Top biomarkers
  const topBiomarkers = geneExpression
    .sort((a, b) => (b.biomarker_score || 0) - (a.biomarker_score || 0))
    .slice(0, 10);

  // Expression trend data (simulated)
  const expressionTrend = geneExpression.slice(0, 20).map((gene, index) => ({
    gene: gene.gene_symbol || `Gene_${index}`,
    control: Math.random() * 2 + 1,
    treatment: (gene.expression_level || 1) * (Math.random() * 0.5 + 0.75),
  }));

  // Compute layman summary
  const summary = useMemo(() => {
    if (!geneExpression || geneExpression.length === 0) return 'No biomarker data available.';
    const total = geneExpression.length;
    const significant = geneExpression.filter(g => g.p_value < 0.05).length;
    const topGenes = geneExpression
      .sort((a, b) => (b.biomarker_score || 0) - (a.biomarker_score || 0))
      .slice(0, 3)
      .map(g => g.gene_symbol)
      .join(', ');
    let focus = '';
    if (significant > 0) {
      focus = `Top biomarker genes: ${topGenes}.`;
    } else {
      focus = `No highly significant biomarkers detected.`;
    }
    return `We analyzed ${total} gene expression records. ${significant} genes show statistically significant changes. ${focus}`;
  }, [geneExpression]);

  const handlePredictBiomarker = async () => {
    setPredictionLoading(true);
    setPredictionError(null);
    setPredictionResult(null);

    try {
      const result = await predictBiomarker(predictionForm);
      setPredictionResult(result);
    } catch (error: any) {
      setPredictionError(error.response?.data?.detail || 'Prediction failed. Please try again.');
    } finally {
      setPredictionLoading(false);
    }
  };

  const getRelevanceColor = (relevance: string) => {
    if (relevance.includes('High')) return 'success';
    if (relevance.includes('Medium')) return 'warning';
    if (relevance.includes('Low')) return 'error';
    return 'default';
  };

  const getSignificanceColor = (significance: string) => {
    if (significance.includes('Significant')) return 'success';
    if (significance.includes('Moderate')) return 'warning';
    return 'default';
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
        <Typography variant="h5">Biomarker Discovery</Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => setPredictionDialogOpen(true)}
        >
          🔬 Predict Biomarker
        </Button>
      </Box>
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6">Total Genes</Typography>
            <Typography variant="h4">{totalGenes}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">Significant Genes</Typography>
            <Typography variant="h4" color="success.main">{significantGenes}</Typography>
            <LinearProgress 
              variant="determinate" 
              value={(significantGenes / totalGenes) * 100} 
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">High Expression</Typography>
            <Typography variant="h4" color="warning.main">{highExpression}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">Avg Fold Change</Typography>
            <Typography variant="h4">{avgFoldChange}x</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Expression Trend Analysis</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={expressionTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gene" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Line type="monotone" dataKey="control" stroke="#8884d8" name="Control" />
                <Line type="monotone" dataKey="treatment" stroke="#82ca9d" name="Treatment" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Top Biomarkers</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={topBiomarkers}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gene_symbol" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Line type="monotone" dataKey="biomarker_score" stroke="#ff7300" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Gene Expression Data</Typography>
          <DataGrid
            rows={geneExpression}
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
        <DialogTitle>🔬 Biomarker Discovery Prediction</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Gene Name"
              value={predictionForm.gene_name}
              onChange={(e) => setPredictionForm({...predictionForm, gene_name: e.target.value})}
              placeholder="e.g., BRCA2"
            />
            <TextField
              fullWidth
              label="Expression Value (FPKM)"
              type="number"
              value={predictionForm.expression_value}
              onChange={(e) => setPredictionForm({...predictionForm, expression_value: parseFloat(e.target.value)})}
              inputProps={{ min: 0, step: 0.01 }}
            />
            <FormControl fullWidth>
              <InputLabel>Sample Type</InputLabel>
              <Select
                value={predictionForm.sample_type}
                label="Sample Type"
                onChange={(e) => setPredictionForm({...predictionForm, sample_type: e.target.value})}
              >
                <MenuItem value="tumor">Tumor</MenuItem>
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="blood">Blood</MenuItem>
                <MenuItem value="tissue">Tissue</MenuItem>
              </Select>
            </FormControl>
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
                  <Typography variant="body2" color="text.secondary">Gene Name</Typography>
                  <Typography variant="body1">{predictionResult.gene_name}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Biomarker Score</Typography>
                  <Typography variant="h6" color="primary">
                    {(predictionResult.biomarker_score * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Clinical Relevance</Typography>
                  <Chip 
                    label={predictionResult.clinical_relevance}
                    color={getRelevanceColor(predictionResult.clinical_relevance) as any}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Significance Level</Typography>
                  <Chip 
                    label={predictionResult.significance_level}
                    color={getSignificanceColor(predictionResult.significance_level) as any}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
                  <Typography variant="body2" color="text.secondary">Interpretation</Typography>
                  <Typography variant="body1" sx={{ mt: 1 }}>
                    {predictionResult.biomarker_score >= 0.8 
                      ? "This gene shows strong potential as a biomarker with high clinical relevance."
                      : predictionResult.biomarker_score >= 0.6
                      ? "This gene shows moderate potential as a biomarker and warrants further investigation."
                      : "This gene shows limited potential as a biomarker based on current analysis."
                    }
                  </Typography>
                </Box>
              </Box>
            </Card>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPredictionDialogOpen(false)}>Close</Button>
          <Button 
            onClick={handlePredictBiomarker}
            variant="contained"
            disabled={predictionLoading || !predictionForm.gene_name}
          >
            {predictionLoading ? <CircularProgress size={20} /> : 'Predict'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 
