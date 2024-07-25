import os
import requests
import logging
import fire
from main import call_llm, get_cover_image, get_emoji
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.ERROR)

NOTION_API_KEY = os.getenv("AUTH_TOKEN")
PARENT_PAGE_ID = "2dd7d0fcd8ef4653a0f32e55bc01a481"

notion_headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
}

recipe_page_block_ids = []
recipe_page_heading_block_ids = []
pagetitle_pageid_data = {}


def get_page_data():
    try:
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

    except requests.RequestException as e:
        logging.error(f"Error fetching page data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occured: {e}")


def available_recipes():
    print("Available recipes: ")
    for title in pagetitle_pageid_data:
        print(title)


def get_page_content(page_id, page_name):
    try:
        response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=notion_headers,
        )

        blocks = response.json()["results"]
        logging.info(f"Blocks in child page: {blocks}")

        content = {
            "heading_2": "",
            "paragraph": "",
            "bulleted_list_item": "",
            "numbered_list_item": "",
        }

        for block in blocks:
            recipe_page_block_ids.append(block["id"])
            block_type = block["type"]
            if block_type == "heading_2":
                recipe_page_heading_block_ids.append(block["id"])
            text_content = block[block_type]["rich_text"][0]["text"]["content"]

            if block_type in content:
                if content[block_type]:
                    content[block_type] += "\n" + text_content
                else:
                    content[block_type] = text_content

        recipe_sections_content = {
            "Title": page_name,
            "Description": content["paragraph"],
            "Ingredients List": content["bulleted_list_item"],
            "Recipe": content["numbered_list_item"],
        }
        logging.info(f"Old content: {recipe_sections_content}")
        return recipe_sections_content

    except requests.RequestException as e:
        logging.error(f"Error in fetching page content: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occured: {e}")


def notion_blocks_to_modify(comment):
    messages = [
        {
            "role": "system",
            "content": """You are a recipe editor. Based on the user comment decide which parts of the recipe to change.\n
            Parts of recipe are as follows:\nDish title\nDescription\nIngredients List\nRecipe\n\n
            Follow these rules:\n1. The answer should be from the parts above.\n2. Do not add explanation and additional text.""",
        },
        {
            "role": "user",
            "content": 'Which parts of the recipe will be changed if the user comment is "The ingredients are not correct, can you add salt as well"?',
        },
        {"role": "assistant", "content": "Ingredients List"},
        {
            "role": "user",
            "content": 'Which parts of the recipe will be changed if the user comment is "I want to add chicken to the dish as well"?',
        },
        {
            "role": "assistant",
            "content": "Title\nDescription\nIngredients List\nRecipe",
        },
        {
            "role": "user",
            "content": 'Which parts of the recipe will be changed if the user comment is "Instead of chicken as the protein I want to use fish"?',
        },
        {
            "role": "assistant",
            "content": "Title\nDescription\nIngredients List\nRecipe",
        },
        {
            "role": "user",
            "content": 'Which parts of the recipe will be changed if the user comment is "The ingredients are not correct, can you add oil as well"?',
        },
        {"role": "assistant", "content": "Ingredients List"},
        {
            "role": "user",
            "content": f'Which parts of the recipe will be changed if the user comment is "{comment}"?',
        },
    ]

    return call_llm(messages)


def modify_page_content(block_heading, old_block_content, comment):
    messages = [
        {
            "role": "system",
            "content": """You are a recipe editor. You will update an old recipe based on the user comment and part of recipe to be edited.\n
            Follow these rules strictly:\n
            1. Only edit the part of recipe specified.\n
            2. Do not use bullets, numbered lists and symbols while generating the text. \n
            3. Only return the modified content without headers and additional text.\n""",
        },
        {
            "role": "user",
            "content": """The current content in "Ingredients List" is "Chicken\nPepper". 
            Modify the "Ingredients List" according to user comment that says "The ingredients are not correct, can you add salt as well\"""",
        },
        {"role": "assistant", "content": "Chicken\nPepper\nSalt"},
        {
            "role": "user",
            "content": 'The current content in "Recipe" is "Cut fish into bite-sized pieces.\\nHeat a pan over medium heat. Add oil.\\nWhen the oil is hot, add ginger and garlic. Sauté until fragrant.\\nAdd fish to the pan. Cook until browned on all sides.\\nAdd red chili powder and salt. Stir well to combine.\\nServe stir-fried fish over rice or noodles. Enjoy!". Modify the "Recipe" according to user comment that says "I want in detail steps for the recipe"',
        },
        {
            "role": "assistant",
            "content": "Cut fish into bite-sized pieces and set aside.\n\nHeat a pan over medium heat. Once the pan is hot, add oil to coat the bottom of the pan evenly.\n\nWhen the oil is hot, add ginger and garlic to the pan. Sauté them until they become fragrant, about 30 seconds to 1 minute.\n\nAdd the prepared fish to the pan. Cook the fish on one side until it becomes browned, about 3-5 minutes. Once the fish is browned, flip it to cook the other side for an additional 3-5 minutes.\n\nAfter the fish is cooked through, add red chili powder and salt to the pan. Stir the spices into the fish until they are evenly distributed.\n\nServe stir-fried fish over rice or noodles. Enjoy your meal!",
        },
        {
            "role": "user",
            "content": 'The current content in "Title" is "Chicken Onion Bread". Modify the "Title" according to user comment that says "I want to make this dish using pork instead of chicken"',
        },
        {"role": "assistant", "content": "Pork Onion Bread"},
        {
            "role": "user",
            "content": '''The current content in "Description" is "Chicken Onion Bread is a satisfying sandwich made with cooked chicken, 
            sliced onions, and toasted bread. Layer the ingredients on a slice, add your favorite condiments and optional veggies, 
            then top with another piece of bread. It\'s an easy, customizable meal that combines protein and crunch for a delightful bite.". 
            Modify the "Description" according to user comment that says "I want to make this dish using pork instead of chicken"''',
        },
        {
            "role": "assistant",
            "content": "Pork Onion Bread is a satisfying sandwich made with cooked pork, sliced onions, and toasted bread. Layer the ingredients on a slice, add your favorite condiments and optional veggies, then top with another piece of bread. It's an easy, customizable meal that combines protein and crunch for a delightful bite. Substitute pork for chicken to create a delicious variation of this sandwich.",
        },
        {
            "role": "user",
            "content": f"The current content in '{block_heading}' is '{old_block_content}'. Modify the '{block_heading}' according to user comment that says '{comment}'.",
        },
    ]

    return call_llm(messages)


