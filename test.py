from pymongo import MongoClient
from llama_cpp import Llama
import re

# Connect to MongoDB
mongo_url = "mongodb://localhost:27017"
client = MongoClient(mongo_url)
db = client['product_db']
collection = db['products']

# Load Qwen GGUF Model
model_path = "qwen2.5-14b-instruct-q5_k_m.gguf"  # Replace with your GGUF model path
print("Loading Qwen GGUF model...")
llm = Llama(model_path=model_path, n_ctx=2048, n_gpu_layers=50, verbose=True)

# Retrieve MongoDB Data as Context
def get_mongodb_data():
    context_data = []
    results = collection.find()
    for doc in results:
        formatted_doc = ", ".join(f"{key}: {value}" for key, value in doc.items() if key != "_id")
        context_data.append(formatted_doc)
    return "\n".join(context_data)

# Query Qwen Model with Controlled Prompt
def query_qwen_with_context(user_question):
    # Retrieve MongoDB data as context
    context = get_mongodb_data()

    # Build the strict instruction prompt
    strict_prompt = (
        "You are an assistant who answers questions strictly based on the provided context data. "
        "Do not add explanations or irrelevant information. "
        "If the question is unrelated to the context, respond with 'I don't know.'.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_question}\n"
        "Answer:"
    )

    print("Querying Qwen model...")
    output = llm(strict_prompt, max_tokens=300, temperature=0.3, echo=False, stop=["Question:", "Context:"])
    response = output['choices'][0]['text'].strip()
    
    return response


if __name__ == "__main__":
    print("Welcome to the Product Q&A System! Type 'exit' to quit.")
    while True:
        question = input("You: ")
        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        response = query_qwen_with_context(question)
        print(f"Bot: {response}")