import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import Home from './pages/home/Home';
import Header from './components/header/Header';
import Resume from './pages/resume/Resume';
import Sidebar from './components/sidebar/Sidebar';
import ProfilePage from './pages/profilePage/ProfilePage';
import RankingPage from './pages/ranking/RankingPage';
import { ResumeProvider } from './context/ResumeContext';
import { ThemeProvider } from './context/ThemeContext';
import InterviewStatus from './pages/interviewStatus/InterviewStatus';
import ShortlistPage from './pages/shortlist/ShortlistPage';

function App() {
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  const handleSidebarToggle = (isExpanded) => {
    setIsSidebarExpanded(isExpanded);
  };

  return (
    <ThemeProvider>
      <ResumeProvider>
        <Router>
          <div className="App">
            <Header />
            <Sidebar onToggle={handleSidebarToggle} />
            <main className={`main-content ${!isSidebarExpanded ? 'sidebar-collapsed' : ''}`}>
              <Routes>
                <Route path="/" element={<Navigate to="/parse-resume" replace />} />
                <Route path="/parse-resume" element={<Resume />} />
                <Route path="/shortlist-resume" element={<Home />} />
                <Route path="/profile/:candidateName" element={<ProfilePage />} />
                <Route path="/ranked" element={<RankingPage />} />
                <Route path="/status" element={<InterviewStatus />} />
                <Route path="/shortlist" element={<ShortlistPage />} />
              </Routes>
            </main>
          </div>
        </Router>
      </ResumeProvider>
    </ThemeProvider>
  );
}

export default App;