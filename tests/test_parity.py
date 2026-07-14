from bitlab.parity import (
    append_parity,
    check_parity,
    check_parity_array,
    compute_message_parity,
    flip_random_bit,
    generate_parity_array,
    get_parity_bit,
)


def test_even_parity_odd_bit_count():
    assert get_parity_bit(0b0000001, "even", 8) == 1


def test_even_parity_even_bit_count():
    assert get_parity_bit(0b0000011, "even", 8) == 0


def test_odd_parity_odd_bit_count():
    assert get_parity_bit(0b0000001, "odd", 8) == 0


def test_odd_parity_even_bit_count():
    assert get_parity_bit(0b0000011, "odd", 8) == 1


def test_bit_width_masks_higher_bits():
    # 0b1_0001 with width=4 only looks at the lowest 4 bits (0001) -> odd
    assert get_parity_bit(0b10001, "even", 4) == 1


def test_append_and_check_round_trip_all_bytes():
    for v in range(256):
        with_parity = append_parity(v, "even", 8)
        assert check_parity(with_parity, "even", 8) is True


def test_check_parity_detects_flipped_bit():
    with_parity = append_parity(0b1011, "even", 4)
    corrupted = with_parity ^ 0b00010  # flip one data bit
    assert check_parity(corrupted, "even", 4) is False


def test_odd_parity_round_trip():
    with_parity = append_parity(0b1010, "odd", 4)
    assert check_parity(with_parity, "odd", 4) is True


def test_generate_parity_array():
    bits = generate_parity_array([0b0001, 0b0011, 0b0111], "even", 4)
    assert bits == [1, 0, 1]


def test_check_parity_array():
    values = [append_parity(v, "even", 4) for v in [0b0001, 0b0011, 0b0111]]
    assert check_parity_array(values, "even", 4) == [True, True, True]


def test_message_parity_deterministic():
    assert compute_message_parity("hello world") == compute_message_parity("hello world")


def test_message_parity_flips_with_type():
    even = compute_message_parity("x", "even")
    odd = compute_message_parity("x", "odd")
    assert even != odd


def test_flip_random_bit_always_changes_value():
    original = 0b0101
    for _ in range(20):
        flipped = flip_random_bit(original, 4)
        assert flipped != original
        assert 0 <= flipped < 16
