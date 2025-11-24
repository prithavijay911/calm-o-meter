"""
Stress Level Analyzer (Typing Speed)

- Shows a target sentence.
- User clicks Start, types the sentence, then clicks Done.
- Measures time, computes WPM, errors (Levenshtein distance), accuracy.
- Calculates a stress score (0-100) and shows friendly feedback.

Author: ChatGPT (example for first-semester project)
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import time


# ---------- Utility: Levenshtein distance ----------
def levenshtein(a: str, b: str) -> int:
    """Return Levenshtein distance between strings a and b."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    # Use dynamic programming (iterative)
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * lb
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            delete = prev[j] + 1
            replace = prev[j - 1] + (0 if ca == cb else 1)
            curr[j] = min(ins, delete, replace)
        prev = curr
    return prev[lb]


# ---------- Stress score logic ----------
def compute_metrics(target: str, typed: str, elapsed_seconds: float):
    target_len = len(target)
    # Protect against zero length target
    if target_len == 0:
        return {"wpm": 0.0, "accuracy": 1.0, "errors": 0, "stress": 0.0}

    # Errors
    dist = levenshtein(target, typed)

    # Words per minute: (correct chars / 5) / minutes
    # We'll let "correct chars" = max(0, len(target) - dist)
    correct_chars = max(0, target_len - dist)
    minutes = max(elapsed_seconds / 60.0, 1e-6)
    wpm = (correct_chars / 5.0) / minutes

    # Accuracy (0..1)
    accuracy = max(0.0, (target_len - dist) / target_len)

    # Stress score design:
    # - Baseline expected WPM for calm student: 35 (you can tune)
    # - Stress increases when WPM << baseline or accuracy low.
    baseline_wpm = 35.0
    wpm_component = max(0.0, (baseline_wpm - wpm) / baseline_wpm)  # 0 when >= baseline
    accuracy_component = 1.0 - accuracy  # 0 when perfect
    # Weight components (50% each) -> score 0..1 then scale to 0..100
    raw = 0.5 * wpm_component + 0.5 * accuracy_component
    stress = min(100.0, max(0.0, raw * 100.0))

    return {"wpm": wpm, "accuracy": accuracy, "errors": dist, "stress": stress}


# ---------- Simple feedback based on stress ----------
def feedback_text(metrics):
    s = metrics["stress"]
    acc = metrics["accuracy"]
    wpm = metrics["wpm"]

    if s < 20:
        mood = "Relaxed — Great typing speed and accuracy!"
    elif s < 40:
        mood = "Mildly stressed — A little rushed or a few mistakes."
    elif s < 70:
        mood = "Stressed — Consider taking short breaks and deep breaths."
    else:
        mood = "Highly stressed — try breathing exercises, slow down and rest."

    tips = []
    if acc < 0.85:
        tips.append("Focus on accuracy over speed; make fewer mistakes.")
    if wpm < 25:
        tips.append("Practice typing regularly to increase speed (short daily drills).")
    if not tips:
        tips.append("Keep up the good work — maintain steady practice!")

    return f"{mood}\n\nTips:\n" + "\n".join(f"- {t}" for t in tips)


