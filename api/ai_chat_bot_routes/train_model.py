import os
from datasets import load_dataset
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, AutoTokenizer

class ChatbotModelTrainer:
    def __init__(self, model_name="bert-base-multilingual-cased", dataset_path="training_data/training_data.csv"):
        self.model_name = model_name
        self.dataset_path = dataset_path
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.dataset = None
        self.model = None

    def load_dataset(self):
        """Load the dataset from CSV."""
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(BASE_DIR, self.dataset_path)

        # Load dataset
        self.dataset = load_dataset("csv", data_files=dataset_path)

    def preprocess_data(self):
        """Tokenize the dataset."""
        def preprocess_function(examples):
            return self.tokenizer(examples['text'], padding="max_length", truncation=True)

        # Tokenize data
        self.dataset = self.dataset.map(preprocess_function, batched=True)

    def load_model(self):
        """Load the pre-trained model."""
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=len(set(self.dataset['train']['label']))  # Number of unique labels
        )

    def setup_training(self):
        """Set up the training arguments."""
        training_args = TrainingArguments(
            output_dir="./models/chatbot_model",           # Output directory for model checkpoints
            evaluation_strategy="epoch",                  # Evaluation at the end of each epoch
            num_train_epochs=3,                           # Number of epochs to train the model
            per_device_train_batch_size=16,               # Batch size per device (GPU or CPU)
            save_steps=10_000,                            # Save checkpoints every 10,000 steps
            save_total_limit=2,                           # Keep only 2 saved checkpoints
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.dataset['train'],
            eval_dataset=self.dataset['validation']
        )

        return trainer

    def train(self):
        """Train and save the model."""
        self.load_dataset()
        self.preprocess_data()
        self.load_model()

        # Set up training
        trainer = self.setup_training()

        # Train the model
        trainer.train()

        # Save the model after training
        self.model.save_pretrained("./models/chatbot_model")
        print("Model saved successfully!")

if __name__ == "__main__":
    # Initialize the trainer class
    trainer = ChatbotModelTrainer(dataset_path="training_data/training_data.csv")

    # Train the model
    trainer.train()
