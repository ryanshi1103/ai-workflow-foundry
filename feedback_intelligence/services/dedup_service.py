"""Deduplication service using content hashing."""

from feedback_intelligence.schemas import compute_content_hash


def compute_hash(
    content: str,
    platform: str = "",
    source_url: str = "",
    external_id: str = "",
) -> str:
    """Compute the content hash for deduplication."""
    return compute_content_hash(content, platform, source_url, external_id)


def is_duplicate(
    content: str,
    existing_hashes: set[str],
    platform: str = "",
    source_url: str = "",
    external_id: str = "",
) -> bool:
    """Check if content already exists in the set of hashes."""
    h = compute_hash(content, platform, source_url, external_id)
    return h in existing_hashes
