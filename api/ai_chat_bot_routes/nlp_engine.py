from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# Load trained model and tokenizer
model_path = "./models/chatbot_model"
model = AutoModelForSequenceClassification.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

classifier = pipeline("text-classification", model=model, tokenizer=tokenizer)

def predict_intent(user_input):
    result = classifier(user_input)
    intent = result[0]['label']
    confidence = result[0]['score']
    return intent, confidence
