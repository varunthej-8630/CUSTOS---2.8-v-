import pytest
import datetime
from database.models import (
    db, Incident, Evidence, PersonProfile, 
    SecuritySituation, SecuritySituationState, RiskTrajectory,
    PersonClassification
)
from database.database_manager import db_manager
from engine.situation_engine import SituationEngine


@pytest.fixture
def situation_engine(app):
    engine = SituationEngine()
    engine.set_flask_app(app)
    return engine


def test_trajectory_calculation(situation_engine):
    """Verify deterministic trajectory calculation thresholds."""
    # delta >= 15 -> RAPIDLY_INCREASING
    h_rap_inc = [{'score': 40, 'time': '2026-09-14T05:00:00'}, {'score': 60, 'time': '2026-09-14T05:00:10'}]
    assert situation_engine.calculate_trajectory(h_rap_inc) == RiskTrajectory.RAPIDLY_INCREASING

    # delta >= 5 -> INCREASING
    h_inc = [{'score': 40, 'time': '2026-09-14T05:00:00'}, {'score': 48, 'time': '2026-09-14T05:00:10'}]
    assert situation_engine.calculate_trajectory(h_inc) == RiskTrajectory.INCREASING

    # -5 < delta < 5 -> STABLE
    h_stable = [{'score': 40, 'time': '2026-09-14T05:00:00'}, {'score': 42, 'time': '2026-09-14T05:00:10'}]
    assert situation_engine.calculate_trajectory(h_stable) == RiskTrajectory.STABLE

    # delta <= -5 -> DECREASING
    h_dec = [{'score': 50, 'time': '2026-09-14T05:00:00'}, {'score': 42, 'time': '2026-09-14T05:00:10'}]
    assert situation_engine.calculate_trajectory(h_dec) == RiskTrajectory.DECREASING

    # delta <= -15 -> RAPIDLY_DECREASING
    h_rap_dec = [{'score': 70, 'time': '2026-09-14T05:00:00'}, {'score': 50, 'time': '2026-09-14T05:00:10'}]
    assert situation_engine.calculate_trajectory(h_rap_dec) == RiskTrajectory.RAPIDLY_DECREASING

    # Insufficient history returns STABLE
    assert situation_engine.calculate_trajectory([]) == RiskTrajectory.STABLE
    assert situation_engine.calculate_trajectory([{'score': 50, 'time': '2026-09-14T05:00:00'}]) == RiskTrajectory.STABLE


def test_state_and_trajectory_independence(app, situation_engine):
    """Verify that state and trajectory are independent dimensions (e.g. CRITICAL + STABLE is valid)."""
    with app.app_context():
        # High risk (85) with stable trajectory
        state = situation_engine.determine_state(
            current_state=SecuritySituationState.DEVELOPING,
            current_risk=85,
            trajectory=RiskTrajectory.STABLE,
            event_type='ZONE_BREACH',
            has_exit=False
        )
        assert state == SecuritySituationState.CRITICAL

        # High risk remains CRITICAL even when trajectory is DECREASING
        state_crit = situation_engine.determine_state(
            current_state=SecuritySituationState.CRITICAL,
            current_risk=82,
            trajectory=RiskTrajectory.DECREASING,
            event_type='DWELL_ALERT',
            has_exit=False
        )
        assert state_crit == SecuritySituationState.CRITICAL

        # Escalating state when risk increases
        state_esc = situation_engine.determine_state(
            current_state=SecuritySituationState.DEVELOPING,
            current_risk=65,
            trajectory=RiskTrajectory.INCREASING,
            event_type='RESTRICTED_ZONE_BREACH',
            has_exit=False
        )
        assert state_esc == SecuritySituationState.ESCALATING


