import random

import pytest

from bitlab.ecc import ReedSolomonError, rs_decode, rs_encode

reedsolo = pytest.importorskip(
    "reedsolo", reason="reedsolo not installed; skipping independent cross-validation"
)


def test_matches_the_classic_bernstein_tutorial_example():
    # From "Reed-Solomon codes for coders": message [64, 2], nsym=10.
    encoded = rs_encode(bytes([64, 2]), nsym=10)
    assert encoded == bytes([64, 2, 0x20, 0xA2, 0xA7, 0xE8, 0xB6, 0x87, 0xCE, 0xAF, 0x63, 0xBC])


def test_encode_matches_reedsolo_across_random_inputs():
    random.seed(1)
    for _ in range(300):
        nsym = random.choice([4, 8, 10, 16, 32])
        msg_len = random.randint(1, 255 - nsym)
        data = bytes(random.randrange(256) for _ in range(msg_len))

        mine = rs_encode(data, nsym)
        ref = bytes(reedsolo.RSCodec(nsym).encode(bytearray(data)))
        assert mine == ref


def test_decode_recovers_original_with_no_errors():
    data = b"no corruption here"
    encoded = rs_encode(data, nsym=10)
    assert rs_decode(encoded, nsym=10) == data


def test_decode_corrects_errors_up_to_capacity():
    random.seed(42)
    for _ in range(500):
        nsym = random.choice([4, 6, 8, 10, 16, 20])
        msg_len = random.randint(1, 255 - nsym)
        data = bytes(random.randrange(256) for _ in range(msg_len))
        encoded = bytearray(rs_encode(data, nsym))

        num_errors = random.randint(0, nsym // 2)
        for p in random.sample(range(len(encoded)), num_errors):
            orig = encoded[p]
            new = orig
            while new == orig:
                new = random.randrange(256)
            encoded[p] = new

        assert rs_decode(bytes(encoded), nsym) == data


def test_decode_agrees_with_reedsolo_across_random_error_injection():
    random.seed(777)
    for _ in range(300):
        nsym = random.choice([4, 6, 8, 10, 16, 20, 32])
        msg_len = random.randint(1, 255 - nsym)
        data = bytes(random.randrange(256) for _ in range(msg_len))
        encoded = bytearray(rs_encode(data, nsym))

        num_errors = random.randint(0, nsym // 2)
        for p in random.sample(range(len(encoded)), num_errors):
            orig = encoded[p]
            new = orig
            while new == orig:
                new = random.randrange(256)
            encoded[p] = new

        mine_ok = True
        try:
            mine_decoded = rs_decode(bytes(encoded), nsym)
        except ReedSolomonError:
            mine_ok = False

        ref_ok = True
        try:
            ref_result = reedsolo.RSCodec(nsym).decode(bytes(encoded))
            ref_decoded = bytes(ref_result[0])
        except reedsolo.ReedSolomonError:
            ref_ok = False

        assert mine_ok == ref_ok
        if mine_ok:
            assert mine_decoded == data
            assert ref_decoded == data


def test_beyond_capacity_errors_are_detected_in_the_vast_majority_of_cases():
    """Not a mathematical guarantee for every corruption pattern (true of
    any RS code), but should fail loudly rather than silently return wrong
    data in the overwhelming majority of over-capacity cases."""
    random.seed(123)
    silent_wrong = 0
    trials = 300
    nsym = 10
    for _ in range(trials):
        msg_len = random.randint(5, 100)
        data = bytes(random.randrange(256) for _ in range(msg_len))
        encoded = bytearray(rs_encode(data, nsym))

        num_errors = random.randint(nsym // 2 + 1, nsym)
        for p in random.sample(range(len(encoded)), num_errors):
            orig = encoded[p]
            new = orig
            while new == orig:
                new = random.randrange(256)
            encoded[p] = new

        try:
            decoded = rs_decode(bytes(encoded), nsym)
            if decoded != data:
                silent_wrong += 1
        except ReedSolomonError:
            pass  # correctly detected

    assert silent_wrong / trials < 0.02  # essentially never silently wrong


def test_encode_rejects_empty_data():
    with pytest.raises(ValueError):
        rs_encode(b"", nsym=4)


def test_encode_rejects_oversized_block():
    with pytest.raises(ValueError):
        rs_encode(bytes(250), nsym=10)  # 250 + 10 > 255


def test_encode_rejects_non_positive_nsym():
    with pytest.raises(ValueError):
        rs_encode(b"data", nsym=0)


def test_decode_rejects_data_not_longer_than_nsym():
    with pytest.raises(ValueError):
        rs_decode(bytes(5), nsym=10)
