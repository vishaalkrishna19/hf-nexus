import React, { useState, useEffect } from 'react';
import './Resume.scss';
import { useNavigate } from 'react-router-dom';
import { useResumeContext } from '../../context/ResumeContext';
import toast, { Toaster } from 'react-hot-toast';
import * as XLSX from 'xlsx';

const Resume = () => {
  const navigate = useNavigate();
  const { parsedResumes, storeResumeData } = useResumeContext();
  
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [allParsedData, setAllParsedData] = useState(parsedResumes || []);
  const [error, setError] = useState('');
  const [currentlyProcessing, setCurrentlyProcessing] = useState('');
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [successMessage, setSuccessMessage] = useState('');
  // Add state for ranking loading
  const [rankingLoading, setRankingLoading] = useState(false);
  const [atsResults, setAtsResults] = useState([]); // [{score, status, details}...]
  const [rawAtsResults, setRawAtsResults] = useState([]); // For immediate ATS after upload
  const [rawParsedData, setRawParsedData] = useState([]); // For immediate raw data
  const [uploadType, setUploadType] = useState('files'); // 'files' or 'excel'
  const [excelFile, setExcelFile] = useState(null);
  const [driveLinks, setDriveLinks] = useState([]);

  // Set parsed data from context when component mounts
  useEffect(() => {
    if (parsedResumes.length > 0) {
      setAllParsedData(parsedResumes);
    }
  }, [parsedResumes]);

  const handleFileChange = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'image/jpeg',
      'image/jpg', 
      'image/png',
      'image/bmp',
      'image/tiff'
    ];
    const validFiles = selectedFiles.filter(file => validTypes.includes(file.type));
    const invalidFiles = selectedFiles.filter(file => !validTypes.includes(file.type));
    if (invalidFiles.length > 0) {
      setError(`Invalid files: ${invalidFiles.map(f => f.name).join(', ')}. Please select only PDF, DOCX, or image files.`);
    } else {
      setError('');
    }
    setFiles(validFiles);
    setAllParsedData([]);
    setAtsResults([]);
    setRawAtsResults([]);
    setRawParsedData([]);
    // Remove immediate ATS check and raw parsing
  };

  const checkATS = async (resume) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/check-ats/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume }),
      });
      if (!response.ok) throw new Error('ATS check failed');
      return await response.json();
    } catch (e) {
      return { score: 0, status: 'Not Compliant', details: ['ATS check failed'] };
    }
  };

  const handleExcelChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && (selectedFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                        selectedFile.type === 'application/vnd.ms-excel')) {
      setExcelFile(selectedFile);
      
      // Read and extract Google Drive links from Excel
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = event.target.result;
          const workbook = XLSX.read(data, { type: 'binary' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          
          // Extract Google Drive links from Excel data
          const links = [];
          jsonData.forEach((row, index) => {
            // Look for Google Drive links in any column
            Object.values(row).forEach(cellValue => {
              if (typeof cellValue === 'string' && 
                  (cellValue.includes('drive.google.com') || cellValue.includes('docs.google.com'))) {
                links.push({
                  index: index + 1,
                  url: cellValue,
                  name: row.Name || row.name || `Candidate_${index + 1}`
                });
              }
            });
          });
          
          setDriveLinks(links);
          console.log('Extracted Google Drive links:', links);
          
        } catch (error) {
          console.error('Error reading Excel file:', error);
          alert('Error reading Excel file. Please make sure it\'s a valid Excel file.');
        }
      };
      
      reader.readAsBinaryString(selectedFile);
    } else {
      alert('Please select a valid Excel file (.xlsx or .xls)');
      setExcelFile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (uploadType === 'files' && files.length === 0) {
      setError('Please select at least one file');
      return;
    }
    
    if (uploadType === 'excel' && !excelFile) {
      setError('Please select an Excel file with Google Drive links');
      return;
    }

    setLoading(true);
    setError('');
    setAllParsedData([]);
    setSuccessMessage('');
    setAtsResults([]);
    
    const parsedResults = [];

    if (uploadType === 'excel' && excelFile) {
      // Process Excel with Google Drive links
      setCurrentlyProcessing('Processing Excel file and testing Google Drive links...');
      
      try {
        const formData = new FormData();
        formData.append('excel_file', excelFile);
        
        const response = await fetch('http://127.0.0.1:8000/api/process-excel-drive-links/', {
          method: 'POST',
          body: formData,
        });

        // Get response text first to debug
        const responseText = await response.text();
        console.log('Raw response:', responseText);

        if (!response.ok) {
          let errorMessage = `HTTP error! status: ${response.status}`;
          try {
            const errorData = JSON.parse(responseText);
            if (errorData.error) {
              errorMessage = errorData.error;
            }
          } catch (parseError) {
            // Use the raw response text if JSON parsing fails
            errorMessage = responseText || errorMessage;
          }
          throw new Error(errorMessage);
        }

        const result = JSON.parse(responseText);
        
        if (result.success) {
          // Show accessibility report
          if (result.accessibility_report && result.accessibility_report.inaccessible > 0) {
            console.warn('Some Google Drive links are not accessible:', result.accessibility_report);
            
            const inaccessibleDetails = result.accessibility_report.inaccessible_details
              .map(item => `• ${item.name}: ${item.error}`)
              .join('\n');
            
            const warningMessage = `Warning: ${result.accessibility_report.inaccessible} of ${result.total_links} Google Drive links are not accessible:\n\n${inaccessibleDetails}\n\nPlease ensure files are set to "Anyone with the link can view"`;
            
            if (result.successful_parses === 0) {
              throw new Error(warningMessage);
            } else {
              // Show warning but continue processing
              console.warn(warningMessage);
              setError(`⚠️ ${result.accessibility_report.inaccessible} files could not be accessed. Successfully processed ${result.successful_parses} files.`);
            }
          }
          
          // Process each parsed resume from the backend
          for (let i = 0; i < result.parsed_resumes.length; i++) {
            const resumeData = result.parsed_resumes[i];
            setCurrentlyProcessing(`Processing resume ${i + 1} of ${result.parsed_resumes.length}: ${resumeData.name || 'Unknown'}`);
            
            // Only run ATS check for successfully parsed resumes
            if (!resumeData.error) {
              const ats = await checkATS(resumeData);
              resumeData.ats = ats;
            } else {
              // Set default ATS for failed resumes
              resumeData.ats = { score: 0, status: 'Error', details: [resumeData.error] };
            }
            
            parsedResults.push(resumeData);
          }
          
          console.log(`Processed ${result.successful_parses} of ${result.total_links} resumes successfully`);
        } else {
          throw new Error(result.error || 'Failed to process Excel file with Google Drive links');
        }
        
      } catch (error) {
        console.error('Error processing Excel with Google Drive links:', error);
        setError('Error processing Excel file: ' + error.message);
        setLoading(false);
        return;
      }
    } else {
      // Process regular files (existing logic)
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setCurrentlyProcessing(`Processing ${file.name} (${i + 1}/${files.length})`);
        
        const formData = new FormData();
        formData.append('resume_file', file);

        try {
          const response = await fetch('http://127.0.0.1:8000/', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();
          
          if (result.success) {
            const parsed = {
              filename: file.name,
              ...result.parsed_data
            };
            const ats = await checkATS(parsed);
            parsed.ats = ats;
            parsedResults.push(parsed);
          } else {
            throw new Error(result.error || 'Failed to parse resume');
          }
          
        } catch (error) {
          console.error(`Error parsing ${file.name}:`, error);
          parsedResults.push({
            filename: file.name,
            error: error.message,
            name: 'Error',
            email: 'Error',
            phone: 'Error',
            github: 'Error',
            linkedin: 'Error',
            school: 'Error',
            college: 'Error',
            tenth_marks: 'Error',
            twelfth_marks: 'Error',
            cgpa: 'Error',
            internships: [],
            internship_projects: [],
            personal_projects: [],
            tech_stack: [],
            achievements: []
          });
        }
      }
    }
    
    setAllParsedData(parsedResults);
    setAtsResults(parsedResults.map(r => r.ats || { score: 0, status: 'Not Compliant', details: [] }));
    // Store the parsed data in context
    storeResumeData(parsedResults);
    setCurrentlyProcessing('');
    setLoading(false);
    // Set success message
    const resumeCount = parsedResults.length;
    setSuccessMessage(`Successfully processed ${resumeCount} resume${resumeCount !== 1 ? 's' : ''}!`);
    
    // Clear the success message after 5 seconds
    setTimeout(() => {
      setSuccessMessage('');
    }, 5000);
  };

  const resetForm = () => {
    setFiles([]);
    setExcelFile(null);
    setDriveLinks([]);
    setAllParsedData([]);
    storeResumeData([]); // Clear the stored data
    setError('');
    setCurrentlyProcessing('');
    setSuccessMessage('');
  };

  const exportToExcel = async () => {
    if (allParsedData.length === 0) {
      alert('No data to export');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/export-excel/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          multiple_resumes: allParsedData,
          filename: 'multiple_resumes'
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `resume_data_extracted_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('Failed to export Excel file');
      }
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      alert('Error exporting to Excel: ' + error.message);
    }
  };

  // Handler for Rank Resumes
  const handleRankResumes = async () => {
    if (allParsedData.length === 0) {
      alert('No data to rank');
      return;
    }
    setRankingLoading(true);
    // Show toast only for ranking resumes, with a leading icon
    const toastId = toast.loading(
      <span>
        <span role="img" aria-label="ranking" style={{ marginRight: 8 }}>🏆</span>
        Ranking resumes...
      </span>
    );
    try {
      const response = await fetch('http://127.0.0.1:8000/api/rank-resumes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resumes: allParsedData }),
      });
      if (!response.ok) throw new Error('Failed to rank resumes');
      const ranked = await response.json();
      toast.success('Ranking complete!', { id: toastId });
      // Navigate to /ranked with ranked data
      navigate('/ranked', { state: { rankedResumes: ranked.ranked_resumes } });
    } catch (err) {
      toast.error('Error ranking resumes: ' + err.message, { id: toastId });
    }
    setRankingLoading(false);
  };

  const toggleRowExpansion = (index) => {
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(index)) {
      newExpandedRows.delete(index);
    } else {
      newExpandedRows.add(index);
    }
    setExpandedRows(newExpandedRows);
  };

  const formatListData = (data, isExpanded = false) => {
    if (!data || !Array.isArray(data) || data.length === 0) return 'Not found';
    
    if (isExpanded) {
      return data; // Return array for expanded view
    } else {
      // Show first 2 items and add "..." if there are more
      if (data.length <= 2) {
        return data.join(', ');
      } else {
        return `${data.slice(0, 2).join(', ')}... (+${data.length - 2} more)`;
      }
    }
  };

  const renderCellContent = (data, isExpanded, type = 'text') => {
    if (type === 'list' && isExpanded && Array.isArray(data) && data.length > 0) {
      return (
        <ul className="expanded-list">
          {data.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      );
    }
    
    if (type === 'list') {
      return formatListData(data, false);
    }
    
    return data;
  };

  const truncateText = (text, maxLength = 30, isExpanded = false) => {
    if (!text || text === 'Not found' || isExpanded) return text;
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  };

  const handleViewProfile = (data) => {
    navigate(`/profile/${data.name?.replace(/\s+/g, '-').toLowerCase() || 'candidate'}`, {
      state: { profileData: data }
    });
  };

  return (
    <div className="resume-parser">
      <Toaster position="top-center" />
      <div className="background-pattern"></div>
      <div className="container">
        <div className="hero-section glass-card">
          <h1>
            Resume Parser
            <img 
              src="https://assets.www.happyfox.com/v2/images/zendesk-alternative/hf-mini.png" 
              alt="HappyFox AI" 
              className="ai-logo-image"
            />
          </h1>
          <p className="subtitle">Upload multiple resumes in PDF or DOCX format to extract key information</p>
        </div>
        
        <form onSubmit={handleSubmit} className="parser-form glass-card">
          <div className="form-section">
            <h2>Upload Method</h2>

            <div className="upload-method-section">
              <div className="method-cards">
                <div 
                  className={`method-card ${uploadType === 'files' ? 'active' : ''}`}
                  onClick={() => setUploadType('files')}
                >
                  <div className="method-card-icon">
                    <span className="icon">📄</span>
                  </div>
                  <div className="method-card-content">
                    <h3>Upload Files Directly</h3>
                    <p>Upload PDF, DOCX, or image files directly from your computer</p>
                   
                  </div>
                  <div className="method-card-radio">
                    <input
                      type="radio"
                      value="files"
                      checked={uploadType === 'files'}
                      onChange={() => {}}
                      className="radio-hidden"
                    />
                    <span className="radio-custom"></span>
                  </div>
                </div>

                <div 
                  className={`method-card ${uploadType === 'excel' ? 'active' : ''}`}
                  onClick={() => setUploadType('excel')}
                >
                  <div className="method-card-icon">
                    <span className="icon">📊</span>
                  </div>
                  <div className="method-card-content">
                    <h3>Excel with Google Drive Links</h3>
                    <p>Upload an Excel file containing Google Drive links to PDF resumes</p>
                   
                  </div>
                  <div className="method-card-radio">
                    <input
                      type="radio"
                      value="excel"
                      checked={uploadType === 'excel'}
                      onChange={() => {}}
                      className="radio-hidden"
                    />
                    <span className="radio-custom"></span>
                  </div>
                </div>
              </div>
            </div>

            {uploadType === 'files' ? (
              // Existing file upload section
              <div className="input-group">
                <label>Select Resume Files:</label>
                <div className="custom-file-input">
                  <input
                    type="file"
                    id="resumeFiles"
                    accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.bmp,.tiff"
                    onChange={handleFileChange}
                    className="file-input-hidden"
                    multiple
                  />
                  <label htmlFor="resumeFiles" className="file-input-label">
                    <span className="file-icon">📄</span>
                    <span className="file-text">Choose Files</span>
                    <span className="file-button">Browse</span>
                  </label>
                </div>
                <small>Supported formats: PDF (.pdf), Word Document (.docx, .doc) - Multiple files allowed</small>
              </div>
            ) : (
              // New Excel upload section
              <div className="input-group">
                <label>Select Excel File with Google Drive Links:</label>
                <div className="custom-file-input">
                  <input
                    type="file"
                    id="excelFile"
                    accept=".xlsx,.xls"
                    onChange={handleExcelChange}
                    className="file-input-hidden"
                  />
                  <label htmlFor="excelFile" className="file-input-label">
                    <span className="file-icon">📊</span>
                    <span className="file-text">Choose Excel File</span>
                    <span className="file-button">Browse</span>
                  </label>
                </div>
                <small>Excel file should contain Google Drive links to PDF resumes in any column</small>
              </div>
            )}
            
            {/* Show file info for regular files */}
            {uploadType === 'files' && files.length > 0 && (
              <div className="file-info glass-inner">
                <div className="file-info-header">
                  <h3>Selected Files ({files.length}):</h3>
                  {/* <span className="file-info-status">
                    {rawAtsResults.length === files.length
                      ? <span className="status-ready">ATS check complete for all files</span>
                      : <span className="status-processing">Checking ATS compliance...</span>
                    }
                  </span> */}
                </div>
                <div className="files-list">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="file-item"
                      style={{
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        position: 'relative',
                        paddingTop: '1.5rem'
                      }}
                    >
                      {/* ATS score at top right */}
                      {rawAtsResults[index] && (
                        <span
                          style={{
                            position: 'absolute',
                            top: 10,
                            right: 12,
                            color:
                              rawAtsResults[index].status === 'Excellent'
                                ? '#28a745'
                                : rawAtsResults[index].status === 'Good'
                                ? '#ffc107'
                                : rawAtsResults[index].status === 'Fair'
                                ? '#fd7e14'
                                : '#dc3545',
                            fontWeight: 400,
                            display: 'inline-block',
                            borderRadius: 6,
                            background:
                              rawAtsResults[index].status === 'Excellent'
                                ? 'rgba(40,167,69,0.08)'
                                : rawAtsResults[index].status === 'Good'
                                ? 'rgba(255,193,7,0.13)'
                                : rawAtsResults[index].status === 'Fair'
                                ? 'rgba(253,126,20,0.13)'
                                : 'rgba(220,53,69,0.08)',
                            padding: '2px 12px',
                            fontSize: '1rem',
                            zIndex: 2,
                            boxShadow: '0 1px 4px 0 rgba(0,0,0,0.04)'
                          }}
                          title={rawAtsResults[index].details && rawAtsResults[index].details.length > 0 ? rawAtsResults[index].details.join('\n') : ''}
                        >
                         ATS Score : {rawAtsResults[index].score}
                        </span>
                      )}
                      <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                        {/* Show ATS status label (color bar) */}
                        {rawAtsResults[index] && (
                          <span
                            style={{
                              marginLeft: 12,
                              color:
                                rawAtsResults[index].status === 'Excellent'
                                  ? '#28a745'
                                  : rawAtsResults[index].status === 'Good'
                                  ? '#ffc107'
                                  : rawAtsResults[index].status === 'Fair'
                                  ? '#fd7e14'
                                  : '#dc3545',
                              fontWeight: 600,
                              display: 'inline-block',
                              borderRadius: 6,
                              background:
                                rawAtsResults[index].status === 'Excellent'
                                  ? 'rgba(40,167,69,0.08)'
                                  : rawAtsResults[index].status === 'Good'
                                  ? 'rgba(255,193,7,0.13)'
                                  : rawAtsResults[index].status === 'Fair'
                                  ? 'rgba(253,126,20,0.13)'
                                  : 'rgba(220,53,69,0.08)',
                              padding: '2px 10px'
                            }}
                            title={rawAtsResults[index].details && rawAtsResults[index].details.length > 0 ? rawAtsResults[index].details.join('\n') : ''}
                          >
                            {rawAtsResults[index].status}
                          </span>
                        )}
                      </div>
                      {/* ATS accuracy message */}
                      {rawAtsResults[index] && (
                        <div
                          style={{
                            marginTop: 4,
                            fontSize: '0.92rem',
                            color:
                              rawAtsResults[index].status === 'Excellent'
                                ? '#28a745'
                                : rawAtsResults[index].status === 'Good'
                                ? '#ffc107'
                                : rawAtsResults[index].status === 'Fair'
                                ? '#fd7e14'
                                : '#dc3545',
                            background:
                              rawAtsResults[index].status === 'Excellent'
                                ? 'rgba(40,167,69,0.08)'
                                : rawAtsResults[index].status === 'Good'
                                ? 'rgba(255,193,7,0.10)'
                                : rawAtsResults[index].status === 'Fair'
                                ? 'rgba(253,126,20,0.10)'
                                : 'rgba(220,53,69,0.10)',
                            borderRadius: 5,
                            padding: '2px 10px',
                            fontWeight: 400,
                            marginLeft: 2,
                            marginBottom: 2,
                            display: 'inline-block'
                          }}
                        >
                          {rawAtsResults[index].status === 'Excellent' && "Data extraction will be highly accurate."}
                          {rawAtsResults[index].status === 'Good' && "Data extraction will be mostly accurate."}
                          {rawAtsResults[index].status === 'Fair' && "Data extraction may not be fully accurate."}
                          {rawAtsResults[index].status === 'Poor' && "Data extraction may be inaccurate or incomplete."}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Show Excel info and Google Drive links */}
            {uploadType === 'excel' && excelFile && (
              <div className="file-info glass-inner">
                <div className="file-info-header">
                  <h3>Excel File: {excelFile.name}</h3>
                  <span className="file-info-status">
                    {driveLinks.length > 0 
                      ? <span className="status-ready">Found {driveLinks.length} Google Drive links</span>
                      : <span className="status-processing">Scanning for Google Drive links...</span>
                    }
                  </span>
                </div>
               
              </div>
            )}
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            {currentlyProcessing && (
              <div className="processing-message">
                {currentlyProcessing}
              </div>
            )}
            
            {successMessage && (
              <div className="success-message">
                <span className="success-icon">✓</span> {successMessage}
              </div>
            )}
          </div>

          <button 
            type="submit" 
            className="submit-btn glass-btn-primary" 
            disabled={loading || (uploadType === 'files' && files.length === 0) || (uploadType === 'excel' && !excelFile)}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {uploadType === 'excel' ? 'Processing Excel & Downloading PDFs...' : 'Processing Resumes...'}
              </>
            ) : (
              uploadType === 'excel' 
                ? `Process Excel File (${driveLinks.length} links)`
                : `Parse ${files.length} Resume${files.length !== 1 ? 's' : ''}`
            )}
          </button>
        </form>

        {allParsedData.length > 0 && (
          <div className="results-section glass-card">
            <div className="results-header">
              <h2>Resume Data - Extracted</h2>
              <div className="header-buttons">
                <button onClick={exportToExcel} className="export-btn glass-btn">
                  📊 Export as Excel
                </button>
                <button
                  onClick={handleRankResumes}
                  className="rank-btn glass-btn"
                  disabled={rankingLoading}
                  style={{ background: '#007bff', color: 'white' }}
                >
                  {rankingLoading ? (
                    <>
                      <span className="loading-spinner"></span>
                      Ranking...
                    </>
                  ) : (
                    'Rank Resumes'
                  )}
                </button>
                <button onClick={resetForm} className="reset-btn glass-btn">
                  Parse More Resumes
                </button>
              </div>
            </div>
            
            <div className="table-container">
              <table className="resume-table">
                <thead>
                  <tr>
                    <th>View</th>
                    <th>S.No</th>
                    <th>File Name</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>GitHub</th>
                    <th>LinkedIn</th>
                    <th>School</th>
                    <th>College</th>
                    <th>10th Marks</th>
                    <th>12th Marks</th>
                    <th>CGPA</th>
                    <th>Internships / Activities</th>
                    <th>Internship Projects</th>
                    <th>Personal Projects</th>
                    <th>Tech Stack</th>
                    <th>Achievements</th>
                    <th>Languages</th> {/* New column */}
                    <th>ATS Status</th> {/* New column */}
                  </tr>
                </thead>
                <tbody>
                  {allParsedData.map((data, index) => {
                    const isExpanded = expandedRows.has(index);
                    const ats = data.ats || { score: 0, status: 'Not Compliant', details: [] };
                    return (
                      <React.Fragment key={index}>
                        <tr 
                          className={`${data.error ? 'error-row' : ''} ${isExpanded ? 'expanded-row' : ''} clickable-row`}
                          onClick={() => toggleRowExpansion(index)}
                          style={{ cursor: 'pointer' }}
                          title={isExpanded ? 'Click to collapse row' : 'Click to expand row'}
                        >
                          <td className="expand-cell">
                            <button 
                              className="expand-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewProfile(data);
                              }}
                              title="View detailed profile"
                            >
                              <span className="view-icon">View</span>
                            </button>
                          </td>
                          <td>{index + 1}</td>
                          <td className="filename-cell">{truncateText(data.filename, 20, isExpanded)}</td>
                          <td>{truncateText(data.name || 'Not found', 25, isExpanded)}</td>
                          <td>{truncateText(data.email || 'Not found', 25, isExpanded)}</td>
                          <td>{truncateText(data.phone || 'Not found', 15, isExpanded)}</td>
                          <td>{truncateText(data.github || 'Not found', 25, isExpanded)}</td>
                          <td>{truncateText(data.linkedin || 'Not found', 25, isExpanded)}</td>
                          <td>{truncateText(data.school || 'Not found', 30, isExpanded)}</td>
                          <td>{truncateText(data.college || 'Not found', 30, isExpanded)}</td>
                          <td>{data.tenth_marks ? `${data.tenth_marks}%` : 'Not found'}</td>
                          <td>{data.twelfth_marks ? `${data.twelfth_marks}%` : 'Not found'}</td>
                          <td>{data.cgpa || 'Not found'}</td>
                          <td>{renderCellContent(data.internships, isExpanded, 'list')}</td>
                          <td>{renderCellContent(data.internship_projects, isExpanded, 'list')}</td>
                          <td>{renderCellContent(data.personal_projects, isExpanded, 'list')}</td>
                          <td>{renderCellContent(data.tech_stack, isExpanded, 'list')}</td>
                          <td>{renderCellContent(data.achievements, isExpanded, 'list')}</td>
                          <td>
                            {Array.isArray(data.languages) && data.languages.length > 0
                              ? (
                                <ul className="expanded-list">
                                  {data.languages.map((lang, i) => (
                                    <li key={i}>
                                      {lang.language}
                                      {lang.proficiency ? ` (${lang.proficiency})` : ''}
                                    </li>
                                  ))}
                                </ul>
                              )
                              : 'Not found'
                            }
                          </td>
                          <td>
                            <span
                              style={{
                                color:
                                  ats.status === 'Excellent'
                                    ? '#28a745'
                                    : ats.status === 'Good'
                                    ? '#ffc107'
                                    : ats.status === 'Fair'
                                    ? '#fd7e14'
                                    : '#dc3545',
                                fontWeight: 600,
                                display: 'inline-block',
                                borderRadius: 6,
                                background:
                                  ats.status === 'Excellent'
                                    ? 'rgba(40,167,69,0.08)'
                                    : ats.status === 'Good'
                                    ? 'rgba(255,193,7,0.13)'
                                    : ats.status === 'Fair'
                                    ? 'rgba(253,126,20,0.13)'
                                    : 'rgba(220,53,69,0.08)',
                                padding: '2px 10px'
                              }}
                              title={ats.details && ats.details.length > 0 ? ats.details.join('\n') : ''}
                            >
                              {ats.status} ({ats.score})
                            </span>
                          </td>
                        </tr>

                        {isExpanded && (
                          <tr className="expanded-content">
                            <td colSpan="17">
                              <div className="expanded-data-container">
                              
                          
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Resume;