def test_correlation_by_person_across_cameras(app, situation_engine):
    """Verify that events involving the same person across cameras correlate to the same situation."""
    with app.app_context():
        person = PersonProfile(id='person_varun', name='Varun Thej', classification=PersonClassification.KNOWN)
        db.session.add(person)
        db.session.commit()

        # Event 1 on Cam 0
        inc1 = Incident(
            camera_id=0,
            zone_name='Observation Area',
            score=35.0,
            subject_id='person_varun',
            events='["OBSERVATION_ZONE_ENTRY"]'
        )
        db.session.add(inc1)
        db.session.commit()

        sit1 = situation_engine.process_incident(inc1, person_profile_id='person_varun')
        assert sit1 is not None
        sit1_data = db_manager.get_situation_by_id(app, sit1.id, include_details=True)
        assert sit1_data['primary_person_id'] == 'person_varun'
        assert len(sit1_data['incidents']) == 1

        # Event 2 on Cam 1 (same person)
        inc2 = Incident(
            camera_id=1,
            zone_name='Restricted Corridor',
            score=75.0,
            subject_id='person_varun',
            events='["RESTRICTED_ZONE_BREACH"]'
        )
        db.session.add(inc2)
        db.session.commit()

        sit2 = situation_engine.process_incident(inc2, person_profile_id='person_varun')
        assert sit2 is not None
        assert sit2.id == sit1.id  # Same situation correlated
        sit2_data = db_manager.get_situation_by_id(app, sit2.id, include_details=True)
        assert len(sit2_data['incidents']) == 2
        assert sit2_data['risk_score'] == 75.0


def test_separation_of_different_people(app, situation_engine):
    """Verify that different persons NEVER merge into the same situation."""
    with app.app_context():
        person_a = PersonProfile(id='person_alice', name='Alice', classification=PersonClassification.KNOWN)
        person_b = PersonProfile(id='person_bob', name='Bob', classification=PersonClassification.KNOWN)
        db.session.add_all([person_a, person_b])
        db.session.commit()

        inc_a = Incident(
            camera_id=0,
            zone_name='Entrance',
            score=40.0,
            subject_id='person_alice',
            events='["ZONE_ENTRY"]'
        )
        inc_b = Incident(
            camera_id=0,
            zone_name='Entrance',
            score=45.0,
            subject_id='person_bob',
            events='["ZONE_ENTRY"]'
        )
        db.session.add_all([inc_a, inc_b])
        db.session.commit()

        sit_a = situation_engine.process_incident(inc_a, person_profile_id='person_alice')
        sit_b = situation_engine.process_incident(inc_b, person_profile_id='person_bob')

        assert sit_a is not None
        assert sit_b is not None
        assert sit_a.id != sit_b.id  # Must be distinct situations
        assert sit_a.primary_person_id == 'person_alice'
        assert sit_b.primary_person_id == 'person_bob'


def test_tamper_situation_without_person(app, situation_engine):
    """Verify that a camera tamper incident creates a CRITICAL situation without requiring a person."""
    with app.app_context():
        inc = Incident(
            camera_id=0,
            zone_name='Perimeter',
            score=95.0,
            events='["CAMERA_TAMPER"]',
            clip_path='/storage/evidence/tamper_pre_event.mp4',
            snapshot_path='/storage/evidence/tamper_snap.jpg',
            snapshot_status='AVAILABLE',
            video_status='AVAILABLE'
        )
        db.session.add(inc)
        db.session.commit()

        # Link pre-event canonical evidence
        ev = Evidence(
            incident_id=inc.id,
            type='clip',
            path='/storage/evidence/tamper_pre_event.mp4'
        )
        db.session.add(ev)
        db.session.commit()

        sit = situation_engine.process_incident(inc)
        assert sit is not None
        assert sit.state == SecuritySituationState.CRITICAL
        assert sit.primary_person_id is None
        assert sit.primary_cluster_id is None
        assert sit.primary_camera_id == 0
        assert 'tampering' in sit.title.lower() or 'tamper' in sit.title.lower()

        # Verify evidence is accessible via canonical incident
        sit_dict = db_manager.get_situation_by_id(app, sit.id, include_details=True)
        assert len(sit_dict['incidents']) == 1
        assert len(sit_dict['incidents'][0]['evidence']) == 1
        assert sit_dict['incidents'][0]['evidence'][0]['path'] == '/storage/evidence/tamper_pre_event.mp4'


