import os
import re
import subprocess
import threading
from pathlib import Path

import requests
from dotenv import load_dotenv

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"

BASE_DIR = Path(__file__).resolve().parent
LEARNING_DIR = BASE_DIR / "learning"
LEARNING_DIR.mkdir(exist_ok=True)


# ============================================================
# AI LESSON GENERATION
# ============================================================

def generate_lesson(topic):
    """Generate a software engineering lesson using OpenRouter."""

    if not API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY was not found.\n\n"
            "Make sure your .env file contains:\n"
            "OPENROUTER_API_KEY=your_key_here"
        )

    prompt = f"""
Create a detailed but beginner-friendly software engineering lesson about:

{topic}

The goal is to help a software engineering student genuinely learn the topic.

Use exactly this structure:

# Topic Title

## 1. What is it?

Explain the concept clearly from the beginning.

## 2. Why does it matter?

Explain why software engineers need to understand it and where it is used.

## 3. How does it work?

Explain the underlying idea step by step.

## 4. Practical Example

Give a realistic software engineering example.
Include code when appropriate.

## 5. Common Mistakes

Explain mistakes beginners commonly make and how to avoid them.

## 6. Engineering Insight

Give deeper engineering lessons that a student should understand beyond memorizing definitions.

## 7. Practice

Give 3 practical exercises:
- Beginner
- Intermediate
- Challenge

## 8. Key Takeaways

Give a concise list of the most important things to remember.

Requirements:

- Write for a software engineering student.
- Explain technical terms when first introduced.
- Prefer practical understanding over memorization.
- Use Python examples when code is useful.
- Do not mention that an AI generated the lesson.
- Make the lesson useful for actual software engineering study.
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Software Engineering Learning Journal",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an experienced software engineering teacher. "
                    "Teach clearly, practically, and accurately."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.7,
        "max_tokens": 5000,
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code != 200:
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get(
                "message",
                response.text,
            )
        except Exception:
            error_message = response.text

        raise RuntimeError(
            f"OpenRouter request failed.\n\n"
            f"Status: {response.status_code}\n"
            f"Message: {error_message}"
        )

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(
            "The AI response did not contain a lesson."
        )

    if not content.strip():
        raise RuntimeError("The AI returned an empty lesson.")

    return content.strip()


# ============================================================
# FILE HELPERS
# ============================================================

def make_slug(text):
    """Convert text into a filename-friendly slug."""

    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    if not slug:
        slug = "lesson"

    return slug


def extract_title(lesson):
    """Extract the first Markdown H1 title."""

    for line in lesson.splitlines():
        line = line.strip()

        if line.startswith("# "):
            return line[2:].strip()

    return "Software Engineering Lesson"


def save_lesson(lesson):
    """Save a lesson as a Markdown file."""

    title = extract_title(lesson)
    slug = make_slug(title)

    file_path = LEARNING_DIR / f"{slug}.md"

    counter = 2

    while file_path.exists():
        file_path = LEARNING_DIR / f"{slug}-{counter}.md"
        counter += 1

    file_path.write_text(
        lesson,
        encoding="utf-8",
    )

    return file_path


# ============================================================
# GIT HELPERS
# ============================================================

def run_git(*args):
    """Run a Git command inside the project directory."""

    result = subprocess.run(
        ["git", *args],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()

        raise RuntimeError(
            f"Git command failed:\n"
            f"git {' '.join(args)}\n\n"
            f"{error}"
        )

    return result.stdout.strip()


def check_git_repository():
    """Check whether this folder is a Git repository."""

    try:
        run_git("rev-parse", "--is-inside-work-tree")
        return True
    except Exception:
        return False


def get_current_branch():
    """Return the current Git branch."""

    return run_git(
        "branch",
        "--show-current",
    )


def get_git_remote():
    """Return the origin remote URL."""

    try:
        return run_git(
            "remote",
            "get-url",
            "origin",
        )
    except Exception:
        return "No origin remote configured"


def git_status():
    """Return a short Git status."""

    try:
        return run_git("status", "--short")
    except Exception:
        return "Git repository not available"


def commit_and_push(file_path):
    """Commit the lesson file and push it to the current branch."""

    if not check_git_repository():
        raise RuntimeError(
            "This folder is not a Git repository.\n\n"
            "Run 'git init' first."
        )

    branch = get_current_branch()

    if not branch:
        raise RuntimeError(
            "Could not determine the current Git branch."
        )

    remote = get_git_remote()

    if remote == "No origin remote configured":
        raise RuntimeError(
            "No GitHub remote named 'origin' is configured.\n\n"
            "Add your GitHub repository as the origin remote first."
        )

    relative_path = file_path.relative_to(BASE_DIR)

    # Only stage the generated lesson.
    run_git(
        "add",
        str(relative_path),
    )

    # Check whether there is actually something to commit.
    status = run_git(
        "status",
        "--short",
        "--",
        str(relative_path),
    )

    if not status:
        return (
            f"No new changes to commit.\n"
            f"Branch: {branch}"
        )

    title = extract_title(
        file_path.read_text(encoding="utf-8")
    )

    commit_message = (
        f"docs: add learning lesson - {title}"
    )

    run_git(
        "commit",
        "-m",
        commit_message,
    )

    run_git(
        "push",
        "origin",
        branch,
    )

    return (
        f"Successfully committed and pushed.\n\n"
        f"Branch: {branch}\n"
        f"File: {relative_path}\n"
        f"Commit: {commit_message}"
    )


# ============================================================
# GUI APPLICATION
# ============================================================

class LearningJournalApp:

    def __init__(self, root):
        self.root = root

        self.root.title(
            "Software Engineering Learning Journal"
        )

        self.root.geometry("1100x750")
        self.root.minsize(900, 650)

        self.current_lesson = ""
        self.current_file = None

        self.build_ui()
        self.update_git_info()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):

        # Main container
        main = ttk.Frame(self.root, padding=20)
        main.pack(
            fill="both",
            expand=True,
        )

        # ====================================================
        # HEADER
        # ====================================================

        title = ttk.Label(
            main,
            text="Software Engineering Learning Journal",
            font=("Segoe UI", 22, "bold"),
        )

        title.pack(
            anchor="w",
            pady=(0, 5),
        )

        subtitle = ttk.Label(
            main,
            text=(
                "Generate, study, save, commit, and push "
                "software engineering lessons."
            ),
            font=("Segoe UI", 10),
        )

        subtitle.pack(
            anchor="w",
            pady=(0, 20),
        )

        # ====================================================
        # TOPIC INPUT
        # ====================================================

        topic_label = ttk.Label(
            main,
            text="What do you want to learn?",
            font=("Segoe UI", 11, "bold"),
        )

        topic_label.pack(
            anchor="w",
        )

        topic_frame = ttk.Frame(main)
        topic_frame.pack(
            fill="x",
            pady=(5, 8),
        )

        self.topic_entry = ttk.Entry(
            topic_frame,
            font=("Segoe UI", 12),
        )

        self.topic_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7,
        )

        self.topic_entry.bind(
            "<Return>",
            lambda event: self.generate_clicked(),
        )

        # ====================================================
        # VERY VISIBLE ACTION BUTTONS
        # ====================================================

        action_frame = ttk.LabelFrame(
            main,
            text="Actions",
            padding=10,
        )

        action_frame.pack(
            fill="x",
            pady=(0, 12),
        )

        self.generate_button = ttk.Button(
            action_frame,
            text="✨ Generate Lesson",
            command=self.generate_clicked,
        )

        self.generate_button.pack(
            side="left",
            padx=(0, 10),
            ipady=5,
        )

        self.save_button = ttk.Button(
            action_frame,
            text="💾 Save Lesson",
            command=self.save_clicked,
        )

        self.save_button.pack(
            side="left",
            padx=(0, 10),
            ipady=5,
        )

        self.push_button = ttk.Button(
            action_frame,
            text="🚀 Commit & Push",
            command=self.push_clicked,
        )

        self.push_button.pack(
            side="left",
            padx=(0, 10),
            ipady=5,
        )

        self.clear_button = ttk.Button(
            action_frame,
            text="🗑 Clear",
            command=self.clear_lesson,
        )

        self.clear_button.pack(
            side="left",
            ipady=5,
        )

        # ====================================================
        # QUICK TOPICS
        # ====================================================

        quick_label = ttk.Label(
            main,
            text="Quick topics:",
            font=("Segoe UI", 10, "bold"),
        )

        quick_label.pack(
            anchor="w",
            pady=(0, 5),
        )

        quick_frame = ttk.Frame(main)
        quick_frame.pack(
            fill="x",
            pady=(0, 12),
        )

        quick_topics = [
            "REST APIs",
            "Git Branching",
            "Database Indexing",
            "Docker",
            "Caching",
            "Authentication",
            "System Design",
            "Clean Code",
            "Testing",
            "Data Structures",
            "SQL Joins",
            "OOP",
        ]

        for index, topic in enumerate(quick_topics):

            button = ttk.Button(
                quick_frame,
                text=topic,
                command=lambda t=topic: self.set_topic(t),
            )

            button.grid(
                row=index // 6,
                column=index % 6,
                padx=3,
                pady=3,
                sticky="ew",
            )

        for column in range(6):
            quick_frame.columnconfigure(
                column,
                weight=1,
            )

        # ====================================================
        # LESSON AREA
        # ====================================================

        lesson_label = ttk.Label(
            main,
            text="Lesson",
            font=("Segoe UI", 11, "bold"),
        )

        lesson_label.pack(
            anchor="w",
            pady=(0, 5),
        )

        self.lesson_text = ScrolledText(
            main,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True,
        )

        self.lesson_text.pack(
            fill="both",
            expand=True,
        )

        # ====================================================
        # STATUS
        # ====================================================

        status_frame = ttk.Frame(main)
        status_frame.pack(
            fill="x",
            pady=(10, 0),
        )

        self.status_label = ttk.Label(
            status_frame,
            text="Ready.",
        )

        self.status_label.pack(
            side="left",
        )

        self.git_label = ttk.Label(
            status_frame,
            text="Checking Git...",
        )

        self.git_label.pack(
            side="right",
        )

    # --------------------------------------------------------
    # UI HELPERS
    # --------------------------------------------------------

    def set_status(self, message):
        self.root.after(
            0,
            lambda: self.status_label.config(
                text=message
            ),
        )

    def set_topic(self, topic):
        self.topic_entry.delete(
            0,
            tk.END,
        )

        self.topic_entry.insert(
            0,
            topic,
        )

    def get_lesson_text(self):
        return self.lesson_text.get(
            "1.0",
            tk.END,
        ).strip()

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    def generate_clicked(self):

        topic = self.topic_entry.get().strip()

        if not topic:
            messagebox.showwarning(
                "Missing Topic",
                "Enter a software engineering topic first.",
            )

            return

        self.generate_button.config(
            state="disabled",
        )

        self.set_status(
            f"Generating lesson about {topic}..."
        )

        thread = threading.Thread(
            target=self.generate_worker,
            args=(topic,),
            daemon=True,
        )

        thread.start()

    def generate_worker(self, topic):

        try:

            lesson = generate_lesson(topic)

            self.root.after(
                0,
                lambda: self.display_lesson(lesson),
            )

            self.set_status(
                "Lesson generated. Read it, then save or push it."
            )

        except Exception as error:

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Generation Error",
                    str(error),
                ),
            )

            self.set_status(
                "Generation failed."
            )

        finally:

            self.root.after(
                0,
                lambda: self.generate_button.config(
                    state="normal",
                ),
            )

    def display_lesson(self, lesson):

        self.current_lesson = lesson
        self.current_file = None

        self.lesson_text.delete(
            "1.0",
            tk.END,
        )

        self.lesson_text.insert(
            "1.0",
            lesson,
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    def save_clicked(self):

        lesson = self.get_lesson_text()

        if not lesson:
            messagebox.showwarning(
                "No Lesson",
                "Generate a lesson first.",
            )

            return

        try:

            file_path = save_lesson(lesson)

            self.current_lesson = lesson
            self.current_file = file_path

            self.set_status(
                f"Saved: {file_path.relative_to(BASE_DIR)}"
            )

            messagebox.showinfo(
                "Saved",
                f"Lesson saved successfully.\n\n"
                f"{file_path.relative_to(BASE_DIR)}",
            )

            self.update_git_info()

        except Exception as error:

            messagebox.showerror(
                "Save Error",
                str(error),
            )

    # --------------------------------------------------------
    # COMMIT & PUSH
    # --------------------------------------------------------

    def push_clicked(self):

        lesson = self.get_lesson_text()

        if not lesson:
            messagebox.showwarning(
                "No Lesson",
                "Generate a lesson first.",
            )

            return

        # Save automatically if it has not been saved yet.
        if (
            self.current_file is None
            or not self.current_file.exists()
            or self.current_lesson != lesson
        ):

            try:

                self.current_file = save_lesson(
                    lesson
                )

                self.current_lesson = lesson

            except Exception as error:

                messagebox.showerror(
                    "Save Error",
                    str(error),
                )

                return

        self.push_button.config(
            state="disabled",
        )

        self.set_status(
            "Committing and pushing..."
        )

        thread = threading.Thread(
            target=self.push_worker,
            daemon=True,
        )

        thread.start()

    def push_worker(self):

        try:

            result = commit_and_push(
                self.current_file
            )

            self.set_status(
                "Commit and push completed."
            )

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "GitHub",
                    result,
                ),
            )

            self.update_git_info()

        except Exception as error:

            self.set_status(
                "Commit and push failed."
            )

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Git Error",
                    str(error),
                ),
            )

        finally:

            self.root.after(
                0,
                lambda: self.push_button.config(
                    state="normal",
                ),
            )

    # --------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------

    def clear_lesson(self):

        self.lesson_text.delete(
            "1.0",
            tk.END,
        )

        self.current_lesson = ""
        self.current_file = None

        self.set_status(
            "Lesson cleared."
        )

    # --------------------------------------------------------
    # GIT INFORMATION
    # --------------------------------------------------------

    def update_git_info(self):

        def worker():

            try:

                if not check_git_repository():

                    text = "Git: not initialized"

                else:

                    branch = get_current_branch()

                    text = f"Git branch: {branch}"

            except Exception:

                text = "Git: unavailable"

            self.root.after(
                0,
                lambda: self.git_label.config(
                    text=text
                ),
            )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("===================================")
    print("I AM RUNNING THE NEW APP.PY")
    print("===================================")

    root = tk.Tk()

    app = LearningJournalApp(root)

    root.mainloop()