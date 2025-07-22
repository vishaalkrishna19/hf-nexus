import React, { useState } from 'react';
import Kanban from '../../components/kanban/Kanban';
import './InterviewStatus.scss';

const InterviewStatus = () => {
  const [candidates, setCandidates] = useState({
    shortlisted: [
      { id: 1, name: 'Vishaal Krishna', email: 'vishaal@gmail.com', phone: '8667322426', role: 'Full-Stack Developer' },
      { id: 2, name: 'Dheekshith', email: 'vishaal@gmail.com', phone: '8667322426', role: 'Backend Developer' },
      { id: 3, name: 'Mike', email: 'vishaal@gmail.com', phone: '8667322426', role: 'Full Stack Developer' }
    ],
    technical: [
      { id: 4, name: 'Alan', email: 'vishaal@gmail.com', phone: '8667322426', role: 'React Developer' }
    ],
    assignment: [],
    cto: [
      { id: 5, name: 'Tom Brown', email: 'vishaal@gmail.com', phone: '8667322426', role: 'Senior Developer' }
    ],
    ceo: []
  });

  const columns = [
    { id: 'shortlisted', title: 'Shortlisted Candidates', candidates: candidates.shortlisted },
    { id: 'technical', title: 'Technical Interview', candidates: candidates.technical },
    { id: 'assignment', title: 'Assignment Round', candidates: candidates.assignment },
    { id: 'cto', title: 'CTO Interview', candidates: candidates.cto },
    { id: 'ceo', title: 'CEO Interview', candidates: candidates.ceo }
  ];

  const handleProceed = (candidateId, currentColumn) => {
    const columnOrder = ['shortlisted', 'technical', 'assignment', 'cto', 'ceo'];
    const currentIndex = columnOrder.indexOf(currentColumn);
    
    if (currentIndex < columnOrder.length - 1) {
      const nextColumn = columnOrder[currentIndex + 1];
      moveCandidateToColumn(candidateId, currentColumn, nextColumn);
    }
  };

  const handleReject = (candidateId, currentColumn) => {
    setCandidates(prev => ({
      ...prev,
      [currentColumn]: prev[currentColumn].filter(candidate => candidate.id !== candidateId)
    }));
  };

  const moveCandidateToColumn = (candidateId, fromColumn, toColumn) => {
    setCandidates(prev => {
      const candidate = prev[fromColumn].find(c => c.id === candidateId);
      if (!candidate) return prev;

      return {
        ...prev,
        [fromColumn]: prev[fromColumn].filter(c => c.id !== candidateId),
        [toColumn]: [...prev[toColumn], candidate]
      };
    });
  };

  const handleDragEnd = (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;
    const candidateId = parseInt(draggableId);

    if (source.droppableId !== destination.droppableId) {
      moveCandidateToColumn(candidateId, source.droppableId, destination.droppableId);
    }
  };

  return (
    <div className="interview-status">
      <div className="interview-status__header">
        <h1>Interview Status Management</h1>
        <p>Track and manage candidate progress through interview stages</p>
      </div>

      <div className='dropdown' style={{ marginBottom: '2rem', maxWidth: 320 }}>
        <label className='dropdown-label' htmlFor="college-select" style={{ fontWeight: 400, marginBottom: '15px', textAlign:'left', display: 'block' }}>Select College</label>
        <select
          id="college-select"
          style={{
            width: '100%',
            padding: '0.5rem 1rem',
            borderRadius: 6,
            border: '1px solid #ccc',
            fontSize: '14px',
            fontWeight:200,
            background: 'var(--bg-secondary, #fff)',
            color: 'var(--text-primary, #222)'
          }}
        >
          <option value="">-- Choose College --</option>
          <option value="IIT">REC</option>
          <option value="NIT">NIT</option>
          <option value="BITS">BITS</option>
          <option value="VIT">VIT</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <div className="kanban-container" onClick={() => setActiveDropdown && setActiveDropdown(null)}>
        <Kanban 
          columns={columns}
          onProceed={handleProceed}
          onReject={handleReject}
          onDragEnd={handleDragEnd}
        />
      </div>
    </div>
  );
};

export default InterviewStatus;
