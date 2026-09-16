# realtime/socket_events.py — Socket event names & registry
class SocketEvents:
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    NEW_ALERT = 'new_alert'
    ALERT_STREAM = 'alert_stream'
    SYSTEM_METRICS = 'system_metrics'
    INCIDENT_UPDATE = 'incident_update'
    SITUATION_UPDATE = 'situation_update'
    CAMERA_STATUS = 'camera_status'
    HEARTBEAT = 'heartbeat'
