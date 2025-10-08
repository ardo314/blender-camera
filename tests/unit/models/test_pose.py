import pytest

from blender_camera.models.pose import Pose, validate_pose


class TestValidatePose:
    """Test cases for the validate_pose function."""

    def test_validate_pose_with_valid_pose_should_return_true(self):
        """Test that a valid pose with 6 floats returns True."""
        # Arrange
        valid_pose: Pose = [1.0, 2.0, 3.0, 0.5, 1.5, 2.5]

        # Act
        result = validate_pose(valid_pose)

        # Assert
        assert result is True

    def test_validate_pose_with_zero_values_should_return_true(self):
        """Test that a pose with all zero values is valid."""
        # Arrange
        zero_pose: Pose = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Act
        result = validate_pose(zero_pose)

        # Assert
        assert result is True

    def test_validate_pose_with_negative_values_should_return_true(self):
        """Test that a pose with negative values is valid."""
        # Arrange
        negative_pose: Pose = [-1.0, -2.0, -3.0, -0.5, -1.5, -2.5]

        # Act
        result = validate_pose(negative_pose)

        # Assert
        assert result is True

    def test_validate_pose_with_mixed_values_should_return_true(self):
        """Test that a pose with mixed positive/negative values is valid."""
        # Arrange
        mixed_pose: Pose = [1.0, -2.0, 3.0, -0.5, 1.5, -2.5]

        # Act
        result = validate_pose(mixed_pose)

        # Assert
        assert result is True

    def test_validate_pose_with_too_few_elements_should_return_false(self):
        """Test that a pose with fewer than 6 elements is invalid."""
        # Arrange
        short_pose = [1.0, 2.0, 3.0, 0.5, 1.5]  # Only 5 elements

        # Act
        result = validate_pose(short_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_too_many_elements_should_return_false(self):
        """Test that a pose with more than 6 elements is invalid."""
        # Arrange
        long_pose = [1.0, 2.0, 3.0, 0.5, 1.5, 2.5, 3.5]  # 7 elements

        # Act
        result = validate_pose(long_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_empty_list_should_return_false(self):
        """Test that an empty list is invalid."""
        # Arrange
        empty_pose = []

        # Act
        result = validate_pose(empty_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_integer_values_should_return_false(self):
        """Test that a pose with integer values is invalid."""
        # Arrange
        integer_pose = [1, 2, 3, 0, 1, 2]  # integers instead of floats

        # Act
        result = validate_pose(integer_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_mixed_types_should_return_false(self):
        """Test that a pose with mixed int/float types is invalid."""
        # Arrange
        mixed_type_pose = [1.0, 2, 3.0, 0.5, 1, 2.5]  # mix of int and float

        # Act
        result = validate_pose(mixed_type_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_string_values_should_return_false(self):
        """Test that a pose with string values is invalid."""
        # Arrange
        string_pose = ["1.0", "2.0", "3.0", "0.5", "1.5", "2.5"]

        # Act
        result = validate_pose(string_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_none_values_should_return_false(self):
        """Test that a pose with None values is invalid."""
        # Arrange
        none_pose = [1.0, 2.0, None, 0.5, 1.5, 2.5]

        # Act
        result = validate_pose(none_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_non_list_input_should_return_false(self):
        """Test that non-list inputs are invalid."""
        # Arrange
        tuple_pose = (1.0, 2.0, 3.0, 0.5, 1.5, 2.5)

        # Act
        result = validate_pose(tuple_pose)

        # Assert
        assert result is False

    def test_validate_pose_with_none_input_should_return_false(self):
        """Test that None input is invalid."""
        # Arrange
        none_input = None

        # Act
        result = validate_pose(none_input)

        # Assert
        assert result is False

    def test_validate_pose_with_dict_input_should_return_false(self):
        """Test that dictionary input is invalid."""
        # Arrange
        dict_input = {"x": 1.0, "y": 2.0, "z": 3.0, "rx": 0.5, "ry": 1.5, "rz": 2.5}

        # Act
        result = validate_pose(dict_input)

        # Assert
        assert result is False

    def test_validate_pose_with_infinity_values_should_return_true(self):
        """Test that poses with infinity values are considered valid floats."""
        # Arrange
        infinity_pose = [float("inf"), 2.0, 3.0, 0.5, 1.5, float("-inf")]

        # Act
        result = validate_pose(infinity_pose)

        # Assert
        assert result is True

    def test_validate_pose_with_nan_values_should_return_true(self):
        """Test that poses with NaN values are considered valid floats."""
        # Arrange
        nan_pose = [float("nan"), 2.0, 3.0, 0.5, 1.5, 2.5]

        # Act
        result = validate_pose(nan_pose)

        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "pose,expected",
        [
            ([1.0, 2.0, 3.0, 0.5, 1.5, 2.5], True),
            ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], True),
            ([-1.0, -2.0, -3.0, -0.5, -1.5, -2.5], True),
            ([1.0, 2.0, 3.0, 0.5, 1.5], False),  # too few
            ([1.0, 2.0, 3.0, 0.5, 1.5, 2.5, 3.5], False),  # too many
            ([], False),  # empty
            ([1, 2, 3, 0, 1, 2], False),  # integers
            (["1.0", "2.0", "3.0", "0.5", "1.5", "2.5"], False),  # strings
            ((1.0, 2.0, 3.0, 0.5, 1.5, 2.5), False),  # tuple
            (None, False),  # None
        ],
    )
    def test_validate_pose_parametrized_cases(self, pose, expected):
        """Parametrized test cases for various pose validation scenarios."""
        # Arrange & Act
        result = validate_pose(pose)

        # Assert
        assert result is expected
