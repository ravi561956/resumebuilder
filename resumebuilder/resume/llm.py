"""
Optional helper for calling the Google Gemini API.

This module previously hardcoded a live API key and made a network
call at *import* time, which meant simply importing this file (e.g. via
`python manage.py shell`) would leak the key and fire an API request.

Nothing else in the project imports this module, so it has been
rewritten as a safe, opt-in helper. Set the GEMINI_API_KEY environment
variable to use it.
"""

import os


def ask_gemini(prompt: str, model: str = "gemini-3-flash-preview") -> str:
    """Send a prompt to Gemini and return the text response.

    Raises RuntimeError if GEMINI_API_KEY is not configured.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set."
        )

    # Imported lazily so this module has zero side effects if unused.
    from google import genai

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text
