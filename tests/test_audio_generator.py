import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPlayFrenchAudio:
    """Test cases for play_french_audio() function."""

    @patch('utils.audio_generator.gTTS')
    @patch('utils.audio_generator.st')
    def test_plays_audio_for_valid_text(self, mock_st, mock_gtts):
        """Test that valid French text generates and plays audio."""
        from utils.audio_generator import play_french_audio

        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance

        def write_fake_audio(fp):
            fp.write(b"fake_audio_data")

        mock_tts_instance.write_to_fp.side_effect = write_fake_audio

        result = play_french_audio("Bonjour le monde")

        assert result is True
        mock_gtts.assert_called_once_with(text="Bonjour le monde", lang='fr', slow=False)
        mock_st.audio.assert_called_once()

    @patch('utils.audio_generator.st')
    def test_returns_false_for_empty_text(self, mock_st):
        """Test that empty text returns False."""
        from utils.audio_generator import play_french_audio

        assert play_french_audio("") is False
        assert play_french_audio("   ") is False
        assert play_french_audio(None) is False
        mock_st.audio.assert_not_called()

    @patch('utils.audio_generator.gTTS')
    @patch('utils.audio_generator.st')
    def test_returns_false_on_tts_error(self, mock_st, mock_gtts):
        """Test that TTS errors return False and show error."""
        from utils.audio_generator import play_french_audio

        mock_gtts.side_effect = Exception("Network error")

        result = play_french_audio("Bonjour")

        assert result is False
        mock_st.caption.assert_called_once()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
