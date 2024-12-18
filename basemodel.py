from pymongo import MongoClient
from llama_cpp import Llama

# MongoDB setup
mongo_url = "mongodb://localhost:27017"
client = MongoClient(mongo_url)
chat_db = client['chat_db']
product_db = client['product_db']
products_collection = product_db['products']
messages_collection = chat_db['messages']

# load Qwen 2.5 14b instruct model
model_path = "qwen2.5-14b-instruct-q5_k_m.gguf"
print("Loading Qwen GGUF model...")
llm = Llama(model_path=model_path, n_ctx=2048, n_gpu_layers=50, verbose=False)

# Get list of brands
def get_brands():
    return list(products_collection.distinct("Brand"))

# Get products by brand
def get_products_by_brand(brand):
    products = []
    for doc in products_collection.find({"Brand": {"$regex": f"^{brand}$", "$options": "i"}}):
        products.append(doc["Product"])
    return products

# Get product details
def get_product_details(brand, product_name):
    return products_collection.find_one({
        "Brand": {"$regex": f"^{brand}$", "$options": "i"},
        "Product": {"$regex": f"^{product_name}$", "$options": "i"}
    })

# Generate product answers by calling Qwen model
def query_product_model(session_id, brand, product_name, user_question):
    product_details = get_product_details(brand, product_name)
    if not product_details:
        return "Sorry, no details found for this product."

    context = ", ".join(f"{key}: {value}" for key, value in product_details.items() if key != "_id")
    prompt = (
        "You are a helpful assistant. Answer strictly based on the product details:\n\n"
        f"Product Details: {context}\n"
        f"Question: {user_question}\n"
        "Answer:"
    )

    output = llm(prompt, max_tokens=50, temperature=0.1, echo=False, stop=["\n", "?", "anything else"])
    reply = output['choices'][0]['text'].strip()

    # Store conversation records
    messages_collection.insert_one({
        "session_id": session_id, "mode": "local", "sender": "User", "message": user_question
    })
    messages_collection.insert_one({
        "session_id": session_id, "mode": "local", "sender": "Assistance", "message": reply
    })

    return reply
