#!/usr/bin/env python3

import json
from litellm import completion
from pprint import pprint

debug = False
model = "github_copilot/gpt-4"
extra_headers = {"editor-version": "vscode/1.85.1"}

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Return the contents of a file at the given relative path. Use this to get regular file contents but do not use it with directory names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"]
            },
        },
    }
]

def read_file(path):
    return open(path).read()


def main():
    print("Simple Litellm Agent (Ctrl-C to quit)")
    messages = [{"content": "You are an advanced coding agent", "role":"system"}]
    while True:
        if messages[-1]["role"] != "tool":
            try:
                user_input = input("\u001b[94myou\u001b[0m> ")
            except EOFError as e:
                break
            messages.append({"content": user_input, "role":"user"})

        if debug:
            print("Sending messages full JSON:")
            pprint(messages)
        response = completion(
            model=model,
            extra_headers=extra_headers,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        if debug:
            print("AI response full JSON:")
            pprint(response.model_dump())

        resp_message = response.choices[0].message
        messages.append(resp_message.model_dump())

        tool_calls = resp_message.tool_calls
        if tool_calls:
            for tc in tool_calls:
                fn = tc['function']
                print(f"\u001b[92mtool_call:\u001b[0m> {fn.model_dump()}")
                if fn.name == "read_file":
                    fn_args = json.loads(fn.arguments)
                    fn_result = read_file(**fn_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc['id'],
                        "name": fn.name,
                        "content": fn_result,
                    })
                else:
                    raise Exception(f"Unknown tool call: {fn.name}")
        else:
            print(f"\u001b[93m{model}\u001b[0m> {resp_message.content}")

main()
