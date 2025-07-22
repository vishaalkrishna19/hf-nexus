import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './RankingPage.scss';

const RankingPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const rankedResumes = location.state?.rankedResumes || [];
  const [error, setError] = React.useState('');
  const [expandedRows, setExpandedRows] = React.useState(new Set());

  // Log the data received from Gemini for debugging
  React.useEffect(() => {
    // Only log if there is data
    if (rankedResumes && rankedResumes.length > 0) {
      // Log the full array and the first item for inspection
      console.log("Gemini rankedResumes data:", rankedResumes);
      if (typeof rankedResumes[0] === 'object') {
        console.log("First resume object keys:", Object.keys(rankedResumes[0]));
        console.log("First resume object:", rankedResumes[0]);
      }
    }
  }, [rankedResumes]);

  // Toggle row expansion
  const toggleRowExpansion = (index) => {
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(index)) {
      newExpandedRows.delete(index);
    } else {
      newExpandedRows.add(index);
    }
    setExpandedRows(newExpandedRows);
  };

  // Export ranked resumes as Excel
  const exportRankedToExcel = async () => {
    if (!rankedResumes.length) return;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/export-excel/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            multiple_resumes: rankedResumes,
            filename: 'ranked_resumes'
          })
        });
        console.log(response);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `ranked_resumes_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('Failed to export Excel file');
      }
    } catch (err) {
      alert('Error exporting ranked resumes: ' + err.message);
    }
  };

  // Render list items as proper lists when expanded
  const renderListContent = (items, isExpanded) => {
    if (!items || items.length === 0) return 'N/A';
    
    if (!isExpanded) {
      return `${items.length} item${items.length !== 1 ? 's' : ''}`;
    }
    
    return (
      <ul className="expanded-list">
        {items.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>
    );
  };

  // Render advantage content with proper formatting
  const renderAdvantageContent = (advantage, isExpanded) => {
    if (!advantage) return 'N/A';
    
    if (!isExpanded) {
      return advantage.length > 50 ? `${advantage.substring(0, 50)}...` : advantage;
    }
    
    return <div className="expanded-text">{advantage}</div>;
  };

  React.useEffect(() => {
    if (location.state?.error) setError(location.state.error);
  }, [location.state]);

  return (
    <div className="ranking-page">
      <div className="background-pattern"></div>
      <div className="container">
        <div className="ranking-header glass-card">
          <h2>Ranked Resumes</h2>
          <div className="header-buttons">
            <button onClick={exportRankedToExcel} className="export-btn glass-btn">
              📊 Export as Excel 
            </button>
            <button onClick={() => navigate(-1)} className="back-btn glass-btn">
              ← Back
            </button>
          </div>
        </div>
        {error && (
          <div style={{ color: 'red', textAlign: 'center', margin: '1rem' }}>
            {error}
          </div>
        )}
        <div className="table-container">
          <table className="ranking-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Name</th>
                <th>Email</th>
                <th>Score</th>
                <th>File Name</th>
                <th>Projects</th>
                <th>Tech Stack</th>
                <th>Achievements</th>
                <th>Company Fit</th>
                <th>Score Split Up</th> {/* New column */}
              </tr>
            </thead>
            <tbody>
            {rankedResumes.map((resume, idx) => (
                <tr 
                  key={idx}
                  className={`clickable-row${expandedRows.has(idx) ? ' expanded-row' : ''}`}
                  onClick={() => toggleRowExpansion(idx)}
                >
                    <td>
                      <div className="rank-cell">
                        {idx + 1}
                        <span className="expand-icon" style={{
                          display: 'inline-block',
                          marginLeft: 8,
                          transition: 'transform 0.3s',
                          transform: expandedRows.has(idx)
                            ? 'rotate(180deg)'
                            : 'rotate(0deg)'
                        }}>
                          <img
                            src="//assets.www.happyfox.com/v2/images/down-arrow.svg"
                            alt="Expand"
                            style={{ width: 10, height: 10, display: 'inline-block', verticalAlign: 'middle' }}
                          />
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.name || 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.email || 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div
                        className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}
                        style={{
                          color:
                            resume.score > 85
                              ? '#28a745'
                              : resume.score > 65
                              ? '#fd7e14'
                              : '#ffc107',
                          fontWeight: 700
                        }}
                      >
                        {resume.score !== undefined ? resume.score : 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.filename}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {renderListContent(resume.personal_projects, expandedRows.has(idx))}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {renderListContent(resume.tech_stack, expandedRows.has(idx))}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {renderListContent(resume.achievements, expandedRows.has(idx))}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {/* Show company_fit instead of advantage */}
                        {resume.company_fit || 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {/* Show score_split_up as pretty JSON or lines if present */}
                        {resume.score_split_up
                          ? (
                            <ul style={{ margin: 0, paddingLeft: 16 }}>
  {Object.entries(resume.score_split_up).map(([key, value]) => (
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
                          )
                          : 'N/A'
                        }
                      </div>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default RankingPage;