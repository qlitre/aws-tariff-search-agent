from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from tariff_service import TariffSearchService
import json

# タリフ検索サービスのインスタンス（遅延初期化）
_search_service = None


def get_search_service():
    """遅延初期化でTariffSearchServiceのインスタンスを取得"""
    global _search_service
    if _search_service is None:
        _search_service = TariffSearchService()
    return _search_service


@tool
def search_tariff_by_keywords(keywords: str) -> str:
    """Search tariff data by Japanese keywords (comma-separated).

    Use Japanese keywords for best results. Multiple keywords can be separated by commas.

    Args:
        keywords: Comma-separated Japanese keywords to search for

    Returns:
        JSON string containing search results with hitCount per keyword and limited results
    """
    if not keywords or not keywords.strip():
        return json.dumps({
            "error": "keywords is required"
        }, ensure_ascii=False, indent=2)

    try:
        # キーワードをリストに分割
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]

        # search_tariff_dataは(results, hit_count)のタプルを返す
        search_service = get_search_service()
        results, hit_count = search_service.search_tariff_data(keyword_list)

        limit = 30
        message = ""
        if len(results) > limit:
            message = f"More than the maximum limit of {limit} items were found. Please refer to hitCount and re-search if necessary."

        return json.dumps({
            "keywords": keywords,
            "found": len(results),
            "message": message,
            "hitCount": hit_count,  # 各キーワードごとのヒット数の辞書
            "results": results[:limit]
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"検索エラー: {str(e)}"
        }, ensure_ascii=False, indent=2)


SYSTEM_PROMPT = """
あなたは日本の関税データを検索する専門エージェントです。
# 利用可能な機能
- 関税データ検索: 商品名やキーワードの配列で関税情報を検索できます。
  - **重要**: ユーザーのメッセージを元に連想される文字列を複数カンマ区切りで渡してください。
  - 統計コード6桁でも検索が可能です。
  - 例: 「チューハイの税番を教えて」→ search_tariff_by_keywords(keywords="チューハイ,酒,アルコール,飲料")

# 検索戦略
1. **初回検索**: ユーザーの質問から複数の関連キーワードを抽出して検索
   - 商品名だけでなく、カテゴリ、用途、素材などの関連語も含める
   - より広範な結果を得るために3-5個のキーワードを使用

2. **検索結果がない場合**:
   - 類似キーワード、上位カテゴリ、別の表現で再検索
   - 例: 「スマートフォン」→「携帯電話,電話機,通信機器」

3. **検索結果が多すぎる場合** (30件以上):
   - 結果に含まれる`hitCount`（各キーワードごとのヒット件数）を確認
   - ヒット数が少ないキーワードに絞って再検索
   - より具体的なキーワードを使用

# 回答形式
- 検索結果を分かりやすく整理して提示
- HSコード、統計コード、税率、単位などの重要情報を明確に表示
- 必要に応じて関連する法令情報も提供
"""

app = BedrockAgentCoreApp()
agent = Agent(
    tools=[search_tariff_by_keywords],
    system_prompt=SYSTEM_PROMPT
)


@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt")
    result = agent(user_message)
    return {"result": result.message}


if __name__ == "__main__":
    app.run()