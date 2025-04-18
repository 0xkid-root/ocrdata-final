import React, { useState, useEffect } from 'react';
import { Upload, FileText, AlertCircle, Loader2, Download } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import axios, { AxiosError } from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import { cn } from './lib/utils';
import * as XLSX from 'xlsx';

interface ExtractedData {
  name: string;
  age: number;
  house_number: string;
  spouse_or_parent_name?: string;
  gender?: string;
  tag_number?: string;
  voter_surname?: string;
  surname?: string; // Added surname field
  section_number?: string;
  section_name?: string;
  polling_station_number?: string;
  polling_station_name?: string;
}

interface ErrorResponse {
  detail: string;
}

const API_URL = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedData[]>([]);
  const [serverStatus, setServerStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0]);
        setError(null);
      }
    },
    onDropRejected: () => {
      setError('Please select a valid PDF file');
      setFile(null);
    },
  });

  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/health`, {
        headers: { 'Content-Type': 'application/json' },
      });
      setServerStatus(response.status === 200 ? 'online' : 'offline');
    } catch (err) {
      setServerStatus('offline');
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setExtractedData([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/api/extract`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: false,
      });

      if (response.status === 200 && Array.isArray(response.data)) {
        setExtractedData(response.data);
        toast.success('Data extracted successfully!');
      } else {
        setError('Unexpected response format from server');
        toast.error('Unexpected server response');
      }
    } catch (err) {
      const error = err as AxiosError<ErrorResponse>;
      const errorMessage = error.response?.data?.detail || 
                          (error.code === 'ECONNABORTED' ? 'Request timed out' : 
                          error.message.includes('CORS') ? 'CORS issue: Check backend configuration' : 
                          'Failed to process the PDF. Please try again.');
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const downloadExcel = () => {
    if (extractedData.length === 0) {
      toast.error('No data to export');
      return;
    }

    const worksheet = XLSX.utils.json_to_sheet(extractedData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'ExtractedData');
    XLSX.writeFile(workbook, 'extracted_data.xlsx');
    toast.success('Data exported to Excel!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
            Hindi PDF Data Extractor
          </h1>

          {serverStatus === 'offline' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
              <div className="flex items-center gap-2 text-red-600">
                <AlertCircle className="h-5 w-5" />
                <span>Server is offline. Please ensure the backend server is running at http://localhost:8000.</span>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed border-gray-300 rounded-lg p-8 text-center transition-colors duration-200",
                  isDragActive && "border-blue-500 bg-blue-50",
                  "hover:border-blue-400 hover:bg-blue-50/50"
                )}
              >
                <input {...getInputProps()} />
                <div className="cursor-pointer flex flex-col items-center">
                  <Upload
                    className={cn(
                      "h-12 w-12 mb-4 transition-colors duration-200",
                      isDragActive ? "text-blue-500" : "text-gray-400"
                    )}
                  />
                  <span className="text-gray-600 mb-2">
                    {file ? file.name : isDragActive ? 'Drop the PDF here' : 'Drop your PDF here or click to upload'}
                  </span>
                  <span className="text-sm text-gray-500">Only PDF files are supported</span>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={!file || loading || serverStatus === 'offline'}
                className={cn(
                  "w-full py-3 px-4 rounded-lg text-white font-medium flex items-center justify-center gap-2 transition-colors duration-200",
                  !file || loading || serverStatus === 'offline'
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                )}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <FileText className="h-5 w-5" />
                    Extract Data
                  </>
                )}
              </button>
            </form>
          </div>

          {extractedData.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Extracted Data</h2>
              <div className="space-y-4">
                {extractedData.map((data, index) => (
                  <div
                    key={index}
                    className="border rounded-lg p-4 hover:border-blue-200 transition-colors duration-200"
                  >
                    <div className="space-y-2">
                      <p className="text-lg font-medium">नाम: {data.name}</p>
                      <p className="text-gray-600">आयु: {data.age} वर्ष</p>
                      <p className="text-gray-600">मकान संख्या: {data.house_number}</p>
                      {data.spouse_or_parent_name && (
                        <p className="text-gray-600">पति/पिता का नाम: {data.spouse_or_parent_name}</p>
                      )}
                      {data.gender && (
                        <p className="text-gray-600">लिंग: {data.gender}</p>
                      )}
                      {data.tag_number && (
                        <p className="text-gray-600">टैग नंबर: {data.tag_number}</p>
                      )}
                      {data.voter_surname && (
                        <p className="text-gray-600">उपनाम: {data.voter_surname}</p>
                      )}
                      {data.surname && ( // Added display for surname
                        <p className="text-gray-600">उपनाम: {data.surname}</p>
                      )}
                      {data.section_number && data.section_name && (
                        <p className="text-gray-600">अनुभाग संख्या और नाम: {data.section_number} - {data.section_name}</p>
                      )}
                      {data.polling_station_number && data.polling_station_name && (
                        <p className="text-gray-600">पोलिंग स्टेशन संख्या और नाम: {data.polling_station_number} - {data.polling_station_name}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <button
                onClick={downloadExcel}
                className="mt-4 w-full py-2 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
              >
                <Download className="h-5 w-5" />
                Download Excel
              </button>
            </div>
          )}
        </div>
      </div>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;