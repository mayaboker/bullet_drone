import pytest

from bullet_simulation_protocol.view_bbox import decode_bbox, encode_bbox


def test_bbox_payload_round_trip_with_padding():
    box = {'x': 3, 'y': 4, 'width': 5, 'height': 6}
    payload = encode_bbox(42, box)
    assert decode_bbox(payload.ljust(249, b'\0')) == {'fid': 42, 'bbox': box}
    assert decode_bbox(encode_bbox(43, None)) == {'fid': 43, 'bbox': None}


@pytest.mark.parametrize('payload', [b'', b'\xff\xff{}', b'\x02\x00{}x'])
def test_bbox_payload_rejects_invalid_framing(payload):
    with pytest.raises(ValueError):
        decode_bbox(payload)
