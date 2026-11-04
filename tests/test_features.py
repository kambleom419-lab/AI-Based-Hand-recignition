"""Unit tests for the landmark feature extractor."""

import numpy as np

from gesture_control import features


def sample_landmarks():
    rng = np.random.default_rng(0)
    return rng.random((21, 2))


def test_feature_length():
    vector = features.pre_process_landmark(sample_landmarks())
    assert vector.shape == (features.FEATURE_DIM,)
    assert vector.shape == (42,)


def test_translation_invariance():
    base = sample_landmarks()
    shifted = base + np.array([0.3, -0.2])
    np.testing.assert_allclose(
        features.pre_process_landmark(base),
        features.pre_process_landmark(shifted),
        atol=1e-9,
    )


def test_scale_invariance():
    base = sample_landmarks()
    scaled = base * 2.5
    np.testing.assert_allclose(
        features.pre_process_landmark(base),
        features.pre_process_landmark(scaled),
        atol=1e-9,
    )


def test_zero_safe():
    same_point = np.zeros((21, 2))
    vector = features.pre_process_landmark(same_point)
    assert np.all(np.isfinite(vector))
    assert np.all(vector == 0.0)
