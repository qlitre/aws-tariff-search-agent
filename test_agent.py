"""
Strands Agent 簡易テストスクリプト
BedrockAgentCoreApp を使わずに直接エージェントを呼び出します。

使い方:
    python test_agent.py
    python test_agent.py "チューハイの税番を教えて"
"""
import sys
from strands import Agent
from strands.models import BedrockModel
from tariffsearchagent import search_tariff_by_keywords, SYSTEM_PROMPT

agent = Agent(
    tools=[search_tariff_by_keywords],
    system_prompt=SYSTEM_PROMPT,
    model=BedrockModel(model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0")
)


def run(prompt: str):
    print(f"\n[質問] {prompt}")
    print("-" * 60)
    result = agent(prompt)
    print(result.message)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        # デフォルトのテストケース
        run("チューハイの税番を教えて")
