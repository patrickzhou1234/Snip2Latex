from google import genai
from google.genai import types

client = genai.Client(api_key="your gemini api key")

with open('image.png', 'rb') as f:
    image_bytes = f.read()

response = client.models.generate_content(
model='gemini-2.0-flash',
contents=[
    types.Part.from_bytes(
    data=image_bytes,
    mime_type='image/jpeg',
    ),
    # 'transcribe this image fully and accurately output in latex. Make sure to also transcribe the question # into the latex (in the format "Question: QuestionNumber" Do not include any of the document setup lines such as "usepackage" or "begin document". If there is any image, just give a brief description of the image in one line. Do not include any other text or explanation.',
    'transcribe this image fully and accurately output in latex. Do not include any of the document setup lines such as "usepackage" or "begin document". If there is any image, just give a brief description of the image in one line. Do not include any other text or explanation. Do not precede the actual transcription with any text saying anything like \"Heres the LaTeX transcription of the image: \"',
]
)

with open("response.txt", "w") as f:
  f.write(response.text)