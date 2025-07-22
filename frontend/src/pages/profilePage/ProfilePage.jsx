import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import './ProfilePage.scss';
import { useResumeContext } from '../../context/ResumeContext';

const ProfilePage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [githubDetails, setGithubDetails] = useState(null);
  const [githubLoading, setGithubLoading] = useState(false);
  const [githubError, setGithubError] = useState(null);
  const { parsedResumes } = useResumeContext();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);
  
  useEffect(() => {
    // Get profile data from location state
    if (location.state && location.state.profileData) {
      setProfile(location.state.profileData);
    } else {
      // If no data in location state, try to find it in context
      const candidateName = window.location.pathname.split('/').pop().replace(/-/g, ' ');
      const foundProfile = parsedResumes.find(
        resume => resume.name && resume.name.toLowerCase() === candidateName.toLowerCase()
      );
      
      if (foundProfile) {
        setProfile(foundProfile);
        console.log('Profile found in context:', profile);
      } else {
        // If still no data, redirect to the resume page
        navigate('/parse-resume');
      }
    }
  }, [location, navigate, parsedResumes]);
  
  // Handler to fetch GitHub details
  const handleFetchGithubDetails = async () => {
    if (!profile.github || profile.github === 'Not found') return;
    setGithubLoading(true);
    setGithubError(null);
    setGithubDetails(null);
    try {
     
      const backendUrl = 'http://localhost:8000'; 
      const response = await fetch(`${backendUrl}/github-details/?url=${encodeURIComponent(profile.github)}`);
      if (!response.ok) {
        let errMsg = 'Failed to fetch GitHub details';
        try {
          const errData = await response.json();
          if (errData && errData.error) errMsg = errData.error;
        } catch {}
        throw new Error(errMsg);
      }
      const data = await response.json();
      setGithubDetails(data);
    } catch (err) {
      setGithubError(err.message || 'Could not fetch GitHub details.');
    } finally {
      setGithubLoading(false);
    }
  };

  if (!profile) {
    return (
      <div className="profile-page loading">
        <div className="container">
          <div className="loading-spinner"></div>
          <p>Loading profile data...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="profile-page">
      <div className="background-pattern"></div>
      <div className="container">
        <div className="profile-header glass-card">
          <button className="back-btn" onClick={() => navigate(-1)}>
            ← Back to Results
          </button>
          <button className="action-btn share-btn">
            <span className="icon">🔗</span>
            <span>Share Profile</span>
          </button>
          <div className="profile-title">
            <h1>{profile.name || 'Unnamed Candidate'}</h1>
            {profile.email && <p className="email">{profile.email}</p>}
          </div>
        </div>
        
        <div className="profile-content">
          <div className="profile-sidebar">
            <div className="profile-card contact-info glass-card">
              <h3 className="card-title">
                <span className="card-icon-round"></span>
                Contact Information
              </h3>
              <div className="info-list">
                {profile.email && (
                  <div className="info-item">
                    <div className="info-label">Email</div>
                    <div className="info-value">
                      <a href={`mailto:${profile.email}`} className="link">{profile.email}</a>
                    </div>
                  </div>
                )}
                
                {profile.phone && profile.phone !== 'Not found' && (
                  <div className="info-item">
                    <div className="info-label">Phone</div>
                    <div className="info-value">
                      <a href={`tel:${profile.phone}`} className="link">{profile.phone}</a>
                    </div>
                  </div>
                )}
                
                {profile.github && profile.github !== 'Not found' && (
                  <div className="info-item">
                    <div className="info-label">GitHub</div>
                    <div className="info-value">
                      <a href={profile.github} target="_blank" rel="noopener noreferrer" className="link">
                        {profile.github.replace(/(https?:\/\/)?(www\.)?github\.com\//, '')}
                      </a>
                    </div>
                  </div>
                )}
                
                {profile.linkedin && profile.linkedin !== 'Not found' && (
                  <div className="info-item">
                    <div className="info-label">LinkedIn</div>
                    <div className="info-value">
                      <a href={profile.linkedin} target="_blank" rel="noopener noreferrer" className="link">
                        {profile.linkedin.replace(/(https?:\/\/)?(www\.)?linkedin\.com\/(in\/)?/, '')}
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="profile-card education-info glass-card">
              <h3 className="card-title">
                <span className="card-icon-round"></span>
                Education
              </h3>
              <div className="info-list">
                {profile.college && profile.college !== 'Not found' && (
                  <div className="info-item">
                    <div className="info-label">College</div>
                    <div className="info-value">{profile.college}</div>
                    {profile.cgpa && profile.cgpa !== 'Not found' && (
                      <div className="info-detail">CGPA: {profile.cgpa}</div>
                    )}
                  </div>
                )}
                
                {profile.school && profile.school !== 'Not found' && (
                  <div className="info-item">
                    <div className="info-label">School</div>
                    <div className="info-value">{profile.school}</div>
                    <div className="school-marks">
                      {profile.twelfth_marks && profile.twelfth_marks !== 'Not found' && (
                        <div className="info-detail">12th: {profile.twelfth_marks}%</div>
                      )}
                      {profile.tenth_marks && profile.tenth_marks !== 'Not found' && (
                        <div className="info-detail">10th: {profile.tenth_marks}%</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {Array.isArray(profile.tech_stack) && profile.tech_stack.length > 0 && (
              <div className="profile-card skills-info glass-card">
                <h3 className="card-title">
                  <span className="card-icon-round"></span>
                  Technical Skills
                </h3>
                <div className="skills-list">
                  {profile.tech_stack.map((skill, index) => (
                    <span key={index} className="skill-tag">{skill}</span>
                  ))}
                </div>
              </div>
            )}
            
            {Array.isArray(profile.achievements) && profile.achievements.length > 0 && (
              <div className="profile-card achievements-info glass-card">
                <h3 className="card-title">
                  <span className="card-icon-round"></span>
                  Achievements
                </h3>
                <ul className="achievements-list">
                  {profile.achievements.map((achievement, index) => (
                    <li key={index} className="achievement-item">{achievement}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          <div className="profile-main">
            {(Array.isArray(profile.internships) && profile.internships.length > 0) && (
              <div className="profile-card internships-info glass-card">
                <h3 className="card-title">
                  <span className="card-icon-round"></span>
                  Internship Experience
                </h3>
                <ul className="experience-list">
                  {profile.internships.map((internship, index) => (
                    <li key={index} className="experience-item">{internship}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {(Array.isArray(profile.internship_projects) && profile.internship_projects.length > 0) && (
              <div className="profile-card projects-info glass-card">
                <h3 className="card-title">
                  <span className="card-icon-round"></span>
                  Internship Projects
                </h3>
                <ul className="projects-list">
                  {profile.internship_projects.map((project, index) => (
                    <li key={index} className="project-item">{project}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {(Array.isArray(profile.personal_projects) && profile.personal_projects.length > 0) && (
              <div className="profile-card projects-info glass-card">
                <h3 className="card-title">
                  <span className="card-icon-round"></span>
                  Personal Projects
                </h3>
                <ul className="projects-list">
                  {profile.personal_projects.map((project, index) => (
                    <li key={index} className="project-item">{project}</li>
                  ))}
                </ul>
              </div>
            )}

{           (Array.isArray(profile.languages) && profile.languages.length > 0) && (
              <div className="profile-card projects-info glass-card">
                <h3 className="card-title">
                  <span className="card-icon-round"></span>
                  Languages
                </h3>
                <ul className="projects-list">
                  {profile.languages.map((project, index) => (
                    <li key={index} className="project-item">{project.language} - {project.proficiency}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Fetch GitHub Details Button */}
            {profile.github && profile.github !== 'Not found' && (
              <div className="profile-card github-details-card glass-card">
                <button
                  className="action-btn fetch-github-btn"
                  onClick={handleFetchGithubDetails}
                  disabled={githubLoading}
                  style={{ marginBottom: '1rem' }}
                >
                  {githubLoading ? 'Fetching...' : 'Fetch GitHub Details'}
                </button>
                {githubError && <div className="error-msg">{githubError}</div>}
                {githubDetails && (
                  <div className="github-details-content">
                    <h3 className="card-title">
                      <span className="card-icon-round"></span>
                      GitHub Profile Details
                    </h3>
                    
                    {/* Avatar */}
                    {githubDetails.avatar_url && (
                      <div className="github-avatar">
                        <img src={githubDetails.avatar_url} alt="GitHub Avatar" style={{ width: 80, borderRadius: '50%' }} />
                      </div>
                    )}
                    
                    {/* Stats Grid */}
                    <div className="github-stats">
                      {githubDetails.public_repos !== undefined && (
                        <div className="stat-item">
                          <span className="stat-number">{githubDetails.public_repos}</span>
                          <span className="stat-label">Repositories</span>
                        </div>
                      )}
                      {githubDetails.followers !== undefined && (
                        <div className="stat-item">
                          <span className="stat-number">{githubDetails.followers}</span>
                          <span className="stat-label">Followers</span>
                        </div>
                      )}
                      
                      {githubDetails.total_commits !== undefined && (
                        <div className="stat-item">
                          <span className="stat-number">{githubDetails.total_commits}</span>
                          <span className="stat-label">Total Commits</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Profile Information */}
                    <div className="github-fields">
                      {githubDetails.name && (
                        <div><strong>Name:</strong> {githubDetails.name}</div>
                      )}
                      {githubDetails.username && (
                        <div><strong>Username:</strong> {githubDetails.username}</div>
                      )}
                      {githubDetails.bio && (
                        <div><strong>Bio:</strong> {githubDetails.bio}</div>
                      )}
                      {githubDetails.location && (
                        <div><strong>Location:</strong> {githubDetails.location}</div>
                      )}
                      {githubDetails.html_url && (
                        <div>
                          <strong>Profile URL:</strong>{' '}
                          <a href={githubDetails.html_url} target="_blank" rel="noopener noreferrer">
                            View on GitHub
                          </a>
                        </div>
                      )}
                      
                      {/* Most Used Languages */}
                      {Array.isArray(githubDetails.most_used_languages) && githubDetails.most_used_languages.length > 0 && (
                        <div>
                          <strong>Most Used Languages:</strong>
                          <div className="languages-grid" style={{ marginTop: '12px' }}>
                            {githubDetails.most_used_languages.map((lang, idx) => (
                              <div key={idx} className="language-item">
                                <div className="language-info">
                                  <span className="language-name">{lang.language}</span>
                                  <span className="language-percentage">{lang.percentage}%</span>
                                </div>
                                <div className="language-bar">
                                  <div 
                                    className="language-progress" 
                                    style={{ width: `${lang.percentage}%` }}
                                  ></div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {Array.isArray(githubDetails.top_repos) && githubDetails.top_repos.length > 0 && (
                        <div>
                          <strong style={{marginBottom:"20px"}}>Top Repositories:</strong>
                          <ul>
                            {githubDetails.top_repos.slice(0, 3).map((repo, idx) => (
                              <li key={repo.html_url || idx}>
                                <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
                                  {repo.name}
                                </a>
                                {repo.stargazers_count !== undefined && (
                                  <span>⭐ {repo.stargazers_count}</span>
                                )}
                                {repo.description && (
                                  <div>{repo.description}</div>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="profile-card file-info glass-card">
              <h3 className="card-title">
                <span className="card-icon-round"></span>
                Original Document
              </h3>
              <div className="file-details">
                <div className="file-name">{profile.filename}</div>
                <button className="view-original-btn">
                
                  View Original Resume
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
