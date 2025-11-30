from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL


def main():
    print("Running Gemini test...")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")

    # Initialize Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Simple prompt
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Say hello! You are responding from Gemini."
    )

    print("\n=== Gemini Response ===\n")
    print(response.text)


if __name__ == "__main__":
    main()
