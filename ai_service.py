import os
import sys
import json
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
                self.client = None # Explicitly set to None if initialization fails; the application handles this and continues without AI features.
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
            
            prompt = f"I am planning a task: '{task_title}'. Provide 3-5 short, actionable sub-steps or pieces of advice to resolve this task. Do not include obvious or trivial steps. Return a JSON object with a key 'suggested_subtasks' which is an array of strings. Keep each item under 30 words."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful productivity assistant. You are dealing gently with someone who has procrastination and needs minimal first steps to start. You MUST return JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            print(f"OpenAI Response received: {content[:50]}...")
            sys.stdout.flush()
            
            try:
                data = json.loads(content)
                suggestions = data.get('suggested_subtasks', [])
                if isinstance(suggestions, list):
                    # Convert to objects with status
                    return [{"text": s, "done": False} for s in suggestions if isinstance(s, str)]
                return [{"text": content, "done": False}] # Fallback if not a list
            except json.JSONDecodeError:
                return [{"text": content, "done": False}] # Fallback if not JSON
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            sys.stdout.flush()
            return [{"text": f"Error contacting AI: {str(e)}", "done": False}]
