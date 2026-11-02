import json
import time

import pytest
import zmq
from tools.zmq_render.flight import FlightLease, FlightReceiver
from bullet_msgs.flight import RC_TOPIC


def packet(**changes):
    value = dict(schema_version=1, physics_id='physics', episode_id='episode', app_id='app', sequence=1,
                 issued_us=1_000_000, valid_until_us=1_100_000, active=False,
                 channels=[1500, 1500, 1000, 1500, 1000, 2000] + [1000] * 12)
    value.update(changes)
    return value


def test_readiness_episode_owner_expiry_and_withdrawal():
    now = [1.]
    lease = FlightLease('physics', clock=lambda: now[0])
    assert not lease.ready()
    assert lease.accept(packet(), 'episode') and lease.ready()
    lease.begin('new_episode')
    assert lease.command() is None
    assert not lease.accept(packet(active=True), 'new_episode')
    value = packet(active=True, episode_id='new_episode')
    assert lease.accept(value, 'new_episode')
    assert lease.command() == value['channels']
    assert not lease.accept(value, 'new_episode')
    assert not lease.accept(dict(value, app_id='restarted', sequence=2), 'new_episode')
    assert lease.accept(dict(value, sequence=2, active=False), 'new_episode')
    assert lease.command() is None and lease.reason == 'app_withdrawn'
    assert lease.accept(dict(value, sequence=3), 'new_episode')
    assert lease.command() is None and lease.reason == 'app_withdrawn'
    lease.end()
    assert lease.accept(packet(), 'episode')
    lease.begin('new_episode')
    assert lease.accept(value, 'new_episode')
    now[0] = 1.1
    assert lease.command() is None and lease.reason == 'rc_expired'


def test_real_tcp_exact_topic_and_malformed_bounds():
    with zmq.Context() as context, context.socket(zmq.PUB) as pub:
        pub.setsockopt(zmq.LINGER, 0)
        port = pub.bind_to_random_port('tcp://127.0.0.1')
        lease = FlightLease('physics', clock=lambda: 1.)
        receiver = FlightReceiver(f'tcp://127.0.0.1:{port}', lease)
        try:
            time.sleep(.1)
            for topic, raw in ((RC_TOPIC + b'/extra', json.dumps(packet()).encode()), (RC_TOPIC, b'{')):
                pub.send_multipart([topic, raw])
            time.sleep(.02)
            receiver.poll('episode')
            assert not lease.ready()
            pub.send_multipart([RC_TOPIC, json.dumps(packet()).encode()])
            deadline = time.monotonic() + 1
            while not lease.ready() and time.monotonic() < deadline:
                receiver.poll('episode')
                time.sleep(.001)
            assert lease.ready()
        finally:
            receiver.close()


@pytest.mark.parametrize('hold_last', [False, True])
def test_v2_mission_signal_obeys_owner_sequence_and_lease_expiry(hold_last):
    from tools.zmq_render.scenario import ScenarioTermination
    clock=[1.]
    lease=FlightLease('physics',clock=lambda:clock[0],hold_last=hold_last)
    assert lease.accept(packet(schema_version=2,mission_started=False),'episode')
    lease.begin('new')
    gate=ScenarioTermination(mission_gated=True)
    idle=packet(schema_version=2,mission_started=False,active=True,episode_id='new')
    idle['channels'][4]=2000
    assert lease.accept(idle,'new') and lease.command() is not None
    gate.command(lease.latest,10)
    assert gate.mission_start_step is None
    start=dict(idle,mission_started=True,sequence=2)
    assert not lease.accept(dict(start,app_id='foreign'),'new')
    gate.command(lease.latest,11)
    assert gate.mission_start_step is None
    assert lease.accept(start,'new')
    gate.command(lease.latest,12)
    assert gate.mission_start_step==12
    clock[0]=1.2
    assert (lease.command() is not None) == hold_last
    assert lease.accept(dict(start,sequence=3,active=False,issued_us=1_200_000,valid_until_us=1_300_000),'new')
    assert lease.command() is None  # withdrawal also stops the Betaflight hold-last lease
    gate.stop_mission()
    lease.end()
    assert gate.mission_start_step is None and not gate.history
