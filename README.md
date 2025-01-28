# MCP-RoCQ (Coq Reasoning Server)

# Currently shows tools but Claude can't use it properly for some reason- invalid syntax generally seems the issue but there could be something else.

There may be a better way to set this up with the coq cli or something.
Anyone want to try and fix it who knows what they are doing would be great.

MCP-RoCQ is a Model Context Protocol server that provides advanced logical reasoning capabilities through integration with the Coq proof assistant. It enables automated dependent type checking, inductive type definitions, and property proving with both custom tactics and automation.

## Features

- **Automated Dependent Type Checking**: Verify terms against complex dependent types
- **Inductive Type Definition**: Define and automatically verify custom inductive data types
- **Property Proving**: Prove logical properties using custom tactics and automation
- **XML Protocol Integration**: Reliable structured communication with Coq
- **Rich Error Handling**: Detailed feedback for type errors and failed proofs

## Installation

1. Install the Coq Platform 8.19 (2024.10)

Coq is a formal proof management system. It provides a formal language to write mathematical definitions, executable algorithms and theorems together with an environment for semi-interactive development of machine-checked proofs.

[https://github.com/coq/platform](https://github.com/coq/platform)

2. Clone this repository:

```bash
git clone https://github.com/angrysky56/mcp-rocq.git
```

cd to the repo

```bash
uv venv
./venv/Scripts/activate
uv pip install -e .
```

# JSON for the Claude App or mcphost config- set your paths according to how you installed coq and the repository.

```json
    "mcp-rocq": {
      "command": "uv",
      "args": [
        "--directory",
        "F:/GithubRepos/mcp-rocq",
        "run",
        "mcp_rocq",
        "--coq-path",
        "F:/Coq-Platform~8.19~2024.10/bin/coqtop.exe",
        "--lib-path",
        "F:/Coq-Platform~8.19~2024.10/lib/coq"
      ]
    },
```


# This might work- I got it going with uv and most of this could be hallucinatory though:

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The server provides three main capabilities:

### 1. Type Checking

```python
{
    "tool": "type_check",
    "args": {
        "term": "<term to check>",
        "expected_type": "<type>",
        "context": ["relevant", "modules"] 
    }
}
```

### 2. Inductive Types

```python
{
    "tool": "define_inductive",
    "args": {
        "name": "Tree",
        "constructors": [
            "Leaf : Tree",
            "Node : Tree -> Tree -> Tree"
        ],
        "verify": true
    }
}
```

### 3. Property Proving

```python
{
    "tool": "prove_property",
    "args": {
        "property": "<statement>",
        "tactics": ["<tactic sequence>"],
        "use_automation": true
    }
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