# ---------- GUI ----------
class StressAnalyzerApp:
    def __init__(self, root):
        self.root = root
        root.title("Typing Stress Analyzer")
        root.geometry("760x420")
        root.resizable(False, False)

        # Example target sentences (you can add more)
        self.targets = [
            "The quick brown fox jumps over the lazy dog.",
            "Practice consistently to improve speed and reduce stress.",
            "In programming, patience and precision are often more valuable than haste.",
            "Python makes many everyday tasks simpler and more fun to automate."
        ]
        self.current_target = self.targets[0]

        # State
        self.start_time = None
        self.ended = False

        # Widgets
        header = tk.Label(root, text="Typing Stress Analyzer", font=("Helvetica", 18, "bold"))
        header.pack(pady=(10, 6))

        # Target display (readonly scrolledtext)
        label = tk.Label(root, text="Type the sentence exactly as shown below:")
        label.pack()
        self.target_box = scrolledtext.ScrolledText(root, height=3, wrap=tk.WORD, font=("Arial", 12))
        self.target_box.pack(fill=tk.X, padx=12)
        self.target_box.insert(tk.END, self.current_target)
        self.target_box.configure(state="disabled", bg="#f0f0f0")

        # Typed area
        label2 = tk.Label(root, text="Your typing (press Start, then type here):")
        label2.pack(pady=(8, 0))
        self.type_box = tk.Text(root, height=6, wrap=tk.WORD, font=("Arial", 12))
        self.type_box.pack(fill=tk.X, padx=12)
        self.type_box.configure(state="disabled")  # only enabled after Start

        # Buttons frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        self.start_btn = tk.Button(btn_frame, text="Start", width=12, command=self.start_test)
        self.start_btn.grid(row=0, column=0, padx=6)
        self.done_btn = tk.Button(btn_frame, text="Done", width=12, state="disabled", command=self.end_test)
        self.done_btn.grid(row=0, column=1, padx=6)
        self.new_btn = tk.Button(btn_frame, text="New Sentence", width=12, command=self.new_sentence)
        self.new_btn.grid(row=0, column=2, padx=6)
        self.clear_btn = tk.Button(btn_frame, text="Clear", width=12, command=self.clear_typed)
        self.clear_btn.grid(row=0, column=3, padx=6)

        # Results area
        self.result_text = tk.Text(root, height=6, wrap=tk.WORD, font=("Arial", 11))
        self.result_text.pack(fill=tk.BOTH, padx=12, pady=(4, 12))
        self.result_text.configure(state="disabled", bg="#f8f8ff")

    def start_test(self):
        # Reset state
        self.type_box.configure(state="normal")
        self.type_box.delete("1.0", tk.END)
        self.type_box.focus_set()
        self.start_time = time.perf_counter()
        self.ended = False
        self.start_btn.configure(state="disabled")
        self.done_btn.configure(state="normal")
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "Test started — type the sentence and click Done when finished.\n")
        self.result_text.configure(state="disabled")

    def end_test(self):
        if self.start_time is None:
            messagebox.showinfo("Info", "Click Start before Done.")
            return
        if self.ended:
            messagebox.showinfo("Info", "Test already finished. Click New Sentence to try again.")
            return

        end_time = time.perf_counter()
        elapsed = end_time - self.start_time
        typed = self.type_box.get("1.0", tk.END).rstrip("\n")

        metrics = compute_metrics(self.current_target, typed, elapsed)
        # Format metrics
        out = []
        out.append(f"Elapsed time: {elapsed:.2f} seconds")
        out.append(f"WPM (estimated): {metrics['wpm']:.1f}")
        out.append(f"Errors (Levenshtein): {metrics['errors']}")
        out.append(f"Accuracy: {metrics['accuracy']*100:.1f}%")
        out.append(f"Stress score: {metrics['stress']:.1f} / 100")
        out.append("\nFeedback:\n" + feedback_text(metrics))

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "\n".join(out))
        self.result_text.configure(state="disabled")

        # Lock typing area and adjust buttons
        self.type_box.configure(state="disabled")
        self.done_btn.configure(state="disabled")
        self.start_btn.configure(state="normal")
        self.ended = True
        self.start_time = None

    def new_sentence(self):
        import random
        self.current_target = random.choice(self.targets)
        self.target_box.configure(state="normal")
        self.target_box.delete("1.0", tk.END)
        self.target_box.insert(tk.END, self.current_target)
        self.target_box.configure(state="disabled")
        self.clear_typed()
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.configure(state="disabled")
        self.start_time = None
        self.ended = False
        self.start_btn.configure(state="normal")
        self.done_btn.configure(state="disabled")

    def clear_typed(self):
        self.type_box.configure(state="normal")
        self.type_box.delete("1.0", tk.END)
        self.type_box.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = StressAnalyzerApp(root)
    root.mainloop()
