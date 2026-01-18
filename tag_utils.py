import re

def extract_tags_from_text(text):
    """
    Extracts tags from text. Tags are one-word entities starting with #.
    Example: "Fix bug #bug #high-priority" -> ["bug", "high-priority"]
    (Wait, requirement says start from #, such as #1 or #health. 
    One-word entities usually means no spaces.)
    """
    if not text:
        return []
    # Find all words starting with #
    # \w matches alphanumeric + underscores. Let's add hyphens as they are common.
    # Requirement says "one-word entities", usually excludes punctuation but 
    # health-check might be a tag.
    tags = re.findall(r'#([\w-]+)', text)
    # The requirement says starting from #, usually includes the # but 
    # the function name "extract_tags" might mean returning just the tag names.
    # Let's return them with # to be safe, or just the word?
    # Requirement 1: tags are one-word entities, starting from #
    # Requirement 6: if such tag exists for user, it's used, if not, it's created.
    # Let's keep the word without # for DB storage, but the identification is by #.
    return list(set(tags)) # Return unique tags from text

def strip_tags_from_text(text):
    """
    Removes hashtags from text and cleans up extra whitespace.
    Example: "Take a shower #health" -> "Take a shower"
    """
    if not text:
        return ""
    # Remove #word or #word-with-hyphens
    cleaned = re.sub(r'#[\w-]+', '', text)
    # Remove extra whitespace left behind
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned
