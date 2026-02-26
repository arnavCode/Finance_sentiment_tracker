# src/finbert.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "ProsusAI/finbert"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

@torch.inference_mode()
def score_titles(titles: list[str], max_length: int = 128):
    enc = tokenizer(
        titles,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    logits = model(**enc).logits
    probs = torch.softmax(logits, dim=-1)  # (N, 3)
    # Map to labels explicitly (don’t assume order)
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    return probs, id2label