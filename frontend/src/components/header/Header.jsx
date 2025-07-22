import React, { useContext } from 'react';
import './Header.scss';
import { ThemeContext } from '../../context/ThemeContext';

const Header = () => {
  const { darkMode, toggleDarkMode } = useContext(ThemeContext);
  
  return (
    <header className="header">
      <div className="header-container">
        <div className="header-left">
          <div className="logo-section">
            <div className="logo-icon">
              <img 
                src="https://assets.www.happyfox.com/v2/images/zendesk-alternative/hf-mini.png" 
                alt="HappyFox AI" 
                className="ai-logo-image"
              />
            </div>
            <h1 className="app-title">HappyFox Nexus</h1>
          </div>
        </div>
        
        <div className="header-right">
          <div className="search-container">
            <input 
              type="text" 
              placeholder="Search..." 
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>
          
          <div className="header-actions">
            <button className="theme-toggle-btn" onClick={toggleDarkMode} title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>
              <img 
                src={darkMode ? "https://cdn-icons-png.flaticon.com/512/3073/3073665.png" : "https://cdn-icons-png.flaticon.com/512/581/581601.png"} 
                alt={darkMode ? "Light Mode" : "Dark Mode"} 
                className="theme-icon"
              />
            </button>
            
            <button className="notification-btn">
              <img 
                src="https://cdn-icons-png.flaticon.com/512/3119/3119338.png" 
                alt="Notifications" 
                className="notification-icon"
              />
              <span className="notification-badge"></span>
            </button>
            
            <div className="user-profile">
              <div className="user-avatar">
                <span>U</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;