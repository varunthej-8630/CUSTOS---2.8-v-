# engine/situation_engine.py — CUSTOS Security Situation Engine (Stage 2)
import os
import time
import json
import uuid
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple

from database.models import (
    db, SecuritySituation, SecuritySituationState, RiskTrajectory,
    Incident, PersonProfile, PersonCluster, PersonAppearance
)
from core.logging import app_logger


class SituationEngine:
    """
    CUSTOS Security Situation Engine (Stage 2)
    Aggregates and correlates discrete security events (detections, zone entries,
    restricted breaches, dwell, camera tamper, people tracking) into evolving, logical
    Security Situations with deterministic risk trajectory, state management, and evidence linking.
    """
    def __init__(self, flask_app=None, socket_emitter=None):
        self.flask_app = flask_app
        self.socket_emitter = socket_emitter
        self.lock = threading.Lock()
        self.last_state_key = None
        self.last_briefing = {
            'summary': 'All zones secure. Normal activity monitored.',
            'risk_level': 'Normal',
            'recommended_action': 'Continue automated monitoring.'
        }

    def set_app(self, app):
        self.flask_app = app

    def set_flask_app(self, app):
        self.flask_app = app

    def set_socket_emitter(self, emitter):
        self.socket_emitter = emitter

    # ═══════════════════════════════════════════════════════════════
    # 1. DETERMINISTIC RISK TRAJECTORY CALCULATION
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_trajectory(risk_history: List[Dict[str, Any]]) -> str:
        """
        Deterministic calculation of risk trajectory based strictly on actual observed points.
        >= +15.0: RAPIDLY_INCREASING
        >= +5.0:  INCREASING
        -5.0 < Δ < +5.0: STABLE
        <= -5.0:  DECREASING
        <= -15.0: RAPIDLY_DECREASING
        If fewer than 2 points exist, returns STABLE.
        """
        if not risk_history or len(risk_history) < 2:
            return RiskTrajectory.STABLE

        # Compare latest observed score against the immediately preceding observation
        latest_score = float(risk_history[-1].get('score', 0.0))
        prev_score = float(risk_history[-2].get('score', latest_score))

        delta = latest_score - prev_score
        if delta >= 15.0:
            return RiskTrajectory.RAPIDLY_INCREASING
        elif delta >= 5.0:
            return RiskTrajectory.INCREASING
        elif delta <= -15.0:
            return RiskTrajectory.RAPIDLY_DECREASING
        elif delta <= -5.0:
            return RiskTrajectory.DECREASING
        return RiskTrajectory.STABLE

    # ═══════════════════════════════════════════════════════════════
    # 2. DETERMINISTIC STATE MACHINE
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def determine_state(
        current_state: str = SecuritySituationState.DEVELOPING,
        risk_score: float = 0.0,
        is_tamper: bool = False,
        is_breach: bool = False,
        is_active: bool = True,
        trajectory: str = RiskTrajectory.STABLE,
        **kwargs
    ) -> str:
        """
        Conservative deterministic state machine:
        - CRITICAL: risk >= 80.0 OR confirmed tamper
        - ESCALATING: risk increasing OR new breach while not critical
        - STABLE: active situation with steady risk and no new escalations (e.g. CRITICAL + STABLE)
        - RESOLVING: subject exited / threat decreasing
        - DEVELOPING: early stage situation with risk < 60
        """
        if 'current_risk' in kwargs:
            risk_score = float(kwargs['current_risk'])
        if 'has_exit' in kwargs and kwargs['has_exit']:
            is_active = False
        if 'event_type' in kwargs:
            ev_t = str(kwargs['event_type']).upper()
            if 'TAMPER' in ev_t:
                is_tamper = True
            if 'BREACH' in ev_t or 'HIGH' in ev_t:
                is_breach = True
            if 'EXIT' in ev_t:
                is_active = False

        if is_tamper or risk_score >= 80.0:
            return SecuritySituationState.CRITICAL

        if not is_active or trajectory in (RiskTrajectory.DECREASING, RiskTrajectory.RAPIDLY_DECREASING):
            return SecuritySituationState.RESOLVING

        if is_breach or trajectory in (RiskTrajectory.INCREASING, RiskTrajectory.RAPIDLY_INCREASING):
            return SecuritySituationState.ESCALATING

        if current_state == SecuritySituationState.CRITICAL and risk_score >= 80.0:
            return SecuritySituationState.CRITICAL

        if risk_score >= 40.0:
            return SecuritySituationState.STABLE

        return SecuritySituationState.DEVELOPING

    # ═══════════════════════════════════════════════════════════════
    # 3. DETERMINISTIC TITLE & SUMMARY GENERATORS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def generate_title(
        primary_person_name: Optional[str] = None,
        cluster_code: Optional[str] = None,
        zone_name: Optional[str] = None,
        camera_id: int = 0,
        is_tamper: bool = False,
        is_breach: bool = False
    ) -> str:
        cam_lbl = 'Built-in Camera' if camera_id == 0 else f'Camera {camera_id + 1}'
        if is_tamper:
            return f"Camera optical tamper detected on {cam_lbl}"

        person_label = primary_person_name or (f"Unknown individual ({cluster_code})" if cluster_code else "Unidentified subject")

        if is_breach:
            return f"Restricted zone breach involving {person_label}"
        elif zone_name and ('OBS' in zone_name.upper() or 'WATCH' in zone_name.upper()):
            return f"Monitored perimeter activity involving {person_label}"
        return f"Security activity detected in {zone_name or 'monitored perimeter'}"

    @staticmethod
    def generate_summary(
        title: str,
        risk_score: float,
        trajectory: str,
        state: str,
        zone_name: str,
        camera_id: int,
        events: List[str]
    ) -> str:
        cam_lbl = 'Built-in Camera' if camera_id == 0 else f'Camera {camera_id + 1}'
        ev_summary = ', '.join(events[:3]) if events else 'Security observations recorded'
        traj_label = trajectory.replace('_', ' ').lower()
        return (
            f"{title}. Current threat risk is {int(risk_score)}/100 ({traj_label}, state: {state}) "
            f"in {zone_name} on {cam_lbl}. Active events: {ev_summary}."
        )

    # ═══════════════════════════════════════════════════════════════
    # 4. CONSERVATIVE CORRELATION & INCIDENT PROCESSING
    # ═══════════════════════════════════════════════════════════════

    def process_incident(
        self,
        incident_id: Any,
        incident_pkg: Optional[Dict[str, Any]] = None,
        person_profile_id: Optional[str] = None,
        cluster_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Correlates an incoming Incident into an existing or new SecuritySituation.
        Conservative matching:
        - Priority 1: Exact Person ID match across cameras
        - Priority 2: Exact Cluster ID match across cameras
        - Priority 3: Exact Tamper match on same camera
        - Priority 4: Same Camera + Zone + Subject ID
        - Distinct people are NEVER merged.
        """
        if not self.flask_app or not incident_id:
            return None

        from database.database_manager import db_manager

        with self.flask_app.app_context():
            # Handle direct Incident model instance or ID
            if hasattr(incident_id, 'id'):
                inc_obj = incident_id
                inc_id = inc_obj.id
                if incident_pkg is None:
                    raw_evs = inc_obj.get_parsed_events() if hasattr(inc_obj, 'get_parsed_events') else []
                    incident_pkg = {
                        'camera_id': inc_obj.camera_id,
                        'zone_name': inc_obj.zone_name,
                        'score': inc_obj.score or 0.0,
                        'subject_id': inc_obj.subject_id,
                        'events': raw_evs
                    }
            else:
                inc_id = int(incident_id)
                if incident_pkg is None:
                    inc_obj = Incident.query.get(inc_id)
                    if inc_obj:
                        raw_evs = inc_obj.get_parsed_events() if hasattr(inc_obj, 'get_parsed_events') else []
                        incident_pkg = {
                            'camera_id': inc_obj.camera_id,
                            'zone_name': inc_obj.zone_name,
                            'score': inc_obj.score or 0.0,
                            'subject_id': inc_obj.subject_id,
                            'events': raw_evs
                        }
                    else:
                        incident_pkg = {}

            if person_profile_id:
                incident_pkg['person_profile_id'] = person_profile_id
            if cluster_id:
                incident_pkg['cluster_id'] = cluster_id

            camera_id = int(incident_pkg.get('camera_id', 0))
            zone_name = incident_pkg.get('zone_name', 'Observation Area')
            score = float(incident_pkg.get('score', 0.0))
            subject_id = incident_pkg.get('subject_id', '')
            raw_events = incident_pkg.get('events', [])
            events = [str(e) for e in raw_events] if isinstance(raw_events, list) else [str(raw_events)]
            is_tamper = any('TAMPER' in e.upper() for e in events)
            is_breach = any('HIGH' in e.upper() or 'BREACH' in e.upper() for e in events)
            has_exit = any('EXIT' in e.upper() for e in events)

            # Determine person or cluster entity from subject_id, explicit params, or database
            person_id = incident_pkg.get('person_profile_id')
            cluster_id = incident_pkg.get('cluster_id')
            person_name = None
            cluster_code = None

            if not person_id and not cluster_id and subject_id and subject_id != 'System-Tamper' and subject_id != 'Person-0':
                clean_subj = subject_id.replace('Person-', '')
                # Check if it corresponds to a PersonProfile
                prof = db_manager.get_person_profile_by_id(self.flask_app, clean_subj)
                if prof:
                    person_id = prof['id']
                    person_name = prof['name']
                else:
                    # Check if it is a cluster
                    clust = db_manager.get_person_cluster_by_id(self.flask_app, clean_subj)
                    if clust:
                        cluster_id = clust['id']
                        cluster_code = clust['cluster_code']
                        if clust.get('person_id'):
                            person_id = clust['person_id']

            if person_id and not person_name:
                prof = db_manager.get_person_profile_by_id(self.flask_app, person_id)
                if prof:
                    person_name = prof['name']

            now = datetime.utcnow()
            now_str = now.strftime("%H:%M:%S")

            # Search active situations for conservative correlation
            active_sits = SecuritySituation.query.filter(
                SecuritySituation.state != SecuritySituationState.RESOLVED
            ).all()

            matched_sit = None
            for sit in active_sits:
                # 1. Person ID match (strongest signal)
                if person_id and sit.primary_person_id == person_id:
                    matched_sit = sit
                    break

                # 2. Cluster ID match (unknown person consistency)
                if cluster_id and sit.primary_cluster_id == cluster_id:
                    matched_sit = sit
                    break

                # 3. Same camera tamper event
                if is_tamper and sit.primary_camera_id == camera_id and 'tamper' in sit.title.lower():
                    matched_sit = sit
                    break

                # 4. Same Camera + Zone + Subject within conservative temporal proximity (5 minutes)
                if not person_id and not cluster_id and not sit.primary_person_id and not sit.primary_cluster_id:
                    if sit.primary_camera_id == camera_id and sit.primary_zone_name == zone_name:
                        time_since = (now - sit.last_updated_at).total_seconds() if sit.last_updated_at else 0
                        if time_since <= 300: # 5 minutes quiet window
                            matched_sit = sit
                            break

            # If distinct persons, do NOT merge
            if matched_sit and person_id and matched_sit.primary_person_id and matched_sit.primary_person_id != person_id:
                matched_sit = None

            if matched_sit:
                # Update existing situation
                sit_id = matched_sit.id
                timeline = matched_sit.get_timeline()
                risk_history = matched_sit.get_risk_history()

                # Record new timeline step
                event_desc = events[0] if events else f"Incident #{inc_id} registered"
                timeline.append({
                    'step': len(timeline) + 1,
                    'time': now_str,
                    'event': f"{event_desc} (Threat score: {int(score)}/100)",
                    'severity': 'CRITICAL' if score >= 80.0 or is_tamper else ('HIGH' if score >= 60.0 or is_breach else 'MEDIUM')
                })

                # Record observed risk point
                risk_history.append({
                    'time': now_str,
                    'score': round(score, 1)
                })
                # Bounded risk history (last 50 points)
                risk_history = risk_history[-50:]

                traj = self.calculate_trajectory(risk_history)
                new_state = self.determine_state(
                    current_state=matched_sit.state,
                    risk_score=score,
                    is_tamper=is_tamper,
                    is_breach=is_breach,
                    is_active=not has_exit,
                    trajectory=traj
                )
                title = self.generate_title(person_name, cluster_code, zone_name, camera_id, is_tamper, is_breach)
                summary = self.generate_summary(title, score, traj, new_state, zone_name, camera_id, events)

                inc_ids = [inc.id for inc in matched_sit.incidents]
                if inc_id not in inc_ids:
                    inc_ids.append(inc_id)

                sit_update_pkg = {
                    'id': sit_id,
                    'title': title,
                    'state': new_state,
                    'risk_score': score,
                    'risk_trajectory': traj,
                    'primary_person_id': person_id or matched_sit.primary_person_id,
                    'primary_cluster_id': cluster_id or matched_sit.primary_cluster_id,
                    'primary_camera_id': camera_id,
                    'primary_zone_name': zone_name,
                    'summary': summary,
                    'timeline': timeline,
                    'risk_history': risk_history,
                    'incident_ids': inc_ids
                }
                db_manager.save_or_update_situation(self.flask_app, sit_update_pkg)
                app_logger.info(f"[SITUATION_UPDATED] #{sit_id} State: {new_state} Trajectory: {traj} Risk: {score}")

                # Emit Socket.IO
                sit_dict = db_manager.get_situation_by_id(self.flask_app, sit_id, include_details=True)
                if self.socket_emitter and sit_dict:
                    self.socket_emitter('situation_updated', sit_dict)

                return db.session.get(SecuritySituation, sit_id)

            else:
                # Create brand new situation
                sit_id = f"sit_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
                timeline = [{
                    'step': 1,
                    'time': now_str,
                    'event': f"{events[0] if events else 'Security situation initiated'} (Threat score: {int(score)}/100)",
                    'severity': 'CRITICAL' if score >= 80.0 or is_tamper else ('HIGH' if score >= 60.0 or is_breach else 'MEDIUM')
                }]
                risk_history = [{
                    'time': now_str,
                    'score': round(score, 1)
                }]
                traj = RiskTrajectory.STABLE
                state = self.determine_state(
                    current_state=SecuritySituationState.DEVELOPING,
                    risk_score=score,
                    is_tamper=is_tamper,
                    is_breach=is_breach,
                    is_active=not has_exit,
                    trajectory=traj
                )
                title = self.generate_title(person_name, cluster_code, zone_name, camera_id, is_tamper, is_breach)
                summary = self.generate_summary(title, score, traj, state, zone_name, camera_id, events)

                sit_create_pkg = {
                    'id': sit_id,
                    'title': title,
                    'state': state,
                    'risk_score': score,
                    'risk_trajectory': traj,
                    'started_at': now,
                    'primary_person_id': person_id,
                    'primary_cluster_id': cluster_id,
                    'primary_camera_id': camera_id,
                    'primary_zone_name': zone_name,
                    'summary': summary,
                    'timeline': timeline,
                    'risk_history': risk_history,
                    'incident_ids': [inc_id]
                }
                db_manager.save_or_update_situation(self.flask_app, sit_create_pkg)
                app_logger.info(f"[SITUATION_CREATED] #{sit_id} Title: '{title}' State: {state} Risk: {score}")

                # Emit Socket.IO
                sit_dict = db_manager.get_situation_by_id(self.flask_app, sit_id, include_details=True)
                if self.socket_emitter and sit_dict:
                    self.socket_emitter('situation_created', sit_dict)

                return db.session.get(SecuritySituation, sit_id)

    # ═══════════════════════════════════════════════════════════════
    # 5. SITUATION RESOLUTION & PERIODIC EVALUATION
    # ═══════════════════════════════════════════════════════════════

    def evaluate_active_situations(self, quiet_period_seconds: float = 45.0) -> List[str]:
        """
        Periodically checks active situations. If all linked incidents have closed/exited
        and quiet period has elapsed with zero new activity, transitions situation to RESOLVED.
        """
        if not self.flask_app:
            return []

        from database.database_manager import db_manager
        resolved_ids = []

        with self.flask_app.app_context():
            now = datetime.utcnow()
            active_sits = SecuritySituation.query.filter(
                SecuritySituation.state != SecuritySituationState.RESOLVED
            ).all()

            for sit in active_sits:
                elapsed = (now - sit.last_updated_at).total_seconds() if sit.last_updated_at else 0
                if elapsed >= quiet_period_seconds:
                    # Check if all incidents are closed
                    all_closed = all(inc.status in ('Closed', 'Resolved') for inc in (sit.incidents or []))
                    if all_closed:
                        db_manager.resolve_situation(self.flask_app, sit.id, notes="Automated quiet-period resolution")
                        resolved_ids.append(sit.id)
                        app_logger.info(f"[SITUATION_AUTO_RESOLVED] #{sit.id} after {round(elapsed, 1)}s quiet period")
                        if self.socket_emitter:
                            sit_dict = db_manager.get_situation_by_id(self.flask_app, sit.id, include_details=True)
                            if sit_dict:
                                self.socket_emitter('situation_resolved', sit_dict)

        return resolved_ids

    # ═══════════════════════════════════════════════════════════════
    # 6. LEGACY BRIEFING METHOD (Backward Compatibility)
    # ═══════════════════════════════════════════════════════════════

    def evaluate(self, system_score, event_log, active_persons_count):
        """
        Maintains backward compatibility with pipeline loop while preserving CPU cycles.
        """
        sorted_events = sorted(list(event_log))
        risk_category = 'Normal' if system_score < 40 else ('Suspicious' if system_score < 60 else ('Threat' if system_score < 80 else 'Critical'))
        current_state_key = (risk_category, tuple(sorted_events), active_persons_count)

        if current_state_key == self.last_state_key:
            return self.last_briefing

        self.last_state_key = current_state_key

        if system_score < 40 and not sorted_events:
            self.last_briefing = {
                'summary': f"Area clear. {active_persons_count} subject(s) monitored with normal activity.",
                'risk_level': 'Normal',
                'recommended_action': 'Continue automated monitoring.'
            }
            return self.last_briefing

        has_high_breach = any('HIGH' in e or 'restricted' in e for e in sorted_events)
        has_tamper = any('TAMPER' in e for e in sorted_events)

        if has_tamper:
            summary = "ALERT: Camera feed is obstructed or covered! Immediate security response required."
            action = "Dispatch guard immediately to inspect camera hardware."
        elif has_high_breach:
            summary = f"HIGH RISK BREACH: Subject entered restricted protection zone. Threat score {int(system_score)}/100."
            action = "Dispatch security officer to intercept subject in restricted area."
        else:
            event_desc = ", ".join(sorted_events[:2]) if sorted_events else "Suspicious movement"
            summary = f"SUSPICIOUS ACTIVITY: {event_desc} detected. Threat score {int(system_score)}/100."
            action = "Monitor live video feed and verify authorization."

        self.last_briefing = {
            'summary': summary,
            'risk_level': risk_category,
            'recommended_action': action
        }
        return self.last_briefing


situation_engine = SituationEngine()
