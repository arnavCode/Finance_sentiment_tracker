import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL = "ProsusAI/finbert"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
model.eval()

@torch.inference_mode()
def score_texts(texts, max_length=256):
    enc = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    logits = model(**enc).logits
    probs = torch.softmax(logits, dim=-1)  # shape [N, 3]
    # label order depends on model config; map explicitly:
    id2label = model.config.id2label  # e.g. {0:'negative',1:'neutral',2:'positive'}
    return probs, id2label

probs, id2label = score_texts(["Shares surged after strong earnings."])
print(probs.tolist(), id2label)