import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    decrypt,
    encrypt,
)


def test_encrypt_decrypt_round_trip():
    plaintext = "refresh-token-xyz-123"
    ct = encrypt(plaintext)
    assert ct != plaintext
    assert decrypt(ct) == plaintext


def test_decrypt_garbage_raises_value_error():
    with pytest.raises(ValueError):
        decrypt("not-a-real-fernet-token")


def test_jwt_round_trip():
    token = create_access_token("user-123", email="a@b.com")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "a@b.com"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_token("not.a.jwt")
