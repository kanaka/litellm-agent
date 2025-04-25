#!/usr/bin/env python3

from litellm import completion
from pprint import pprint

debug = False
model = "github_copilot/gpt-4"
extra_headers = {"editor-version": "vscode/1.85.1"}

def main():
    print("Simple Litellm Agent (Ctrl-C to quit)")
    messages = [{"content": "You are an advanced coding agent", "role":"system"}]
    while True:
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
            messages=messages)
        if debug:
            print("AI response full JSON:")
            pprint(response.model_dump())
        resp_message = response.choices[0].message
        print(f"\u001b[93m{model}\u001b[0m> {resp_message.content}")
        messages.append(resp_message.model_dump())

main()
