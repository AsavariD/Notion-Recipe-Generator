from dotenv import load_dotenv, set_key

load_dotenv()
import os
import requests
import fire
import logging

logging.basicConfig(level=logging.INFO)

NOTION_KEY = os.getenv("AUTH_TOKEN")
TUNEAI_TOKEN = os.getenv("TUNE_KEY")
SERPER_API_KEY = os.getenv("SERPER_KEY")
PARENT_PAGE_ID = "2dd7d0fcd8ef4653a0f32e55bc01a481"


notion_headers = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

serper_headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

model = "rohan/mixtral-8x7b-inst-v0-1-32k"
pagetitle_pageid_data = {}


def get_parent_page_data():
    response = requests.get(
        f"https://api.notion.com/v1/blocks/{PARENT_PAGE_ID}/children",
        headers=notion_headers,
    )

    response_data = response.json()
    list_of_pages = response_data["results"]

    for page in list_of_pages:
        title = page["child_page"]["title"]
        page_id = page["id"]
        pagetitle_pageid_data[title] = page_id

    return pagetitle_pageid_data


def call_llm(messages):
    url = "https://proxy.tune.app/chat/completions"
    headers = {
        "Authorization": TUNEAI_TOKEN,
        "Content-Type": "application/json",
    }
    data = {
        "temperature": 0.8,
        "messages": messages,
        "model": model,
        "stream": False,
        "frequency_penalty": 0,
        "max_tokens": 500,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    response_data = response.json()
    return response_data["choices"][0]["message"]["content"].strip()


def gen_recipe(dish_title, ingredients, num_ingredients):
    messages = [
        {
            "role": "system",
            "content": """You are a recipe generator. Your task is to generate the recipe using the title and ingredients. Follow these rules strictly:
            1. Print each recipe step on a new line.
            2. Do not use bullets, numbers, hyphens, and any other symbols.
            3. Only print the recipe steps.
            4. Do not include any additional ingredients in the recipe steps.
            
            For example if the ingredients are almonds, flour, milk, eggs the output should be:
            Preheat your oven to 350°F (175°C).\nGrind almonds into a fine flour using a food processor or coffee grinder.
            \nIn a bowl, whisk together the almond flour, milk, and eggs until well combined.\nPour the mixture\ninto a baking dish.
            \nBake for 25-30 minutes, or until the pudding is set and golden brown on top.\nLet it cool before serving. Enjoy!""",
        },
        {
            "role": "user",
            "content": f"Generate a recipe for {dish_title} using {num_ingredients} ingredients which are {ingredients}",
        },
    ]

    return call_llm(messages)


def gen_recipe_title(topic):
    messages = [
        {
            "role": "system",
            "content": "You are a recipe title generator. Your task is to create a concise and engaging dish title based on the ingredients provided by the user. Follow these rules strictly:\n1. Collect the ingredients from the user.\n2. Generate a dish title that is no more than 5 words long.\n3. Only print the title without any quotation marks.\n4. Do not include the list of ingredients, steps, markdowns or any additional information.\n5. Do not include any text, quotes or anything before and after the title.",
        },
        {
            "role": "user",
            "content": "give me a recipe using fish, red chili powder, salt, ginger, garlic",
        },
        {"role": "assistant", "content": "Fish Curry"},
        {
            "role": "user",
            "content": "give me a recipe using potato, flour, corn flour, peri-peri",
        },
        {"role": "assistant", "content": "Spicy Potato Cakes"},
        {
            "role": "user",
            "content": "give me a recipe using chicken, garlic, lemon, onion",
        },
        {"role": "assistant", "content": "Lemon Chicken"},
        {"role": "user", "content": topic},
    ]

    return call_llm(messages)


def gen_num_ingredients(topic):
    messages = [
        {
            "role": "system",
            "content": """You are a mathematical counter. Count the number of ingredients entered by the user. Strictly follow these rules:
                1. Only print the number of ingredients. 
                2. The output should be a number.
                2. Do not print title, steps and additional information. 
                3. Do not print the word 'ingredients' and '.'""",
        },
        {"role": "user", "content": topic},
    ]

    return call_llm(messages)


def gen_ingredient_list(topic):
    messages = [
        {
            "role": "system",
            "content": """You are a list maker. Your task is to create a list of ingredients entered by the user. Follow these rules strictly:
                1. Print each ingredient on a new line.
                2. Do not use bullets, numbers, hyphens, or any other symbols.
                3. The first letter of each ingredient should be capitalized.
                4. Do not include any additional ingredients, dish titles, recipe steps, or extra information.
                5. Do not add any introductory or concluding text. Only list the ingredients as provided by the user.

                For example, if the user enters "eggs, flour, milk", the output should be:

                Eggs
                Flour
                Milk

                Ensure that all provided ingredients are listed exactly as specified.
                
                Exception:
                If the user enters a dish name and does not mention specific ingredients, you may add ingredients suitable to the dish name.""",
        },
        {
            "role": "user",
            "content": f"Find ingredients from the following prompt: {topic}",
        },
    ]

    return call_llm(messages)


def gen_description(dish_title, ingredients, recipe):
    messages = [
        {
            "role": "system",
            "content": """You generate descriptions for recipes. Follow these rules strictly:
                1. Do not add quotes to generated text. 
                2. Keep the description brief and do not include the recipe steps. 
                3. Limit the description length to 4-5 sentences.""",
        },
        {
            "role": "user",
            "content": f"""Generate a description for the dish with the following details. 
            Dish name: {dish_title}, Ingredients needed: {ingredients} and Recipe: {recipe}""",
        },
    ]

    return call_llm(messages)


def get_cover_image(dish_title):
    url = "https://google.serper.dev/images"
    data = {"q": dish_title}
    response = requests.post(url, headers=serper_headers, json=data)
    response.raise_for_status()
    response_data = response.json()

    return response_data["images"][0]["imageUrl"]


def get_emoji(dish_title):
    messages = [
        {
            "role": "system",
            "content": """List of emojis: 👌, 😋, 🍗,🍝,🍚,🍴,🍰,🍪,🍩,🍜,🍝,🍠,🍣,🍤,🦐,🥗,🍲,🥘,🥚,
            🥙,🍖,🥓,🍔,🍕,🥞,🥖,🥐,🍞,🫘,🥜,🫒,🥑,🍆,🥔,🥕,🥒,🍅,🥝,🍓,🍒,🍑,🍍,🍇,🍈,🍉,🍊.🍌\n
            Follow these rules strictly: \n
            1. The output should be exactly 1 emoji character.\n
            2. Do not include any text before and after the emoji.""",
        },
        {
            "role": "user",
            "content": "I want one emoji for the dish titled Chicken Onion Sandwich. Choose one emoji from the list you have and return it.",
        },
        {"role": "assistant", "content": "🍔"},
        {
            "role": "user",
            "content": "I want one emoji for the dish titled Chicken Onion Tomato. Choose one emoji from the list you have and return it.",
        },
        {"role": "assistant", "content": "🍅"},
        {
            "role": "user",
            "content": "I want one emoji for the dish titled Caramelized Onion Pasta. Choose one emoji from the list you have and return it.",
        },
        {"role": "assistant", "content": "🍝"},
        {
            "role": "user",
            "content": f"I want one emoji for the dish titled {dish_title}. Choose one emoji from the list you have and return it.",
        },
    ]

    return call_llm(messages)


def check_unique_titles(page_id, dish_title):
    response = requests.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children", headers=notion_headers
    )
    response_data = response.json()
    list_of_pages = response_data["results"]
    recipe_titles = []
    page_ids = []

    for i in range(len(list_of_pages)):
        recipe_titles.append(list_of_pages[i]["child_page"]["title"])
        page_ids.append(list_of_pages[i]["id"])

    messages = [
        {
            "role": "system",
            "content": 'Your task is to verify if a title is unique compared to an existing list of titles. Follow these steps:\n\n2. Compare the "Title" against the existing "List" of titles.\n3. The output should be either "unique" or "not unique".\n4. Do not print any additional text.',
        },
        {
            "role": "user",
            "content": "Title: \"Chicken Onion Bread\"\nList: ['Garlic Onion Chicken', 'Lemon Ginger Fish', 'Chicken Rice Onion', 'Chicken Onion Sandwich', 'Chicken Onion Bread']?\nReturn \"unique\" if the title is not found in the given list. \nReturn \"not unique\" if the title is found in the given list.",
        },
        {
            "role": "user",
            "content": "Title: \"Honey Garlic Chicken\"\nList: ['Garlic Onion Chicken', 'Lemon Ginger Fish', 'Chicken Rice Onion', 'Chicken Onion Sandwich', 'Chicken Onion Bread']?\nReturn \"unique\" if the title is not found in the given list. \nReturn \"not unique\" if the title is found in the given list.",
        },
        {"role": "assistant", "content": "unique"},
        {
            "role": "user",
            "content": "Title: \"Chicken Onion Bread\"\nList: ['Garlic Onion Chicken', 'Lemon Ginger Fish', 'Chicken Rice Onion', 'Chicken Onion Sandwich', 'Chicken Onion Bread']?\nReturn \"unique\" if the title is not found in the given list. \nReturn \"not unique\" if the title is found in the given list.",
        },
        {"role": "assistant", "content": "not unique"},
        {
            "role": "user",
            "content": "Title: \"Chocolate Pudding\"\nList: ['Garlic Onion Chicken', 'Lemon Ginger Fish', 'Chicken Rice Onion', 'Chicken Onion Sandwich', 'Chicken Onion Bread']?\nReturn \"unique\" if the title is not found in the given list. \nReturn \"not unique\" if the title is found in the given list.",
        },
        {"role": "assistant", "content": "unique"},
        {
            "role": "user",
            "content": f"""Title: "{dish_title}"
            List: {recipe_titles}
            Return "unique" if the title is not found in the given list. 
            Return "not unique" if the title is found in the given list.""",
        },
    ]

    return call_llm(messages)


