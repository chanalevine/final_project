import re

# ---------------------------------------------------------
# INGREDIENT NORMALIZER
# ---------------------------------------------------------

def normalize_ingredient(raw_text):
    text = raw_text.lower().strip()

    # Remove commas and parentheses
    text = re.sub(r"[(),]", " ", text)

    # Remove unicode fractions like ½, ¼, ¾
    text = re.sub(r"[¼½¾⅓⅔⅛⅜⅝⅞]", " ", text)

    # Remove numeric fractions like 1/2, 3/4
    text = re.sub(r"\b\d+\/\d+\b", " ", text)

    # Remove whole numbers
    text = re.sub(r"\b\d+\b", " ", text)

    # Remove measurement units
    units = [
        "tsp", "tbsp", "tablespoon", "teaspoon",
        "cup", "cups", "oz", "ounce", "ounces",
        "lb", "pound", "pounds", "gram", "g", "kg",
        "clove", "cloves", "slice", "slices",
        "medium", "large", "small"
    ]
    for u in units:
        text = re.sub(rf"\b{u}\b", " ", text)

    # Remove preparation words
    prep_words = [
        "diced", "chopped", "minced", "sliced",
        "fresh", "ground", "crushed", "peeled",
        "shredded", "grated"
    ]
    for p in prep_words:
        text = re.sub(rf"\b{p}\b", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Handle simple plurals
    if text.endswith("s") and len(text) > 3:
        text = text[:-1]

    return text