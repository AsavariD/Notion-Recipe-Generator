# Recipe Generator in Python using Notion and Tune Studio
## Project Description
This project is a Notion Recipe Generator that uses the Notion API, Tune Studio, a FASTAPI server, and a large language model (LLM) for creating and modifying recipes. The project consists of a parent page, which contains an index page and sub-pages for individual recipes. The index page has a database with three columns: recipe name, ingredient list, and prices of the individual ingredients. The index page is updated every time a new recipe is created.

For the creation of recipes, the user-entered ingredients are read by the LLM, based on which it generates a recipe title, description, bullet list of ingredients, and numbered list of the recipe steps. In addition, a cover image and emoji best suited for the recipe title are added to the Notion recipe page. The components are added to a new notion page and published as a recipe on the parent page. For modifying existing recipes, the LLM identifies which part of the recipe needs to be changed based on the user comment. For example, if the user says "Add salt to the ingredients list," the program will only update the ingredients list in the existing recipe.

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
      "content": "Add a new recipe with mushroom, onion, capsicum and rice"
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
      "content": "The Mushroom Rice recipe is missing salt in the ingredients. Please add."
    }
  ],
  "stream": false,
  "frequency_penalty": 0.2,
  "max_tokens": 100
}'
```

Project Demo:

https://github.com/user-attachments/assets/6dce5949-447a-4e29-a31b-9e7675024d27




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
