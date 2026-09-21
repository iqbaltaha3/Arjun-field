import os, tempfile
os.environ['ARJUN_FIELD_DB']=os.path.join(tempfile.gettempdir(),'arjun_field_test.sqlite')
import config
config.DB_PATH=os.environ['ARJUN_FIELD_DB']
import db

def setup_function():
    try: os.remove(config.DB_PATH)
    except FileNotFoundError: pass
    db.init_db()

def test_worker_session_location_report():
    db.add_worker('W001','Ravi','147','Shivpur')
    assert db.get_worker('W001')['name']=='Ravi'
    sid=db.start_session('W001')
    assert db.active_session('W001')['session_id']==sid
    db.add_location(sid,'W001',25.3,82.9,10)
    rows=db.latest_locations(); assert len(rows)==1 and abs(rows[0]['latitude']-25.3)<1e-9
    db.add_report({'worker_id':'W001','session_id':sid,'booth_id':'147','region':'Shivpur','activity_type':'meeting','observation':'Meeting held','attendance_estimate':20,'follow_up':'Tomorrow','transcript':'raw','latitude':25.3,'longitude':82.9})
    assert len(db.worker_reports('W001'))==1
    db.end_session('W001')
    assert db.active_session('W001') is None

def test_deactivate_ends_session():
    db.add_worker('W002','Amit','152','Ramnagar')
    db.start_session('W002'); db.deactivate_worker('W002')
    assert db.get_worker('W002')['active']==0
    assert db.active_session('W002') is None
