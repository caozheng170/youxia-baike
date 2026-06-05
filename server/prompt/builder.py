"""Prompt builder for generating information visualization images."""

# System-level style guidance for all generated images
STYLE_SYSTEM_PROMPT = """You are creating an information visualization / infographic image. Follow these rules:
- Clean, modern design with clear visual hierarchy
- Use warm, earthy color palette (browns, ambers, creams, with accent colors)
- Include clear labels, titles, and annotations
- Data-driven layout: charts, diagrams, maps, or structured layouts
- No photographs of people — use icons, symbols, and abstract representations
- Professional infographic aesthetic
- Text should be readable and well-organized
- Include visual connections between related elements (lines, arrows, clusters)
"""

# Templates for different types of queries
QUERY_TEMPLATES = {
    "concept": """Create an infographic explaining "{topic}":
- Central title with the topic name
- Key concepts arranged in a clear hierarchy
- Visual connections showing relationships
- Supporting details and annotations
- Color-coded sections for different aspects""",

    "comparison": """Create a comparison infographic for "{topic}":
- Side-by-side layout comparing key aspects
- Clear labels for each comparison dimension
- Visual indicators (charts, scales, icons) for differences
- Summary section highlighting key takeaways""",

    "process": """Create a process flow infographic for "{topic}":
- Step-by-step visual flow (left-to-right or top-to-bottom)
- Numbered steps with icons or illustrations
- Connecting arrows showing progression
- Key details at each stage
- Timeline or milestone markers""",

    "data": """Create a data visualization infographic for "{topic}":
- Charts and graphs as the primary visual elements
- Clear axis labels and legends
- Data points with annotations for key insights
- Color-coded categories
- Summary statistics highlighted""",

    "default": """Create an information visualization for "{topic}":
- Eye-catching title at the top
- Organized sections with clear visual hierarchy
- Icons, charts, or diagrams to illustrate key points
- Connecting elements showing relationships
- Warm color scheme with professional layout
- Informative and engaging design""",
}


def classify_query(query: str) -> str:
    """Classify a query into a template type."""
    q = query.lower()

    comparison_keywords = ["compare", "vs", "versus", "difference", "better", "contrast", "versus"]
    process_keywords = ["how to", "steps", "process", "workflow", "guide", "tutorial", "method", "way to"]
    data_keywords = ["data", "statistics", "chart", "graph", "numbers", "trends", "growth", "rate", "ranking"]

    if any(kw in q for kw in comparison_keywords):
        return "comparison"
    if any(kw in q for kw in process_keywords):
        return "process"
    if any(kw in q for kw in data_keywords):
        return "data"
    return "default"


def build_generation_prompt(query: str, parent_context: str = "") -> str:
    """Build a detailed image generation prompt from a user query.

    Args:
        query: The user's search query or click exploration text.
        parent_context: Optional context from the parent page.

    Returns:
        A detailed prompt for image generation.
    """
    query_type = classify_query(query)
    template = QUERY_TEMPLATES.get(query_type, QUERY_TEMPLATES["default"])
    prompt = template.format(topic=query)

    if parent_context:
        prompt += f"\n\nContext from parent topic: {parent_context}"
        prompt += "\nThis is a deeper exploration — focus on details and sub-topics."

    return prompt


def build_exploration_prompt(click_intent: str, parent_query: str) -> str:
    """Build a prompt for an exploration (click) page.

    Args:
        click_intent: The understood intent from the click.
        parent_query: The query that generated the parent page.

    Returns:
        A detailed prompt for image generation.
    """
    query_type = classify_query(click_intent)
    template = QUERY_TEMPLATES.get(query_type, QUERY_TEMPLATES["default"])
    prompt = template.format(topic=click_intent)

    prompt += f"\n\nThis page explores a specific aspect of: \"{parent_query}\""
    prompt += "\nDesign it as a focused deep-dive with more detail than the overview."

    return prompt
