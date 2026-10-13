"""Visible two-publisher integration check: uv run renderers/godot/smoke_test.py."""
import shutil
import subprocess
import time
from pathlib import Path

from bullet_drone.rendering.config import CameraSettings, RenderSettings, UdpSettings
from bullet_drone.rendering.models import RenderSnapshot
from bullet_drone.rendering.udp import UdpRenderer


def main():
    executable = shutil.which('godot')
    if executable is None:
        raise SystemExit('Godot 4.3+ must be installed to run the visible smoke test')
    project = Path(__file__).resolve().parent
    process = subprocess.Popen([executable, '--path', str(project), '--script', 'test_viewer.gd', '--', '--port=19870'])
    try:
        # Repeat initial states while the viewer initializes; no production ACKs.
        settings = [RenderSettings(drone_id='alpha', udp=UdpSettings(port=19870)),
                    RenderSettings(drone_id='bravo', udp=UdpSettings(port=19870), camera=CameraSettings(width_px=320, height_px=240, fov_y_deg=60))]
        publishers = [UdpRenderer(profile) for profile in settings]
        try:
            for publisher, profile, position in zip(publishers, settings, [(0.,0.,3.), (1.5,.1,2.8)]):
                publisher.reset(RenderSnapshot(profile.drone_id, 'smoke', 0, 0, position, (0,0,0,1), profile.sources))
            for step in range(1, 11):
                time.sleep(0.1)
                for publisher, profile, position in zip(publishers, settings, [(0.,0.,3.), (1.5,.1,2.8)]):
                    publisher.render(RenderSnapshot(profile.drone_id, 'smoke', step, step / 10, position, (0,0,0,1), profile.sources))
        finally:
            for publisher in publishers:
                publisher.close()
        return process.wait(timeout=55)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


if __name__ == '__main__':
    raise SystemExit(main())
