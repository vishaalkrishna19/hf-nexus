import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './ShortlistPage.scss';

const ShortlistPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const shortlisted = location.state?.shortlistedCandidates || [];
  const [error, setError] = React.useState('');
  const [expandedRows, setExpandedRows] = React.useState(new Set());

  React.useEffect(() => {
    if (shortlisted && shortlisted.length > 0) {
      console.log("Shortlisted candidates data:", shortlisted);
      if (typeof shortlisted[0] === 'object') {
        console.log("First candidate object keys:", Object.keys(shortlisted[0]));
        console.log("First candidate object:", shortlisted[0]);
      }
    }
  }, [shortlisted]);

  const toggleRowExpansion = (index) => {
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(index)) {
      newExpandedRows.delete(index);
    } else {
      newExpandedRows.add(index);
    }
    setExpandedRows(newExpandedRows);
  };

  const exportShortlistToExcel = async () => {
    if (!shortlisted.length) return;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/export-excel/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          multiple_resumes: shortlisted,
          filename: 'shortlisted_candidates'
        })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `shortlisted_candidates_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('Failed to export Excel file');
      }
    } catch (err) {
      alert('Error exporting shortlisted candidates: ' + err.message);
    }
  };

  // Helper to render score/reason objects
  const renderScoreReason = (obj) => {
    if (!obj) return 'N/A';
    return (
      <span>
        <b>{obj.score}</b>
        {obj.reason && (
          <>
            {" "}
            <span style={{ color: "#666", fontSize: "0.95em" }}>
              ({obj.reason})
            </span>
          </>
        )}
      </span>
    );
  };

  // Helper to render criteria_analysis object
  const renderCriteriaAnalysis = (criteria_analysis) => {
    if (!criteria_analysis) return 'N/A';
    return (
      <ul style={{ margin: 0, paddingLeft: 16 }}>
        {Object.entries(criteria_analysis).map(([key, value]) => (
          <li key={key}>
            <strong>{key.replace(/_/g, ' ').toUpperCase()}:</strong>{" "}
            {renderScoreReason(value)}
          </li>
        ))}
      </ul>
    );
  };

  React.useEffect(() => {
    if (location.state?.error) setError(location.state.error);
  }, [location.state]);

  return (
    <div className="shortlist-page">
      <div className="background-pattern"></div>
      <div className="container">
        <div className="ranking-header glass-card">
          <h2>Shortlisted Candidates</h2>
          <div className="header-buttons">
            <button onClick={exportShortlistToExcel} className="export-btn glass-btn">
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
                <th>Phone</th>
                <th>GitHub Link</th>
                <th>Internships</th>
                <th>Projects</th>
                <th>GitHub Profile Analysis</th>
                <th>Achievements</th>
                <th>Shortlist Score</th>
                <th>Criteria Match</th>
                <th>Criteria Analysis</th>
              </tr>
            </thead>
            <tbody>
            {shortlisted.map((resume, idx) => (
                <tr 
                  key={idx}
                  className={`clickable-row${expandedRows.has(idx) ? ' expanded-row' : ''}`}
                  onClick={() => toggleRowExpansion(idx)}
                >
                    <td>
                      <div className="rank-cell">
                        {resume.Rank || idx + 1}
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
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.phone || 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.github && resume.github !== 'Not provided' ? (
                          <a href={resume.github} target="_blank" rel="noopener noreferrer" style={{ color: '#007bff', textDecoration: 'underline' }}>
                            {resume.github}
                          </a>
                        ) : 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {Array.isArray(resume.internships) ? (
                          expandedRows.has(idx) ? (
                            <ul className="expanded-list">
                              {resume.internships.map((internship, i) => (
                                <li key={i}>{internship}</li>
                              ))}
                            </ul>
                          ) : (
                            `${resume.internships.length} internship${resume.internships.length !== 1 ? 's' : ''}`
                          )
                        ) : (
                          resume.internships || 'N/A'
                        )}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {Array.isArray(resume.projects) ? (
                          expandedRows.has(idx) ? (
                            <ul className="expanded-list">
                              {resume.projects.map((project, i) => (
                                <li key={i}>{project}</li>
                              ))}
                            </ul>
                          ) : (
                            `${resume.projects.length} project${resume.projects.length !== 1 ? 's' : ''}`
                          )
                        ) : (
                          resume.projects || 'N/A'
                        )}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.github_profile_analysis || 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {Array.isArray(resume.achievements) ? (
                          expandedRows.has(idx) ? (
                            <ul className="expanded-list">
                              {resume.achievements.map((achievement, i) => (
                                <li key={i}>{achievement}</li>
                              ))}
                            </ul>
                          ) : (
                            `${resume.achievements.length} achievement${resume.achievements.length !== 1 ? 's' : ''}`
                          )
                        ) : (
                          resume.achievements || 'N/A'
                        )}
                      </div>
                    </td>
                    <td>
                      <div
                        className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}
                        style={{
                          color:
                            resume.shortlist_score > 85
                              ? '#28a745'
                              : resume.shortlist_score > 65
                              ? '#fd7e14'
                              : '#ffc107',
                          fontWeight: 700
                        }}
                      >
                        {resume.shortlist_score !== undefined && resume.shortlist_score !== null
                          ? resume.shortlist_score
                          : 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.criteria_match !== undefined && resume.criteria_match !== null && resume.criteria_match !== ''
                          ? resume.criteria_match
                          : 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div className={`cell-content${expandedRows.has(idx) ? ' expanded' : ''}`}>
                        {resume.criteria_analysis && Object.keys(resume.criteria_analysis).length > 0
                          ? (
                            <ul style={{ margin: 0, paddingLeft: 16 }}>
                              {Object.entries(resume.criteria_analysis).map(([key, value]) => (
                                <li key={key}>
                                  <strong>{key.replace(/_/g, ' ').toUpperCase()}:</strong>{" "}
                                  <span>
                                    <b>{value.score !== undefined && value.score !== null ? value.score : 'N/A'}</b>
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

export default ShortlistPage;
