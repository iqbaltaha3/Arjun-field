ARJUN FIELD

Field Operations & Intelligence Platform
Simple field reporting • Explicit location sessions • Voice-first reporting • Offline-friendly workflows

Arjun Field is a field-operations application designed for teams working across booths, regions, and local areas in Uttar Pradesh and other Indian field environments.

The system is built around one simple idea:

A worker should be able to report what happened in the field without filling long forms.

A worker can start an explicit Field Mode session, obtain their current GPS location, record a natural-language voice report, have the audio transcribed with Sarvam, have the transcript converted into structured data with an LLM, review the result, and save the report.

Administrators get a command-center view for workers, active sessions, locations, reports, and field coverage.

1. Core Workflow

Worker

Login
  ↓
Get current location
  ↓
Start Field Mode
  ↓
Location sharing becomes active
  ↓
Record field report
  ↓
Stop recording
  ↓
Automatic audio chunking
  ↓
Sarvam Speech-to-Text
  ↓
Groq LLM structured extraction
  ↓
Review "Arjun understood"
  ↓
Save report

Admin

Admin Login
  ↓
Command Center
  ├── Dashboard
  ├── Live Workers
  ├── Worker Management
  ├── Map
  └── Recent Field Reports

2. Main Features

Worker App

Worker login using a pre-created Worker ID

Worker identity, booth, region, and area shown clearly

Explicit Field Mode start/stop

Browser GPS permission

Current location capture with accuracy

Location updates targeted at approximately every 3 minutes while Field Mode is active

Voice-first field reporting

Multi-minute recordings

Automatic audio chunking before STT requests

Sarvam speech-to-text

Groq-based structured report extraction

"Arjun understood" review step

Manual text-report fallback

Saved report history for the worker

Audio is not intentionally persisted by the application after processing

Admin Command Center

Worker count

Active workers

Reports today

Booth/area coverage indicators

Live worker list

Current worker locations during active sessions

Map view

Recent reports

Worker creation

Worker deactivation

Basic operational status information

3. Design Principles

Arjun Field is intentionally designed around field conditions rather than office workflows.

Simple

Workers should not have to navigate complex forms while moving around in the field.

Voice-first

Workers can describe an event or observation naturally instead of typing a long structured report.

Explicit location sharing

Location sharing happens only during an explicitly started Field Mode session.

Review before save

The extracted structured report is shown to the worker before it is saved.

Controlled schema

The LLM extracts into a predefined report structure rather than dynamically creating database fields.

Admin clarity

The admin dashboard emphasizes current operational information: who is active, where they are, and what has been reported.

Hindi + English friendly

The UI is intended to work naturally for Uttar Pradesh field teams, with Hindi/English language support as the product evolves.

4. Technology Stack

Frontend

Streamlit

Custom HTML/CSS styling

Streamlit geolocation component

Speech

Sarvam Speech-to-Text

saaras:v4 by default

Multi-minute recordings are split into smaller in-memory chunks before STT requests

LLM

Groq API

Configurable Groq model

Structured JSON extraction for field reports

Database

SQLite

Relational tables for workers, field sessions, locations, and reports

Language/runtime

Python

python-dotenv

requests

pandas

pydub

audioop-lts compatibility package for newer Python versions

5. Project Structure

A typical Arjun Field project looks like:

arjun_field/
│
├── app.py
├── streamlit_app.py
├── config.py
├── db.py
├── location.py
├── sarvam_voice.py
├── llm.py
├── security.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
│
└── tests/
    ├── conftest.py
    ├── test_db.py
    ├── test_security.py
    └── test_llm.py

File responsibilities

File

Purpose

app.py

Main Worker and Admin Streamlit interface

streamlit_app.py

Streamlit entry point

config.py

Environment/configuration loading

db.py

SQLite schema and database operations

location.py

Browser geolocation integration and location parsing

sarvam_voice.py

Audio handling and Sarvam STT

llm.py

Groq API integration and structured extraction

security.py

Authentication/password helpers

requirements.txt

Python dependencies

6. Database Model

Arjun Field uses relational records rather than a separate database table for every worker.

Workers

workers
--------------------------------
worker_id
name
booth_id
region
area
phone
active
created_at

Field Sessions

field_sessions
--------------------------------
session_id
worker_id
started_at
ended_at
status

Worker Locations

worker_locations
--------------------------------
location_id
session_id
worker_id
latitude
longitude
accuracy
recorded_at

Field Reports

field_reports
--------------------------------
report_id
worker_id
session_id
booth_id
region
activity_type
observation
attendance_estimate
follow_up
transcript
latitude
longitude
created_at

