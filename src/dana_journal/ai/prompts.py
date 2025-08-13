"""
Prompt Engineering System

Handles prompt templates and response parsing for journal reflection generation.
Optimized for Qwen2.5-3B-Instruct model with structured JSON output.
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ReflectionPromptConfig:
    """Configuration for reflection prompt generation."""

    max_content_length: int = 2000  # Max characters from journal entry
    min_content_length: int = 50  # Min characters to generate reflection
    max_insights: int = 3  # Maximum number of insights
    max_questions: int = 3  # Maximum number of questions
    max_themes: int = 3  # Maximum number of themes


class JournalPromptEngine:
    """Generates prompts for journal reflection and parses AI responses."""

    def __init__(self, config: Optional[ReflectionPromptConfig] = None):
        self.config = config or ReflectionPromptConfig()

    def create_reflection_prompt(
        self, content: str, entry_date: Optional[str] = None
    ) -> str:
        """
        Create a prompt for generating journal reflection.

        Args:
            content: The journal entry content
            entry_date: Optional date of the entry for context

        Returns:
            str: Formatted prompt for AI model
        """
        # Preprocess content
        processed_content = self._preprocess_content(content)

        # Check if content is sufficient for meaningful reflection
        if len(processed_content.strip()) < self.config.min_content_length:
            return None

        date_context = ""
        if entry_date:
            date_context = f"Entry Date: {entry_date}\n\n"

        prompt = f"""You are thoughtful and empathetic journaling psychologist Melanie Klein. Your role is to help people gain deeper insights into their thoughts and experiences through reflective analysis.

Analyze the following journal entry and provide meaningful insights, thoughtful questions, and identify key themes. Focus on emotional intelligence, self-awareness, and personal growth opportunities.

{date_context}Journal Entry:
{processed_content}

Please respond in this exact JSON format:
{{
    "insights": [
        "First key insight about the writer's thoughts, feelings, or situation",
        "Second insight that helps them understand the external influence. Patterns, connections, people, and relationships. "
    ],
    "questions": [
        "What deeper question helps them explore their feelings?",
        "What question encourages them to consider different perspectives?",
        "What question guides them toward actionable next steps?"
    ],
    "themes": [
        "primary_theme",
        "secondary_theme",
        "tertiary_theme"
    ]
}}

Guidelines:
- Address the writer directly as "you"
- Be more personal and suggestive rather than factual.
- Insights should be compassionate, specific, and actionable
- Questions should be open-ended and encourage deeper reflection
- Themes should be 1-2 words describing key topics (e.g., "relationships", "career", "self_care", "growth", "creativity")
- Focus on what the writer can learn or do, not just observations
- Be encouraging and supportive in tone
- Avoid being preachy or overly prescriptive

JSON Response:"""

        return prompt

    def create_theme_analysis_prompt(self, entries: List[str], date_range: str) -> str:
        """
        Create a prompt for analyzing themes across multiple entries.

        Args:
            entries: List of journal entry contents
            date_range: String describing the date range

        Returns:
            str: Formatted prompt for theme analysis
        """
        combined_content = "\n\n---\n\n".join(entries[:5])  # Limit to 5 entries
        processed_content = self._preprocess_content(combined_content, max_length=3000)

        prompt = f"""You are analyzing journal entries from {date_range} to identify recurring themes and patterns. Look for emotional patterns, life themes, and areas of growth or concern.

Journal Entries:
{processed_content}

Please respond in this exact JSON format:
{{
    "recurring_themes": [
        "theme1",
        "theme2",
        "theme3"
    ],
    "emotional_patterns": [
        "pattern1",
        "pattern2"
    ],
    "growth_areas": [
        "area1",
        "area2"
    ],
    "insights": [
        "Overall insight about patterns across these entries",
        "Observation about emotional or life themes"
    ]
}}

