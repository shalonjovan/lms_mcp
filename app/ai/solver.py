"""AI solution generation for assignments."""

from pathlib import Path

from app.ai.client import LLMClient
from app.ai.classifier import classify_assignment

SOLVER_PROMPTS = {
    "document": """You are writing a formal academic assignment submission. 
Given the assignment title, instructions, and any additional context, produce a 
well-structured, professionally written document. Use proper academic tone, 
include relevant explanations, and format with clear section headings. 
Output in Markdown format.""",

    "programming": """You are solving a programming assignment. 
Given the assignment instructions, produce:
1. A clear explanation of the approach
2. Well-commented source code
3. Example input/output or test cases
4. Any necessary setup instructions

Output your solution in Markdown format with code blocks.""",

    "presentation": """You are creating content for a presentation assignment.
Given the topic and instructions, produce:
1. A slide outline with slide titles and bullet points
2. Speaker notes for each slide
3. Key diagrams or concepts to include

Output in Markdown format.""",

    "handwritten": """You are generating content for a handwritten notebook submission.
Given the assignment instructions, produce:
1. Clear step-by-step solutions
2. Important formulas, diagrams (described in text), and derivations
3. Final answers highlighted

Output in Markdown format suitable for conversion to a document.""",

    "quiz": """You are answering a quiz/test.
Answer each question concisely and accurately.
For multiple choice, explain why the correct answer is right. 
For numerical problems, show your work.""",

    "image": """You are describing content for an image-based assignment.
Given the instructions, describe what should be created/drawn,
including all labels, annotations, and key elements.""",

    "other": """Provide a comprehensive solution for the following assignment.
Output in well-structured Markdown format.""",
}


def solve_assignment(
    title: str,
    description: str,
    assignment_type: str | None = None,
    attachment_texts: list[str] | None = None,
) -> str:
    """Generate a solution for an assignment using the LLM.

    Args:
        title: Assignment title
        description: Full assignment description/instructions
        assignment_type: Pre-classified type (auto-classify if None)
        attachment_texts: Text extracted from any attachments

    Returns:
        Solution content in Markdown format.
    """
    if not assignment_type:
        assignment_type = classify_assignment(title, description)

    system_prompt = SOLVER_PROMPTS.get(assignment_type, SOLVER_PROMPTS["other"])

    user_prompt = f"# Assignment: {title}\n\n## Instructions\n{description}\n"
    if attachment_texts:
        user_prompt += "\n## Reference Material\n"
        for i, text in enumerate(attachment_texts, 1):
            user_prompt += f"### Attachment {i}\n{text[:3000]}\n\n"

    client = LLMClient()
    return client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=8192,
        temperature=0.5,
    )
