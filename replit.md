# BRAC Exhibition Quiz - Tablet Kiosk PWA

## Overview
A tablet-friendly Progressive Web App (PWA) quiz kiosk for BRAC exhibitions. Displays 10 randomly generated questions with weighted difficulty distribution. Programme names are hidden (replaced with "this programme") to increase challenge. Winners (≥70% = 7/10) are tracked with automatic Excel export.

## Project Status
**Status:** ✅ Fully Functional  
**Last Updated:** October 22, 2025  
**Version:** 2.1

## Key Features
- **Tablet-Optimized UI:** Large tap targets (48px min), readable 18px fonts, sticky progress bar
- **PWA Enabled:** Service worker caching, installable to home screen, offline asset support
- **Kiosk Mode:** Prevention of accidental back/refresh with confirmation dialogs
- **Weighted Random Selection:** Questions randomly selected with 40% Easy, 30% Medium, 30% Hard distribution
- **Winner Detection:** 70% threshold (7/10 questions) triggers winner status
- **Anonymous Questions:** Programme names replaced with "this programme" to increase difficulty
- **Admin Dashboard:** Real-time stats, winner list, gift tracking, CSV export
- **SQLite with WAL:** Concurrent access support for multiple tablets

## Architecture

### Database Schema (SQLite with WAL mode)
- **questions:** 220 questions across all programmes with difficulty (Easy/Medium/Hard) and weight (1/1.5/2)
- **participants:** Name, PIN, phone, consent timestamp
- **attempts:** Quiz scores (out of 10), winner status, gift given flag
- **responses:** Individual question answers and correctness

### Application Routes
- `GET /` - Landing page with participant sign-in form
- `POST /start` - Creates participant record, selects 10 weighted random questions, displays quiz
- `POST /submit` - Grades responses, saves attempt, exports to Excel
- `GET /result` - Shows score with confetti animation
- `GET /admin` - Admin dashboard with stats and winner list
- `GET /admin/mark_gift/<id>` - Marks gift as given
- `GET /admin/export` - Downloads winners.csv
- `GET /manifest.json` - PWA manifest

### Weighted Random Selection Logic
Each quiz generates a fresh set of 10 questions:
1. **4 Easy questions** (weight 1.0) - 40% of quiz
2. **3 Medium questions** (weight 1.5) - 30% of quiz
3. **3 Hard questions** (weight 2.0) - 30% of quiz
4. Questions shuffled to mix difficulty levels
5. Programme names replaced with "this programme" to hide identity

## File Structure
```
.
├── app.py                          # Flask application (all routes & logic)
├── quiz.db                         # SQLite database (auto-created)
├── templates/
│   ├── base.html                   # Base template with PWA meta tags
│   ├── index.html                  # Sign-in form with numeric keyboards
│   ├── quiz.html                   # 22-question quiz with progress bar
│   ├── result.html                 # Results page with winner messaging
│   └── admin.html                  # Admin dashboard
├── static/
│   ├── styles.css                  # Tablet-optimized CSS (touch targets)
│   ├── main.js                     # Quiz progress tracking & kiosk protection
│   ├── sw.js                       # Service worker (PWA caching)
│   ├── brac-logo.jpg               # BRAC logo for sign-in page
│   ├── favicon.png                 # PWA favicon
│   └── icons/
│       ├── icon-192.png            # PWA icon (192×192)
│       └── icon-512.png            # PWA icon (512×512)
└── attached_assets/
    └── brac_exhibition_quiz_220_questions.csv  # Source question bank
```

## Technical Specifications

### Tablet-Friendly Features
1. **Viewport Meta:** `maximum-scale=1, viewport-fit=cover` prevents zoom
2. **Touch Targets:** All interactive elements ≥48px height
3. **Numeric Keyboards:** `inputmode="numeric"` for 6-digit PIN, `inputmode="tel"` for phone
4. **Kiosk Protection:** `beforeunload` event prevents accidental navigation
5. **No Text Selection:** `user-select: none` prevents bounce/highlight issues

