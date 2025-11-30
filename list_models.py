import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

for m in genai.list_models():
    print(
        m.name,
        m.input_token_limit,
        m.output_token_limit,
        m.supported_generation_methods
    )
