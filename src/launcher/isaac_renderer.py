"""Own one Isaac Sim renderer process and its local pose/image transport."""
from contextlib import ExitStack
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from bullet_simulation_protocol.transport import ImageSubscription
from bullet_simulation_protocol import load_transport
from bullet_image_transport.shm import FrameReader, SLOTS, slot_name, topic_prefix

from launcher.publisher import RenderPublisher


IMAGE_TOPIC = 'camera/front/image'
STARTUP_TIMEOUT_S = 360.0
SHUTDOWN_TIMEOUT_S = 5.0
POLL_TIMEOUT_MS = 50
SHM_DIRECTORY = Path('/dev/shm')


def _isaac_python(isaac_dir):
    """Return the Isaac Sim python.sh interpreter path."""
    candidate = isaac_dir / 'python.sh'
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate
    raise FileNotFoundError(f'Isaac Sim python.sh not found at {candidate}')


class IsaacRenderer:
    def __init__(self, config, *, isaac_dir=None, render_script=None,
                 profile_name='isaac_render', backend='internal',
                 headless=False, world=None, target=None):
        if isaac_dir is None:
            isaac_dir = Path(os.environ.get('ISAAC_SIM_DIR') or Path.home() / 'isaacsim6.2').expanduser()
        self.isaac_dir = Path(isaac_dir)
        self.python_sh = _isaac_python(self.isaac_dir)
        if render_script is None:
            render_script = Path(__file__).resolve().parents[2] / '..' / 'bullet_render' / 'isaac' / 'main.py'
        self.render_script = Path(render_script).resolve()
        if not self.render_script.is_file():
            raise FileNotFoundError(f'Isaac render script not found: {self.render_script}')
        self.publisher = RenderPublisher(config, profile_name=profile_name, backend=backend)
        self.transport = load_transport(self.publisher.transport_path)
        self.headless = headless
        self.world = world
        self.target = target
        self.process = self.log = self.images = self.reader = None
        self.resources = ExitStack()

    def __enter__(self):
        try:
            self.log = self.resources.enter_context(tempfile.TemporaryFile(mode='w+'))
            self._start_zmq()
            self._start_isaac()
            return self
        except BaseException:
            self.resources.close()
            raise

    def _start_zmq(self):
        self.images = ImageSubscription(self.transport['image_endpoint'], topic_prefix(IMAGE_TOPIC))
        self.resources.callback(self.images.close)
        self.reader = FrameReader(IMAGE_TOPIC)
        self.resources.callback(self.reader.close)
        self.resources.callback(self.publisher.close)
        self.publisher.start()

    def _start_isaac(self):
        cmd = [str(self.python_sh), str(self.render_script),
               '--transport-config', str(self.publisher.transport_path.resolve())]
        if self.headless:
            cmd.append('--headless')
        if self.world:
            cmd.extend(['--world', str(self.world)])
        if self.target:
            cmd.extend(['--target'] + [str(c) for c in self.target])
        self.process = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT)
        self.resources.callback(self._stop_process)

    def ensure_running(self):
        if self.publisher.error:
            raise RuntimeError(self.publisher.error)
        if self.process is None or self.process.poll() is not None:
            detail = ''
            if self.log is not None:
                self.log.seek(0)
                detail = self.log.read()[-4000:]
            raise RuntimeError(f'Isaac renderer exited before mission completion.\n{detail}')

    def set_running(self, running):
        self.publisher.set_running(running)

    def consume(self, observation):
        self.ensure_running()
        self.publisher.consume(observation)

    def wait_ready(self, observation, *, timeout_s=STARTUP_TIMEOUT_S):
        self.set_running(False)
        self.consume(observation)
        deadline = time.monotonic() + timeout_s
        last_consume = time.monotonic()
        while time.monotonic() < deadline:
            self.ensure_running()
            now = time.monotonic()
            if now - last_consume >= 1.0:
                self.publisher.consume(observation)
                last_consume = now
            if self.images.poll(POLL_TIMEOUT_MS):
                raw = self.images.recv()
                frame = self.reader.read(raw)
                if frame is not None:
                    metadata, pixels = frame
                    camera_info = self.publisher.config['camera']
                    if (metadata['width'] == camera_info['width_px']
                            and metadata['height'] == camera_info['height_px']):
                        return frame
        detail = ''
        if self.log is not None:
            self.log.seek(0)
            detail = self.log.read()[-4000:]
        raise TimeoutError(f'No rendered camera image within {timeout_s:g} seconds\n{detail}')

    def _stop_process(self):
        if self.process is not None and self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=SHUTDOWN_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=SHUTDOWN_TIMEOUT_S)

    def __exit__(self, *exc):
        return self.resources.__exit__(*exc)
