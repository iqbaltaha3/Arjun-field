import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from config import DB_PATH


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA journal_mode=WAL')
        yield c
        c.commit()
    finally:
        c.close()

def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS workers (
            worker_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            booth_id TEXT NOT NULL,
            region TEXT NOT NULL,
            area TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS field_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL CHECK(status IN ('active','ended')),
            FOREIGN KEY(worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS worker_locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            worker_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES field_sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY(worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_locations_worker_time ON worker_locations(worker_id, recorded_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_status ON field_sessions(status);
        CREATE TABLE IF NOT EXISTS field_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            session_id INTEGER,
            booth_id TEXT NOT NULL,
            region TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            observation TEXT NOT NULL,
            attendance_estimate INTEGER,
            follow_up TEXT DEFAULT '',
            transcript TEXT DEFAULT '',
            latitude REAL,
            longitude REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE,
            FOREIGN KEY(session_id) REFERENCES field_sessions(session_id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_reports_worker_time ON field_reports(worker_id, created_at);
        ''')

def get_worker(worker_id):
    with conn() as c:
        return c.execute('SELECT * FROM workers WHERE worker_id=?', (worker_id,)).fetchone()

def list_workers(include_inactive=True):
    with conn() as c:
        q='SELECT * FROM workers ORDER BY name COLLATE NOCASE'
        if not include_inactive: q='SELECT * FROM workers WHERE active=1 ORDER BY name COLLATE NOCASE'
        return c.execute(q).fetchall()

def add_worker(worker_id, name, booth_id, region, area='', phone=''):
    with conn() as c:
        c.execute('INSERT INTO workers(worker_id,name,booth_id,region,area,phone,created_at) VALUES(?,?,?,?,?,?,?)',
                  (worker_id.strip(), name.strip(), booth_id.strip(), region.strip(), area.strip(), phone.strip(), utcnow()))

def deactivate_worker(worker_id):
    with conn() as c:
        c.execute('UPDATE workers SET active=0 WHERE worker_id=?', (worker_id,))
        c.execute("UPDATE field_sessions SET status='ended', ended_at=? WHERE worker_id=? AND status='active'", (utcnow(), worker_id))

def start_session(worker_id):
    with conn() as c:
        c.execute("UPDATE field_sessions SET status='ended', ended_at=? WHERE worker_id=? AND status='active'", (utcnow(), worker_id))
        cur=c.execute('INSERT INTO field_sessions(worker_id,started_at,status) VALUES(?,?,?)', (worker_id,utcnow(),'active'))
        return cur.lastrowid

def end_session(worker_id):
    with conn() as c:
        c.execute("UPDATE field_sessions SET status='ended', ended_at=? WHERE worker_id=? AND status='active'", (utcnow(),worker_id))

def active_session(worker_id):
    with conn() as c:
        return c.execute("SELECT * FROM field_sessions WHERE worker_id=? AND status='active' ORDER BY session_id DESC LIMIT 1", (worker_id,)).fetchone()

def add_location(session_id, worker_id, lat, lon, accuracy=None):
    with conn() as c:
        c.execute('INSERT INTO worker_locations(session_id,worker_id,latitude,longitude,accuracy,recorded_at) VALUES(?,?,?,?,?,?)',
                  (session_id,worker_id,float(lat),float(lon),accuracy,utcnow()))

def expire_stale_sessions(max_age_seconds=420):
    # A browser tab can disappear without sending a final 'Stop' event.
    # Sessions with no GPS heartbeat for longer than the grace period are ended.
    with conn() as c:
        rows=c.execute("SELECT s.session_id, s.worker_id, COALESCE(MAX(l.recorded_at), s.started_at) AS last_seen FROM field_sessions s LEFT JOIN worker_locations l ON l.session_id=s.session_id WHERE s.status='active' GROUP BY s.session_id").fetchall()
        now=datetime.now(timezone.utc)
        for row in rows:
            try: age=(now-datetime.fromisoformat(row['last_seen'])).total_seconds()
            except Exception: age=0
            if age > max_age_seconds:
                c.execute("UPDATE field_sessions SET status='ended', ended_at=? WHERE session_id=? AND status='active'", (utcnow(), row['session_id']))

def latest_locations(active_only=True):
    expire_stale_sessions()
    with conn() as c:
        q='''SELECT w.worker_id,w.name,w.booth_id,w.region,w.area,s.session_id,s.started_at,
                    l.latitude,l.longitude,l.accuracy,l.recorded_at
             FROM workers w JOIN field_sessions s ON s.worker_id=w.worker_id AND s.status='active'
             LEFT JOIN worker_locations l ON l.location_id=(SELECT l2.location_id FROM worker_locations l2 WHERE l2.session_id=s.session_id ORDER BY l2.location_id DESC LIMIT 1)
             WHERE w.active=1 ORDER BY w.name COLLATE NOCASE'''
        return c.execute(q).fetchall()

def add_report(data):
    with conn() as c:
        c.execute('''INSERT INTO field_reports(worker_id,session_id,booth_id,region,activity_type,observation,attendance_estimate,follow_up,transcript,latitude,longitude,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', tuple(data.get(k) for k in ['worker_id','session_id','booth_id','region','activity_type','observation','attendance_estimate','follow_up','transcript','latitude','longitude']) + (utcnow(),))

def worker_reports(worker_id, limit=25):
    with conn() as c:
        return c.execute('SELECT * FROM field_reports WHERE worker_id=? ORDER BY report_id DESC LIMIT ?', (worker_id,limit)).fetchall()

def recent_reports(limit=100):
    with conn() as c:
        return c.execute('''SELECT r.*,w.name FROM field_reports r JOIN workers w ON w.worker_id=r.worker_id ORDER BY r.report_id DESC LIMIT ?''',(limit,)).fetchall()

def stats():
    expire_stale_sessions()
    with conn() as c:
        total=c.execute('SELECT COUNT(*) n FROM workers WHERE active=1').fetchone()['n']
        active=c.execute("SELECT COUNT(*) n FROM field_sessions s JOIN workers w ON w.worker_id=s.worker_id WHERE s.status='active' AND w.active=1").fetchone()['n']
        reports=c.execute("SELECT COUNT(*) n FROM field_reports WHERE created_at >= date('now')").fetchone()['n']
        booths=c.execute("SELECT COUNT(DISTINCT booth_id) n FROM field_reports WHERE created_at >= date('now')").fetchone()['n']
        return total,active,reports,booths
