import React, { createContext, useContext, useEffect, useState } from "react";
import { setAuthToken, verifyLogin } from "./api";
import { auth, logoutFirebase } from "./firebaseClient";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fallbackFromFirebaseUser = () => {
    const fbUser = auth.currentUser;
    if (!fbUser) return null;
    const mapped = {
      firebase_uid: fbUser.uid,
      email: fbUser.email || "",
      display_name: fbUser.displayName || "",
      is_registered: true,
      role: "registered",
    };
    setUser(mapped);
    return mapped;
  };

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) {
      setAuthToken(token);
      verifyLogin()
        .then((data) => setUser(data))
        .catch(() => {
          // If backend verification fails (e.g., API down), fall back to Firebase user so UI can continue.
          const fb = fallbackFromFirebaseUser();
          if (!fb) {
            setAuthToken(null);
            setUser(null);
          }
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const loginWithToken = async (token) => {
    setLoading(true);
    setError("");
    setAuthToken(token);
    try {
      const data = await verifyLogin();
      setUser(data);
      return true;
    } catch (err) {
      const fb = fallbackFromFirebaseUser();
      if (fb) {
        setError("Backend verification failed; using Firebase session only. API calls may not work until backend is up.");
        return true;
      }
      setAuthToken(null);
      setUser(null);
      setError("Login failed. Backend did not accept the token.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
    // Best-effort Firebase sign-out so browser sessions are cleared client-side.
    logoutFirebase().catch(() => {});
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, loginWithToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
