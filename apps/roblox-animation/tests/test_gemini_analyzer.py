"""Tests for Gemini analyzer tools."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSingleImage:
    """Tests for single image analysis."""

    def test_get_frame_files_empty_dir(self, tmp_path: Path) -> None:
        """Test error when no frames found."""
        from gemini_analyzer.frame_sequence import get_frame_files

        with pytest.raises(ValueError, match="No frames found"):
            get_frame_files(tmp_path)

    def test_get_frame_files_returns_sorted(self, tmp_path: Path) -> None:
        """Test frames are returned in sorted order."""
        from gemini_analyzer.frame_sequence import get_frame_files

        # Create test frames out of order
        (tmp_path / "frame_003.png").touch()
        (tmp_path / "frame_001.png").touch()
        (tmp_path / "frame_002.png").touch()

        frames = get_frame_files(tmp_path)

        assert len(frames) == 3
        assert frames[0].name == "frame_001.png"
        assert frames[1].name == "frame_002.png"
        assert frames[2].name == "frame_003.png"


class TestEnvironment:
    """Tests for environment configuration."""

    def test_missing_api_key_raises(self) -> None:
        """Test error when GEMINI_API_KEY not set."""
        from gemini_analyzer.single_image import get_client

        # Ensure API key is not set
        with patch.dict(os.environ, {}, clear=True):
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                get_client()
