import React, { useEffect, useState, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Chip, 
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
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { fetchDrugTargets, predictDrugResponse } from '../api';
import SearchFilterBar from '../components/SearchFilterBar';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'drug_name', headerName: 'Drug Name', width: 150 },
  { field: 'target_protein', headerName: 'Target Protein', width: 150 },
  { field: 'binding_affinity', headerName: 'Binding Affinity (nM)', width: 150, type: 'number' },
  { field: 'prediction_score', headerName: 'Response Score', width: 130, type: 'number' },
  { 
    field: 'response_prediction', 
    headerName: 'Predicted Response', 
    width: 150,
    renderCell: (params) => (
      <Chip 
        label={params.value} 
        color={params.value === 'High' ? 'success' : params.value === 'Medium' ? 'warning' : 'error'}
        size="small"
      />
    )
  },
  { field: 'source', headerName: 'Source', width: 120 },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

interface DrugPredictionResult {
  drug_name: string;
  response_probability: number;
  confidence_score: number;
  recommendations: string[];
}

export default function DrugResponseTab() {
  const [drugTargets, setDrugTargets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});
  
  // ML Prediction states
  const [predictionDialogOpen, setPredictionDialogOpen] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState<DrugPredictionResult | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  
  // Prediction form data
  const [predictionForm, setPredictionForm] = useState({
    drug_name: '',
    molecular_weight: 400,
    logp: 2.0,
    hbd: 2,
    hba: 6,
    drug_likeness: 0.8,
    patient_age: 45,
    patient_gender: 'female'
  });

  useEffect(() => {
    fetchDrugTargets()
      .then((data) => {
        setDrugTargets(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Filter and search drug targets
  const filteredDrugTargets = useMemo(() => {
    let filtered = drugTargets;

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(drug =>
        drug.drug_name?.toLowerCase().includes(query) ||
        drug.target_protein?.toLowerCase().includes(query) ||
        drug.response_prediction?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(drug => drug[key] === value);
      }
    });

    return filtered;
  }, [drugTargets, searchQuery, filters]);

  // Filter options
  const filterOptions = {
    response_prediction: [
      { label: 'High Response', value: 'High' },
      { label: 'Medium Response', value: 'Medium' },
      { label: 'Low Response', value: 'Low' },
    ],
    source: [
      { label: 'DrugBank', value: 'DrugBank' },
      { label: 'ChEMBL', value: 'ChEMBL' },
      { label: 'Clinical Trials', value: 'Clinical' },
    ],
  };

  // Summary statistics
  const totalDrugs = filteredDrugTargets.length;
  const highResponse = filteredDrugTargets.filter(d => d.response_prediction === 'High').length;
  const mediumResponse = filteredDrugTargets.filter(d => d.response_prediction === 'Medium').length;
  const lowResponse = filteredDrugTargets.filter(d => d.response_prediction === 'Low').length;
  
  const avgAffinity = filteredDrugTargets.length > 0 
    ? (filteredDrugTargets.reduce((sum, d) => sum + (d.binding_affinity || 0), 0) / filteredDrugTargets.length).toFixed(2)
    : 0;

  // Chart data
  const responseData = [
    { name: 'High Response', value: highResponse },
    { name: 'Medium Response', value: mediumResponse },
    { name: 'Low Response', value: lowResponse },
  ];

  // Compute layman summary
  const summary = useMemo(() => {
    if (!drugTargets || drugTargets.length === 0) return 'No drug response data available.';
    const total = drugTargets.length;
    const high = drugTargets.filter(d => d.response_prediction === 'High').length;
    const medium = drugTargets.filter(d => d.response_prediction === 'Medium').length;
    const low = drugTargets.filter(d => d.response_prediction === 'Low').length;
    const topDrugs = drugTargets
      .filter(d => d.response_prediction === 'High')
      .slice(0, 3)
      .map(d => d.drug_name)
      .join(', ');
    let focus = '';
    if (high > 0) {
      focus = `Top drugs predicted to be most effective: ${topDrugs}.`;
    } else if (medium > 0) {
      focus = `Some drugs show moderate predicted response.`;
    } else {
      focus = `Most drugs are predicted to have low response.`;
    }
    return `We analyzed ${total} drug-target interactions. High response: ${high}, Medium: ${medium}, Low: ${low}. ${focus}`;
  }, [drugTargets]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilter = (newFilters: Record<string, any>) => {
    setFilters(newFilters);
  };

  const handleExport = () => {
    // Simple CSV export
    const csvContent = [
      ['ID', 'Drug Name', 'Target Protein', 'Binding Affinity', 'Response Score', 'Predicted Response', 'Source'],
      ...filteredDrugTargets.map(d => [
        d.id,
        d.drug_name,
        d.target_protein,
        d.binding_affinity,
        d.prediction_score,
        d.response_prediction,
        d.source,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'drug_response_export.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handlePredictDrugResponse = async () => {
    setPredictionLoading(true);
    setPredictionError(null);
    setPredictionResult(null);

    try {
      const result = await predictDrugResponse(predictionForm);
      setPredictionResult(result);
    } catch (error: any) {
      setPredictionError(error.response?.data?.detail || 'Prediction failed. Please try again.');
    } finally {
      setPredictionLoading(false);
    }
  };

  const getResponseColor = (probability: number) => {
    if (probability >= 0.7) return 'success';
    if (probability >= 0.4) return 'warning';
    return 'error';
  };

  const getResponseLabel = (probability: number) => {
    if (probability >= 0.7) return 'High';
    if (probability >= 0.4) return 'Medium';
    return 'Low';
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
        <Typography variant="h5">Drug Response Prediction</Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => setPredictionDialogOpen(true)}
        >
          💊 Predict Drug Response
        </Button>
      </Box>
      
      {/* Search and Filter Bar */}
      <SearchFilterBar
        onSearch={handleSearch}
        onFilter={handleFilter}
        onExport={handleExport}
        searchPlaceholder="Search drugs by name, target protein, or response..."
        filterOptions={filterOptions}
      />
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6">Total Drugs</Typography>
            <Typography variant="h4">{totalDrugs}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">High Response</Typography>
            <Typography variant="h4" color="success.main">{highResponse}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">Medium Response</Typography>
            <Typography variant="h4" color="warning.main">{mediumResponse}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6">Avg Binding Affinity</Typography>
            <Typography variant="h4">{avgAffinity} nM</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Response Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={responseData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {responseData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Binding Affinity Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={filteredDrugTargets.slice(0, 10)}>
                <XAxis dataKey="drug_name" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Bar dataKey="binding_affinity" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Drug Response Data</Typography>
          <DataGrid
            rows={filteredDrugTargets}
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
        <DialogTitle>💊 Drug Response Prediction</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Drug Name"
              value={predictionForm.drug_name}
              onChange={(e) => setPredictionForm({...predictionForm, drug_name: e.target.value})}
              placeholder="e.g., Olaparib"
            />
            <TextField
              fullWidth
              label="Molecular Weight"
              type="number"
              value={predictionForm.molecular_weight}
              onChange={(e) => setPredictionForm({...predictionForm, molecular_weight: parseFloat(e.target.value)})}
              inputProps={{ min: 0, step: 0.1 }}
            />
            <TextField
              fullWidth
              label="LogP"
              type="number"
              value={predictionForm.logp}
              onChange={(e) => setPredictionForm({...predictionForm, logp: parseFloat(e.target.value)})}
              inputProps={{ step: 0.1 }}
            />
            <TextField
              fullWidth
              label="HBD (Hydrogen Bond Donors)"
              type="number"
              value={predictionForm.hbd}
              onChange={(e) => setPredictionForm({...predictionForm, hbd: parseInt(e.target.value)})}
              inputProps={{ min: 0 }}
            />
            <TextField
              fullWidth
              label="HBA (Hydrogen Bond Acceptors)"
              type="number"
              value={predictionForm.hba}
              onChange={(e) => setPredictionForm({...predictionForm, hba: parseInt(e.target.value)})}
              inputProps={{ min: 0 }}
            />
            <TextField
              fullWidth
              label="Drug Likeness"
              type="number"
              value={predictionForm.drug_likeness}
              onChange={(e) => setPredictionForm({...predictionForm, drug_likeness: parseFloat(e.target.value)})}
              inputProps={{ min: 0, max: 1, step: 0.01 }}
            />
            <TextField
              fullWidth
              label="Patient Age"
              type="number"
              value={predictionForm.patient_age}
              onChange={(e) => setPredictionForm({...predictionForm, patient_age: parseInt(e.target.value)})}
              inputProps={{ min: 0, max: 120 }}
            />
            <FormControl fullWidth>
              <InputLabel>Patient Gender</InputLabel>
              <Select
                value={predictionForm.patient_gender}
                label="Patient Gender"
                onChange={(e) => setPredictionForm({...predictionForm, patient_gender: e.target.value})}
              >
                <MenuItem value="male">Male</MenuItem>
                <MenuItem value="female">Female</MenuItem>
                <MenuItem value="other">Other</MenuItem>
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
                  <Typography variant="body2" color="text.secondary">Drug Name</Typography>
                  <Typography variant="body1">{predictionResult.drug_name}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Response Probability</Typography>
                  <Typography variant="h6" color="primary">
                    {(predictionResult.response_probability * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Predicted Response</Typography>
                  <Chip 
                    label={getResponseLabel(predictionResult.response_probability)}
                    color={getResponseColor(predictionResult.response_probability) as any}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Confidence Score</Typography>
                  <Typography variant="body1">
                    {(predictionResult.confidence_score * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
                  <Typography variant="body2" color="text.secondary">Recommendations</Typography>
                  <Box sx={{ mt: 1 }}>
                    {predictionResult.recommendations.map((rec, index) => (
                      <Chip 
                        key={index}
                        label={rec}
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                </Box>
              </Box>
            </Card>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPredictionDialogOpen(false)}>Close</Button>
          <Button 
            onClick={handlePredictDrugResponse}
            variant="contained"
            disabled={predictionLoading || !predictionForm.drug_name}
          >
            {predictionLoading ? <CircularProgress size={20} /> : 'Predict'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 
