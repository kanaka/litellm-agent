#!/usr/bin/env python3

import inspect
import json
from litellm import completion
import subprocess

model = "github_copilot/o3-mini"
#model = "github_copilot/gpt-4"
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
                "name": name,
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
    """Read the file at path.
    Returns a map {'content':content} (raw file string in content)"""
    return {"content": open(path).read()}

def ls_dir(path):
    """Runs `ls -la path` to list files in the current directory.
    Returns a map {'stdout':stdout,'stderr':stderr,'returncode':code}"""
    cp = subprocess.run(["ls", "-la", path], capture_output=True, text=True)
    res = {k: getattr(cp, k) for k in ('stdout', 'stderr', 'returncode')}
    return res

def edit_file(path, match, replace):
    """Edit the file at 'path' replacing the first occurence of
    'match' string with 'replace' string. 'match' and 'replace' are
    raw strings and should not have escaped newlines, backslashes, etc.
    Returns an empty map on success"""
    orig = open(path).read()
    new = orig.replace(match, replace, 1)
    if new == orig: raise Exception("match string not found")
    open(path, "w").write(new)
    return {}

def create_file(path, content):
    """Create (or replace) file at 'path' with 'content'.
    'content' is a raw string and does not need extra escaping.
    Returns an empty map on success"""
    open(path, "w").write(content)
    return {}

TOOLS_MAP = {
    "read_file": read_file,
    "ls_dir": ls_dir,
    "edit_file": edit_file,
    "create_file": create_file,
}

def trunc(s, max=80):
    return s[:max-4] + '...' if len(s) >= max else s

messages = [{"content": "You are a coding agent", "role":"system"}]
tools = get_tools_param(TOOLS_MAP)

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
        if fn.name in TOOLS_MAP:
            fn_args = json.loads(fn.arguments)
            print(trunc(f"tool call> {fn.name}({fn_args})"))
            try:
                fn_result = TOOLS_MAP[fn.name](**fn_args)
            except Exception as e:
                fn_result = {"error": str(e)}
            res_str = json.dumps(fn_result)
            print(trunc(f"tool result> {res_str}"))
            messages.append({
                "role": "tool",
                "tool_call_id": tc['id'],
                "name": fn.name,
                "content": res_str,
            })
        else:
            raise Exception(f"Unknown tool call: {fn.name}")
