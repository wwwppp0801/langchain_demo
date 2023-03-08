# Import libraries
import _env
import openai
openai.log="debug"
import pandas as pd
import numpy as np
import sqlite3 # Import sqlite3 library
import pickle # Import pickle module


model_engine="text-embedding-ada-002"

# Set up Azure OpenAI client

# Download BillSum dataset and load it into a pandas dataframe
#!wget https://www.dropbox.com/s/7n0yq6z9k8v0l9f/billsum.zip?dl=1 -O billsum.zip
#!unzip billsum.zip

df = pd.read_json("billsum_v4_1/test.jsonl", lines=True)

# Use embeddings API to index bill documents and store them in sqlite database
conn = sqlite3.connect("bill_embeddings.db") # Create a sqlite database file and connect to it
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE bill_embeddings (id INTEGER PRIMARY KEY, title TEXT, summary TEXT, text TEXT, title_embedding BLOB, summary_embedding BLOB, text_embedding BLOB)
    """) # Create a table to store bill embeddings

for i, row in df.iterrows():
  title = row["title"]
  summary = row["summary"]
  text = row["text"]

  # Encode the title, summary and text using embeddings API with text-search-doc-davinci-001 model
  response = openai.Embedding.create(
    input=[title, summary, text],
    engine=model_engine
  )

  # Get the embeddings as numpy arrays
  title_embedding = np.array(response['data'][0]["embedding"])
  summary_embedding = np.array(response['data'][1]["embedding"])
  text_embedding = np.array(response['data'][2]["embedding"])

  # Convert the embeddings to bytes objects and wrap them with sqlite3.Binary() function
  title_embedding_bytes = pickle.dumps(title_embedding)
  summary_embedding_bytes = pickle.dumps(summary_embedding)
  text_embedding_bytes = pickle.dumps(text_embedding)

  title_embedding_blob = sqlite3.Binary(title_embedding_bytes)
  summary_embedding_blob = sqlite3.Binary(summary_embedding_bytes)
  text_embedding_blob = sqlite3.Binary(text_embedding_bytes)

  # Store the embeddings in sqlite database using cursor.execute() method
  cursor.execute(f"""
    INSERT INTO bill_embeddings (id, title, summary, text, title_embedding, summary_embedding, text_embedding)
    VALUES ({i}, '{title}', '{summary}', '{text}', ?, ?, ?)
    """, (title_embedding_blob, summary_embedding_blob, text_embedding_blob))

conn.commit() # Commit the changes to the database

# Define a function to calculate cosine similarity between two vectors
def cosine_similarity(a, b):
  return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Define a query string to search for relevant bills
query = "A bill to provide relief for small businesses affected by COVID-19"

# Encode the query string using embeddings API with text-search-query-davinci-001 model
response = openai.Embedding.create(
    input=query,
    engine=model_engine
)

# Get the query embedding as a numpy array
query_embedding = np.array(response['data'][0]["embedding"])

# Retrieve all bill embeddings from sqlite database and compare them with query embedding using cosine similarity
results = cursor.execute("SELECT * FROM bill_embeddings")
scores = []

for result in results:
  id = result[0]
  title = result[1]
  summary = result[2]
  text = result[3]

  # Unpickle the bytes objects to get the numpy arrays of embeddings
  title_embedding_bytes = result[4]
  summary_embedding_bytes = result[5]
  text_embedding_bytes = result[6]

  title_embedding = pickle.loads(title_embedding_bytes)
  summary_embedding = pickle.loads(summary_embedding_bytes)
  text_embedding = pickle.loads(text_embedding_bytes)

  # Calculate the cosine similarity between query embedding and title, summary and text embeddings
  title_score = cosine_similarity(query_embedding, title_embedding)
  summary_score = cosine_similarity(query_embedding, summary_embedding)
  text_score = cosine_similarity(query_embedding, text_embedding)

  # Average the three scores to get the final score for each bill
  final_score = (title_score + summary_score + text_score) / 3

  # Append the id, title and final score to a list
  scores.append((id, title, final_score))

# Sort the list by final score in descending order
scores.sort(key=lambda x: x[2], reverse=True)

# Print the top five results with their titles and scores
for i in range(5):
  print(f"Rank {i+1}: {scores[i][1]} (Score: {scores[i][2]})")

# Close the database connection
conn.close()
