"""
Unit & Integration Tests for CUSTOS Database-Backed Analytics & Evidence Pipeline
"""
import pytest
import json
from datetime import datetime, timedelta
from database.models import db, Incident, PersonProfile, PersonAppearance

def test_analytics_stats_empty_db(admin_client, app):
    res = admin_client.get('/api/analytics/stats')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['success'] is True
    data = json_data['data']
    assert data['total_incidents'] == 0
    assert data['high_risk_incidents'] == 0
    assert data['peak_risk'] == 0
    assert data['average_risk'] == 0
    assert len(data['hourly_incidents']) == 24
    assert len(data['risk_history_24h']) == 0

def test_analytics_stats_populated(admin_client, app):
    now = datetime.utcnow()
    
    with app.app_context():
        inc1 = Incident(
            camera_id=0,
            zone_name='HIGH',
            score=85,
            events=json.dumps(['RESTRICTED_BREACH']),
            status='Active',
            timestamp=now - timedelta(hours=2),
            clip_path='evidence/inc_001.mp4'
        )
        inc2 = Incident(
            camera_id=0,
            zone_name='OBSERVATION',
            score=45,
            events=json.dumps(['LOITERING']),
            status='Resolved',
            timestamp=now - timedelta(hours=5)
        )
        db.session.add_all([inc1, inc2])
        db.session.commit()
        
    res = admin_client.get('/api/analytics/stats')
    assert res.status_code == 200
    data = res.get_json()['data']
    
    assert data['total_incidents'] == 2
    assert data['high_risk_incidents'] == 1  # 85 >= 60
    assert data['peak_risk'] == 85
    assert data['average_risk'] == 65.0  # (85 + 45)/2 = 65.0
    assert len(data['hourly_incidents']) == 24
    assert len(data['risk_history_24h']) == 2

def test_person_appearance_to_incident_evidence_linkage(admin_client, app):
    import os
    now = datetime.utcnow()
    
    os.makedirs('data/evidence', exist_ok=True)
    os.makedirs('data/snapshots', exist_ok=True)
    with open('data/evidence/test_clip.mp4', 'wb') as f:
        f.write(b'\x00\x00\x00\x20ftypisom')
    with open('data/snapshots/test.jpg', 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        
    try:
        with app.app_context():
            inc = Incident(
                camera_id=1,
                zone_name='HIGH',
                score=90,
                events=json.dumps(['RESTRICTED_BREACH']),
                status='Active',
                timestamp=now,
                clip_path='data/evidence/test_clip.mp4'
            )
            db.session.add(inc)
            db.session.commit()
            
            person = PersonProfile(
                id='PER-TEST-01',
                name='Test Subject',
                classification='SUSPICIOUS',
                status='ACTIVE'
            )
            app_rec = PersonAppearance(
                person_id='PER-TEST-01',
                camera_id=1,
                zone_name='HIGH',
                snapshot_path='data/snapshots/test.jpg',
                incident_id=inc.id,
                timestamp=now,
                recognition_score=0.92
            )
            db.session.add_all([person, app_rec])
            db.session.commit()
            
            # Test appearance to_dict payload
            app_dict = app_rec.to_dict()
            assert app_dict['has_clip'] is True
            assert app_dict['clip_url'] == f'/api/evidence/{inc.id}/media/clip'
            assert app_dict['has_snapshot'] is True
            assert app_dict['incident_type'] == 'RESTRICTED_BREACH'
            assert app_dict['incident_score'] == 90
            
            # Test person to_dict risk context and incidents
            person_dict = person.to_dict(include_appearances=True)
            assert 'risk_context' in person_dict
            assert person_dict['risk_context']['highest_risk'] == 90
            assert person_dict['risk_context']['incident_count'] == 1
            assert len(person_dict['incidents']) == 1
            assert person_dict['incidents'][0]['id'] == inc.id
    finally:
        for p in ['data/evidence/test_clip.mp4', 'data/snapshots/test.jpg']:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
