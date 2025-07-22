import React, { createContext, useState, useEffect } from 'react';

// Create the theme context
export const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  // Check if dark mode was previously set in localStorage
  const savedTheme = localStorage.getItem('theme');
  const [darkMode, setDarkMode] = useState(savedTheme === 'dark');

  // Toggle dark mode function
  const toggleDarkMode = () => {
    setDarkMode(prevMode => !prevMode);
  };

  // Update body class and localStorage when darkMode changes
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark-mode');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  // Context value
  const value = {
    darkMode,
    toggleDarkMode
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};
