import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env
load_dotenv()

def get_llm():
    """
    Initializes and returns a LangChain BaseChatModel pointing to OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set in the environment or .env file.\n"
            "Please create a .env file containing OPENROUTER_API_KEY=your_key"
        )
    
    model_name = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    base_url = "https://openrouter.ai/api/v1"
    
    # Configure LangChain ChatOpenAI instance with OpenRouter credentials and model
    llm = ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=0.7,
        default_headers={
            "HTTP-Referer": "https://github.com/langchain-ai/deepagents",
            "X-Title": "Coach Clone Deep Agent"
        }
    )
    
    return llm
