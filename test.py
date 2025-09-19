import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score, classification_report
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# -------------------
# 1. Load data
# -------------------
df = pd.read_csv("/workspaces/Dansah_LearnPack/combined_data.csv")

X = df["Review"].tolist()
y = df.drop("Review", axis=1).values 
label_cols = df.drop("Review", axis=1).columns.tolist()

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# -------------------
# 2. Dataset class
# -------------------
class ReviewDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
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

model_name = "distilbert-base-multilingual-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

train_dataset = ReviewDataset(X_train, y_train, tokenizer)
test_dataset = ReviewDataset(X_test, y_test, tokenizer)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=y.shape[1],
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
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=2,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True,
    dataloader_pin_memory=False

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
# 6. Evaluation & Predictions
# -------------------

# Predict on full dataset
all_dataset = ReviewDataset(X, y, tokenizer)
all_preds = trainer.predict(all_dataset)

logits = all_preds.predictions
probs = torch.sigmoid(torch.tensor(logits)).numpy()
binary_preds = (probs > 0.5).astype(int)

# Convert to DataFrame with labels
results_df = pd.DataFrame(binary_preds, columns=label_cols)
results_df.insert(0, "Review", X)

# Save to CSV
results_df.to_csv("categorized_reviews.csv", index=False)
print("✅ Saved predictions to categorized_reviews.csv")

# Save Model and tokenizer
trainer.save_model("./trained_model")
tokenizer.save_pretrained("./trained_model")
