import numpy as np
import pytest

from src import change


sample_0 = np.zeros((2, 2))
sample_1 = np.ones((2, 2))
sample_2 = np.add(sample_1, 1)
samples = np.stack([sample_0, sample_1, sample_2], axis=2)
baseline = np.ones((2, 2))


class TestMeasureChange:

    def test_happy_path(self):
        expected = np.ones((2, 2))
        actual = change._measure_change(samples, baseline)

        assert np.array_equal(actual, expected)

    def test_handles_nan_values_in_samples(self):
        samples_with_nan = np.copy(samples)
        samples_with_nan[0, 0, 2] = np.nan

        expected = np.array([[0., 1.],
                             [1., 1.]])
        actual = change._measure_change(samples_with_nan, baseline)

        assert np.array_equal(actual, expected)

    def test_returns_none_if_too_few_samples_present(self):
        too_few_samples = np.zeros((2, 2, 1))
        actual = change._measure_change(too_few_samples, baseline)

        assert not actual
