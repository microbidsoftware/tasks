import configparser
from pathlib import Path
try:
    from openai import OpenAI, OpenAIError
except ImportError:
    OpenAI = None
    OpenAIError = Exception

CONFIG_FILE = 'config.ini'

class AIService:
    def __init__(self):
        self.api_key = None
        self.model = 'gpt-3.5-turbo'
        self.client = None
        self._load_config()

    def _load_config(self):
        config = configparser.ConfigParser()
        if Path(CONFIG_FILE).exists():
            config.read(CONFIG_FILE)
            if 'openai' in config:
                self.api_key = config['openai'].get('api_key')
                self.model = config['openai'].get('model', 'gpt-3.5-turbo')
        
        if self.api_key and self.api_key != 'YOUR_API_KEY_HERE' and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                self.client = None
        else:
            self.client = None

    def get_task_suggestion(self, task_title):
        """Ask OpenAI for a short suggestion/breakdown for the task."""
        if not self.client:
            return None # AI not configured or import failed

        try:
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
            return suggestion
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return f"Error contacting AI: {str(e)}"
