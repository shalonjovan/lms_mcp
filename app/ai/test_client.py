import pytest


def test_generate_with_images():
    result = generate_with_images()
    assert result is not None


def test_generate_with_images_edge_case():
    with pytest.raises((ValueError, TypeError)):
        generate_with_images(None)
