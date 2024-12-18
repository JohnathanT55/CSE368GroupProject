from pymongo import MongoClient
import pandas as pd

# MongoDB setup
mongo_url = "mongodb://localhost:27017"
database_name = "product_db"
collection_name = "products"

file_path = 'product_data.csv'

# Auto import CSV data into MongoDB
def import_csv_to_mongodb(csv_path, mongo_url, db_name, collection_name):
    try:
        client = MongoClient(mongo_url)
        db = client[db_name]
        collection = db[collection_name]

        # Read and convert CSV Files
        df = pd.read_csv(csv_path, sep=None, engine='python')
        df = df.dropna()
        data = df.to_dict(orient="records")

        # Insert data into MongoDB
        if data:
            collection.insert_many(data)
            print(f"Successfully inserted {len(data)} records into the MongoDB collection '{db_name}.{collection_name}'!")
        else:
            print("No valid data found in the CSV file!")
    except Exception as e:
        print("Error occurred:", e)

if __name__ == "__main__":
    import_csv_to_mongodb(file_path, mongo_url, database_name, collection_name)
