import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score, classification_report


# -------------------
# 1. Load data
# -------------------
df = read_csv("/workspaces/Dansah_LearnPack/combined_data.csv")

X = df["review"].tolist()
y = df[label_cols].values  # numpy array shape (N, num_labels)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# -------------------
# 2. Dataset class
# -------------------
class ReviewDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        inputs = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt"
        )
        item = {key: val.squeeze(0) for key, val in inputs.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)
        return item

# -------------------
# 3. Tokenizer & Model
# -------------------
tokenizer = XLMRobertaTokenizer.from_pretrained("xlm-roberta-base")

train_dataset = ReviewDataset(X_train, y_train, tokenizer)
test_dataset = ReviewDataset(X_test, y_test, tokenizer)

model = XLMRobertaForSequenceClassification.from_pretrained(
    "xlm-roberta-base",
    num_labels=len(label_cols),
    problem_type="multi_label_classification"
)

# -------------------
# 4. Metrics
# -------------------
def compute_metrics(pred):
    logits, labels = pred
    preds = (torch.sigmoid(torch.tensor(logits)) > 0.5).int().numpy()
    labels = labels.astype(int)
    return {
        "f1": f1_score(labels, preds, average="micro"),
        "accuracy": accuracy_score(labels, preds)
    }

# -------------------
# 5. Training
# -------------------
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

trainer.train()

# -------------------
# 6. Evaluation
# -------------------
preds = trainer.predict(test_dataset)
logits = preds.predictions
probs = torch.sigmoid(torch.tensor(logits)).numpy()
binary_preds = (probs > 0.5).astype(int)

print("Classification Report:\n")
print(classification_report(y_test, binary_preds, target_names=label_cols))
