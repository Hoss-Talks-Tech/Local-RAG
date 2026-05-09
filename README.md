Local RAG Assistant with Persistent Memory
This is a private, terminal-based assistant that doesn't just chat—it remembers. 
It is built using Ollama and RAG, it allows you to chat with your local documents while maintaining a persistent conversation history.

---

## Features
- ** Persistent Memory: Saves every conversation to a local `history.jsonl` file.
- ** 100% Private: Everything runs locally on your machine. No API keys, no data leaks.
- ** Rich Terminal UI: Beautifully formatted responses and a custom "thinking" spinner.

---

## Setup

### 1. Prerequisites
Make sure you have [Ollama](https://ollama.com) installed and running.
    
### 2. Folders
Create these folders if they don't exist:

- memory/: Where your history is stored. AND you need to create a markdown file (summary.md) to tell the AI what your project is all about and what you want to achieve. 
- context/: Place your PDFs or code files here for the AI to read.

//////////////////////////////////////////////////////////////////////////////////////////////////////
