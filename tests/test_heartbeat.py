from rd_theory_v8 import GhostVaultV8_Production
import time
def test_heartbeat_monotonic():
    v = GhostVaultV8_Production()
    v.start_heartbeat(interval=0.05)
    time.sleep(0.25)
    v.stop_heartbeat()
    times = v._heartbeat_times
    assert len(times) >= 3
    assert times == sorted(times) # monotonic increasing
