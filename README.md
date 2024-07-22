# Recipe Generator in Python using Notion and Tune Studio
## Project Description
This project is a Notion Recipe Generator that allows users to create, modify and find recipes from a Notion page. The API, built using a FASTAPI server and a Large Language Model (LLM), allows user to interact with Notion easily. 

Following is an example execution of this project.

1. Start the server:
```
python3 server.py
```
2. cURL command to create a new recipe:
```
curl -X POST "http://0.0.0.0:8000/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{ 
  "temperature": 0.9,
  "messages": [
    {
      "role": "user",
      "content": "Add a new recipe with peas, onion, rice and capsicum"
    }
  ],
  "stream": false,
  "frequency_penalty": 0.2,
  "max_tokens": 100
}'
```
3. cURL command to update an exisiting recipe:
```
curl -X POST "http://0.0.0.0:8000/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{
  "temperature": 0.9,
  "messages": [
    {
      "role": "user",
      "content": "In Chili Scramble recipe, please add salt to the ingredients list"
    }
  ],
  "stream": false,
  "frequency_penalty": 0.2,
  "max_tokens": 100
}'
```

Project Demo:

[Demo Video](./assets/Notion%20Demo.mp4)


## Installation
To install the dependencies in the requirements.txt file run the following command:
```
pip install -r requirements.txt
```

## Environment variables
Set the environment variables in a `.env` file
```
NOTION_KEY = <your-notion-api-key>
TUNEAI_TOKEN = <your-tuneai-api-key>
SERPER_KEY = <your-serper-api-key>
OPENAI_KEY = <your-openai-api-key>
```

## Project Structure:
The project consists of three files: main.py, cleanup.py and server.py.
- `server.py`: This file starts the FASTAPI server and contains the entry point for the API.

- `main.py`: This file contains the functionality for creating and adding a new recipe to a Notion page based on user-inputted ingredients.

- `cleanup.py`: This file handles the functionality for modifying and updating an exisiting recipe in a Notion page based on the user comment.
