import pytest


def test_init_db():
    result = init_db()
    assert result is not None


def test_init_db_edge_case():
    with pytest.raises((ValueError, TypeError)):
        init_db(None)
