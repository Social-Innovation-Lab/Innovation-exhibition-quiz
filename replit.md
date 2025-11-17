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
The core application is built with Flask, served by `app.py`. It utilizes a PostgreSQL database for data storage. Questions are sourced from a CSV file (`Quiz App ques set2 - QuestionBank_1763360490832.csv`) rather than the database.

**Key Features:**
- **PWA Enabled:** Includes a service worker for caching static assets and offline support, along with a `manifest.json` for home screen installation.
- **Weighted Random Question Selection:** Each quiz dynamically generates 10 questions with a distribution of 2 Easy (0.5 marks each), 4 Medium (0.75 marks each), and 4 Hard (1.5 marks each) questions, shuffled to mix difficulty. Total weighted marks: 10.0
- **Winner Detection:** Participants scoring 70% or higher (7.0 weighted marks) are marked as winners.
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
- `weighted_score` (REAL, nullable) - Weighted score based on difficulty (max 10.0)
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

## Recent Changes
- **2025-11-17 (Latest):** Landing page button validation and result screen updates:
  - **Real-time button validation:** Start Quiz button now activates/deactivates based on input validation
  - **PIN form:** Button enabled only when exactly 6 digits entered, greyed out otherwise
  - **Registration form:** Button enabled only when name is filled AND phone is exactly 11 digits, greyed out otherwise
  - **Auto-digit filtering:** PIN and phone inputs automatically remove non-digit characters
  - **Disabled state styling:** Greyed out button with reduced opacity (0.6) and no-hover effects
- **2025-11-17:** Result screen messaging update and UX improvements:
  - **Smooth transitions:** Changed carousel animation from bouncy cubic-bezier to smooth ease-in-out (0.4s)
  - **Minimal option boxes:** Significantly reduced size - padding (8-10px vertical, 10-12px horizontal), min-height (44-50px), border radius (8px), tighter gaps (8-10px)
  - **Larger option text:** Increased font to 16-18px (from 14-16px) with bold weight (600) for better readability
  - **Smaller letter circles:** Reduced to 32-36px for more compact design
  - **Clean white design:** White background, gray border on all answer options
  - **Clean question display:** White background, normal weight (500) for questions
  - **Weighted score display:** Result page now shows weighted score (out of 10) in the circle instead of regular score
  - **Weighted percentage:** Percentage calculation based on weighted score (weighted_score / 10.0 * 100)
  - **Winner detection:** Updated to use weighted_score >= 7.0 (70% of max weighted marks)
  - **New tiered messaging system:**
    - Below 60%: "Good Try!" / "We appreciate your effort"
    - 60-74%: "Good Job!" / "Please collect your gift from the counter"
    - 75-84%: "Great Work!" / "Please collect your gift from the counter"
    - 85-99%: "Amazing!" / "There is a gift for you at the counter"
    - 100%: "PERFECT!" / "You know BRAC inside-out. There is a surprise waiting for you!"
  - **Updated CTA:** Changed "Thank You" to "Thank you for participating"
  - **Button text:** Changed "Next" to "Next Player"
  - **Removed Back buttons:** Cleaner login flow without back navigation buttons
- **2025-11-17:** Added visible swipe indicators for quiz navigation:
  - **Visual indicators:** Animated red circular buttons with left/right arrows appear on the screen edges
  - **Smart visibility:** Left arrow shows when not on first question, right arrow shows when not on last question
  - **Interactive:** Users can tap the indicators or swipe to navigate between questions
  - **Pulsing animation:** Subtle pulse effect to draw attention and guide users
  - **Responsive sizing:** Indicators scale proportionally using clamp() for all screen sizes
- **2025-11-04:** Complete mobile Submit button proportions fix:
  - **Mobile-specific overrides:** Applied `!important` rules to fully override desktop CSS constraints
  - **Full-width mobile:** Submit button uses 100% width with no max-width constraint on mobile
  - **Viewport-based sizing:** Height uses `clamp(48px, 12vw, 60px)` for proper aspect ratio
  - **Flex display fix:** Changed JavaScript from `display: block` to `display: flex` for proper centering
  - **Phone validation:** Added 11-digit phone number validation (maxlength, pattern, and JavaScript)
- **2025-11-17:** Updated question bank and weighting system:
  - **New CSV:** Switched to `Quiz App ques set2 - QuestionBank_1763360490832.csv` (281 questions)
  - **Custom weights:** Easy = 0.5, Medium = 0.75, Hard = 1.5 (total max: 10.0 marks)
  - **Weight source:** Using custom weight mapping instead of CSV weights
  - **Question distribution:** 2 Easy (1.0) + 4 Medium (3.0) + 4 Hard (6.0) = 10.0 total marks
  - **Winner threshold:** 70% of 10.0 = 7.0 weighted marks
- **2025-10-29:** Comprehensive responsive design fixes with SVG viewBox and clamp() scaling

## External Dependencies
- **PostgreSQL:** Used as the primary database for storing all quiz records. Accessible via the `DATABASE_URL` environment variable provided by Replit.
- **psycopg2:** Python adapter for PostgreSQL.
- **Flask:** Web framework for the application backend.
- **CSV files:** Used for storing the question bank (`Quiz App ques set2 - QuestionBank_1763360490832.csv`).