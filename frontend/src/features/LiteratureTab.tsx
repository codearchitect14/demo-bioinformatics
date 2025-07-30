import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Chip, Avatar, List, ListItem, ListItemText, ListItemAvatar } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { fetchLiterature } from '../api';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120 },
  { field: 'title', headerName: 'Title', width: 300, flex: 1 },
  { field: 'abstract', headerName: 'Abstract', width: 400, flex: 1 },
  { field: 'sentiment_score', headerName: 'Sentiment', width: 120, type: 'number' },
  { 
    field: 'sentiment_label', 
    headerName: 'Sentiment Label', 
    width: 130,
    renderCell: (params) => (
      <Chip 
        label={params.value} 
        color={params.value === 'Positive' ? 'success' : params.value === 'Neutral' ? 'default' : 'error'}
        size="small"
      />
    )
  },
  { field: 'source', headerName: 'Source', width: 120 },
];

export default function LiteratureTab() {
  const [literature, setLiterature] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLiterature()
      .then((data) => {
        setLiterature(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Summary statistics
  const totalPapers = literature.length;
  const positiveSentiment = literature.filter(p => p.sentiment_label === 'Positive').length;
  const negativeSentiment = literature.filter(p => p.sentiment_label === 'Negative').length;
  const neutralSentiment = literature.filter(p => p.sentiment_label === 'Neutral').length;
  
  const avgSentiment = literature.length > 0 
    ? (literature.reduce((sum, p) => sum + (p.sentiment_score || 0), 0) / literature.length).toFixed(3)
    : 0;

  // Topic distribution (simulated)
  const topics = [
    { topic: 'Genomics', count: Math.floor(totalPapers * 0.3) },
    { topic: 'Drug Discovery', count: Math.floor(totalPapers * 0.25) },
    { topic: 'Biomarkers', count: Math.floor(totalPapers * 0.2) },
    { topic: 'Clinical Trials', count: Math.floor(totalPapers * 0.15) },
    { topic: 'AI/ML', count: Math.floor(totalPapers * 0.1) },
  ];

  // Entity extraction (simulated)
  const entities = [
    { entity: 'BRCA1', count: 45, type: 'Gene' },
    { entity: 'TP53', count: 38, type: 'Gene' },
    { entity: 'EGFR', count: 32, type: 'Gene' },
    { entity: 'Cancer', count: 120, type: 'Disease' },
    { entity: 'Mutation', count: 85, type: 'Process' },
  ];

  // Recent papers
  const recentPapers = literature.slice(0, 5);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Literature Mining & NLP Analysis</Typography>
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="primary">Total Papers</Typography>
            <Typography variant="h4">{totalPapers}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="success.main">Positive Sentiment</Typography>
            <Typography variant="h4">{positiveSentiment}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="error.main">Negative Sentiment</Typography>
            <Typography variant="h4">{negativeSentiment}</Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary">Avg Sentiment Score</Typography>
            <Typography variant="h4">{avgSentiment}</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Charts and Analysis */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Topic Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topics}>
                <XAxis dataKey="topic" />
                <YAxis />
                
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Sentiment Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { sentiment: 'Positive', count: positiveSentiment },
                { sentiment: 'Neutral', count: neutralSentiment },
                { sentiment: 'Negative', count: negativeSentiment },
              ]}>
                <XAxis dataKey="sentiment" />
                <YAxis />
                
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Entity Extraction */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Extracted Entities</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {entities.map((entity, index) => (
              <Chip
                key={index}
                label={`${entity.entity} (${entity.count})`}
                color={entity.type === 'Gene' ? 'primary' : entity.type === 'Disease' ? 'error' : 'default'}
                variant="outlined"
                size="medium"
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Recent Papers */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Recent Publications</Typography>
          <List>
            {recentPapers.map((paper, index) => (
              <ListItem key={paper.id || index} alignItems="flex-start">
                <ListItemAvatar>
                  <Avatar>{paper.title?.charAt(0) || 'P'}</Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={paper.title || `Paper ${index + 1}`}
                  secondary={
                    <React.Fragment>
                      <Typography component="span" variant="body2" color="text.primary">
                        {paper.abstract?.substring(0, 150) || 'Abstract not available'}...
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip 
                          label={paper.sentiment_label || 'Neutral'} 
                          size="small"
                          color={paper.sentiment_label === 'Positive' ? 'success' : paper.sentiment_label === 'Negative' ? 'error' : 'default'}
                        />
                        <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                          Score: {paper.sentiment_score?.toFixed(3) || 'N/A'}
                        </Typography>
                      </Box>
                    </React.Fragment>
                  }
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Literature Database</Typography>
          <DataGrid
            rows={literature}
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
