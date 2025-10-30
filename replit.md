# BRAC Exhibition Quiz - Tablet Kiosk PWA

## Overview
This project is a tablet-friendly Progressive Web App (PWA) designed as a quiz kiosk for BRAC exhibitions. Its primary purpose is to engage participants with 10 randomly generated questions, incorporating weighted difficulty and actual BRAC programme names. The application identifies winners (achieving ≥70% score) and automatically tracks them for gift distribution, with all data stored in a PostgreSQL database and accessible via an admin dashboard. The project aims to provide an engaging, robust, and easily manageable quiz experience for exhibition attendees.

## User Preferences
- **Design:** Clean, minimal, BRAC brand colors (#e31837 red)
- **UX:** Touch-first, tablet-optimized, kiosk-safe
- **Code Style:** Simple, readable Python/Flask with inline comments

## System Architecture

### UI/UX Decisions
The application features a tablet-optimized UI with large tap targets (minimum 48px), 18px readable fonts, and a sticky progress bar. It supports responsive design for various screen sizes (mobile, tablet, large tablet) with scaled UI elements, proportional countdown using vw/vh units, and fixed header for the quiz timer. Input fields for PIN and phone numbers utilize `inputmode="numeric"` and `inputmode="tel"` respectively. Kiosk protection is implemented via `beforeunload` events and `user-select: none` to prevent accidental navigation and text selection. The results page includes an animated SVG score circle, confetti for winners, and clear messaging.

### Technical Implementations
The core application is built with Flask, served by `app.py`. It utilizes a PostgreSQL database for data storage. Questions are sourced from a CSV file (`brac_exhibition_quiz_220_questions.csv`) rather than the database.

**Key Features:**
- **PWA Enabled:** Includes a service worker for caching static assets and offline support, along with a `manifest.json` for home screen installation.
- **Weighted Random Question Selection:** Each quiz dynamically generates 10 questions with a distribution of 2 Easy, 4 Medium, and 4 Hard questions, shuffled to mix difficulty.
- **Winner Detection:** Participants scoring 70% or higher are marked as winners.
- **Two-path Sign-in:** Participants can sign in with a PIN or register with their name and phone number.
- **Admin Dashboard:** Provides real-time statistics, a list of winners, gift tracking, and CSV export functionality, secured by an admin PIN.
- **Security:** Admin routes are protected by PIN authentication, and session management uses a `SESSION_SECRET`.

### Database Schema (PostgreSQL)
A single `quiz_records` table stores all participant and quiz data:
- `id` (SERIAL PRIMARY KEY)
- `name` (TEXT, nullable)
- `pin` (TEXT, nullable)
- `phone` (TEXT, nullable)
- `score` (INTEGER, NOT NULL) - Number of correct answers (0-10)
- `percent` (REAL, NOT NULL) - Percentage score (0-100)
- `weighted_score` (REAL, nullable) - Weighted score based on difficulty (max 16.0)
- `is_winner` (INTEGER, DEFAULT 0) - 1 if score ≥70%, 0 otherwise
- `gift_given` (INTEGER, DEFAULT 0) - 1 if gift has been distributed, 0 otherwise
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### Application Routes
- `GET /`: Landing page for participant sign-in.
- `POST /start`: Initiates a quiz session, creates participant record, and selects questions.
- `POST /submit`: Grades responses and saves the attempt.
- `GET /result`: Displays quiz results and winner status.
- `GET /admin`: Admin dashboard.
- `GET /admin/mark_gift/<id>`: Marks a gift as given for a specific winner.
- `GET /admin/export`: Downloads winners data in CSV format.
- `GET /manifest.json`: PWA manifest file.

## External Dependencies
- **PostgreSQL:** Used as the primary database for storing all quiz records. Accessible via the `DATABASE_URL` environment variable provided by Replit.
- **psycopg2:** Python adapter for PostgreSQL.
- **Flask:** Web framework for the application backend.
- **CSV files:** Used for storing the question bank (`brac_exhibition_quiz_220_questions.csv`).