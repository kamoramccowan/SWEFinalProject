import React from "react";
import { Link } from "react-router-dom";
import "./NavBar.css";
import { useAuth } from "../AuthContext";

export default function NavBar() {
  const { user, logout } = useAuth();

  return (
    <header className="nav-header">
      <Link to="/" className="brand">
        THEE BOGGLE BOOST
      </Link>
      <nav className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/leaderboard">Leaderboard</Link>
        <Link to="/stats">Stats</Link>
        <Link to="/settings">Settings</Link>
      </nav>
      <div className="nav-user">
        {user ? (
          <>
            <Link to="/settings" className="user-menu">User Menu</Link>
            <span className="username">{user.display_name || user.email || "User"}</span>
            <button className="link-button" onClick={logout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/signup">Sign Up</Link>
          </>
        )}
      </div>
    </header>
  );
}