def create_index_page():
    data = {
        "parent": {"page_id": PARENT_PAGE_ID},
        "properties": {"title": [{"text": {"content": "Index"}}]},
        "cover": {
            "external": {
                "url": "https://www.shutterstock.com/image-photo/recipes-word-made-herbs-spices-260nw-108508472.jpg"
            }
        },
        "icon": {"emoji": "📄"},
    }

    response = requests.post(
        "https://api.notion.com/v1/pages", headers=notion_headers, json=data
    )

    logging.info("Index page created")

    index_page_data = response.json()

    logging.info(f"Index page id: {index_page_data['id']}")

    return index_page_data["id"]


def create_database(index_page_id):
    data_database = {
        "parent": {
            "type": "page_id",
            "page_id": index_page_id,
        },
        "title": [{"type": "text", "text": {"content": "Recipes List"}}],
        "properties": {
            "Recipe Name": {"title": {}},
            "Ingredients": {"rich_text": {}},
            "Pricing": {"rich_text": {}},
        },
    }

    response = requests.post(
        "https://api.notion.com/v1/databases",
        headers=notion_headers,
        json=data_database,
    )

    logging.info("Database created")


def get_database_id(index_page_id):
    response = requests.get(
        f"https://api.notion.com/v1/blocks/{index_page_id}/children",
        headers=notion_headers,
    )

    database_data = response.json()
    database_id = database_data["results"][0]["id"]
    logging.info(f"Database id: {database_id}")

    return database_id


