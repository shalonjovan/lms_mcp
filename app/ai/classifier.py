"""Assignment type classification using the AI client."""

from app.ai.client import LLMClient

CLASSIFICATION_SYSTEM_PROMPT = """You are an assignment classifier. Given the assignment title, 
description, and any attachment filenames, classify the assignment into exactly one of these types:

- document: A written report, essay, or document submission (PDF, DOCX, text)
- programming: A coding/programming assignment
- handwritten: Handwritten notebook or scanned document submission
- presentation: PowerPoint or slide deck submission
- quiz: Online quiz or test
- image: Image/drawing upload
- other: Anything that doesn't fit above

Respond with ONLY the type name, nothing else."""


def classify_assignment(
    title: str,
    description: str,
    attachment_names: list[str] | None = None,
) -> str:
    """Classify an assignment type using the LLM.

    Returns one of: document, programming, handwritten, presentation, quiz, image, other.
    """
    client = LLMClient()
    user_prompt = f"Title: {title}\n\nDescription:\n{description[:2000]}"
    if attachment_names:
        user_prompt += f"\n\nAttachments: {', '.join(attachment_names)}"

    result = client.generate(
        system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=50,
        temperature=0.1,
    )

    valid_types = {"document", "programming", "handwritten", "presentation", "quiz", "image", "other"}
    result = result.strip().lower()
    return result if result in valid_types else "other"
