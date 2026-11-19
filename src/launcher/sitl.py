"""Own one externally installed Betaflight SITL process."""

import os
from pathlib import Path
import socket
import subprocess
import tempfile

from loguru import logger
from bullet_drone.betaflight.firmware import validate_gps_firmware

HOST = '127.0.0.1'
MSP_PORT = 5761
UDP_PORTS = (9002, 9003, 9004)
STARTUP_TIMEOUT_S = 10.0
STOP_TIMEOUT_S = 3.0
LOG_TAIL_BYTES = 2000


class SitlSession:
    def __init__(self, binary, *, profile_path, extra_ports=()):
        self.binary = Path(binary).resolve()
        self.profile_path = Path(profile_path).resolve()
        self.extra_ports = extra_ports
        if not self.binary.is_file() or not os.access(self.binary, os.X_OK):
            raise ValueError(f'SITL binary missing or not executable: {self.binary}')
        if not self.profile_path.is_file():
            raise ValueError(f'SITL profile missing: {self.profile_path}')
        validate_gps_firmware(self.binary, self.profile_path, gps_enabled=False)
        self.process = self.work = self.log = None

    def __enter__(self):
        for kind, port in ((socket.SOCK_STREAM, MSP_PORT),
                           *((socket.SOCK_STREAM, port) for port in self.extra_ports),
                           *((socket.SOCK_DGRAM, port) for port in UDP_PORTS)):
            with socket.socket(socket.AF_INET, kind) as probe:
                if kind == socket.SOCK_STREAM:
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    probe.bind((HOST, port))
                except OSError as error:
                    raise RuntimeError(f'SITL port {port} is occupied. Stop the other simulation first.') from error
        try:
            self.work = tempfile.TemporaryDirectory(prefix='bullet-launcher-')
            self.log = tempfile.TemporaryFile(mode='w+')
            logger.info('Starting SITL: binary={} profile={} workdir={}',
                        self.binary, self.profile_path, self.work.name)
            subprocess.run([str(self.binary), '--config', str(self.profile_path)], cwd=self.work.name,
                           stdout=self.log, stderr=self.log, timeout=STARTUP_TIMEOUT_S, check=True)
            self.process = subprocess.Popen([str(self.binary), '--ip', HOST], cwd=self.work.name,
                                            stdout=self.log, stderr=self.log)
            logger.info('SITL process started: pid={} MSP={} (external controller owns connection)',
                        self.process.pid, MSP_PORT)
            return self
        except BaseException:
            logger.error('SITL startup failed. Recent firmware output:\n{}', self.recent_output())
            self.close()
            raise

    def recent_output(self):
        if self.log is None or self.log.closed:
            return '(no firmware output)'
        size = os.fstat(self.log.fileno()).st_size
        return os.pread(self.log.fileno(), LOG_TAIL_BYTES, max(0, size - LOG_TAIL_BYTES)).decode(
            errors='replace').strip() or '(no firmware output)'

    def check_running(self):
        if self.process.poll() is not None:
            raise RuntimeError('SITL exited: ' + self.recent_output())

    def close(self):
        try:
            if self.process is not None and self.process.poll() is None:
                logger.info('Stopping owned SITL process pid={}', self.process.pid)
                self.process.terminate()
                try:
                    self.process.wait(timeout=STOP_TIMEOUT_S)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=STOP_TIMEOUT_S)
        finally:
            if self.log is not None:
                self.log.close()
            if self.work is not None:
                self.work.cleanup()

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is not None:
                logger.error('SITL output before teardown:\n{}', self.recent_output())
        finally:
            self.close()
