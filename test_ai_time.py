from ai_service import AIService
from dotenv import load_dotenv
import os

def test_ai_time():
    load_dotenv()
    service = AIService()
    if not service.client:
        print("AI Client not initialized. Check OPENAI_API_KEY.")
        return

    task = "Prepare for a job interview"
    print(f"Requesting suggestions for: {task}")
    suggestions = service.get_task_suggestion(task)
    
    print("\nSuggestions received:")
    for s in suggestions:
        print(f"- {s.get('text')} ({s.get('time')}m)")
        assert 'text' in s
        assert 'time' in s
        assert isinstance(s['time'], int)

if __name__ == "__main__":
    test_ai_time()
