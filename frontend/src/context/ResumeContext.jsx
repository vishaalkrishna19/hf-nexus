import React, { createContext, useState, useContext } from 'react';

const ResumeContext = createContext();

export const ResumeProvider = ({ children }) => {
  const [parsedResumes, setParsedResumes] = useState([]);
  
  // Store the parsed resume data
  const storeResumeData = (data) => {
    setParsedResumes(data);
  };
  
  return (
    <ResumeContext.Provider value={{ parsedResumes, storeResumeData }}>
      {children}
    </ResumeContext.Provider>
  );
};

// Custom hook to use the resume context
export const useResumeContext = () => useContext(ResumeContext);

export default ResumeContext;
