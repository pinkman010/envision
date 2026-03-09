import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 检查必要的环境变量
required_vars = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise ValueError(f"缺少环境变量: {missing}")

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# 从环境变量读取是否禁用思考能力（默认为true，即禁用）
disable_thinking = os.getenv("DISABLE_THINKING", "true").lower() == "true"

# 构建 extra_body：如果禁用思考能力，添加thinking参数
extra_body = {"thinking": {"type": "disabled"}} if disable_thinking else {}

# 测试：询问1+1
response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),  # 应为 kimi-k2.5
    temperature=0.6,  # 注意：这里设置为1.0以测试是否完全禁用思考能力（即使模型默认温度较高）
    messages=[{"role": "user", "content": "1+1=?只回答数字"}],
    extra_body=extra_body  # 关键：传递禁用思考能力的参数
)

message = response.choices[0].message
content = message.content
reasoning_content = getattr(message, 'reasoning_content', None)

print(f"使用模型: {os.getenv('LLM_MODEL')}")
print(f"禁用思考: {disable_thinking}")
print(f"回答内容: {content}")

# 检查思考过程
if reasoning_content:
    print(f"思考过程: {reasoning_content[:200]}...")
    print("⚠️  警告：仍检测到思考内容，禁用可能未生效")
else:
    print("思考过程: None")
    print("✅ 成功禁用思考能力")

# 检查内容中是否包含think标签（双重保险）
has_think_tag = '<think' in (content or '').lower()
print(f"是否含<think>标签: {has_think_tag}")