def add_database_row(
    database_id, recipe_title, ingredients_list, ingredients_price_list
):

    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Recipe Name": {"title": [{"text": {"content": recipe_title}}]},
            "Ingredients": {"rich_text": [{"text": {"content": ingredients_list}}]},
            "Pricing": {"rich_text": [{"text": {"content": ingredients_price_list}}]},
        },
    }

    response = requests.post(
        "https://api.notion.com/v1/pages", headers=notion_headers, json=data
    )

    logging.info("New row created")


def get_ingredients_price_list(ingredients_list):
    price_list = []

    for ingredient in ingredients_list:
        try:
            url = "https://google.serper.dev/shopping"
            data = {"q": ingredient}
            response = requests.request("POST", url, headers=serper_headers, json=data)
            response.raise_for_status()
            response_data = response.json()

            messages = [
                {
                    "role": "system",
                    "content": """From the given list of data, you will return the cheapest price for the ingredients. 
                    You only return the dollar value. The format of your answer will be $price.
                    Do not include any additional text in your response""",
                },
                {"role": "user", "content": str(response_data)},
            ]

            ingredient_price = call_llm(messages)

            price_list.append(ingredient_price)
        except Exception as e:
            logging.error(f"Error in finding price for ingredient {ingredient}: {e}")

    ingredients_price_list = ",".join(price_list)

    logging.info("Ingredients Price List ready")

    return ingredients_price_list


