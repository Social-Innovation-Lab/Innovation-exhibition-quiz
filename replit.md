# BRAC Exhibition Quiz - Tablet Kiosk PWA

## Overview
This project is a tablet-friendly Progressive Web App (PWA) designed as a quiz kiosk for BRAC exhibitions. Its primary purpose is to engage participants with 10 randomly generated questions, incorporating weighted difficulty and actual BRAC programme names. The application identifies winners (achieving ≥70% score) and automatically tracks them for gift distribution, with all data stored in a PostgreSQL database and accessible via an admin dashboard. The project aims to provide an engaging, robust, and easily manageable quiz experience for exhibition attendees, enhancing the visibility of BRAC's innovation initiatives.

## User Preferences
- **Design:** Vibrant orange-to-pink gradient background (#FF9500 → #FF6B35 → #E91E63), Innovation Exhibition branding
- **UX:** Touch-first, tablet-optimized, kiosk-safe
- **Code Style:** Simple, readable Python/Flask with inline comments

## System Architecture

### UI/UX Decisions
The application features a tablet-optimized UI with large tap targets (minimum 48px), 18px readable fonts, and a sticky progress bar. It supports responsive design for various screen sizes with scaled UI elements, proportional countdown using vw/vh units, and a fixed header for the quiz timer. Input fields for PIN and phone numbers utilize `inputmode="numeric"` and `inputmode="tel"` respectively. Kiosk protection is implemented via `beforeunload` events and `user-select: none` to prevent accidental navigation and text selection. The results page includes an animated SVG score circle, confetti for winners, and clear messaging. Language selection is available for English and Bangla.

### Technical Implementations
The core application is built with Flask, served by `app.py`. It utilizes a PostgreSQL database for data storage, with questions sourced from CSV files.

**Key Features:**
- **PWA Enabled:** Includes a service worker for caching static assets and offline support, and a `manifest.json` for home screen installation.
- **Weighted Random Question Selection:** Each quiz dynamically generates 10 questions with a distribution of 6 Easy (0.75 marks each = 4.5), 2 Medium (1.25 marks each = 2.5), and 2 Hard (1.5 marks each = 3.0), shuffled for mixed difficulty. Total weighted marks: 10.0. Questions are automatically cleaned to remove number prefixes like "15. Q:".
- **Winner Detection:** Participants scoring 70% or higher (7.0 weighted marks) are marked as winners.
- **Single Registration:** Participants register with their name and email address.
- **Admin Dashboard:** Provides real-time statistics, a list of all quiz attempts, and CSV export functionality, secured by an admin PIN.
- **Security:** Admin routes are protected by PIN authentication with CSRF protection, and session management uses a `SESSION_SECRET`.
- **Language Selection:** Supports bilingual content (English and Bangla) with dynamic question loading.
- **Attempt Limit:** Participants are limited to 3 quiz attempts, tracked by email address.
- **Experience Rating:** After completing the quiz, participants can rate their experience with a 5-star rating system. Ratings are stored in the database for feedback analysis.

### Database Schema (PostgreSQL)

**quiz_records** - Stores all participant and quiz data:
- `id` (SERIAL PRIMARY KEY)
- `name` (TEXT, nullable)
- `email` (TEXT, nullable)
- `percent` (REAL, NOT NULL) - Percentage score (0-100) based on weighted score
- `weighted_score` (REAL, nullable) - Weighted score based on difficulty (max 10.0)
- `rating` (INTEGER, nullable) - Experience rating (1-5 stars) given after quiz
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### Application Routes
- `GET /`: Landing page for participant sign-in.
- `POST /start`: Initiates a quiz session, creates participant record, and selects questions.
- `POST /submit`: Grades responses and saves the attempt.
- `GET /result`: Displays quiz results and winner status.
- `GET /rate`: Rate your experience page with 5-star rating.
- `POST /rate/submit`: Saves rating to database.
- `GET /rate/thankyou`: Thank you page after rating.
- `GET /admin`: Admin dashboard.
- `GET /admin/export`: Downloads all quiz records in CSV format.
- `GET /manifest.json`: PWA manifest file.

## External Dependencies
- **PostgreSQL:** Used as the primary database for storing all quiz records.
- **psycopg2:** Python adapter for PostgreSQL.
- **Flask:** Web framework for the application backend.
- **CSV files:** Used for storing the question bank:
  - `questions_english.csv` (376 questions)
  - `questions_bangla.csv` (324 questions)