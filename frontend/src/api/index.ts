import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const fetchVariants = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/variants`, { params });
  return response.data;
};

export const fetchDatasets = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/datasets`, { params });
  return response.data;
};

export const fetchDrugTargets = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/drugs`, { params });
  return response.data;
};

export const fetchLiterature = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/literature`, { params });
  return response.data;
};

export const fetchSamples = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/samples`, { params });
  return response.data;
};

export const fetchGeneExpression = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/gene-expression`, { params });
  return response.data;
};

export const fetchAnnotations = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/annotations`, { params });
  return response.data;
};

export const fetchMolecules = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/molecules`, { params });
  return response.data;
};

export const fetchGWAS = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/gwas`, { params });
  return response.data;
};

export const fetchVariantPrioritization = async (params = {}) => {
  const response = await axios.get(`${API_URL}/api/v1/variant-prioritization`, { params });
  return response.data;
};

// ML Prediction API Functions
export const predictVariantPathogenicity = async (variantData: {
  chromosome: string;
  position: number;
  reference_allele: string;
  alternate_allele: string;
  quality_score?: number;
  allele_frequency?: number;
}) => {
  const response = await axios.post(`${API_URL}/api/v1/predict/variant`, variantData);
  return response.data;
};

export const predictDrugResponse = async (drugData: {
  drug_name: string;
  molecular_weight: number;
  logp: number;
  hbd: number;
  hba: number;
  drug_likeness: number;
  patient_age: number;
  patient_gender: string;
}) => {
  const response = await axios.post(`${API_URL}/api/v1/predict/drug-response`, drugData);
  return response.data;
};

export const predictBiomarker = async (biomarkerData: {
  gene_name: string;
  expression_value: number;
  sample_type: string;
}) => {
  const response = await axios.post(`${API_URL}/api/v1/predict/biomarker`, biomarkerData);
  return response.data;
};

export const batchPredictVariants = async (variants: Array<{
  chromosome: string;
  position: number;
  reference_allele: string;
  alternate_allele: string;
  quality_score?: number;
  allele_frequency?: number;
}>) => {
  const response = await axios.post(`${API_URL}/api/v1/batch/predict-variants`, variants);
  return response.data;
};

export const getModelStatus = async () => {
  const response = await axios.get(`${API_URL}/api/v1/models/status`);
  return response.data;
};

export const getModelPerformance = async () => {
  const response = await axios.get(`${API_URL}/api/v1/models/performance`);
  return response.data;
}; 