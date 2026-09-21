from security import hash_password, verify_password

def test_password():
    h=hash_password('secret')
    assert verify_password('secret',h)
    assert not verify_password('wrong',h)