def test_acceptance_full_evolving_situation(app, situation_engine):
    """
    Acceptance Test 1:
    Unknown person detected -> Observation zone -> Approaches restricted area ->
    Restricted-zone breach -> Dwell -> High risk -> Person exits.
    
    Must produce ONE evolving situation with correct lifecycle, trajectory, real timeline, and canonical evidence.
    """
    with app.app_context():
        cluster_id = 'cluster_test_99'

        # 1. Observation zone entry
        inc1 = Incident(
            camera_id=0,
            zone_name='Observation Area',
            score=30.0,
            events='["OBSERVATION_ZONE_ENTRY"]'
        )
        db.session.add(inc1)
        db.session.commit()
        sit = situation_engine.process_incident(inc1, cluster_id=cluster_id)
        assert sit is not None
        sit_d1 = db_manager.get_situation_by_id(app, sit.id, include_details=True)
        assert sit_d1['state'] == SecuritySituationState.DEVELOPING
        assert sit_d1['risk_score'] == 30.0
        assert sit_d1['cluster_id'] == cluster_id

        # 2. Restricted zone breach (Risk increases)
        inc2 = Incident(
            camera_id=0,
            zone_name='Restricted Corridor',
            score=70.0,
            events='["RESTRICTED_ZONE_BREACH"]'
        )
        db.session.add(inc2)
        db.session.commit()
        sit = situation_engine.process_incident(inc2, cluster_id=cluster_id)
        sit_d2 = db_manager.get_situation_by_id(app, sit.id, include_details=True)
        assert sit_d2['state'] in [SecuritySituationState.ESCALATING, SecuritySituationState.CRITICAL]
        assert sit_d2['risk_score'] == 70.0
        assert sit_d2['risk_trajectory'] in [RiskTrajectory.INCREASING, RiskTrajectory.RAPIDLY_INCREASING]

        # 3. Dwell & Critical Risk
        inc3 = Incident(
            camera_id=0,
            zone_name='Restricted Corridor',
            score=90.0,
            events='["DWELL_TIME_EXCEEDED"]'
        )
        db.session.add(inc3)
        db.session.commit()
        sit = situation_engine.process_incident(inc3, cluster_id=cluster_id)
        sit_d3 = db_manager.get_situation_by_id(app, sit.id, include_details=True)
        assert sit_d3['state'] == SecuritySituationState.CRITICAL
        assert sit_d3['risk_score'] == 90.0

        # 4. Person Exits / Activity decreases
        inc4 = Incident(
            camera_id=0,
            zone_name='Restricted Corridor',
            score=40.0,
            events='["PERSON_EXITED"]'
        )
        db.session.add(inc4)
        db.session.commit()
        sit = situation_engine.process_incident(inc4, cluster_id=cluster_id)
        sit_d4 = db_manager.get_situation_by_id(app, sit.id, include_details=True)
        
        # State transitions to RESOLVING as subject exits and risk drops
        assert sit_d4['state'] == SecuritySituationState.RESOLVING
        assert sit_d4['risk_trajectory'] in [RiskTrajectory.DECREASING, RiskTrajectory.RAPIDLY_DECREASING]
        assert len(sit_d4['incidents']) == 4
        assert len(sit_d4['timeline']) >= 4


def test_rest_api_situations(admin_client, app, situation_engine):
    """Verify REST API endpoints for Security Situations."""
    with app.app_context():
        inc = Incident(
            camera_id=0,
            zone_name='Main Zone',
            score=85.0,
            events='["RESTRICTED_ZONE_BREACH"]'
        )
        db.session.add(inc)
        db.session.commit()

        sit = situation_engine.process_incident(inc)
        sit_id = sit.id

    # 1. GET /api/situations/active
    res_active = admin_client.get('/api/situations/active')
    assert res_active.status_code == 200
    json_active = res_active.get_json()
    assert json_active['success'] is True
    assert len(json_active['data']['situations']) >= 1
    assert json_active['data']['situations'][0]['id'] == sit_id

    # 2. GET /api/situations/<id>
    res_detail = admin_client.get(f'/api/situations/{sit_id}')
    assert res_detail.status_code == 200
    json_detail = res_detail.get_json()
    assert json_detail['success'] is True
    assert json_detail['data']['id'] == sit_id
    assert json_detail['data']['risk_score'] == 85.0

    # 3. GET /api/situations/stats
    res_stats = admin_client.get('/api/situations/stats')
    assert res_stats.status_code == 200
    json_stats = res_stats.get_json()
    assert json_stats['success'] is True
    assert json_stats['data']['active_situations'] >= 1

    # 4. POST /api/situations/<id>/resolve
    res_resolve = admin_client.post(f'/api/situations/{sit_id}/resolve')
    assert res_resolve.status_code == 200
    json_resolve = res_resolve.get_json()
    assert json_resolve['success'] is True
    assert json_resolve['data']['state'] == 'RESOLVED'

    # Verify no longer active
    res_active2 = admin_client.get('/api/situations/active')
    json_active2 = res_active2.get_json()
    assert not any(s['id'] == sit_id for s in json_active2['data']['situations'])
