import pytest

from bitlab.parity import decode_hamming, encode_hamming


def test_round_trip_no_error():
    for data in range(16):
        codeword = encode_hamming(data)
        result = decode_hamming(codeword)
        assert result.data == data
        assert result.corrected is False
        assert result.error_position == 0


def test_corrects_any_single_bit_error():
    for data in range(16):
        codeword = encode_hamming(data)
        for pos in range(1, 8):
            shift = 7 - pos
            corrupted = codeword ^ (1 << shift)
            result = decode_hamming(corrupted)
            assert result.data == data
            assert result.corrected is True
            assert result.error_position == pos


def test_encode_out_of_range_raises():
    with pytest.raises(ValueError):
        encode_hamming(16)
    with pytest.raises(ValueError):
        encode_hamming(-1)


def test_decode_out_of_range_raises():
    with pytest.raises(ValueError):
        decode_hamming(128)
    with pytest.raises(ValueError):
        decode_hamming(-1)
