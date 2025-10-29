# BRAC Exhibition Quiz - Tablet Kiosk PWA

## Overview
A tablet-friendly Progressive Web App (PWA) quiz kiosk for BRAC exhibitions. Displays 10 randomly generated questions with weighted difficulty distribution showing actual BRAC programme names. Winners (≥70% = 7/10) are tracked with automatic Excel export.

## Project Status
**Status:** ✅ Fully Functional  
**Last Updated:** October 29, 2025  
**Version:** 2.6

## Key Features
- **Tablet-Optimized UI:** Large tap targets (48px min), readable 18px fonts, sticky progress bar
- **PWA Enabled:** Service worker caching, installable to home screen, offline asset support
- **Kiosk Mode:** Prevention of accidental back/refresh with confirmation dialogs
- **Weighted Random Selection:** Questions randomly selected with 3 Easy, 3 Medium, 4 Hard distribution
- **Winner Detection:** 70% threshold (7/10 questions) triggers winner status
- **Programme Names Visible:** Questions display actual BRAC programme names
- **Admin Dashboard:** Real-time stats, winner list, gift tracking, CSV export
- **PostgreSQL Database:** Production-grade database with concurrent access support for multiple tablets

## Architecture

### Database Schema (PostgreSQL)
- **Single Table:** `quiz_records` - Stores all quiz data in one simplified table
  - **Login credentials (nullable):**
    - `name` - Only filled for "Don't Have PIN" users
    - `pin` - Only filled for "Have PIN" users
    - `phone` - Only filled for "Don't Have PIN" users
  - **Quiz results:** score (out of 10), percent
  - **Prize tracking:** is_winner (70% threshold), gift_given (admin tracking)
  - **Timestamp:** created_at (auto-generated)
- **Sign-up Methods:**
  - **"Have PIN" users:** Only PIN is stored (name and phone are NULL)
  - **"Don't Have PIN" users:** Only name and phone are stored (PIN is NULL)
- **Questions:** Loaded directly from CSV file (not stored in database)
- **Storage:** Uses Replit's built-in PostgreSQL database (accessible via DATABASE_URL)

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
1. **2 Easy questions** (weight 1.0) - 20% of quiz
2. **4 Medium questions** (weight 1.5) - 40% of quiz
3. **4 Hard questions** (weight 2.0) - 40% of quiz
4. Questions shuffled to mix difficulty levels
5. Actual BRAC programme names displayed in questions

