import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { useNavigate } from 'react-router-dom';
import './Home.scss';

const Home = () => {
  const [sheetUrl, setSheetUrl] = useState('');
  const [file, setFile] = useState(null);
  const [inputType, setInputType] = useState('url');
  const [criteria, setCriteria] = useState({
    cgpa: { min: 6.0, max: 10.0, weight: 25 },
    tenthMarks: { min: 60, max: 100, weight: 10 },
    twelfthMarks: { min: 60, max: 100, weight: 10 },
    internships: { min: 0, max: 10, weight: 15 },
    projects: { min: 1, max: 20, weight: 15 },
    techStack: { required: [], preferred: [], weight: 20 },
    achievements: { keywords: [], weight: 5 }
  });
  const [numCandidates, setNumCandidates] = useState(10);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  
  // Form input states
  const [newTech, setNewTech] = useState({ required: '', preferred: '' });
  const [newKeyword, setNewKeyword] = useState('');

  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && (selectedFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                        selectedFile.type === 'application/vnd.ms-excel')) {
      setFile(selectedFile);
      
      // Read and display the Excel file data
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = event.target.result;
          const workbook = XLSX.read(data, { type: 'binary' });
          
          // Get the first worksheet
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          
          // Convert to JSON
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          
          console.log('=== EXCEL FILE DATA ===');
          console.log('Sheet Name:', sheetName);
          console.log('Total Rows:', jsonData.length);
          console.log('Column Headers:', Object.keys(jsonData[0] || {}));
          console.log('Raw Data:', jsonData);
          console.log('========================');
          
          // Display first few rows in a formatted way
          if (jsonData.length > 0) {
            console.log('=== FIRST 5 ROWS (FORMATTED) ===');
            jsonData.slice(0, 5).forEach((row, index) => {
              console.log(`Row ${index + 1}:`, row);
            });
            console.log('===============================');
          }
          
        } catch (error) {
          console.error('Error reading Excel file:', error);
          alert('Error reading Excel file. Please make sure it\'s a valid Excel file.');
        }
      };
      
      reader.readAsBinaryString(selectedFile);
      
    } else {
      alert('Please select a valid Excel file (.xlsx or .xls)');
      setFile(null);
    }
  };

  const handleCriteriaChange = (category, field, value) => {
    setCriteria(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value
      }
    }));
  };

  const addTechStack = (type) => {
    const tech = newTech[type];
    if (tech && tech.trim()) {
      setCriteria(prev => ({
        ...prev,
        techStack: {
          ...prev.techStack,
          [type]: [...prev.techStack[type], tech.trim()]
        }
      }));
      setNewTech(prev => ({ ...prev, [type]: '' }));
    }
  };

  const removeTechStack = (type, index) => {
    setCriteria(prev => ({
      ...prev,
      techStack: {
        ...prev.techStack,
        [type]: prev.techStack[type].filter((_, i) => i !== index)
      }
    }));
  };

  const addAchievementKeyword = () => {
    if (newKeyword && newKeyword.trim()) {
      setCriteria(prev => ({
        ...prev,
        achievements: {
          ...prev.achievements,
          keywords: [...prev.achievements.keywords, newKeyword.trim()]
        }
      }));
      setNewKeyword('');
    }
  };

  const removeAchievementKeyword = (index) => {
    setCriteria(prev => ({
      ...prev,
      achievements: {
        ...prev.achievements,
        keywords: prev.achievements.keywords.filter((_, i) => i !== index)
      }
    }));
  };

  // Add this function to handle the API call
  const processWithBackend = async (excelData, criteria) => {
    try {
      console.log('DEBUG: Sending to backend:', { excelData, criteria, numCandidates });
      
      const response = await fetch('http://localhost:8000/api/shortlist-candidates/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
          candidates_data: excelData,
          criteria: criteria,
          num_candidates: numCandidates
        })
      });

      console.log('DEBUG: Backend response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('DEBUG: Backend response:', result);
      
      return result;
    } catch (error) {
      console.error('DEBUG: Error processing with backend:', error);
      throw error;
    }
  };

  // Helper function to get CSRF token
  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (inputType === 'url' && !sheetUrl) {
      alert('Please enter a Google Sheets URL');
      return;
    }
    
    if (inputType === 'file' && !file) {
      alert('Please select an Excel file');
      return;
    }

    setLoading(true);
    
    // If file is selected, process the actual Excel data
    if (inputType === 'file' && file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const data = event.target.result;
          const workbook = XLSX.read(data, { type: 'binary' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          
          console.log('=== SENDING DATA TO BACKEND ===');
          console.log('Excel Data:', jsonData);
          console.log('Criteria:', criteria);
          console.log('===============================');
          
          // Send to backend for AI processing
          const backendResults = await processWithBackend(jsonData, criteria);
          
          console.log('=== BACKEND RESPONSE DEBUG ===');
          console.log('Full backend response:', backendResults);
          console.log('Success:', backendResults.success);
          console.log('Shortlisted candidates:', backendResults.shortlisted_candidates);
          console.log('Total processed:', backendResults.total_processed);
          console.log('Total shortlisted:', backendResults.total_shortlisted);
          console.log('==============================');
          
          // Handle response properly
          let candidatesData = [];
          if (backendResults.success && backendResults.shortlisted_candidates) {
            candidatesData = backendResults.shortlisted_candidates;
          } else if (Array.isArray(backendResults)) {
            candidatesData = backendResults;
          }
          
          console.log('Final candidates data to navigate with:', candidatesData);
          
          setResults(candidatesData);
          setShowResults(true);
          setLoading(false);

          // Navigate to shortlist page with proper data
          if (candidatesData.length > 0) {
            navigate('/shortlist', {
              state: { 
                shortlistedCandidates: candidatesData,
                totalProcessed: backendResults.total_processed,
                criteria: criteria
              }
            });
          } else {
            alert('No candidates were shortlisted based on your criteria. Please adjust your criteria and try again.');
            setLoading(false);
          }
        } catch (error) {
          console.error('Error processing Excel file:', error);
          alert('Error processing data: ' + error.message);
          setLoading(false);
        }
      };
      
      reader.readAsBinaryString(file);
    } else {
      // For URL input, you might want to handle Google Sheets API integration
      // For now, showing mock data
      setTimeout(() => {
        const mockResults = [
          {
            id: 1,
            name: 'Rahul Sharma',
            email: 'rahul.sharma@student.edu',
            cgpa: 8.7,
            tenthMarks: 92,
            twelfthMarks: 88,
            internships: 2,
            projects: 5,
            techStack: ['React', 'Node.js', 'Python', 'MongoDB', 'JavaScript'],
            achievements: ['Winner - Smart India Hackathon', 'Dean\'s List Scholar', 'Best Project Award'],
            score: 94,
            priority: 1
          },
          {
            id: 2,
            name: 'Priya Patel',
            email: 'priya.patel@student.edu',
            cgpa: 8.2,
            tenthMarks: 89,
            twelfthMarks: 91,
            internships: 1,
            projects: 4,
            techStack: ['Java', 'Spring Boot', 'MySQL', 'React', 'AWS'],
            achievements: ['Google Summer of Code Participant', 'Technical Lead - College Society'],
            score: 89,
            priority: 2
          },
          {
            id: 3,
            name: 'Arjun Reddy',
            email: 'arjun.reddy@student.edu',
            cgpa: 8.5,
            tenthMarks: 85,
            twelfthMarks: 87,
            internships: 3,
            projects: 6,
            techStack: ['Python', 'Django', 'PostgreSQL', 'Docker', 'Machine Learning'],
            achievements: ['Published Research Paper', 'Internship at Microsoft', 'Coding Competition Winner'],
            score: 87,
            priority: 3
          },
          {
            id: 4,
            name: 'Sneha Gupta',
            email: 'sneha.gupta@student.edu',
            cgpa: 7.9,
            tenthMarks: 90,
            twelfthMarks: 89,
            internships: 1,
            projects: 3,
            techStack: ['JavaScript', 'Vue.js', 'PHP', 'Laravel', 'MySQL'],
            achievements: ['Scholarship Recipient', 'Volunteer Lead - NGO Project'],
            score: 83,
            priority: 4
          },
          {
            id: 5,
            name: 'Vikram Singh',
            email: 'vikram.singh@student.edu',
            cgpa: 8.1,
            tenthMarks: 88,
            twelfthMarks: 86,
            internships: 2,
            projects: 4,
            techStack: ['C++', 'Java', 'Android', 'Firebase', 'Git'],
            achievements: ['App Development Contest Winner', 'Technical Blogger'],
            score: 81,
            priority: 5
          }
        ];
        
        setResults(mockResults.slice(0, numCandidates));
        setShowResults(true);
        setLoading(false);

        // Redirect to shortlist page with mock data
        navigate('/shortlist', {
          state: { shortlistedCandidates: mockResults.slice(0, numCandidates) }
        });
      }, 2000);
    }
  };

  const resetForm = () => {
    setSheetUrl('');
    setFile(null);
    setShowResults(false);
    setResults([]);
  };

  if (showResults) {
    // Fix: Use the correct backend response structure
    const candidates = Array.isArray(results.shortlisted_candidates)
      ? results.shortlisted_candidates
      : results;

    return (
      <div className="home">
        <div className="background-pattern"></div>
        <div className="results-container">
          <div className="results-header glass-card">
            <h1>Shortlisted Candidates</h1>
            <button onClick={resetForm} className="back-btn glass-btn">
              ← Back to Form
            </button>
          </div>
          
          <div className="results-summary glass-card">
            <p>
              Showing <b>top {candidates.length}</b> candidates based on your criteria.
              <br />
              <span style={{ fontSize: '1rem', color: '#888' }}>
                Click on a candidate card to expand and view more details.
              </span>
            </p>
          </div>

          <div className="shortlist-grid">
            {candidates.map((candidate, idx) => (
              <div key={candidate['#'] || idx} className="candidate-card glass-card shortlist-card">
                <div className="candidate-rank-badge">
                  <span>#{candidate.Rank || idx + 1}</span>
                </div>
                <div className="candidate-main-info">
                  <div className="candidate-name-email">
                    <h3>{candidate.name || candidate.Name || 'N/A'}</h3>
                    <p className="email">{candidate.email || candidate.Email || 'N/A'}</p>
                  </div>
                  <div className="candidate-score">
                    <span className="score-label">Score</span>
                    <span className="score-value">{candidate.score !== undefined ? candidate.score : 'N/A'}</span>
                  </div>
                </div>
                <div className="candidate-details-section">
                  <div className="candidate-detail-row">
                    <span className="detail-label">CGPA:</span>
                    <span className="detail-value">{candidate.cgpa || candidate.CGPA || 'N/A'}</span>
                    <span className="detail-label">10th:</span>
                    <span className="detail-value">{candidate.tenth_marks || candidate['10th Marks (%)'] || candidate['10th (%)'] || 'N/A'}%</span>
                    <span className="detail-label">12th:</span>
                    <span className="detail-value">{candidate.twelfth_marks || candidate['12th Marks (%)'] || candidate['12th (%)'] || 'N/A'}%</span>
                  </div>
                  <div className="candidate-detail-row">
                    <span className="detail-label">Internships:</span>
                    <span className="detail-value">{Array.isArray(candidate.internships) ? candidate.internships.length : candidate.internships || 'N/A'}</span>
                    <span className="detail-label">Projects:</span>
                    <span className="detail-value">{Array.isArray(candidate.personal_projects) ? candidate.personal_projects.length : candidate.personal_projects || 'N/A'}</span>
                  </div>
                  <div className="candidate-detail-row">
                    <span className="detail-label">Tech Stack:</span>
                    <span className="detail-value">
                      {(candidate.tech_stack || candidate['Tech Stack'] || [])
                        .toString()
                        .split(',')
                        .map((tech, i) => (
                          <span key={i} className="skill-tag glass-tag">{tech.trim()}</span>
                        ))}
                    </span>
                  </div>
                  <div className="candidate-detail-row">
                    <span className="detail-label">Achievements:</span>
                    <span className="detail-value">
                      {(candidate.achievements || candidate.Achievements || [])
                        .toString()
                        .split(',')
                        .map((ach, i) => (
                          <span key={i} className="achievement-tag glass-tag">{ach.trim()}</span>
                        ))}
                    </span>
                  </div>
                  {candidate.github_summary && (
                    <div className="candidate-detail-row">
                      <span className="detail-label">GitHub:</span>
                      <span className="detail-value">{candidate.github_summary}</span>
                    </div>
                  )}
                  {candidate.company_fit && (
                    <div className="candidate-detail-row">
                      <span className="detail-label">Company Fit:</span>
                      <span className="detail-value">{candidate.company_fit}</span>
                    </div>
                  )}
                  {candidate.score_split_up && (
                    <div className="candidate-detail-row">
                      <span className="detail-label">Score Split Up:</span>
                      <span className="detail-value">
                        <ul style={{ margin: 0, paddingLeft: 16 }}>
                          {Object.entries(candidate.score_split_up).map(([key, value]) => (
                            <li key={key}>
                              <strong>{key}:</strong>{" "}
                              <span>
                                <b>{value.score}</b>
                                {value.reason && (
                                  <>
                                    {" "}
                                    <span style={{ color: "#666", fontSize: "0.95em" }}>
                                      ({value.reason})
                                    </span>
                                  </>
                                )}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="home">
      <div className="background-pattern"></div>
      <div className="container">
        <div className="hero-section glass-card">
          <h1>
            
            Shortlist Resume  <img 
              src="https://assets.www.happyfox.com/v2/images/zendesk-alternative/hf-mini.png" 
              alt="HappyFox AI" 
              className="ai-logo-image"
            />
          </h1>
          <p className="subtitle">Upload your student resume data and set academic & technical criteria to find the best candidates</p>
        </div>
        
        <form onSubmit={handleSubmit} className="shortlister-form glass-card">
          {/* Data Input Section */}
          <div className="form-section">
            <h2>Data Source</h2>
            <div className="input-type-selector">
              <label className="radio-label glass-radio">
                <input
                  type="radio"
                  value="url"
                  checked={inputType === 'url'}
                  onChange={(e) => setInputType(e.target.value)}
                />
                <span>Google Sheets URL</span>
              </label>
              <label className="radio-label glass-radio">
                <input
                  type="radio"
                  value="file"
                  checked={inputType === 'file'}
                  onChange={(e) => setInputType(e.target.value)}
                />
                <span>Upload Excel File</span>
              </label>
            </div>

            {inputType === 'url' ? (
              <div className="input-group">
                <label>Google Sheets URL:</label>
                <input
                  type="url"
                  value={sheetUrl}
                  onChange={(e) => setSheetUrl(e.target.value)}
                  placeholder="https://docs.google.com/spreadsheets/d/..."
                  className="glass-input"
                />
                <small>Make sure the sheet is publicly accessible and contains columns: Name, Email, CGPA, 10th Marks, 12th Marks, Internships, Projects, Tech Stack, Achievements</small>
              </div>
            ) : (
              <div className="input-group">
                <label>Upload Excel File:</label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                  className="glass-input file-input"
                />
                <small>Excel file should contain columns: Name, Email, CGPA, 10th Marks, 12th Marks, Internships, Projects, Tech Stack, Achievements</small>
              </div>
            )}
          </div>

          {/* Criteria Section */}
          <div className="form-section">
            <h2>Academic & Technical Criteria</h2>
            
            {/* CGPA Criteria */}
            <div className="criteria-group glass-inner">
              <h3>CGPA Requirements</h3>
              <div className="criteria-row">
                <div className="input-group">
                  <label>Minimum CGPA:</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.1"
                    value={criteria.cgpa.min}
                    onChange={(e) => handleCriteriaChange('cgpa', 'min', parseFloat(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
                <div className="input-group">
                  <label>Maximum CGPA:</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.1"
                    value={criteria.cgpa.max}
                    onChange={(e) => handleCriteriaChange('cgpa', 'max', parseFloat(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
                <div className="input-group">
                  <label>Weight (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.cgpa.weight}
                    onChange={(e) => handleCriteriaChange('cgpa', 'weight', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
              </div>
            </div>

            {/* 10th & 12th Marks Criteria */}
            <div className="criteria-group glass-inner">
              <h3>Board Exam Performance</h3>
              <div className="criteria-row">
                <div className="input-group">
                  <label>Min 10th Marks (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.tenthMarks.min}
                    onChange={(e) => handleCriteriaChange('tenthMarks', 'min', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
                <div className="input-group">
                  <label>Weight (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.tenthMarks.weight}
                    onChange={(e) => handleCriteriaChange('tenthMarks', 'weight', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
              </div>
              <div className="criteria-row">
                <div className="input-group">
                  <label>Min 12th Marks (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.twelfthMarks.min}
                    onChange={(e) => handleCriteriaChange('twelfthMarks', 'min', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
                <div className="input-group">
                  <label>Weight (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.twelfthMarks.weight}
                    onChange={(e) => handleCriteriaChange('twelfthMarks', 'weight', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
              </div>
            </div>

            {/* Experience Criteria */}
            <div className="criteria-group glass-inner">
              <h3>Practical Experience</h3>
              <div className="criteria-row">
                <div className="input-group">
                  <label>Min Internships:</label>
                  <input
                    type="number"
                    min="0"
                    value={criteria.internships.min}
                    onChange={(e) => handleCriteriaChange('internships', 'min', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
                <div className="input-group">
                  <label>Min Projects:</label>
                  <input
                    type="number"
                    min="0"
                    value={criteria.projects.min}
                    onChange={(e) => handleCriteriaChange('projects', 'min', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
              </div>
              <div className="criteria-row">
                <div className="input-group">
                  <label>Internship Weight (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.internships.weight}
                    onChange={(e) => handleCriteriaChange('internships', 'weight', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
                <div className="input-group">
                  <label>Project Weight (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.projects.weight}
                    onChange={(e) => handleCriteriaChange('projects', 'weight', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
              </div>
            </div>

            {/* Tech Stack Criteria */}
            <div className="criteria-group glass-inner">
              <h3>Technical Skills</h3>
              <div className="skills-section">
                <div className="skill-category">
                  <h4>Required Technologies</h4>
                  <div className="add-skill-section">
                    <div className="add-skill-input-group">
                      <input
                        type="text"
                        value={newTech.required}
                        onChange={(e) => setNewTech(prev => ({ ...prev, required: e.target.value }))}
                        placeholder="Enter required technology..."
                        className="glass-input"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTechStack('required'))}
                      />
                      <button
                        type="button"
                        onClick={() => addTechStack('required')}
                        className="add-btn glass-btn"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                  <div className="skills-list">
                    {criteria.techStack.required.map((tech, index) => (
                      <span key={index} className="skill-tag glass-tag">
                        {tech}
                        <button
                          type="button"
                          onClick={() => removeTechStack('required', index)}
                          className="remove-skill"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="skill-category">
                  <h4>Preferred Technologies</h4>
                  <div className="add-skill-section">
                    <div className="add-skill-input-group">
                      <input
                        type="text"
                        value={newTech.preferred}
                        onChange={(e) => setNewTech(prev => ({ ...prev, preferred: e.target.value }))}
                        placeholder="Enter preferred technology..."
                        className="glass-input"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTechStack('preferred'))}
                      />
                      <button
                        type="button"
                        onClick={() => addTechStack('preferred')}
                        className="add-btn glass-btn preferred"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                  <div className="skills-list">
                    {criteria.techStack.preferred.map((tech, index) => (
                      <span key={index} className="skill-tag glass-tag preferred">
                        {tech}
                        <button
                          type="button"
                          onClick={() => removeTechStack('preferred', index)}
                          className="remove-skill"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
                <div className="input-group">
                  <label>Tech Stack Weight (%):</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={criteria.techStack.weight}
                    onChange={(e) => handleCriteriaChange('techStack', 'weight', parseInt(e.target.value) || 0)}
                    className="glass-input"
                  />
                </div>
              </div>
            </div>

            <div className="criteria-group glass-inner">
              <h3>Achievements & Recognition</h3>
              <div className="skills-section">
              <div className="skill-category">
                <h4>Achievement Keywords</h4>
                <div className="add-skill-section">
                  <div className="add-skill-input-group">
                    <input
                      type="text"
                      value={newKeyword}
                      onChange={(e) => setNewKeyword(e.target.value)}
                      placeholder="Enter achievement keyword..."
                      className="glass-input"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAchievementKeyword())}
                    />
                    <button
                      type="button"
                      onClick={addAchievementKeyword}
                      className="add-btn glass-btn achievement"
                    >
                      Add
                    </button>
                  </div>
                </div>
                <div className="skills-list">
                  {criteria.achievements.keywords.map((keyword, index) => (
                    <span key={index} className="skill-tag glass-tag achievement">
                      {keyword}
                      <button
                        type="button"
                        onClick={() => removeAchievementKeyword(index)}
                        className="remove-skill"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <small>Keywords to look for in achievements (e.g., "winner", "first prize", "scholarship", "published", "certified")</small>
              </div>
              <div className="input-group">
                <label>Achievement Weight (%):</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={criteria.achievements.weight}
                  onChange={(e) => handleCriteriaChange('achievements', 'weight', parseInt(e.target.value) || 0)}
                  className="glass-input"
                />
              </div>
            </div>
              </div>
          </div>

          {/* Output Settings */}
          <div className="form-section">
            <h2>Output Settings</h2>
            <div className="input-group">
              <label>Number of top candidates to show:</label>
              <input
                type="number"
                min="1"
                max="100"
                value={numCandidates}
                onChange={(e) => setNumCandidates(parseInt(e.target.value) || 1)}
                className="glass-input"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button type="submit" className="submit-btn glass-btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Processing Resumes...
              </>
            ) : (
              'Shortlist Candidates'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Home;