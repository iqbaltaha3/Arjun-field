# Arjun Field

A structurally simple field-operations Streamlit app with explicit Field Mode location sharing, 3-minute GPS refresh, worker voice reports, admin live-worker dashboard, and SQLite.

## Flow
Worker login -> Start Field Mode -> browser GPS permission -> location point every 3 minutes while the page is open -> voice report -> Sarvam STT -> LLM extraction -> worker review -> SQLite.

Admin login -> live active workers -> latest GPS -> map -> worker management -> reports.

Audio is processed in memory and is not written to disk or SQLite.

## Run
```bash
conda activate ml_env
pip install -r requirements.txt
cp .env.example .env
# edit .env
streamlit run app.py
```

Default admin ID is `admin`; change the password before deployment.

## GPS
Browser geolocation requires permission and a secure context. `localhost` works for local development; a deployed app should use HTTPS. GPS refresh is scheduled every 180 seconds while Field Mode is active. The worker must keep the page open. If the browser suspends the tab/background, a scheduled browser refresh may be delayed.

## Voice
Sarvam's real-time speech-to-text endpoint has a 30-second limit, so worker recordings are intentionally limited to short field notes. The app does not save the audio bytes.