## File Structure
```
.
├── app.py                          # Flask application (all routes & logic)
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

### Database Structure
```sql
CREATE TABLE quiz_records (
    id SERIAL PRIMARY KEY,
    name TEXT,              -- NULL for "Have PIN" users
    pin TEXT,               -- NULL for "Don't Have PIN" users
    phone TEXT,             -- NULL for "Have PIN" users
    score INTEGER NOT NULL,
    percent REAL NOT NULL,
    is_winner INTEGER DEFAULT 0,
    gift_given INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Database Connection
```python
# PostgreSQL connection using psycopg2
import psycopg2
import psycopg2.extras

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn
```

## Winner Criteria
- **Threshold:** 16/22 questions correct (70%)
- **Prize Desk:** Winners instructed to collect gift
- **Admin Tracking:** Mark gifts as given, export to CSV

## CSV Export Format (Admin Dashboard Only)
```
Name,PIN,Phone,Score,Percentage,Date,Gift Given
John Doe,1234,****5678,9,90.00%,2025-10-29 10:30:15,Yes
```
Note: CSV export is now only available through the admin dashboard at `/admin/export`. All data is permanently stored in PostgreSQL.

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
- **Programme Names:** Visible in questions

## User Preferences
- **Design:** Clean, minimal, BRAC brand colors (#e31837 red)
- **UX:** Touch-first, tablet-optimized, kiosk-safe
- **Code Style:** Simple, readable Python/Flask with inline comments

## Recent Changes
- **2025-10-29 v2.6:** Simplified database to single table:
  - **Single table design**: Replaced 4-table schema with one `quiz_records` table storing login credentials, scores, and prize data
  - **CSV-based questions**: Questions loaded directly from CSV file instead of database storage (220 questions remain available)
  - **Simplified data flow**: Each quiz submission creates one database record with name, PIN, phone, score, percent, and winner status
  - **Reduced complexity**: Eliminated participant/attempt/response relationships for streamlined kiosk operation
- **2025-10-29 v2.5:** Migrated to PostgreSQL database:
  - **Database migration**: Migrated from SQLite to Replit's built-in PostgreSQL database
  - **Removed Excel export**: All data is now stored permanently in PostgreSQL instead of temporary Excel files
  - **Persistent storage**: Quiz results, participants, and scores are now stored in a production-grade database
  - **Updated dependencies**: Removed openpyxl, added psycopg2-binary for PostgreSQL support
  - **Database queries**: Updated all queries to use PostgreSQL syntax (%s placeholders instead of ?)
- **2025-10-29 v2.4:** Weighted scoring and tiered prize messages:
  - **Dual score display**: Results now show BOTH number of questions correct (out of 10) in the circle AND weighted marks (out of 16.0) in separate box
  - **Weighted calculation**: Easy questions = 1.0 mark, Medium = 1.5 marks, Hard = 2.0 marks
  - **Total possible weighted marks**: 2 Easy (2.0) + 4 Medium (6.0) + 4 Hard (8.0) = 16.0
  - **Tiered prize messages**: 90%+ wins one-on-one meeting with leader, 80-90% wins gift, 70-80% wins lunch token
  - **Removed "Missed prize by" message**: Cleaner results page without showing how close non-winners were
  - **Fixed progress bar**: Progress ribbon now reaches stamps precisely using formula ((answered-1)/(total-1))*100
  - **Less bright stamps**: Reduced stamp brightness with 90% opacity and softer glow effect
- **2025-10-29 v2.3:** Two-path login system and timer enhancements:
  - **Two-path sign-in**: Landing page now has two options - "Have PIN?" (PIN-only entry) and "Don't Have PIN?" (Name+Phone registration)
  - **Auto-generated data**: "Have PIN" users auto-generate name as "Player-{PIN}" and phone as "PIN{PIN}"; "Don't Have PIN" users auto-generate random 6-digit PIN
  - **Countdown timer**: Added 3-2-1 countdown before quiz starts with full-screen overlay animation
  - **150-second timer**: Increased quiz duration from 100 to 150 seconds with clock emoji (⏰)
  - **Fixed timer bar**: Quiz header now uses position:fixed to stay visible during scrolling
  - **Clean UI**: Removed all emojis from option buttons and form labels for professional look
  - **Updated messaging**: Changed "Choose an option to continue" to "Sign-up to play"
  
## Recent Changes
- **2025-10-22 v2.2:** Restored actual BRAC programme names in questions (removed "this programme" replacement), changed results page header from "Results" to "Score", compact landing page with smaller proportions
- **2025-10-22 v2.1:** Interactive UX/UI overhaul with tablet kiosk optimizations:
  - **Landing page**: Animated hero with bouncing logo, "How It Works" step cards, gradient background, smooth fade-in animations
  - **Quiz carousel**: Single-question display with bidirectional swipe navigation (swipe left/right freely), prev/next buttons, auto-advance after selection, all questions and options properly capitalized, 4 answer options (A, B, C, D) per question
  - **80-second timer**: Countdown timer with clock emoji (⏰) at top-left, warning state at 30s (yellow), danger state at 10s (red pulsing), auto-submit when time expires
  - **Visual feedback**: Blue glow on selected answers (#2196F3), animated checkmarks, rotating option letters, instant encouragement messages
  - **Touch optimization**: 60px+ touch targets, hover effects, scale animations, passive touch listeners, no-scroll layout
  - **Clean UI**: Removed difficulty level badges (Easy/Medium/Hard) from quiz display for cleaner look
  - **Results page**: Animated SVG score circle with progressive ring fill, counting animation from 0 to final score, confetti for winners, "out of 10" format, "Missed a prize by X points" message with lightbulb emoji, "Next Player" button, playful messaging (💪 "Bravo! We see you! Stop flexing now!" for winners, ✌️ "Good Try! Not enough knowledge to flex" for non-winners)
  - **Micro-interactions**: Smooth slide transitions between questions, shake animation for unanswered questions
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
