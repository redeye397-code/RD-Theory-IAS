from rd_vault import GhostVaultProduction
import time
def test_heartbeat_monotonic():
    v = GhostVaultProduction()
    v.start_heartbeat(interval=0.05)
    time.sleep(0.25)
    v.stop_heartbeat()
    times = v._heartbeat_times
    assert len(times) >= 3
    assert times == sorted(times) # monotonic increasing