The exact schema may evolve as the product develops.

7. Environment Setup

7.1 Create or activate your Python environment

Example:

conda create -n arjun_field python=3.10
conda activate arjun_field

You can also use another supported Python environment.

7.2 Install dependencies

pip install -r requirements.txt

For newer Python versions, the dependency list includes audioop-lts to provide audio compatibility for libraries that historically depended on Python's audioop module.

7.3 Create .env

Copy the example:

cp .env.example .env

Then configure the required secrets.

Example:

ADMIN_ID=admin
ADMIN_PASSWORD=change-this-password

SARVAM_API_KEY=your_sarvam_api_key
SARVAM_STT_MODEL=saaras:v4
SARVAM_STT_MODE=transcribe

LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your_groq_api_key
LLM_BASE_URL=https://api.groq.com/openai/v1

Never commit .env or API keys to Git.

8. Run the Application

From the project directory:

streamlit run streamlit_app.py

The terminal will normally show:

Local URL: http://localhost:8501

Open that address in your browser.

9. Worker Setup

First login

A worker must already exist in the database.

An administrator can create a worker from:

Admin → Workers → Add Worker

The worker receives:

Worker ID

Name

Booth

Region

Area

Phone (optional)

Starting Field Mode

The worker:

Logs in.

Presses Get current location.

Allows browser location permission.

Confirms that a GPS position is available.

Presses Start Field Mode.

Only after Field Mode is active is the worker treated as an active field session.

Recording a report

The worker can:

Press Start recording.

Speak naturally.

Press Stop recording.

Let Arjun process the recording.

Review the transcript and structured interpretation.

Save the report.

For longer reports, the application automatically divides the recording into smaller audio chunks before sending them to the STT service.

10. Location Model

Arjun Field uses an explicit session model.

Field Mode OFF
    ↓
Worker chooses Start Field Mode
    ↓
GPS sharing active
    ↓
Worker works
    ↓
Worker chooses Stop Field Mode
    ↓
GPS sharing session ends

The product should not be used as a hidden continuous tracking system.

Recommended operational controls:

Clearly display when location sharing is active.

Keep the active session visible to the worker.

Use only the minimum location frequency required for the operational purpose.

Avoid retaining detailed location history longer than necessary.

Protect admin access and database files.

11. Voice Processing Architecture

The voice pipeline is intentionally separated into two systems:

Speech-to-text

Browser recording
      ↓
Audio bytes
      ↓
Audio chunking
      ↓
Sarvam STT
      ↓
Transcript

Structured understanding

Transcript
      ↓
Groq LLM
      ↓
Controlled JSON structure
      ↓
Worker review
      ↓
SQLite

This separation means the speech provider and reasoning provider can be changed independently.

12. Multi-Minute Recording

Interactive Sarvam REST transcription requests have a shorter per-request duration limit than a normal field conversation.

Arjun Field therefore uses:

Long recording
      ↓
25-second-ish chunks
      ↓
STT request per chunk
      ↓
Combined transcript

The worker does not need to manually stop and start each chunk.

The application handles chunking internally.

The current application is intended for several-minute field reports rather than very long interviews.

For future versions, a streaming STT/WebSocket architecture can be added when live partial transcription is required.

13. LLM Provider

The current Arjun Field configuration uses Groq.

Example:

LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your_groq_api_key
LLM_BASE_URL=https://api.groq.com/openai/v1

The LLM is used for structured extraction, not for inventing database structure.

A typical extracted report may contain:

{
  "activity_type": "worker_meeting",
  "observation": "A local worker meeting was conducted.",
  "attendance_estimate": 60,
  "follow_up": "Follow-up meeting discussed for next Sunday."
}

The final data structure should remain controlled by the application.

14. Offline-Friendly Design

Field environments can have unstable connectivity.

The intended product direction is:

Worker
  ↓
Capture report
  ↓
Store locally
  ↓
Network available
  ↓
Sync

The current application provides operational fallbacks such as typed reports, but full offline queueing and reliable background synchronization should be treated as a dedicated product enhancement for production mobile deployment.

15. Error Handling

Sarvam DNS/network error

Example:

Failed to resolve 'api.sarvam.ai'

Check:

nslookup api.sarvam.ai
curl -I https://api.sarvam.ai

If curl reaches the Sarvam server, the machine's network/DNS path is working and the issue should be investigated at the Python/runtime/request layer.

Gemini errors

Older versions of Arjun Field used Gemini. The current configuration uses Groq, so Gemini credentials are not required for the current LLM pipeline.

Missing pyaudioop

On newer Python versions, install:

pip install audioop-lts

Then reinstall the project requirements:

pip install -r requirements.txt

Location unavailable

Check:

Browser location permission

Browser privacy settings

HTTPS requirements when deployed remotely

Device GPS availability

Network/browser restrictions

For local development, use:

http://localhost:8501

and allow location access for the local site when prompted.

16. Security

At minimum:

Never commit .env

Never hard-code API keys

Use a strong admin password

Deactivate workers who should no longer access the system

Restrict access to the SQLite database

Protect deployed HTTPS endpoints

Review location retention regularly

Store only operationally necessary personal information

Do not silently track workers outside an explicit active session

For production deployment, authentication, authorization, audit logging, secret management, encrypted storage, and database backups should be strengthened beyond the development implementation.

17. Production Roadmap

The current Streamlit implementation is useful for validating the workflow. A production version can evolve toward:

Worker mobile application

Android / PWA
  ↓
Offline-first local store
  ↓
Background sync
  ↓
Secure API

Backend

API
 ↓
PostgreSQL
 ↓
Queue / workers
 ↓
STT + LLM services

Admin platform

Web Command Center
  ├── Live Operations
  ├── Workers
  ├── Reports
  ├── Maps
  ├── Booth / Area Coverage
  └── Audit Logs

18. Product Direction for Uttar Pradesh

Arjun Field is designed for local field conditions rather than assuming a highly connected enterprise environment.

The UI can evolve around:

Hindi-first labels

Hindi/English switching

Clear booth and area identity

Large touch targets

Very limited typing

Voice-first reporting

Low-bandwidth behavior

Obvious GPS status

Simple worker instructions

Local date/time formatting

Easy-to-read admin dashboards

Mobile-friendly layouts

Explicit worker privacy notices

The goal is to make the worker workflow understandable without requiring technical training.

19. Example Worker Session

राम कुमार
Booth 001
Phulpur

FIELD MODE OFF

[ 📍 Get current location ]

GPS Ready
Accuracy: ±8 m

[ ▶ Start Field Mode ]

────────────────────────

FIELD MODE ACTIVE
Location sharing is ON

Last GPS update
10:42 AM

[ 🎙️ Start recording ]

Speak naturally about what happened in the field.

Recording: 02:17

[ ⏹ Stop recording ]

[ ✨ Understand report ]

────────────────────────

ARJUN UNDERSTOOD

Activity:
Worker meeting

Observation:
...

Follow-up:
...

[ ✓ Save report ]

20. Example Admin Session

ARJUN FIELD · COMMAND

Dashboard

Active Workers        48
Reports Today         37
Areas Covered         26
Last Sync              09:42

Filters
District | Assembly | Booth | Area | Date

────────────────────────────────────────

LIVE WORKER MAP

     ●     ●
          ●
   ●             ●

────────────────────────────────────────

ACTIVE WORKERS

Worker       Booth      Area       Last Update
Ram Kumar    001        Gopalpur   09:42
Seema Yadav  002        Rani       09:38
Arjun Singh  003        Katra      09:31

────────────────────────────────────────

RECENT FIELD REPORTS
...

The production UI should prioritize clarity and action over visual density.

21. Responsible Use

Arjun Field is an operational reporting system.

When deployed in real-world settings, implement clear governance around:

Worker consent and notice for location collection

Access to personal data

Data retention

Audit trails

Administrative permissions

Device security

Use of AI-generated interpretations

Human review of extracted reports

AI-generated structured reports should be treated as an interpretation of the worker's submitted information and reviewed before consequential use.

22. Development Checklist

Before starting a field deployment:

[ ] Set a strong ADMIN_PASSWORD
[ ] Add valid SARVAM_API_KEY
[ ] Add valid GROQ_API_KEY
[ ] Install requirements
[ ] Verify microphone permission
[ ] Verify location permission
[ ] Create worker accounts
[ ] Test Start/Stop Field Mode
[ ] Test GPS updates
[ ] Test a short report
[ ] Test a multi-minute report
[ ] Test STT chunking
[ ] Test Groq extraction
[ ] Test report saving
[ ] Test admin dashboard
[ ] Test worker deactivation
[ ] Back up the database
[ ] Review data retention settings

23. License

Add your organization's chosen license before public distribution.

24. Status

Current status: Working end-to-end prototype / field operations MVP.

The current application successfully connects:

Worker
  → GPS
  → Field Session
  → Voice Recording
  → Sarvam STT
  → Groq Structured Extraction
  → Worker Review
  → SQLite
  → Admin Dashboard

The next major engineering step is production hardening: authentication, offline-first synchronization, secure backend APIs, stronger database infrastructure, mobile deployment, observability, and robust data governance