import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from zhipuai import ZhipuAI
from typing import List


os.environ["GLM_API_KEY"] = "e23b635d0a804cdbb62bc78e7477b16c.nJEP4958y8GlF5sQ"
os.environ["GLM_MODEL"] = "glm-4-flash"

# 加载环境变量
env_path = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# 获取配置
api_key = os.getenv("GLM_API_KEY")
model_name = os.getenv("GLM_MODEL")

def mabe_warp_for_glm_chat_completion(prompt_list: List[str], config=None):
    """对 GLM API 的输入进行包装
    glm-4-flash 模型需要包含用户和助手的角色信息，
    example:
        messages=[
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "Please describe this video carefully"
            }
            ]
        }
        ]
    args:
        prompt: str, 用户输入的对话, such as f": {content}\n" or f"Assistant: {content}\n"
        config: config['system_instruction'] = system_instruction
    """
    # if config and 'system_instruction' in config:
    #     wrapped_prompt["content"].append({
    #         "type": "system",
    #         "text": config['system_instruction']
    #     })
    msg = []
    # prompt_list = prompt.split("\n")
    for p in prompt_list:
        if "system" in p:
            msg.append({
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": f"{p}"
                    }
                ]
            })
        if "User" in p:
            msg.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{p}"
                    }
                ]
            })
        else:
            msg.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": f"{p}"
                    }
                ]
            })
    
   
    return msg


def test_simple_prompt():
    """测试简单的提示词生成"""
    print(f"Using model: {model_name}")
    # 初始化客户端
    client = ZhipuAI(api_key=api_key)

    # 测试简单生成
    contents = [
        "system: You are a helpfull human Assistant.",
        "User: Write a story about a magic backpack.",
    ]
    contents = mabe_warp_for_glm_chat_completion(contents)
    response = client.chat.completions.create(
        model=model_name,
        messages=contents,
    )

    print("\nSimple prompt response:")
    # print("Response type:", type(response))
    # print("Response attributes:", dir(response))
    print("\nResponse text:", response.choices[0].message.content)

    # 打印完整的响应对象结构
    print("\nFull response structure:")
    print(json.dumps(response.model_dump(), indent=2))


def test_chat_format():
    """测试聊天格式的提示词"""
    """测试简单的提示词生成"""
    print(f"Using model: {model_name}")
    # 初始化客户端
    client = ZhipuAI(api_key=api_key)

    # 测试简单生成
    contents = [
        "User: Write a story about a magic backpack.",
    ]
    contents = mabe_warp_for_glm_chat_completion(contents)
    response = client.chat.completions.create(
        model=model_name,
        messages=contents,
    )

    print("\nSimple prompt response:")
    # print("Response type:", type(response))
    # print("Response attributes:", dir(response))
    print("\nResponse text:", response.choices[0].message.content)

    # 打印完整的响应对象结构
    print("\nFull response structure:")
    print(json.dumps(response.dict(), indent=2))
    


if __name__ == "__main__":
    print("Testing Gemini API...")
    test_simple_prompt()
    print("\n" + "="*50 + "\n")
    test_chat_format()
