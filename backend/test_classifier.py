import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from classifier import predict_tier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "classifier.pkl")

test_prompts = [
    "What is the capital of Germany?",
    "Summarize this article in 3 bullet points.",
    "Design a distributed rate limiter for 10,000 requests per second.",
    "Convert 50 miles to kilometers.",
    "Write a Python function to check if a number is prime.",
    "Analyze the tradeoffs between Kafka and RabbitMQ for a microservices architecture at scale.",
    "What does REST stand for?",
    "Classify these support tickets by urgency.",
    "Write a technical RFC for migrating a monolith to microservices with zero downtime.",
]

for prompt in test_prompts:
    result = predict_tier(prompt, MODEL_PATH)
    print(f"Tier {result['tier']} ({result['label']:8s}) | conf={result['confidence']:.2f} | {prompt[:70]}")