### PWA Configuration
- **Manifest:** `/manifest.json` with BRAC branding (#e31837 red)
- **Service Worker:** Caches static assets (HTML, CSS, JS, icons)
- **Offline Support:** Quiz submissions require network, assets cached locally
- **Install Prompt:** Works on iOS Safari and Android Chrome

### Database Concurrency
```python
# WAL mode for concurrent reads/writes
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
```

## Winner Criteria
- **Threshold:** 16/22 questions correct (70%)
- **Prize Desk:** Winners instructed to collect gift
- **Admin Tracking:** Mark gifts as given, export to CSV

## CSV Export Format
```
Name,PIN,Phone,Score,Percentage,Date,Gift Given
John Doe,1234,****5678,18,81.82%,2025-10-21 10:30:15,Yes
```

## Security

### Admin Authentication
- **Admin PIN Required:** All admin routes (`/admin`, `/admin/export`, `/admin/mark_gift`) are protected by PIN authentication
- **Default PIN:** `2025` (can be changed via `ADMIN_PIN` environment variable)
- **Session-based:** Admin login persists in session, can be logged out
- **POST for Actions:** Gift marking uses POST requests to prevent URL manipulation

### Session Management
- The app uses `SESSION_SECRET` environment variable for Flask sessions
- Auto-generated if not set
- Separate sessions for participants and admin authentication

## Running the App
```bash
python3 app.py
```
Server runs on `http://0.0.0.0:5000`

## Question Bank
- **Total Questions:** 220
- **Difficulty Levels:** Easy (66), Medium (66), Hard (88)
- **Weight Distribution:** Easy=1.0, Medium=1.5, Hard=2.0
- **Format:** Multiple choice (A, B, C, D)
- **Programme Names:** Hidden - replaced with "this programme"

## User Preferences
- **Design:** Clean, minimal, BRAC brand colors (#e31837 red)
- **UX:** Touch-first, tablet-optimized, kiosk-safe
- **Code Style:** Simple, readable Python/Flask with inline comments

## Recent Changes
- **2025-10-22 v2.1:** Interactive UX/UI overhaul:
  - **Landing page**: Animated hero with bouncing logo, "How It Works" step cards, gradient background, smooth fade-in animations
  - **Quiz carousel**: Single-question display with swipe navigation, prev/next buttons, auto-advance after selection
  - **Visual feedback**: Green glow on selected answers, animated checkmarks, rotating option letters, instant encouragement messages
  - **Gamification**: Streak counter with fire emoji, animated progress dots, smooth progress bar transitions
  - **Touch optimization**: 60px+ touch targets, hover effects, scale animations, passive touch listeners for performance
  - **Results page**: Animated SVG score circle with progressive ring fill, counting animation from 0 to final score, confetti for winners
  - **Micro-interactions**: Smooth slide transitions between questions, shake animation for unanswered questions, pulse effects on streak
  - **Enhanced accessibility**: Better visual hierarchy, clear labels with icons, improved contrast, responsive design
- **2025-10-22 v2.0:** Complete quiz system overhaul:
  - Switched from 22 fixed questions to 10 randomly generated questions
  - Implemented weighted random selection (40% Easy, 30% Medium, 30% Hard)
  - Removed programme names from questions (replaced with "this programme")
  - Updated winner threshold to 7/10 (70%)
  - Updated all displays, scoring, and Excel export to show /10
  - New question bank with difficulty and weight columns
  - Removed rotation queue system in favor of true random selection
- **2025-10-22 v1.2:** Enhanced result page and Excel export:
  - Redesigned score page with centered layout, larger bold score display
  - Added visual progress bar showing percentage with green gradient
  - Added confetti animation (canvas-confetti) that plays when results are shown
  - Added "Thank you for playing!" message
  - Implemented automatic Excel export (quiz_results.xlsx) - saves each quiz result with BRAC branding
  - Fixed session cookie issues in iframe by removing redirects and passing data via form fields
- **2025-10-21 v1.1:** Updated sign-in page - Added BRAC logo, changed title to "BRAC Innovation Exhibition 2025", added tagline "Play the Quiz to Flex Your Reflex", changed PIN requirement to exactly 6 digits, removed consent checkbox
- **2025-10-21 v1.0:** Initial build - Complete PWA quiz kiosk with rotation queues, admin dashboard, and CSV export
