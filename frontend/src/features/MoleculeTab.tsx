import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Chip, Button } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Scatter, CartesianGrid } from 'recharts';
import { fetchDrugTargets } from '../api';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'smiles', headerName: 'SMILES', width: 200 },
  { field: 'molecular_weight', headerName: 'MW', width: 100, type: 'number' },
  { field: 'logp', headerName: 'LogP', width: 100, type: 'number' },
  { field: 'hbd', headerName: 'HBD', width: 80, type: 'number' },
  { field: 'hba', headerName: 'HBA', width: 80, type: 'number' },
  { field: 'drug_likeness', headerName: 'Drug Likeness', width: 130, type: 'number' },
  { 
    field: 'generation_score', 
    headerName: 'RL Score', 
    width: 120,
    renderCell: (params) => (
      <Chip 
        label={params.value?.toFixed(3) || 'N/A'} 
        color={params.value > 0.7 ? 'success' : params.value > 0.4 ? 'warning' : 'error'}
        size="small"
      />
    )
  },
];

export default function MoleculeTab() {
  const [molecules, setMolecules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchDrugTargets()
      .then((data) => {
        setMolecules(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleGenerateMolecules = () => {
    setGenerating(true);
    // Simulate molecule generation
    setTimeout(() => {
      const newMolecules = Array.from({ length: 5 }, (_, i) => ({
        id: `mol_${Date.now()}_${i}`,
        smiles: `CCOC(=O)c${i}cc${i}cc${i}`,
        molecular_weight: 200 + Math.random() * 300,
        logp: Math.random() * 5,
        hbd: Math.floor(Math.random() * 5),
        hba: Math.floor(Math.random() * 10),
        drug_likeness: Math.random(),
        generation_score: Math.random(),
      }));
      setMolecules(prev => [...newMolecules, ...prev]);
      setGenerating(false);
    }, 2000);
  };

  // Summary statistics
  const totalMolecules = molecules.length;
  const drugLike = molecules.filter(m => m.drug_likeness > 0.5).length;
  const highScore = molecules.filter(m => m.generation_score > 0.7).length;
  const avgScore = molecules.length > 0 
    ? (molecules.reduce((sum, m) => sum + (m.generation_score || 0), 0) / molecules.length).toFixed(3)
    : 0;

  // Property distributions
  const mwData = molecules.slice(0, 20).map((mol, index) => ({
    molecule: `Mol_${index + 1}`,
    mw: mol.molecular_weight || 0,
    logp: mol.logp || 0,
  }));

  const scoreData = [
    { range: '0.0-0.2', count: molecules.filter(m => m.generation_score >= 0 && m.generation_score < 0.2).length },
    { range: '0.2-0.4', count: molecules.filter(m => m.generation_score >= 0.2 && m.generation_score < 0.4).length },
    { range: '0.4-0.6', count: molecules.filter(m => m.generation_score >= 0.4 && m.generation_score < 0.6).length },
    { range: '0.6-0.8', count: molecules.filter(m => m.generation_score >= 0.6 && m.generation_score < 0.8).length },
    { range: '0.8-1.0', count: molecules.filter(m => m.generation_score >= 0.8 && m.generation_score <= 1.0).length },
  ];

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Molecule Generation (RL)</Typography>
      
      {/* Generate Button */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6">Generate New Molecules</Typography>
            <Button 
              variant="contained" 
              onClick={handleGenerateMolecules}
              disabled={generating}
            >
              {generating ? 'Generating...' : 'Generate Molecules'}
            </Button>
            <Typography variant="body2" color="text.secondary">
              Uses Reinforcement Learning to generate drug-like molecules
            </Typography>
          </Box>
        </CardContent>
      </Card>
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="primary">Total Molecules</Typography>
            <Typography variant="h4">{totalMolecules}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="success.main">Drug-like</Typography>
            <Typography variant="h4">{drugLike}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="warning.main">High RL Score</Typography>
            <Typography variant="h4">{highScore}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary">Avg RL Score</Typography>
            <Typography variant="h4">{avgScore}</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>RL Score Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreData}>
                <XAxis dataKey="range" />
                <YAxis />
                
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Molecular Weight vs LogP</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <Scatter data={mwData}>
                <CartesianGrid />
                <XAxis type="number" dataKey="mw" name="Molecular Weight" />
                <YAxis type="number" dataKey="logp" name="LogP" />
                
                <Scatter fill="#82ca9d" />
              </Scatter>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Top Molecules */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Top Generated Molecules</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
            {molecules
              .sort((a, b) => (b.generation_score || 0) - (a.generation_score || 0))
              .slice(0, 6)
              .map((mol, index) => (
                <Card key={mol.id} variant="outlined">
                  <CardContent>
                    <Typography variant="h6" noWrap>{mol.smiles || `Molecule_${index}`}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      RL Score: {mol.generation_score?.toFixed(3) || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Drug Likeness: {mol.drug_likeness?.toFixed(3) || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      MW: {mol.molecular_weight?.toFixed(1) || 'N/A'}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Chip 
                        label={mol.generation_score > 0.7 ? 'High Quality' : mol.generation_score > 0.4 ? 'Medium' : 'Low Quality'} 
                        size="small"
                        color={mol.generation_score > 0.7 ? 'success' : mol.generation_score > 0.4 ? 'warning' : 'error'}
                      />
                    </Box>
                  </CardContent>
                </Card>
              ))}
          </Box>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Generated Molecules Database</Typography>
          <DataGrid
            rows={molecules}
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
