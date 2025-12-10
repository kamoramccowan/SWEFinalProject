import React, { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./NavBar.css";
import { useAuth } from "../AuthContext";
import { useTheme, THEMES } from "../ThemeContext";

export default function NavBar() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    setDropdownOpen(false);
    logout();
    navigate("/login");
  };

  const userInitials = user
    ? (user.display_name || user.email || "U")[0].toUpperCase()
    : "?";

  return (
    <header className="nav-header">
      <Link to="/" className="brand">
        THEE BOGGLE BOOST
      </Link>

      {/* Mobile menu toggle */}
      <button
        className="mobile-menu-btn"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
      >
        ☰
      </button>

      <nav className={`nav-links ${mobileMenuOpen ? "open" : ""}`}>
        <Link to="/" onClick={() => setMobileMenuOpen(false)}>Home</Link>
        <Link to="/create" onClick={() => setMobileMenuOpen(false)}>Create</Link>
        <Link to="/leaderboard" onClick={() => setMobileMenuOpen(false)}>Leaderboard</Link>
        <Link to="/stats" onClick={() => setMobileMenuOpen(false)}>Stats</Link>
      </nav>

      <div className="nav-user">
        {user ? (
          <div className="user-dropdown-container" ref={dropdownRef}>
            <button
              className="user-menu-btn"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <div className="user-avatar">{userInitials}</div>
              <span className="user-name">{user.display_name || user.email || "User"}</span>
              <span className="dropdown-arrow">{dropdownOpen ? "▲" : "▼"}</span>
            </button>

            {dropdownOpen && (
              <div className="user-dropdown">
                <Link
                  to="/profile"
                  className="dropdown-item"
                  onClick={() => setDropdownOpen(false)}
                >
                  ⚙️ Profile Settings
                </Link>
                <Link
                  to="/"
                  className="dropdown-item"
                  onClick={() => setDropdownOpen(false)}
                >
                  📋 My Challenges
                </Link>
                <div className="dropdown-divider" />
                <div className="dropdown-item theme-selector">
                  🎨 Theme:
                  <div className="theme-buttons">
                    <button
                      className={theme === 'light' ? 'active' : ''}
                      onClick={() => setTheme('light')}
                      title="Light"
                    >☀️</button>
                    <button
                      className={theme === 'dark' ? 'active' : ''}
                      onClick={() => setTheme('dark')}
                      title="Dark"
                    >🌙</button>
                    <button
                      className={theme === 'high-contrast' ? 'active' : ''}
                      onClick={() => setTheme('high-contrast')}
                      title="High Contrast"
                    >⬛</button>
                  </div>
                </div>
                <button
                  className="dropdown-item logout-item"
                  onClick={handleLogout}
                >
                  🚪 Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="auth-links">
            <Link to="/login" className="login-link">Login</Link>
            <Link to="/signup" className="signup-btn">Sign Up</Link>
          </div>
        )}
      </div>
    </header>
  );
}
