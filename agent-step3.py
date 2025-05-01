#!/usr/bin/env python3

import json
from litellm import completion

model = "github_copilot/gpt-4"
#model = "github_copilot/o3-mini"
extra_headers = {"editor-version": "vscode/1.85.1"}

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the file at path. Returns a map {'content':content}",
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

def trunc(s, max=80):
    return s[:max-4] + '...' if len(s) >= max else s

messages = [{"content": "You are a coding agent", "role":"system"}]

while True:
    if messages[-1]["role"] != "tool":
        try:
            user_input = input("user> ")
        except EOFError as e:
            break

        messages.append({"content": user_input, "role":"user"})

    response = completion(
        model=model,
        extra_headers=extra_headers,
        messages=messages,
        tools=tools,
    )

    resp_message = response.choices[0].message
    messages.append(resp_message.model_dump())

    tool_calls = resp_message.tool_calls
    if not tool_calls:
        print(f"assistant> {resp_message.content}")
        continue

    for tc in tool_calls:
        fn = tc['function']
        if fn.name == "read_file":
            fn_args = json.loads(fn.arguments)
            print(trunc(f"calling read_file({fn_args})"))
            fn_result = {"content": open(**fn_args).read()}
            res_str = json.dumps(fn_result)"
            print(trunc(f"result: {res_str}"))
            messages.append({
                "role": "tool",
                "tool_call_id": tc['id'],
                "name": fn.name,
                "content": res_str,
            })
        else:
            raise Exception(f"Unknown tool call: {fn.name}")
