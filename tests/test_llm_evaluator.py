import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_evaluator import extract_json


class TestExtractJson:
    """Test cases for extract_json() function."""

    def test_plain_json(self):
        """Test extraction of plain JSON without any wrapper."""
        text = '{"overall_score": 85, "feedback": "Good job!"}'
        result = extract_json(text)
        assert result == '{"overall_score": 85, "feedback": "Good job!"}'

    def test_json_with_markdown_json_block(self):
        """Test extraction from ```json code block."""
        text = '''Here is the evaluation:
```json
{"overall_score": 75, "feedback": "Nice try!"}
```
Hope this helps!'''
        result = extract_json(text)
        assert '"overall_score": 75' in result
        assert '"feedback": "Nice try!"' in result

    def test_json_with_plain_markdown_block(self):
        """Test extraction from plain ``` code block."""
        text = '''```
{"overall_score": 90, "meaning_preserved": true}
```'''
        result = extract_json(text)
        assert '"overall_score": 90' in result

    def test_json_with_leading_text(self):
        """Test extraction when there's text before the JSON."""
        text = 'The evaluation result is: {"overall_score": 80}'
        result = extract_json(text)
        assert result == '{"overall_score": 80}'

    def test_json_with_trailing_text(self):
        """Test extraction when there's text after the JSON."""
        text = '{"overall_score": 70} Let me know if you have questions.'
        result = extract_json(text)
        assert result == '{"overall_score": 70}'

    def test_complex_nested_json(self):
        """Test extraction of complex nested JSON structure."""
        text = '''```json
{
  "overall_score": 65,
  "critical_errors": [
    {"type": "WRONG_WORD", "original": "à", "student_wrote": "dans"}
  ],
  "minor_errors": [],
  "feedback": "Good effort!"
}
```'''
        result = extract_json(text)
        assert '"overall_score": 65' in result
        assert '"critical_errors"' in result
        assert '"WRONG_WORD"' in result

    def test_defense_attachment_case(self):
        """
        Regression test for the failing case reported by user.

        English: "We're at the defense attachment, it's where we start and end our service."
        User French: "on est dans attachment de defense, c'est ou on commence et finit notre service"
        """
        # Simulate LLM response with markdown wrapper
        llm_response = '''```json
{
  "overall_score": 72,
  "meaning_preserved": true,
  "critical_errors": [
    {
      "type": "WRONG_WORD",
      "original": "à l'attachement",
      "student_wrote": "dans attachment",
      "explanation": "Use 'à' for location, not 'dans'. Also 'attachement' needs French spelling."
    }
  ],
  "minor_errors": [
    {
      "type": "ACCENT",
      "original": "défense",
      "student_wrote": "defense",
      "explanation": "Missing accent on 'défense'"
    },
    {
      "type": "ACCENT",
      "original": "où",
      "student_wrote": "ou",
      "explanation": "'où' (where) needs accent to distinguish from 'ou' (or)"
    }
  ],
  "feedback": "Good attempt! Pay attention to prepositions and French accents.",
  "corrected_version": "On est à l'attachement de la défense, c'est où on commence et finit notre service."
}
```'''
        result = extract_json(llm_response)

        # Should be valid JSON after extraction
        import json
        parsed = json.loads(result)

        assert parsed["overall_score"] == 72
        assert parsed["meaning_preserved"] is True
        assert len(parsed["critical_errors"]) == 1
        assert len(parsed["minor_errors"]) == 2
        assert "feedback" in parsed
        assert "corrected_version" in parsed


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
