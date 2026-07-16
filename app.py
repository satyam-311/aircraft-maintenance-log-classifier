"""
Fallback entrypoint for Hugging Face Spaces using the Gradio SDK instead of Docker.
Mounts the EXACT SAME FastAPI app (api/main.py, unchanged) inside a minimal Gradio
wrapper -- every route (/classify, /search, /corrections, /ask, /stats,
/model-performance, /health) works identically, just served through Gradio's app
object instead of raw uvicorn+Docker.

Only used if the Docker SDK isn't available for free on the account -- otherwise
the Dockerfile path is simpler and preferred.
"""
import spaces

import gradio as gr

from api.main import app as fastapi_app


@spaces.GPU
def _zerogpu_placeholder():
    """
    Required by Hugging Face's ZeroGPU Spaces: at least one @spaces.GPU-decorated
    function must exist for the Space to start, even though this app runs entirely
    on CPU (DistilBERT/MiniLM inference at our scale doesn't need a GPU at all).
    This function is never called by any real request path -- it exists purely to
    satisfy that platform startup check.
    """
    return "not used -- this app runs on CPU only"


def status_check():
    import requests
    try:
        resp = requests.get("http://localhost:7860/health", timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


with gr.Blocks(title="Maintenance Log Classifier API") as demo:
    gr.Markdown("""
    # Maintenance Log Classifier — API
    This Space hosts the backend API only. The real frontend is deployed separately.

    API docs: [/docs](/docs) (FastAPI's auto-generated interactive docs)

    Endpoints: `/classify`, `/search`, `/corrections`, `/ask`, `/stats`, `/model-performance`, `/health`
    """)
    check_btn = gr.Button("Check API health")
    output = gr.JSON()
    check_btn.click(fn=status_check, outputs=output)

    # Wired into the Blocks graph (not just defined standalone) so ZeroGPU's
    # startup detector actually finds this @spaces.GPU function. Hidden since
    # it's not meant for real use -- this app runs entirely on CPU.
    with gr.Row(visible=False):
        gpu_check_btn = gr.Button("_zerogpu_placeholder")
        gpu_output = gr.Textbox()
        gpu_check_btn.click(fn=_zerogpu_placeholder, outputs=gpu_output)


# This is the key line: mount the real FastAPI app (all our actual routes) at the
# root path, with Gradio's own UI living at /gradio instead of /.
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")