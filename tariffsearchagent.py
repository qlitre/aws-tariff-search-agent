from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from strands import Agent, tool
from strands.models import BedrockModel
from tariff_service import TariffSearchService
from pathlib import Path
import json
import logging
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.txt").read_text(encoding="utf-8")

app = FastAPI()


@app.get("/ping")
async def ping():
    """AgentCore required health check"""
    return {"status": "healthy"}


@app.post("/invocations")
async def invocations(request: Request):
    body = await request.body()
    request_data = json.loads(body.decode())

    # promptはStrandsContentBlock[]形式で来る
    prompt = request_data.get("prompt", [])
    model_info = request_data.get("model", {})

    # content blockのリストをStrandsが扱える形式に変換
    if isinstance(prompt, list):
        processed_prompt = ''.join([
            block.get('text', '') for block in prompt
            if isinstance(block, dict)
        ])
    else:
        processed_prompt = str(prompt)

    model_id = model_info.get("modelId", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    region = model_info.get("region", "us-west-2")

    bedrock_model = BedrockModel(
        model_id=model_id,
        boto_session=boto3.Session(region_name=region),
    )

    agent = Agent(
        tools=[search_tariff_by_keywords],
        system_prompt=SYSTEM_PROMPT,
        model=bedrock_model,
    )

    async def generate():
        try:
            async for event in agent.stream_async(processed_prompt):
                if "event" in event:
                    yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            yield json.dumps({
                "event": {"internalServerException": {"message": str(e)}}
            }, ensure_ascii=False) + "\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning", access_log=False)
