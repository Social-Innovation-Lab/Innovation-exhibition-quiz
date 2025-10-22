# BRAC Exhibition Quiz - Tablet Kiosk PWA

## Overview
A tablet-friendly Progressive Web App (PWA) quiz kiosk for BRAC exhibitions. Displays 22 questions (one per programme) with intelligent rotation to minimize repeats across participants. Winners (≥70% score) are tracked with CSV export capability.

## Project Status
**Status:** ✅ Fully Functional  
**Last Updated:** October 22, 2025  
**Version:** 1.2

## Key Features
- **Tablet-Optimized UI:** Large tap targets (48px min), readable 18px fonts, sticky progress bar
- **PWA Enabled:** Service worker caching, installable to home screen, offline asset support
- **Kiosk Mode:** Prevention of accidental back/refresh with confirmation dialogs
- **Smart Rotation:** Per-programme question rotation queues minimize repeats across participants
- **Winner Detection:** 70% threshold (16/22 questions) triggers winner status
- **Admin Dashboard:** Real-time stats, winner list, gift tracking, CSV export
- **SQLite with WAL:** Concurrent access support for multiple tablets

## Architecture

### Database Schema (SQLite with WAL mode)
- **questions:** 220 questions (22 programmes × 10 questions each)
- **rotation_queue:** Tracks question usage per programme to rotate fairly
- **participants:** Name, PIN, phone, consent timestamp
- **attempts:** Quiz scores, winner status, gift given flag
- **responses:** Individual question answers and correctness

### Application Routes
- `GET /` - Landing page with participant sign-in form
- `POST /start` - Creates participant record, starts quiz
- `GET /quiz` - Displays 22 questions (one per programme)
- `POST /submit` - Grades responses, saves attempt
- `GET /result` - Shows score and winner status
- `GET /admin` - Admin dashboard with stats and winner list
- `GET /admin/mark_gift/<id>` - Marks gift as given
- `GET /admin/export` - Downloads winners.csv
- `GET /manifest.json` - PWA manifest

### Rotation Queue Logic
Each programme has its own rotation queue. When a quiz starts:
1. System selects question with minimum `times_used` for each programme
2. Preference given to lower position on ties
3. Selected question's `times_used` counter increments
4. Result: Even distribution across all questions, minimal repeats

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
- **Programmes:** 22 (UDP, DRMP, CCP, KUMON, ASC, BEP, BHP, BPL, BYP, DAIRY, FISH, GJD, etc.)
- **Questions per Programme:** 10
- **Format:** Multiple choice (A, B, C, D)

## User Preferences
- **Design:** Clean, minimal, BRAC brand colors (#e31837 red)
- **UX:** Touch-first, tablet-optimized, kiosk-safe
- **Code Style:** Simple, readable Python/Flask with inline comments

## Recent Changes
- **2025-10-22 v1.2:** Enhanced result page and Excel export:
  - Redesigned score page with centered layout, larger bold score display
  - Added visual progress bar showing percentage with green gradient
  - Added confetti animation (canvas-confetti) that plays when results are shown
  - Added "Thank you for playing!" message
  - Implemented automatic Excel export (quiz_results.xlsx) - saves each quiz result with BRAC branding
  - Fixed session cookie issues in iframe by removing redirects and passing data via form fields
- **2025-10-21 v1.1:** Updated sign-in page - Added BRAC logo, changed title to "BRAC Innovation Exhibition 2025", added tagline "Play the Quiz to Flex Your Reflex", changed PIN requirement to exactly 6 digits, removed consent checkbox
- **2025-10-21 v1.0:** Initial build - Complete PWA quiz kiosk with rotation queues, admin dashboard, and CSV export
