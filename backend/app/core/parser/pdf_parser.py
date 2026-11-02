"""PyMuPDF PDF text extraction with multi-column layout handling and unreadable scan detection."""

import logging
from pathlib import Path
import fitz  # PyMuPDF

logger = logging.getLogger("rankwise.parser.pdf")


def extract_text_from_pdf(file_path: str | Path) -> tuple[str, list[str]]:
    """Extract plain text from PDF with column-aware ordering and unreadable warning detection.

    Returns:
        tuple[str, list[str]]: (extracted_text, list_of_warnings)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    warnings: list[str] = []
    text_blocks: list[str] = []
    total_images = 0

    try:
        doc = fitz.open(str(path))
    except Exception as e:
        logger.error(f"Failed to open PDF {path}: {e}")
        return "", [f"corrupted_pdf_file: {str(e)}"]

    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            total_images += len(page.get_images())

            # get_text("blocks") returns tuples: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type 0 is text, 1 is image
            blocks = page.get_text("blocks")
            text_only_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

            # Multi-column layout sorting heuristic:
            # Sort by approximate column bucket (x0 divided by column width threshold) then vertical y0
            # Detect if page seems 2-column: check if there are blocks on left (x0 < width/2) and right (x0 >= width/2)
            page_width = page.rect.width
            col_width = page_width / 2.0 if page_width > 0 else 300.0

            # Sort primarily by horizontal column index, then vertically by y0
            sorted_blocks = sorted(
                text_only_blocks,
                key=lambda b: (int(b[0] // (col_width * 0.85)), b[1])
            )

            for b in sorted_blocks:
                text_blocks.append(b[4].strip())

    finally:
        doc.close()

    full_text = "\n\n".join(text_blocks).strip()

    # Detect scanned / unreadable documents
    if len(full_text) < 50:
        if total_images > 0:
            warnings.append("scanned_pdf_detected: Document appears to be a scanned image with minimal machine-readable text.")
        else:
            warnings.append("unreadable_pdf_detected: Document contains negligible extractable text.")

    return full_text, warnings
