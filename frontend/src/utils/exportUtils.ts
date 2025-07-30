import * as XLSX from 'xlsx';

export interface ExportOptions {
  filename?: string;
  format?: 'csv' | 'json' | 'excel';
  includeHeaders?: boolean;
}

export const exportToCSV = (data: any[], options: ExportOptions = {}) => {
  const { filename = 'export', includeHeaders = true } = options;
  
  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  let csvContent = '';

  if (includeHeaders) {
    csvContent += headers.join(',') + '\n';
  }

  data.forEach(row => {
    const values = headers.map(header => {
      const value = row[header];
      // Handle values that contain commas or quotes
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    });
    csvContent += values.join(',') + '\n';
  });

  downloadFile(csvContent, `${filename}.csv`, 'text/csv');
};

export const exportToJSON = (data: any[], options: ExportOptions = {}) => {
  const { filename = 'export' } = options;
  
  const jsonContent = JSON.stringify(data, null, 2);
  downloadFile(jsonContent, `${filename}.json`, 'application/json');
};

export const exportToExcel = (data: any[], options: ExportOptions = {}) => {
  const { filename = 'export' } = options;
  
  if (data.length === 0) return;

  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');
  
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  
  downloadBlob(blob, `${filename}.xlsx`);
};

export const downloadFile = (content: string, filename: string, mimeType: string) => {
  const blob = new Blob([content], { type: mimeType });
  downloadBlob(blob, filename);
};

export const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const exportData = (data: any[], options: ExportOptions = {}) => {
  const { format = 'csv' } = options;
  
  switch (format) {
    case 'csv':
      exportToCSV(data, options);
      break;
    case 'json':
      exportToJSON(data, options);
      break;
    case 'excel':
      exportToExcel(data, options);
      break;
    default:
      exportToCSV(data, options);
  }
}; 