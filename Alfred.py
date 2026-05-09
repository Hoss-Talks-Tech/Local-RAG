import json
from pathlib import Path
import ollama
import fitz  # pymupdf
from rich.console import Console
from rich.markdown import Markdown

# ── Spinner ────────────────────────────────────────────────
import random
import itertools
import threading
import time
# ── Config ────────────────────────────────────────────────
MODEL = "llama3.2"          # change to qwen3 or gemma later
HISTORY_TURNS = 10          # how many past messages to include
MAX_FILE_CHARS = 3000       # characters to read per file

MEMORY_DIR = Path("memory")
CONTEXT_DIR = Path("context")
HISTORY_FILE = MEMORY_DIR / "history.jsonl"
SUMMARY_FILE = MEMORY_DIR / "summary.md"


SPINNER_VERBS = [
    "Thinking",
    "Brewing",
    "Simmering",
    "Crunching",
    "Untangling",
    "Connecting dots",
    "Reading the room",
    "Summoning context",
    "Polishing answer",
    "Debugging the universe",
]

console = Console()

# ── Helpers ───────────────────────────────────────────────
def load_summary() -> str:
    if SUMMARY_FILE.exists():
        return SUMMARY_FILE.read_text().strip()
    return ""


def load_recent_history(n: int) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []

    lines = HISTORY_FILE.read_text().strip().splitlines()
    turns = [json.loads(l) for l in lines if l]
    return turns[-n:]  # keep only last n messages


def save_turn(role: str, content: str):
    HISTORY_FILE.parent.mkdir(exist_ok=True)

    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps({"role": role, "content": content}) + "\n")


def extract_text_from_file(path: Path) -> str:
    if path.suffix == ".pdf":
        doc = fitz.open(path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
    else:
        text = path.read_text(errors="ignore")

    return text[:MAX_FILE_CHARS]


def load_context_files(query: str) -> str:
    """Load all files in context/ — simple version (no vector search needed at this scale)."""
    if not CONTEXT_DIR.exists():
        return ""

    parts = []

    for f in CONTEXT_DIR.iterdir():
        if f.suffix in {".py", ".ts", ".js", ".md", ".txt", ".pdf", ".json"}:
            content = extract_text_from_file(f)
            parts.append(f"--- {f.name} ---\n{content}")

    return "\n\n".join(parts)


def build_system_prompt(summary: str, context_files: str) -> str:
    parts = ["You are a helpful assistant with memory of the current project."]

    if summary:
        parts.append(f"\n## Project summary\n{summary}")

    if context_files:
        parts.append(f"\n## Context files\n{context_files}")

    return "\n".join(parts)

def loading_spinner(stop_event: threading.Event) -> None:
    spinner_frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    verbs = SPINNER_VERBS.copy()
    random.shuffle(verbs)
    verb_index = 0

    current_verb = verbs[verb_index]
    last_change = time.time()

    while not stop_event.is_set():
        now = time.time()

        if now - last_change > 1.2:
            verb_index += 1

            if verb_index >= len(verbs):
                random.shuffle(verbs)
                verb_index = 0

            current_verb = verbs[verb_index]
            last_change = now

        frame = next(spinner_frames)
        ORANGE = "\033[38;2;217;119;87m"
        RESET = "\033[0m"
        CLEAR_LINE = "\033[K"


        print(f"\r{CLEAR_LINE}{ORANGE}{frame}{RESET}{ORANGE} {current_verb}...", end="", flush=True)
        time.sleep(0.1)

    print("\r" + " " * 80 + "\r", end="", flush=True)

# ── Main loop ─────────────────────────────────────────────
def chat():
    MEMORY_DIR.mkdir(exist_ok=True)
    CONTEXT_DIR.mkdir(exist_ok=True)

    console.print("[bold green]AI assistant ready.[/bold green] Type [bold]/quit[/bold] to exit, [bold]/clear[/bold] to reset history.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input == "/quit":
            break

        if user_input == "/clear":
            HISTORY_FILE.unlink(missing_ok=True)
            console.print("[yellow]History cleared.[/yellow]\n")
            continue

        # Build context
        summary = load_summary()
        history = load_recent_history(HISTORY_TURNS)
        context_files = load_context_files(user_input)
        system = build_system_prompt(summary, context_files)

        # Assemble messages
        messages = [{"role": "system", "content": system}]
        messages += history
        messages.append({"role": "user", "content": user_input})

        # Call Ollama
        stop_spinner = threading.Event()

        spinner_thread = threading.Thread(
        target=loading_spinner,
        args=(stop_spinner,)
        )

        spinner_thread.start()

        try:
            response = ollama.chat(
            model=MODEL,
            messages=messages
        )
        finally:
            stop_spinner.set()
            spinner_thread.join()
        
        reply = response["message"]["content"]

        # Save turn
        save_turn("user", user_input)
        save_turn("assistant", reply)

        # Display
        console.print("\n[bold cyan]Assistant:[/bold cyan]")
        console.print(Markdown(reply))
        console.print()


if __name__ == "__main__":
    chat()
