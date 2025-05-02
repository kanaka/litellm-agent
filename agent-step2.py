#!/usr/bin/env python3

from litellm import completion

model = "github_copilot/o3-mini"
#model = "github_copilot/gpt-4"
extra_headers = {"editor-version": "vscode/1.85.1"}

messages = [{"content": "You are a coding agent", "role":"system"}]

while True:
    try:
        user_input = input("user> ")
    except EOFError as e:
        break
    messages.append({"content": user_input, "role":"user"})

    response = completion(
        model=model,
        extra_headers=extra_headers,
        messages=messages,
    )

    resp_message = response.choices[0].message
    messages.append(resp_message.model_dump())

    print(f"assistant> {resp_message.content}")
