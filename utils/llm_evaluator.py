import json
from typing import Dict, Any
from groq import Groq


def extract_json(text: str) -> str:
    """Extract JSON from text that may contain markdown code blocks or extra text."""
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]

    # Try to find JSON object boundaries
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end > start:
        text = text[start:end]

    return text.strip()

EVALUATION_PROMPT = """You are a French language teacher evaluating a student's translation.

ORIGINAL FRENCH SENTENCE:
{french_sentence}

REFERENCE ENGLISH TRANSLATION:
{reference_english}

STUDENT'S FRENCH TRANSLATION:
{user_french}

Evaluate the student's French translation against the original. Respond in JSON format:

{{
  "overall_score": <0-100>,
  "meaning_preserved": <true/false>,
  "critical_errors": [
    {{
      "type": "WRONG_WORD|NEGATION|SUBJECT_OBJECT|VERB_TENSE|GENDER",
      "original": "<correct text>",
      "student_wrote": "<what student wrote>",
      "explanation": "<brief explanation>"
    }}
  ],
  "minor_errors": [
    {{
      "type": "SPELLING|ARTICLE|WORD_ORDER|ACCENT|CONJUGATION",
      "original": "<correct text>",
      "student_wrote": "<what student wrote>",
      "explanation": "<brief explanation>"
    }}
  ],
  "feedback": "<2-3 sentence constructive feedback>",
  "corrected_version": "<student's text with corrections applied>"
}}

Scoring guidelines:
- 90-100: Near perfect, minor stylistic differences only
- 70-89: Good understanding, minor grammatical errors
- 50-69: Core meaning preserved but significant errors
- 30-49: Partial understanding, critical errors present
- 0-29: Major meaning errors or incomprehensible

Be encouraging but accurate. Focus on learning."""


def evaluate_translation(
    french_sentence: str,
    reference_english: str,
    user_french: str,
    groq_client: Groq
) -> Dict[str, Any]:
    """
    Use LLM to evaluate user's French translation.

    Args:
        french_sentence: The original French sentence
        reference_english: The English translation shown to user
        user_french: The user's French translation attempt
        groq_client: Groq client instance

    Returns:
        Dictionary with evaluation results including score and errors
    """
    prompt = EVALUATION_PROMPT.format(
        french_sentence=french_sentence,
        reference_english=reference_english,
        user_french=user_french
    )

    raw_content = None
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a French language evaluation assistant. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
        )

        raw_content = response.choices[0].message.content
        cleaned_json = extract_json(raw_content)
        result = json.loads(cleaned_json)
        return result

    except json.JSONDecodeError as e:
        # Log the raw response for debugging
        print(f"JSON parse error: {e}")
        if raw_content:
            print(f"Raw response: {raw_content[:500]}")
        # Fallback if JSON parsing fails
        return {
            "overall_score": 50,
            "meaning_preserved": True,
            "critical_errors": [],
            "minor_errors": [],
            "feedback": "Unable to parse evaluation. Please try again.",
            "corrected_version": user_french
        }
    except Exception as e:
        return {
            "overall_score": 0,
            "meaning_preserved": False,
            "critical_errors": [],
            "minor_errors": [],
            "feedback": f"Evaluation error: {str(e)}",
            "corrected_version": user_french
        }


def calculate_score(critical_errors: int, minor_errors: int) -> int:
    """
    Calculate score based on error counts.

    Base: 100 points
    - Critical errors: -25 each (max -75)
    - Minor errors: -5 each (max -25)
    - Perfect bonus: +5 if no errors
    """
    score = 100

    critical_penalty = min(critical_errors * 25, 75)
    minor_penalty = min(minor_errors * 5, 25)

    score -= critical_penalty
    score -= minor_penalty

    if critical_errors == 0 and minor_errors == 0:
        score += 5

    return max(0, min(105, score))
