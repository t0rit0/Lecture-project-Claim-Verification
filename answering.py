import openai
from googleapiclient.discovery import build
import pprint
import os
import re
from prompts_library import openai_google_search_tool_description, GoogleSearchAgentSystemPrompt
import json
from functools import wraps
from typing import Callable
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI()


# decorator to form tool call result message
def tool(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(tool_input: ChatCompletionMessageToolCall) -> dict:
        # Validate the input structure
        if not isinstance(tool_input, ChatCompletionMessageToolCall):
            raise ValueError("Input must be a dictionary containing 'tool_calls'.")

        # function_call_id = tool_input.id
        # function_call = tool_input.function
        function_arguments = json.loads(tool_input.function.arguments)

        # Call the original function with extracted arguments
        result = func(**function_arguments)

        function_arguments["tool_output"] = result

        # Format the result into the required message structure
        function_call_result_message = {
            "role": "tool",
            "content": json.dumps(function_arguments),
            "tool_call_id": tool_input.id,
        }

        return function_call_result_message
    return wrapper


@tool
def google_search(search_term, num_results):
    """
    search your search_term on google and return the top num_results results
    Args:
        search_term (str): the term you want to search on google
        num_results (int): the number of results you want to return
    Returns:
        results(list): a list of dictionaries containing the search results and their links, titles, and snippets
    """
    # print(f"[DEBUG] search with term: {search_term}, num_results: {num_results}")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    service = build("customsearch", "v1", developerKey=google_api_key)
    # res = service.cse().list(q=search_term, cx=google_cse_id, **kwargs).execute()
    search_res = service.cse().list(q=search_term, cx=google_cse_id, num=num_results).execute()
    # res = [{"link": item["link"], "title": item["title"], "snippet": item["snippet"]} for item in search_res["items"]]
    res = [{"title": item["title"], "snippet": item["snippet"]} for item in search_res["items"]]
    # print(type(res))
    return res

class GoogleChatAgent:
    tools = {"google_search": google_search}
    tools_description = [openai_google_search_tool_description]


    def __init__(self, system_prompt=GoogleSearchAgentSystemPrompt, temperature=0.7, max_tokens=1024):
        self.system = system_prompt
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system_prompt})
        self.temperature = temperature
        self.max_tokens = max_tokens

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})

        # while True:
        for _ in range(10):
            response = self.execute()
            content = response.content
            tool_calls = response.tool_calls
            # if content:
            #     self.messages.append({"role": "assistant", "content": content})

            self.messages.append(response.to_dict(exclude_none=True))
            if content and "END" in content:
                return re.sub(r'<\*\*END\*\*>', '', content)

            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    # print(f"[DEBUG] calling tool: {tool_name}")
                    # print(f"[DEBUG] tool_call: {tool_call.to_dict(exclude_none=True)}")

                    tool_output_message = self.tools[tool_name](tool_call)

                    self.messages.append(tool_output_message)
                    # self.show_messages()
                continue
            # break
        return "Sorry, I can not help you with that."

    def execute(self):
        completion = client.chat.completions.create(
                        model="gpt-3.5-turbo", 
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        messages=self.messages,
                        tools=self.tools_description)
        return completion.choices[0].message
    
    def show_messages(self):
        print("Messages:")
        for message in self.messages:
            if message["role"] == "system":
                continue
            pprint.pprint(message)
            print("-"*10)
            # print(message["role"])
            # if message.get("content"):
            #     pprint.pprint(message["content"])
            # if message.get("tool_calls"):
            #     pprint.pprint(message["tool_calls"])
    
    def memory_length(self):
        return len(self.messages)

    def extend_messages(self, messages):
        self.messages.extend(messages)
    
    def cut_messages(self, remain_count):
        if remain_count >= len(self.messages) or remain_count <= 0:
            raise ValueError("remain_count should be less than the total number of messages and greater than 0")
        cut = self.messages[remain_count:]
        self.messages = self.messages[:remain_count]
        return cut
    
    def reset_messages(self):
        self.messages = self.messages[0:1]

    

if __name__ == "__main__":

    # bot = GoogleChatAgent()
    # bot("How to properly setup docker desktop on a new pc with win11")
    # bot.show_messages()




    k = ChatCompletionMessageToolCall(
        id="1234", 
        function=Function(
            name="google_search",
            arguments='{"search_term": "How to install Python on Windows", "num_results": 2}'
        ),
        type="function"
    )
    # res = google_search("How to install Python on Windows", 5)
    res = google_search(k)
    pprint.pprint(res)