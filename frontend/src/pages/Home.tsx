import React from 'react';
import { AppBar, Tabs, Tab, Box } from '@mui/material';
import VariantTab from '../features/VariantTab';
import DrugResponseTab from '../features/DrugResponseTab';
import BiomarkerTab from '../features/BiomarkerTab';
import LiteratureTab from '../features/LiteratureTab';
import AnnotationTab from '../features/AnnotationTab';
import MoleculeTab from '../features/MoleculeTab';
import GWASTab from '../features/GWASTab';
import VariantPrioritizationTab from '../features/VariantPrioritizationTab';

const tabLabels = [
  'Variant Interpretation',
  'Drug Response Prediction',
  'Biomarker Discovery',
  'Literature Mining',
  'Genome Annotation',
  'Molecule Generation',
  'GWAS Enhancer',
  'Variant Prioritization',
];

const tabComponents = [
  <VariantTab />, <DrugResponseTab />, <BiomarkerTab />, <LiteratureTab />, <AnnotationTab />, <MoleculeTab />, <GWASTab />, <VariantPrioritizationTab />
];

export default function Home() {
  const [value, setValue] = React.useState(0);
  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };
  return (
    <Box sx={{ width: '100%' }}>
      <AppBar position="static" color="default">
        <Tabs value={value} onChange={handleChange} variant="scrollable" scrollButtons="auto">
          {tabLabels.map((label, idx) => (
            <Tab label={label} key={label} />
          ))}
        </Tabs>
      </AppBar>
      <Box sx={{ p: 3 }}>
        {tabComponents[value]}
      </Box>
    </Box>
  );
} 