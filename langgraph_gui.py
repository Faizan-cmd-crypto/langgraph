import subprocess
import sys
from pathlib import Path

import gradio as gr


BASE_DIR = Path(__file__).resolve().parent
WORKFLOW_FILE = BASE_DIR / "sequental_workflow_langgraph.py"
OUTPUT_MARKER = "your result are : -"


def extract_final_output(stdout: str) -> str:
    lowered = stdout.lower()
    idx = lowered.find(OUTPUT_MARKER)
    if idx != -1:
        extracted = stdout[idx + len(OUTPUT_MARKER):].strip()
        if extracted:
            return extracted

    # Fallback if marker text changes in the workflow script.
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return lines[-1] if lines else "No output was produced."


def run_workflow(raw_input: str) -> tuple[str, str]:
    raw_input = (raw_input or "").strip()
    if not raw_input:
        return "", "Please enter text before running the workflow."

    if not WORKFLOW_FILE.exists():
        return "", f"Workflow file not found: {WORKFLOW_FILE}"

    try:
        process = subprocess.run(
            [sys.executable, str(WORKFLOW_FILE)],
            input=raw_input + "\n",
            text=True,
            capture_output=True,
            cwd=str(BASE_DIR),
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "", "Workflow timed out after 300 seconds."
    except Exception as exc:
        return "", f"Unexpected error: {exc}"

    stdout = process.stdout or ""
    stderr = process.stderr or ""

    if process.returncode != 0:
        return "", stderr.strip() or stdout.strip() or "Unknown workflow error."

    return extract_final_output(stdout), "Completed"


custom_css = """
:root {
  --bg-1: #f5f8ff;
  --bg-2: #eef6f4;
  --ink: #102a43;
  --muted: #486581;
  --accent: #0f766e;
  --accent-2: #1d4ed8;
}

body, .gradio-container {
  background:
    radial-gradient(1200px 600px at 0% 0%, #e4f0ff 0%, transparent 70%),
    radial-gradient(1000px 500px at 100% 100%, #daf5ed 0%, transparent 70%),
    linear-gradient(135deg, var(--bg-1), var(--bg-2));
}

.main-card {
  border: 1px solid #dbeafe;
  border-radius: 20px;
  box-shadow: 0 12px 30px rgba(16, 42, 67, 0.08);
  padding: 14px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(4px);
}

.title {
  color: var(--ink);
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 0.2px;
}

.subtitle {
  color: var(--muted);
  margin-top: -8px;
}

#run-btn {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  color: white;
  border: 0;
}
"""


with gr.Blocks() as demo:
    gr.Markdown("<div class='title'>LangGraph Sequential Workflow</div>")
    gr.Markdown(
        "<div class='subtitle'>Enter raw text, run your existing sequential graph, and view final Hinglish output.</div>"
    )

    with gr.Column(elem_classes=["main-card"]):
        raw_input_box = gr.Textbox(
            label="Raw Input",
            lines=8,
            placeholder="Type your topic or paragraph here...",
        )

        with gr.Row():
            run_btn = gr.Button("Run Workflow", elem_id="run-btn", variant="primary")
            clear_btn = gr.Button("Clear")

        status_box = gr.Textbox(label="Status", interactive=False)
        output_box = gr.Textbox(label="Final Output", lines=14, interactive=False)

    run_btn.click(fn=run_workflow, inputs=[raw_input_box], outputs=[output_box, status_box])
    clear_btn.click(
        fn=lambda: ("", "", "Ready"),
        inputs=[],
        outputs=[raw_input_box, output_box, status_box],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        show_error=True,
        css=custom_css,
        theme=gr.themes.Soft(),
    )
