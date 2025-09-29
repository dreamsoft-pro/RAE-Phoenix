import pytest
from src.feniks.core import sha1

def test_sha1_consistency():
    """
    Tests that the sha1 function produces a consistent, expected hash for a given string.
    """
    input_string = "hello world"
    expected_hash = "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"

    actual_hash = sha1(input_string)

    assert actual_hash == expected_hash

def test_sha1_empty_string():
    """
    Tests that the sha1 function correctly handles an empty string.
    """
    input_string = ""
    # SHA1 hash for an empty string
    expected_hash = "da39a3ee5e6b4b0d3255bfef95601890afd80709"

    actual_hash = sha1(input_string)

    assert actual_hash == expected_hash

def test_sha1_different_strings():
    """
    Tests that different input strings produce different hashes.
    """
    hash1 = sha1("string one")
    hash2 = sha1("string two")

    assert hash1 != hash2