def update_recipe_title(page_id, new_title, new_cover, new_emoji):
    try:
        data = {
            "properties": {"title": [{"text": {"content": new_title.strip()}}]},
            "cover": {"external": {"url": new_cover}},
            "icon": {"emoji": new_emoji},
        }

        response = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=notion_headers,
            json=data,
        )

        logging.info("Title updated on Notion")

    except requests.RequestException as e:
        logging.error(f"Error updating recipe title: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while updating recipe title: {e}")


def update_recipe_description(new_description):
    try:
        description_block_id = recipe_page_block_ids[1]
        logging.info(f"block id: {description_block_id}")

        data = {
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": new_description.strip()},
                    }
                ]
            }
        }
        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{description_block_id}",
            headers=notion_headers,
            json=data,
        )

        logging.info("Description updated on Notion")

    except requests.RequestException as e:
        logging.error(f"Error updating recipe description: {e}")
    except Exception as e:
        logging.error(
            f"Unexpected error occurred while updating recipe description: {e}"
        )


def update_ingredients_list(page_id, new_ingredients_list, indices_heading_blocks):
    try:
        for index in range(indices_heading_blocks[1] + 1, indices_heading_blocks[2]):
            response = requests.delete(
                f"https://api.notion.com/v1/blocks/{recipe_page_block_ids[index]}",
                headers=notion_headers,
            )
            logging.info(f"Block with id {recipe_page_block_ids[index]} deleted.")

        ingredients = new_ingredients_list.split("\n")
        logging.info(ingredients)

        data = {"children": [], "after": recipe_page_heading_block_ids[1]}

        for ingredient in ingredients:
            data["children"].append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": ingredient.strip()},
                            }
                        ]
                    },
                },
            )

        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=notion_headers,
            json=data,
        )

        logging.info("New ingredients blocks added")

    except requests.RequestException as e:
        logging.error(f"Error updating ingredients list: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while updating ingredients list: {e}")


def update_recipe_steps(page_id, new_recipe, indices_heading_blocks):
    try:
        for index in range(indices_heading_blocks[2] + 1, len(recipe_page_block_ids)):
            response = requests.delete(
                f"https://api.notion.com/v1/blocks/{recipe_page_block_ids[index]}",
                headers=notion_headers,
            )
            logging.info(f"Block with id {recipe_page_block_ids[index]} deleted.")

        recipe_steps = new_recipe.split("\n")
        cleaned_steps = []

        for step in recipe_steps:
            if step.strip():
                cleaned_steps.append(step)

        logging.info(cleaned_steps)

        data = {"children": [], "after": recipe_page_heading_block_ids[2]}

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

        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=notion_headers,
            json=data,
        )

        logging.info("New recipe steps added")

    except requests.RequestException as e:
        logging.error(f"Error updating recipe steps: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while updating recipe steps: {e}")


def main(page, comment):
    try:
        pagetitle_pageid_data = get_page_data()
        page_id = pagetitle_pageid_data[page]
        available_recipes()

        notion_blocks_to_modify = notion_blocks_to_modify(comment).split("\n")

        logging.info(f"Content area to modify: {notion_blocks_to_modify}")

        old_recipe_blocks_content = get_page_content(page_id, page)

        logging.info(f"Block Ids: {recipe_page_block_ids}")
        logging.info(f"Heading block ids: {recipe_page_heading_block_ids}")

        indices_heading2_blocks = []
        for heading2_block_id in recipe_page_heading_block_ids:
            indices_heading2_blocks.append(
                recipe_page_block_ids.index(heading2_block_id)
            )
        logging.info(indices_heading2_blocks)

        for notion_block in notion_blocks_to_modify:
            new_content = modify_page_content(
                notion_block, old_recipe_blocks_content[notion_block], comment
            )

            logging.info(new_content)

            if notion_block == "Title":
                new_emoji = get_emoji(new_content)
                new_cover = get_cover_image(new_content)
                update_recipe_title(page_id, new_content, new_cover, new_emoji)
            elif notion_block == "Description":
                update_recipe_description(new_content)
            elif notion_block == "Ingredients List":
                update_ingredients_list(page_id, new_content, indices_heading2_blocks)
            elif notion_block == "Recipe":
                update_recipe_steps(page_id, new_content, indices_heading2_blocks)

    except Exception as e:
        logging.error(f"Unexpected error in cleanup main function: {e}")


if __name__ == "__main__":
    fire.Fire(main)
