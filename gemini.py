"""Transcribe image.png with Gemini and write the LaTeX to response.txt.

Snipper.ahk waits on response.done, which is always written last and always
written, even on failure.  Both files are written atomically (temp file +
os.replace) so the watcher can never read a half-written file.
"""

import os
import sys
import tempfile
import time

from google import genai
from google.genai import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "image.png")
RESPONSE_PATH = os.path.join(BASE_DIR, "response.txt")
DONE_PATH = os.path.join(BASE_DIR, "response.done")

API_KEY = os.environ.get("GEMINI_API_KEY", "ur api key lol")
MODEL = "gemini-flash-latest"

# The API hands out 429/503 under load often enough to look like a broken snip,
# so ride out the short ones rather than reporting a failure.
RETRY_DELAYS = (1.0, 2.5, 5.0)
RETRY_ON = ("429", "500", "502", "503", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED")

# Alternate prompt, also transcribes the question number:
# 'transcribe this image fully and accurately output in latex. Make sure to also
#  transcribe the question # into the latex (in the format "Question: QuestionNumber")
#  Do not include any of the document setup lines such as "usepackage" or
#  "begin document". If there is any image, just give a brief description of the
#  image in one line. Do not include any other text or explanation.'
PROMPT = (
    'transcribe this image fully and accurately output in latex. Do not include '
    'any of the document setup lines such as "usepackage" or "begin document". '
    'If there is any image, just give a brief description of the image in one '
    'line. Do not include any other text or explanation. Do not precede the '
    'actual transcription with any text saying anything like "Heres the LaTeX '
    'transcription of the image: "'
)


def write_atomic(path, text):
    """Write text to path so a reader sees either the old file or the new one."""
    fd, tmp = tempfile.mkstemp(dir=BASE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def is_transient(exc):
    text = "{}: {}".format(exc.__class__.__name__, exc)
    return any(marker in text for marker in RETRY_ON)


def generate(client, image_bytes):
    return client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            PROMPT,
        ],
    )


def transcribe():
    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()

    client = genai.Client(api_key=API_KEY)

    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            response = generate(client, image_bytes)
            break
        except Exception as exc:
            if attempt == len(RETRY_DELAYS) or not is_transient(exc):
                raise
            time.sleep(RETRY_DELAYS[attempt])

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("model returned no text (response blocked or empty)")

    write_atomic(RESPONSE_PATH, text)


def main():
    try:
        transcribe()
        status = "OK"
    except BaseException as exc:
        # Flattened to one line: Snipper.ahk shows it in the failure indicator.
        detail = " ".join(str(exc).split()) or exc.__class__.__name__
        status = "ERR {}: {}".format(exc.__class__.__name__, detail)

    write_atomic(DONE_PATH, status)
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
