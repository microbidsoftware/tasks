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

    def get_task_suggestion(self, task_title, branch_context=None, current_leaf_title=None):
        """Ask OpenAI for a short suggestion/breakdown for the task, considering context."""
        if not self.client:
            print("OpenAI request skipped: Client not initialized.")
            sys.stdout.flush()
            return None 

        try:
            print(f"Sending OpenAI request for task: '{task_title}'")
            sys.stdout.flush()
            
            context_str = ""
            if branch_context:
                context_str = f"Context of the task branch: {branch_context}. "
            if current_leaf_title:
                context_str += f"Current subtask being created: {current_leaf_title}. "

            prompt = f"I am planning a task: '{task_title}'. {context_str}Provide 3-5 short, actionable sub-steps or pieces of advice to resolve this task. Think deeply, try to use NLP systems and methods to improve results make it's motivational oriented, emphesize easiness of the step and make the task more attractive to start and easy to fulfill take into account the context of the task and you can include obvious or trivial steps. Return a JSON object with a key 'suggested_subtasks' which is an array of objects, each containing 'text' (under 30 words) and 'estimated_time' (in minutes, as an integer)."
            print(f"Prompt: {prompt}")
            sys.stdout.flush()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful productivity assistant. You are dealing gently with someone who has procrastination and needs minimal first steps to start. You MUST return JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            print(f"OpenAI Response received: {content[:100]}...")
            sys.stdout.flush()
            
            try:
                data = json.loads(content)
                suggestions = data.get('suggested_subtasks', [])
                if isinstance(suggestions, list):
                    # Convert to objects with status, text and time
                    result = []
                    for s in suggestions:
                        if isinstance(s, dict):
                            result.append({
                                "text": s.get('text', ''),
                                "time": s.get('estimated_time', 0),
                                "done": False
                            })
                        elif isinstance(s, str):
                            result.append({"text": s, "time": 0, "done": False})
                    return result
                return [{"text": content, "time": 0, "done": False}] # Fallback
            except json.JSONDecodeError:
                return [{"text": content, "time": 0, "done": False}] # Fallback
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            sys.stdout.flush()
            return [{"text": f"Error contacting AI: {str(e)}", "done": False}]
