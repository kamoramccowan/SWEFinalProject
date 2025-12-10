import React, { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { useTheme, THEMES } from '../ThemeContext';
import { fetchProfile, updateProfile } from '../api';
import './ProfilePage.css';

// Cloudinary upload widget configuration
const CLOUDINARY_CLOUD_NAME = process.env.REACT_APP_CLOUDINARY_CLOUD_NAME || 'demo';
const CLOUDINARY_UPLOAD_PRESET = process.env.REACT_APP_CLOUDINARY_UPLOAD_PRESET || 'ml_default';

export default function ProfilePage() {
    const { user } = useAuth();
    const { theme, setTheme } = useTheme();
    const [avatarUrl, setAvatarUrl] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [message, setMessage] = useState('');
    const [uploading, setUploading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(true);

    // Load profile on mount
    useEffect(() => {
        const loadProfile = async () => {
            try {
                const profile = await fetchProfile();
                setAvatarUrl(profile.avatar_url || '');
                setDisplayName(profile.display_name || '');
            } catch (err) {
                // Fallback to user context data
                setAvatarUrl(user?.avatar_url || '');
                setDisplayName(user?.display_name || '');
            } finally {
                setLoading(false);
            }
        };
        loadProfile();
    }, [user]);

    const handleAvatarUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setUploading(true);
        setMessage('');

        // Use the configured cloud or fallback to demo
        const cloudName = CLOUDINARY_CLOUD_NAME;
        const uploadPreset = CLOUDINARY_UPLOAD_PRESET;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('upload_preset', uploadPreset);

        try {
            const response = await fetch(
                `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`,
                {
                    method: 'POST',
                    body: formData,
                }
            );

            const data = await response.json();

            if (data.secure_url) {
                setAvatarUrl(data.secure_url);
                setMessage('✅ Avatar uploaded! Click Save Profile to keep it.');
            } else if (data.error) {
                // Provide helpful error message for common issues
                if (data.error.message.includes('Upload preset')) {
                    setMessage('⚠️ To enable uploads, create a Cloudinary account and add REACT_APP_CLOUDINARY_CLOUD_NAME and REACT_APP_CLOUDINARY_UPLOAD_PRESET to your .env file');
                } else {
                    setMessage(`Upload failed: ${data.error.message}`);
                }
            } else {
                setMessage('Upload failed. Please check your Cloudinary settings.');
            }
        } catch (error) {
            setMessage('Upload error: ' + error.message);
        } finally {
            setUploading(false);
        }
    };

    const handleSaveProfile = async () => {
        setSaving(true);
        setMessage('');
        try {
            await updateProfile({ display_name: displayName, avatar_url: avatarUrl });
            setMessage('✅ Profile saved successfully!');
        } catch (err) {
            const detail = err?.response?.data?.message || 'Failed to save profile.';
            setMessage(`❌ ${detail}`);
        } finally {
            setSaving(false);
        }
    };

    const userInitials = user
        ? (user.display_name || user.email || 'U')[0].toUpperCase()
        : '?';

    return (
        <div className="page profile-page">
            <h1>Profile Settings</h1>

            <div className="profile-card">
                <div className="avatar-section">
                    <div className="avatar-preview">
                        {avatarUrl ? (
                            <img src={avatarUrl} alt="Avatar" className="avatar-image" />
                        ) : (
                            <div className="avatar-placeholder">{userInitials}</div>
                        )}
                    </div>
                    <div className="avatar-upload">
                        <label className="upload-btn">
                            {uploading ? 'Uploading...' : 'Upload Avatar'}
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleAvatarUpload}
                                disabled={uploading}
                                hidden
                            />
                        </label>
                        <p className="upload-hint">Powered by Cloudinary</p>
                    </div>
                </div>

                <div className="profile-form">
                    <div className="form-group">
                        <label>Display Name</label>
                        <input
                            type="text"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                            placeholder="Your display name"
                        />
                    </div>

                    <div className="form-group">
                        <label>Email</label>
                        <input
                            type="email"
                            value={user?.email || ''}
                            disabled
                            className="disabled"
                        />
                        <span className="hint">Email cannot be changed</span>
                    </div>

                    <div className="form-group">
                        <label>Theme Preference</label>
                        <div className="theme-options">
                            <button
                                className={`theme-btn ${theme === 'light' ? 'active' : ''}`}
                                onClick={() => setTheme('light')}
                            >
                                ☀️ Light
                            </button>
                            <button
                                className={`theme-btn ${theme === 'dark' ? 'active' : ''}`}
                                onClick={() => setTheme('dark')}
                            >
                                🌙 Dark
                            </button>
                            <button
                                className={`theme-btn ${theme === 'high-contrast' ? 'active' : ''}`}
                                onClick={() => setTheme('high-contrast')}
                            >
                                ⬛ High Contrast
                            </button>
                        </div>
                    </div>

                    {message && <div className="message">{message}</div>}

                    <button className="save-btn" onClick={handleSaveProfile} disabled={saving}>
                        {saving ? 'Saving...' : 'Save Profile'}
                    </button>
                </div>
            </div>
        </div>
    );
}
