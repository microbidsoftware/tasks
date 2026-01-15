import os
import sys
try:
    from openai import OpenAI, OpenAIError
except ImportError:
    OpenAI = None
    OpenAIError = Exception

class AIService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("OpenAI client initialized successfully.")
                sys.stdout.flush()
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                sys.stdout.flush()
                self.client = None
        else:
            print("OpenAI client not initialized. Missing API Key or openai library.")
            sys.stdout.flush()
            self.client = None

    def get_task_suggestion(self, task_title):
        """Ask OpenAI for a short suggestion/breakdown for the task."""
        if not self.client:
            print("OpenAI request skipped: Client not initialized.")
            sys.stdout.flush()
            return None 

        try:
            print(f"Sending OpenAI request for task: '{task_title}'")
            sys.stdout.flush()
            
            prompt = f"I am planning a task: '{task_title}'. Give me 3 short, actionable sub-steps or a brief piece of advice. Keep it under 50 words."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful productivity assistant. Be concise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            
            suggestion = response.choices[0].message.content.strip()
            print(f"OpenAI Response received: {suggestion[:50]}...")
            sys.stdout.flush()
            return suggestion
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            sys.stdout.flush()
            return f"Error contacting AI: {str(e)}"