def main(topic):

    try:
        parent_page_data = get_parent_page_data()
        logging.info(f"Parent page data: {parent_page_data}")

        if "Index" not in parent_page_data.keys():
            try:
                index_page_id = create_index_page()
                create_database(index_page_id)
                database_id = get_database_id(index_page_id)
            except Exception as e:
                logging.error(f"Error creating index page or database: {e}")
        else:
            index_page_id = parent_page_data["Index"]
            database_id = get_database_id(index_page_id)

        if type(topic) == tuple:
            topic = ",".join(topic)

        try:
            num_ingredients = gen_num_ingredients(topic)
            dish_title = gen_recipe_title(topic)
            while check_unique_titles(PARENT_PAGE_ID, dish_title) != "unique":
                dish_title = gen_recipe_title(topic)
                logging.info("Generating unique title")

            ingredients = gen_ingredient_list(topic)
            recipe = gen_recipe(dish_title, ingredients, num_ingredients)
            description = gen_description(dish_title, ingredients, recipe)
        except Exception as e:
            logging.error(f"Error generating recipe details: {e}")
            return

        ingredient = ingredients.split("\n")
        ingredients_price_list = get_ingredients_price_list(ingredient)
        comma_separated_ingredients_list = ", ".join(ingredient)

        steps = recipe.split("\n")
        cleaned_steps = [step for step in steps if step.strip()]

        data = {
            "parent": {"page_id": PARENT_PAGE_ID},
            "properties": {"title": [{"text": {"content": dish_title.strip()}}]},
            "cover": {"external": {"url": get_cover_image(dish_title)}},
            "icon": {"emoji": get_emoji(dish_title)},
        }

        try:
            response = requests.post(
                "https://api.notion.com/v1/pages", headers=notion_headers, json=data
            )
            response.raise_for_status()
            new_page_data = response.json()
        except requests.RequestException as e:
            logging.error(f"Error creating Notion page: {e}")
            return

        data = {
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Dish Description"}}
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": description.strip()},
                            }
                        ]
                    },
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Ingredients List"}}
                        ]
                    },
                },
            ]
        }

        for item in ingredient:
            data["children"].append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": item.strip()},
                            }
                        ]
                    },
                },
            )

        data["children"].append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Recipe"}}]
                },
            },
        )

        for step in cleaned_steps:
            data["children"].append(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": step.strip()}}
                        ]
                    },
                }
            )

        try:
            response = requests.patch(
                f"https://api.notion.com/v1/blocks/{new_page_data['id']}/children",
                headers=notion_headers,
                json=data,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Error updating Notion page: {e}")
            return

        logging.info("Recipe added")

        try:
            add_database_row(
                database_id,
                dish_title,
                comma_separated_ingredients_list,
                ingredients_price_list,
            )
        except Exception as e:
            logging.error(f"Error adding row to database: {e}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    fire.Fire(main)
