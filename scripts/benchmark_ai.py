# scripts/benchmark_ai.py — Benchmarks Perception and Tracking latency
import time
import numpy as np
from engine.vision.perception_engine import PerceptionEngine
from engine.tracking.tracking_engine import MultiObjectTracker
from engine.behavior.behavior_analyzer import BehaviorAnalyzer
from engine.risk.risk_engine import RiskEngine

def run_benchmarks():
    print("=" * 60)
    print(" CUSTOS 2.6 AI VISION & BEHAVIOR BENCHMARK")
    print("=" * 60)

    perception = PerceptionEngine()
    tracker = MultiObjectTracker()
    behavior = BehaviorAnalyzer()
    risk = RiskEngine()

    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Warmup
    for _ in range(5):
        perception.detect(dummy_frame)

    # 1. Perception Benchmark
    n_iters = 30
    latencies = []
    for _ in range(n_iters):
        t0 = time.perf_counter()
        dets = perception.detect(dummy_frame)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_det_ms = sum(latencies) / len(latencies)
    min_det_ms = min(latencies)
    max_det_ms = max(latencies)

    # 2. Tracking Benchmark
    track_latencies = []
    mock_dets = [{'bbox': [100, 100, 200, 300], 'confidence': 0.9, 'class_id': 0, 'class_name': 'person'}]
    for _ in range(n_iters):
        t0 = time.perf_counter()
        tracks = tracker.update(mock_dets, dummy_frame)
        track_latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_trk_ms = sum(track_latencies) / len(track_latencies)
    min_trk_ms = min(track_latencies)
    max_trk_ms = max(track_latencies)

    # 3. Behavior Analyzer Benchmark
    mock_tracks = [{'track_id': 1, 'bbox': [100, 100, 200, 300], 'confidence': 0.9, 'class_name': 'person'}]
    beh_latencies = []
    for _ in range(n_iters):
        t0 = time.perf_counter()
        behs = behavior.process(mock_tracks)
        beh_latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_beh_ms = sum(beh_latencies) / len(beh_latencies)

    print(f"Perception Latency (YOLOv8n @ 480p): Avg: {avg_det_ms:.2f} ms | Min: {min_det_ms:.2f} ms | Max: {max_det_ms:.2f} ms")
    print(f"Tracker Latency (MultiObjectTracker):  Avg: {avg_trk_ms:.2f} ms | Min: {min_trk_ms:.2f} ms | Max: {max_trk_ms:.2f} ms")
    print(f"Behavior Latency (Analyzer Matrix):    Avg: {avg_beh_ms:.2f} ms")
    print("=" * 60)
    print(" Benchmark execution completed successfully.")
    print("=" * 60)

if __name__ == '__main__':
    run_benchmarks()
