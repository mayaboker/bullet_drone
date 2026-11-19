"""Version-one Bullet View bbox payload for MAVLink V2_EXTENSION."""

import json
import struct


MESSAGE_TYPE = 32768
MAX_PAYLOAD_BYTES = 249
MAX_FID = 2**53 - 1
MAX_COORDINATE = 2**32 - 1
LENGTH = struct.Struct('<H')
BOX_FIELDS = {'x', 'y', 'width', 'height'}


def validate_bbox(value):
    if not isinstance(value, dict) or set(value) != {'fid', 'bbox'}:
        raise ValueError('expected fid and bbox')
    fid, box = value['fid'], value['bbox']
    if type(fid) is not int or not 0 <= fid <= MAX_FID:
        raise ValueError('invalid image fid')
    if box is not None:
        if not isinstance(box, dict) or set(box) != BOX_FIELDS:
            raise ValueError('invalid bbox fields')
        for name, coordinate in box.items():
            if type(coordinate) is not int or not 0 <= coordinate <= MAX_COORDINATE:
                raise ValueError(f'invalid bbox {name}')
        if box['width'] == 0 or box['height'] == 0:
            raise ValueError('empty bbox')
    return value


def encode_bbox(fid, box):
    value = validate_bbox({'fid': fid, 'bbox': box})
    body = json.dumps(value, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(body) > MAX_PAYLOAD_BYTES - LENGTH.size:
        raise ValueError('bbox payload too large')
    return LENGTH.pack(len(body)) + body


def decode_bbox(payload):
    payload = bytes(payload)
    if len(payload) < LENGTH.size or len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError('invalid bbox payload size')
    length = LENGTH.unpack_from(payload)[0]
    if not 0 < length <= len(payload) - LENGTH.size:
        raise ValueError('invalid bbox payload length')
    if any(payload[LENGTH.size + length:]):
        raise ValueError('nonzero bbox padding')
    try:
        value = json.loads(payload[LENGTH.size:LENGTH.size + length].decode('utf-8'),
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError) as error:
        raise ValueError('invalid bbox JSON') from error
    return validate_bbox(value)
