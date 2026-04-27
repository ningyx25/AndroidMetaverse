import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# llm = ChatOpenAI(
#     model="ZhipuAI/GLM-5",
#     openai_api_key=os.getenv('MODELSCOPE_API_KEY'),
#     openai_api_base=os.getenv('MODELSCOPE_BASE_UR'),
#     temperature=0.0
# )

llm = ChatOpenAI(
    model="deepseek/deepseek-v4-pro-free",
    openai_api_key=os.getenv('ZENMUX_API_KEY'),
    openai_api_base=os.getenv('ZENMUX_BASE_UR'),
    temperature=0.0
)

