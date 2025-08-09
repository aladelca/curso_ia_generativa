#!/usr/bin/env python3
import argparse
import os
from dotenv import load_dotenv


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[INFO] No OPENAI_API_KEY. Simulando salida.\n")
        print(f"Prompt: {args.prompt}\n\n[Respuesta simulada] ...")
        return

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": args.prompt}],
            temperature=0.7,
        )
        print(resp.choices[0].message.content)
    except Exception as e:
        print(f"Error llamando a OpenAI: {e}")


if __name__ == "__main__":
    main()
