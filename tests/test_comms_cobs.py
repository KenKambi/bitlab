import random

import pytest

from bitlab.comms import cobs_decode, cobs_encode, cobs_frame, cobs_unframe

KNOWN_VECTORS = [
    (bytes([0x00]), bytes([0x01, 0x01])),
    (bytes([0x00, 0x00]), bytes([0x01, 0x01, 0x01])),
    (bytes([0x00, 0x11, 0x00]), bytes([0x01, 0x02, 0x11, 0x01])),
    (bytes([0x11, 0x22, 0x00, 0x33]), bytes([0x03, 0x11, 0x22, 0x02, 0x33])),
    (bytes([0x11, 0x22, 0x33, 0x44]), bytes([0x05, 0x11, 0x22, 0x33, 0x44])),
    (bytes([0x11, 0x00, 0x00, 0x00]), bytes([0x02, 0x11, 0x01, 0x01, 0x01])),
    (bytes(), bytes([0x01])),
]


@pytest.mark.parametrize("raw,expected", KNOWN_VECTORS, ids=lambda x: x.hex() or "empty")
def test_matches_known_reference_vectors(raw, expected):
    assert cobs_encode(raw) == expected


@pytest.mark.parametrize("raw,expected", KNOWN_VECTORS, ids=lambda x: x.hex() or "empty")
def test_decode_reverses_known_vectors(raw, expected):
    assert cobs_decode(expected) == raw


def test_round_trip_random_data():
    random.seed(99)
    for _ in range(1000):
        length = random.randint(0, 800)
        data = bytes(random.randrange(256) for _ in range(length))
        encoded = cobs_encode(data)
        assert 0 not in encoded
        assert cobs_decode(encoded) == data


def test_encoded_output_never_contains_zero_byte():
    random.seed(1)
    for _ in range(200):
        length = random.randint(0, 300)
        data = bytes(random.randrange(256) for _ in range(length))
        assert 0 not in cobs_encode(data)


def test_254_byte_block_boundary():
    # Exactly 254 non-zero bytes triggers the max-block-length split.
    data = bytes(range(1, 255)) + bytes([7, 8, 9])
    encoded = cobs_encode(data)
    assert 0 not in encoded
    assert cobs_decode(encoded) == data


def test_all_zeros():
    data = bytes([0] * 10)
    encoded = cobs_encode(data)
    assert cobs_decode(encoded) == data


def test_no_zeros_at_all():
    data = bytes(range(1, 200))
    encoded = cobs_encode(data)
    assert cobs_decode(encoded) == data


def test_decode_rejects_embedded_zero():
    with pytest.raises(ValueError, match="zero byte"):
        cobs_decode(bytes([0x02, 0x00]))


def test_decode_rejects_truncated_block():
    with pytest.raises(ValueError, match="truncated"):
        cobs_decode(bytes([0x05, 0x11, 0x22]))


def test_frame_appends_delimiter():
    framed = cobs_frame(b"hi")
    assert framed.endswith(b"\x00")
    assert framed.count(b"\x00") == 1


def test_unframe_strips_delimiter_and_decodes():
    msg = b"hello\x00world"
    assert cobs_unframe(cobs_frame(msg)) == msg


def test_unframe_tolerates_missing_trailing_delimiter():
    msg = b"no delimiter here"
    encoded = cobs_encode(msg)
    assert cobs_unframe(encoded) == msg
