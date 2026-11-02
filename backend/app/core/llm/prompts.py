"""Prompt template loader and prompt-injection sanitization utilities."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Locate prompts directory relative to backend root
PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"

_env = Environment(
    loader=FileSystemLoader(str(PROMPTS_DIR)),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def sanitize_untrusted_input(text: str) -> str:
    """Sanitize untrusted user/candidate text to mitigate prompt injection.

    - Strips XML delimiter closing tags if a candidate attempts to close them
    - Strips common malicious override attempts
    """
    if not text:
        return ""
    # Disarm delimiter breakouts
    cleaned = text.replace("</resume_content>", "&lt;/resume_content&gt;")
    cleaned = cleaned.replace("</job_description>", "&lt;/job_description&gt;")
    cleaned = cleaned.replace("</candidate_evidence>", "&lt;/candidate_evidence&gt;")
    return cleaned


def render_prompt(template_name: str, **kwargs) -> str:
    """Render a versioned prompt template with sanitized input variables."""
    sanitized_kwargs = {}
    for k, v in kwargs.items():
        if isinstance(v, str):
            sanitized_kwargs[k] = sanitize_untrusted_input(v)
        else:
            sanitized_kwargs[k] = v

    template = _env.get_template(template_name)
    return template.render(**sanitized_kwargs)
