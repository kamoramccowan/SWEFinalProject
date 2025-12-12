# THEE BOGGLE BOOST 🎲

A community-driven, web-based word puzzle platform inspired by the classic Boggle game. Create custom puzzles, challenge friends, compete on leaderboards, and improve your vocabulary!

## 🎮 Features

- **Create Challenges** - Build custom Boggle boards (4×4, 5×5, 6×6) with auto-generated valid word lists
- **Play Challenges** - Solve puzzles created by others with timed gameplay
- **Daily Challenge** - New global challenge every day for all players
- **Leaderboards** - Compete for top rankings with real-time score tracking
- **Hints System** - Get help finding words (limited per game)
- **Shuffle & Rotate** - Rearrange the board for a fresh perspective
- **Multilingual** - Support for English, Spanish, and French
- **Email Invites** - Challenge friends via email with SendGrid integration
- **Profile Customization** - Upload avatars and choose themes (Light/Dark/High-Contrast)
- **Stats Dashboard** - Track your performance over time

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React.js |
| Backend | Django REST Framework |
| Database | PostgreSQL |
| Authentication | Firebase Auth (Google OAuth) |
| Frontend Hosting | Firebase Hosting |
| Backend Hosting | Railway |
| Image Storage | Cloudinary |
| Email Service | SendGrid |

## 📁 Project Structure

```
SWEFinalProject-backend/
├── boggle-app/                 # React Frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components
│   │   ├── api.js              # API client
│   │   ├── AuthContext.js      # Auth state management
│   │   └── ThemeContext.js     # Theme management
│   ├── public/
│   └── package.json
│
├── boggle_backend/             # Django Backend
│   ├── accounts/               # User authentication & profiles
│   ├── game/                   # Core game logic
│   │   ├── views.py            # API endpoints
│   │   ├── models.py           # Database models
│   │   ├── word_solver.py      # Boggle solving algorithm
│   │   └── hints.py            # Hint generation
│   ├── boggle_backend/         # Django settings
│   ├── requirements.txt
│   └── manage.py
```

## 🚀 Getting Started

### Prerequisites

- Node.js (v18+)
- Python (3.11+)
- PostgreSQL (for production) or SQLite (for local development)
- Firebase account
- Railway account (for deployment)

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/SWEFinalProject-backend.git
cd SWEFinalProject-backend
```

#### 2. Backend Setup

```bash
cd boggle_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your Firebase credentials and secret key

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

#### 3. Frontend Setup

```bash
cd boggle-app

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env with your API URL and Firebase config

# Start development server
npm start
```

### Environment Variables

#### Backend (.env)
```
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://user:pass@host:5432/dbname
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=your-verified-email@example.com
```

#### Frontend (.env)
```
REACT_APP_API_BASE=http://localhost:8000/api
REACT_APP_CLOUDINARY_CLOUD_NAME=your-cloud-name
REACT_APP_CLOUDINARY_UPLOAD_PRESET=your-preset
```

## 🌐 Deployment

### Deploy Backend to Railway

1. Push code to GitHub
2. Create new project on Railway
3. Connect GitHub repository
4. Set root directory to `boggle_backend`
5. Add environment variables (DATABASE_URL, SECRET_KEY, etc.)
6. Railway auto-deploys on push

### Deploy Frontend to Firebase

```bash
cd boggle-app

# Build production bundle
npm run build

# Deploy to Firebase
npx firebase deploy --only hosting
```

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/firebase-login/` | Login with Firebase token |
| GET | `/api/auth/verify/` | Verify session |
| GET | `/api/challenges/` | List challenges |
| POST | `/api/challenges/` | Create challenge |
| POST | `/api/challenges/generate/` | Generate solvable grid |
| POST | `/api/sessions/` | Start game session |
| POST | `/api/sessions/{id}/submit-word/` | Submit word |
| GET | `/api/sessions/{id}/hint/` | Get hint |
| POST | `/api/sessions/{id}/end/` | End session |
| GET | `/api/leaderboards/daily/` | Daily leaderboard |
| GET | `/api/daily/` | Get daily challenge |
| GET | `/api/profile/` | Get user profile |
| PUT | `/api/profile/` | Update profile |

## 🎯 Game Rules

1. Find words by connecting adjacent letters (horizontal, vertical, diagonal)
2. Each letter tile can only be used once per word
3. Words must be at least 3 letters long
4. Words must exist in the game's dictionary
5. Score points based on word length:
   - 3-4 letters: 1 point
   - 5 letters: 2 points
   - 6 letters: 3 points
   - 7 letters: 5 points
   - 8+ letters: 11 points

## 👥 Team

- Lum Kelly Chelsie Choh
- Nia Greene
- Kamora Jhenne McCowan
- Ibrahim Osman
- Michael Cobbins

## 📄 License

This project was created for CS 422 - Software Engineering Final Project.

## 🔗 Links

- **Live App:** [thee-boggle-boost-4ec28.web.app](https://thee-boggle-boost-4ec28.web.app)
- **Backend API:** Hosted on Railway
