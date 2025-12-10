import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const THEMES = {
    light: 'light',
    dark: 'dark',
    highContrast: 'high-contrast'
};

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(() => {
        // Load from localStorage or default to light
        const saved = localStorage.getItem('boggle-theme');
        return saved && Object.values(THEMES).includes(saved) ? saved : THEMES.light;
    });

    useEffect(() => {
        // Apply theme class to document body
        document.body.classList.remove('theme-light', 'theme-dark', 'theme-high-contrast');
        document.body.classList.add(`theme-${theme}`);
        localStorage.setItem('boggle-theme', theme);
    }, [theme]);

    const toggleTheme = (newTheme) => {
        if (Object.values(THEMES).includes(newTheme)) {
            setTheme(newTheme);
        }
    };

    return (
        <ThemeContext.Provider value={{ theme, setTheme: toggleTheme, THEMES }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
