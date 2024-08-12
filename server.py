import logging.config
from typing import List
from pydantic import BaseModel
import logging
from cleanup import get_parent_page_data
from main import main as add_recipe_to_notion
from cleanup import main as update_recipe_contents

from tuneapi import types as tt
from tuneapi import utils as tu
from tuneapi import apis as ta

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(level=logging.INFO)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
PARENT_PAGE_ID = "2dd7d0fcd8ef4653a0f32e55bc01a481"
MODEL_ID = "gpt-3.5-turbo"


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    temperature: float
    max_tokens: int = 1024
    stream: bool = False


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    choices: List[ChatCompletionResponseChoice]


def find_recipes(recipe_pages_data):
    recipe_titles = list(recipe_pages_data.keys())
    logging.info(recipe_titles)

    return recipe_titles


def add_recipe(ingredient):
    add_recipe_to_notion(ingredient)


def update_recipe(page, comment):
    update_recipe_contents(page, comment)


recipe_pages_data = get_parent_page_data()
recipe_titles = find_recipes(recipe_pages_data)


find_recipes_tool = tt.Tool(
    name="find_recipes",
    description="find recipes available on a Notion page based on user input",
    parameters=[
        tt.Tool.Prop(
            "ingredient",
            "Ingredients available to choose a recipe",
            "string",
            required=True,
        )
    ],
)
logging.info(find_recipes_tool)


add_recipe_tool = tt.Tool(
    name="add_recipe",
    description="create and add a recipe to Notion page based on user inputted ingredients",
    parameters=[
        tt.Tool.Prop(
            "ingredient",
            "Ingredients for creating a recipe",
            "string",
            required=True,
        )
    ],
)
logging.info(add_recipe_tool)

update_recipe_tool = tt.Tool(
    name="update_recipe",
    description="update the parts of the recipe according to user comment",
    parameters=[
        tt.Tool.Prop("page title", "Page title of the recipe to be updated", "string"),
        tt.Tool.Prop("comment", "User comment for updating recipe", "string"),
    ],
)
logging.info(update_recipe_tool)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, data: ChatCompletionRequest):
    # API validations
    if data.temperature < 0.0 or data.temperature > 1.0:
        raise HTTPException(400, "Temperature must be between 0 and 1")

    # call the model
    model = ta.Openai(MODEL_ID)
    model.set_api_token(os.getenv("OPENAI_KEY"))

    logging.info(data.messages)
    user_message = "\n".join(msg.content for msg in data.messages if msg.role == "user")
    thread = tt.Thread(
        tt.system(
            """You are a cookbook having access to a Notion page with recipes.
            You can do the following tasks:
            1. Find appropriate recipe titles from the Notion page based on the user input.
            2. Add a new recipe to the Notion page based on user inputted ingredients.
            3. Update parts of the recipe according to user comment in Notion.
            """
        ),
        tt.human(user_message),
        tools=[find_recipes_tool, add_recipe_tool, update_recipe_tool],
    )
    logging.info(thread)

    out = model.chat(thread)
    logging.info(out)

    function_call = tt.function_call(out)
    logging.info(function_call)

    if out["name"] == "find_recipes":
        thread.append(function_call)
        logging.info(thread)

        thread.append(tt.function_resp({"titles": recipe_titles}))
        logging.info(thread)
    elif out["name"] == "add_recipe":
        ingredients = out["arguments"]["ingredient"]

        thread.append(function_call)
        logging.info(thread)

        thread.append(tt.function_resp({"recipe": add_recipe(ingredients)}))
        logging.info(thread)
    elif out["name"] == "update_recipe":
        page_title = out["arguments"]["page title"]
        user_comment = out["arguments"]["comment"]

        thread.append(function_call)
        logging.info(thread)

        thread.append(
            tt.function_resp(
                {"updated recipe": update_recipe(page_title, user_comment)}
            )
        )
        logging.info(thread)

    # return the response
    if data.stream:
        stream_resp = model.stream_chat(
            thread,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )
        api_resp = tu.generator_to_api_events(
            model=MODEL_ID,
            generator=stream_resp,
        )
        return StreamingResponse(api_resp, media_type="text/event-stream")
    else:
        output = model.chat(thread)
        logging.info(output)
        response = ChatCompletionResponse(
            id=f"chatcmpl-{tu.get_snowflake()}",
            object="chat.completion",
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(content=str(output), role="assistant"),
                    finish_reason="stop",
                )
            ],
        )
        return response


@app.post("/")
async def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
