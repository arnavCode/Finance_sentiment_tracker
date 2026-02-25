from transformers import pipeline

clf = pipeline(
    task="text-classification",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert",
    return_all_scores=True,
)

texts = [
    "Company reported record revenue growth and raised guidance for next quarter.",
    "The firm missed earnings expectations and cut its outlook."
]

out = clf(texts)
for t, scores in zip(texts, out):
    print(t)
    print(scores)  # list of dicts: [{'label': 'positive', 'score': ...}, ...]