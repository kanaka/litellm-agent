#!/usr/bin/env python3

import inspect
import json
from litellm import completion
from pprint import pprint
import subprocess

debug = False
model = "github_copilot/gpt-4"
extra_headers = {"editor-version": "vscode/1.85.1"}


def get_tools_param(tools_map):
    typemap = {int: "integer", float: "number", bool: "boolean"}
    tools = []
    for name, fn in tools_map.items():
        props, req = {}, []
        for p in inspect.signature(fn).parameters.values():
            if p.kind.name.startswith("VAR"):  # skip *args/**kw
                continue
            props[p.name] = {"type": typemap.get(p.annotation, "string")}
            if p.default is p.empty:
                req.append(p.name)
        tools.append({
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": (fn.__doc__ or "").strip(),
                "parameters": {
                    "type": "object",
                    "properties": props,
                    **({"required": req} if req else {})
                }
            }
        })
    return tools

def read_file(path):
    """Read the contents of a file at path and return as a string"""
    return json.dumps(open(path).read())

def ls_dir(path):
    """Run `ls -la path` and returns map with 'stdout', 'stderr', and 'returncode'"""
    cp = subprocess.run(["ls", "-la", path], capture_output=True, text=True)
    res = {k: getattr(cp, k) for k in ('stdout', 'stderr', 'returncode')}
    return json.dumps(res)

TOOLS_MAP = {
    "read_file": read_file,
    "ls_dir": ls_dir,
}

def main():
    print("Simple Litellm Agent (Ctrl-C to quit)")
    messages = [{"content": "You are an advanced coding agent", "role":"system"}]
    tools = get_tools_param(TOOLS_MAP)

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
                if fn.name in TOOLS_MAP:
                    fn_args = json.loads(fn.arguments)
                    print(f"\u001b[92mtool_call\u001b[0m> {fn.name}({fn_args})")
                    fn_result = TOOLS_MAP[fn.name](**fn_args)
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