JSON Response:"""

        return prompt

    def _preprocess_content(
        self, content: str, max_length: Optional[int] = None
    ) -> str:
        """
        Preprocess journal content for AI analysis.

        Args:
            content: Raw journal content
            max_length: Maximum length to truncate to

        Returns:
            str: Processed content
        """
        if not content or not content.strip():
            return ""

        # Remove excessive whitespace and normalize
        content = re.sub(r"\s+", " ", content.strip())

        # Use config max length if not specified
        if max_length is None:
            max_length = self.config.max_content_length

        # Truncate if too long
        if len(content) > max_length:
            # Try to truncate at sentence boundary
            truncated = content[:max_length]
            last_period = truncated.rfind(".")
            if last_period > max_length * 0.8:  # If we can keep 80% of content
                content = truncated[: last_period + 1]
            else:
                content = truncated + "..."

        return content

    def parse_reflection_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response into structured reflection data.

        Args:
            response: Raw AI response text

        Returns:
            Dict: Parsed reflection data or error information
        """
        if not response or not response.strip():
            return self._create_error_response("Empty response from AI")

        try:
            # Extract JSON from response
            # Clean response by removing empty JSON objects and extra whitespace
            cleaned_response = response.strip()
            # Remove empty JSON objects at the start or anywhere in the response
            cleaned_response = re.sub(
                r"\{\s*\}\s*\n?", "", cleaned_response, flags=re.MULTILINE
            )
            # Also remove the specific "JSON Response:" prefix if it exists
            cleaned_response = re.sub(
                r"JSON Response:\s*\{\s*\}\s*", "", cleaned_response, flags=re.MULTILINE
            )

            # Try multiple JSON extraction patterns
            json_patterns = [
                r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})",  # Nested JSON pattern
                r"\{.*\}",  # Original pattern
                r"```json\s*(\{.*?\})\s*```",  # JSON in code blocks
                r"```\s*(\{.*?\})\s*```",  # JSON in any code blocks
                r"(\{[\s\S]*?\})",  # More permissive JSON
            ]

            json_match = None
            for pattern in json_patterns:
                json_match = re.search(pattern, cleaned_response, re.DOTALL)
                if json_match:
                    break

            if not json_match:
                return self._create_fallback_response(response)

            # Extract JSON string (use group(1) if capture group exists, otherwise group())
            json_str = (
                json_match.group(1) if json_match.groups() else json_match.group()
            )

            # Try to parse the JSON
            data = json.loads(json_str)

            # Validate required fields
            if not all(key in data for key in ["insights", "questions", "themes"]):
                return self._create_fallback_response(response)

            # Clean and validate data
            cleaned_data = self._clean_reflection_data(data)

            return {"success": True, "data": cleaned_data, "raw_response": response}

        except json.JSONDecodeError as e:
            # Try to extract partial information
            return self._create_fallback_response(
                response, f"JSON parsing error: {str(e)}"
            )

        except Exception as e:
            return self._create_error_response(f"Parsing error: {str(e)}")

    def _clean_reflection_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate reflection data."""
        cleaned = {"insights": [], "questions": [], "themes": []}

        # Clean insights
        if "insights" in data and isinstance(data["insights"], list):
            for insight in data["insights"][: self.config.max_insights]:
                if isinstance(insight, str) and len(insight.strip()) > 10:
                    cleaned["insights"].append(insight.strip())

        # Clean questions
        if "questions" in data and isinstance(data["questions"], list):
            for question in data["questions"][: self.config.max_questions]:
                if isinstance(question, str) and len(question.strip()) > 5:
                    # Ensure question ends with question mark
                    q = question.strip()
                    if not q.endswith("?"):
                        q += "?"
                    cleaned["questions"].append(q)

        # Clean themes
        if "themes" in data and isinstance(data["themes"], list):
            for theme in data["themes"][: self.config.max_themes]:
                if isinstance(theme, str) and len(theme.strip()) > 0:
                    # Normalize theme (lowercase, underscores)
                    theme_clean = re.sub(r"[^a-zA-Z0-9\s]", "", theme.lower())
                    theme_clean = re.sub(r"\s+", "_", theme_clean.strip())
                    if theme_clean:
                        cleaned["themes"].append(theme_clean)

        return cleaned

    def _create_fallback_response(
        self, response: str, error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create fallback response by extracting what we can from unstructured text."""
        # Try to extract insights and questions using patterns
        insights = []
        questions = []

        # Look for bullet points or numbered lists
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line looks like an insight
            if any(
                line.startswith(prefix) for prefix in ["•", "-", "*", "1.", "2.", "3."]
            ):
                cleaned_line = re.sub(r"^[•\-\*\d\.]\s*", "", line)
                if len(cleaned_line) > 10 and not cleaned_line.endswith("?"):
                    insights.append(cleaned_line)
                elif cleaned_line.endswith("?"):
                    questions.append(cleaned_line)

        # If we couldn't extract structured data, create generic response
        if not insights and not questions:
            insights = [
                "Your journal entry shows thoughtful reflection on your experiences."
            ]
            questions = [
                "What aspects of this experience would you like to explore further?"
            ]

        fallback_data = {
            "insights": insights[: self.config.max_insights],
            "questions": questions[: self.config.max_questions],
            "themes": ["reflection", "personal_growth"],
        }

        return {
            "success": True,
            "data": fallback_data,
            "raw_response": response,
            "fallback": True,
            "error": error,
        }

    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create error response with minimal fallback data."""
        return {
            "success": False,
            "error": error,
            "data": {
                "insights": [
                    "I'm having trouble analyzing your entry right now, but your thoughts are valuable."
                ],
                "questions": ["What would help you reflect on this experience?"],
                "themes": ["reflection"],
            },
        }

    def validate_content_for_reflection(self, content: str) -> bool:
        """
        Check if content is suitable for AI reflection.

        Args:
            content: Journal entry content

        Returns:
            bool: True if content is sufficient for meaningful reflection
        """
        if not content or not content.strip():
            return False

        # Check minimum length
        if len(content.strip()) < self.config.min_content_length:
            return False

        # Check if content has meaningful words (not just punctuation/spaces)
        word_count = len([word for word in content.split() if word.strip()])
        if word_count < 10:  # Minimum 10 words
            return False

        return True

    def get_reflection_preview(self, content: str) -> str:
        """
        Get a preview of what will be sent for AI reflection.

        Args:
            content: Journal entry content

        Returns:
            str: Preview text showing what will be analyzed
        """
        processed = self._preprocess_content(content)
        if len(processed) <= 100:
            return processed

        # Show first 100 characters with ellipsis
        return processed[:100] + "..."
