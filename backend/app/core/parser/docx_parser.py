"""DOCX text extraction using python-docx."""

import logging
from pathlib import Path
import docx

logger = logging.getLogger("rankwise.parser.docx")


def extract_text_from_docx(file_path: str | Path) -> tuple[str, list[str]]:
    """Extract text from DOCX paragraphs and tables.

    Returns:
        tuple[str, list[str]]: (extracted_text, list_of_warnings)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    warnings: list[str] = []
    lines: list[str] = []

    try:
        doc = docx.Document(str(path))
    except Exception as e:
        logger.error(f"Failed to open DOCX {path}: {e}")
        return "", [f"corrupted_docx_file: {str(e)}"]

    for para in doc.paragraphs:
        txt = para.text.strip()
        if txt:
            lines.append(txt)

    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                lines.append(" | ".join(row_cells))

    full_text = "\n".join(lines).strip()

    if len(full_text) < 30:
        warnings.append("empty_or_minimal_docx: Document contains very little extractable text.")

    return full_text, warnings
