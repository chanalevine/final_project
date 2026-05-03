import re

def normalize_ingredient(raw_text):
    text = raw_text.lower().strip()

    text = re.sub(r"[(),]", " ", text)
    text = re.sub(r"[¼½¾⅓⅔⅛⅜⅝⅞]", " ", text)
    text = re.sub(r"\b\d+\/\d+\b", " ", text)
    text = re.sub(r"\b\d+\b", " ", text)

    units = [
        "tsp", "tbsp", "tablespoon", "teaspoon",
        "cup", "cups", "oz", "ounce", "ounces",
        "lb", "pound", "pounds", "gram", "g", "kg",
        "clove", "cloves", "slice", "slices",
        "medium", "large", "small"
    ]
    for u in units:
        text = re.sub(rf"\b{u}\b", " ", text)

    prep_words = [
        "diced", "chopped", "minced", "sliced",
        "fresh", "ground", "crushed", "peeled",
        "shredded", "grated"
    ]
    for p in prep_words:
        text = re.sub(rf"\b{p}\b", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    if text.endswith("s") and len(text) > 3:
        text = text[:-1]

    return text
