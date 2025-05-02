#!/usr/bin/env python3

from litellm import completion
import sys

model = "github_copilot/o3-mini"
#model = "github_copilot/gpt-4"
extra_headers = {"editor-version": "vscode/1.85.1"}

response = completion(
    model=model,
    extra_headers=extra_headers,
    messages=[{"content": sys.argv[1], "role":"user"}],
)

print(response.choices[0].message.content)
