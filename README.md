# Tariff Search Agent

日本の関税データを検索する Strands Agent です。
AWS Bedrock Agent Core 上で動作し、商品名や統計コードから関税番号・税率を調べられます。

## 構成

```
tariff-search-agent/
├── tariffsearchagent.py   # エージェント本体 + BedrockAgentCoreApp エントリポイント
├── tariff_service.py      # S3 から関税データを取得・検索するサービス
├── test_agent.py          # ローカルテスト用スクリプト
└── requirements.txt       # 依存パッケージ
```

## 前提条件

- Python 3.11+
- AWS 認証情報（Bedrock / S3 へのアクセス権限）
- S3 バケットに関税データが配置済み（`index.json` + `tariffdata/j_XX_tariff_data.json`）

## セットアップ

```bash
python -m venv myvenv
source myvenv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

`.env` ファイルを作成して環境変数を設定:

```env
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-west-2
```

## ローカルテスト

```bash
# デフォルトのテストケース（チューハイ）を実行
python test_agent.py

# 任意の質問
python test_agent.py "スマートフォンの関税率は？"
python test_agent.py "鉄鋼の税番を調べて"
```

使用モデル: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`（Bedrock 経由）

## ローカルサーバー起動

BedrockAgentCoreApp としてローカル HTTP サーバーを起動します。

```bash
python tariffsearchagent.py
```

起動後、`http://localhost:8080` にリクエストを送信:

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "チューハイの税番を教えて"}'
```

## AWS へのデプロイ

デプロイ方式は3種類あり、**Docker は必須ではありません**。

### 方式 1: CodeBuild（推奨・Docker 不要）

AWS CodeBuild がクラウド上でコンテナをビルドするため、ローカルに Docker が不要です。

```bash
# 設定ファイルを生成（初回のみ）
agentcore configure

# デプロイ（デフォルトで CodeBuild を使用）
agentcore deploy
```

### 方式 2: direct_code_deploy（Docker 不要）

コードを zip に固めて S3 経由でデプロイします。`uv` と `zip` コマンドが必要です。

```bash
# uv のインストール（未インストールの場合）
pip install uv

# 設定で deployment_type: direct_code_deploy を指定してから
agentcore deploy
```

### 方式 3: ローカルビルド（Docker 必要）

Docker/Finch/Podman がある場合のみ利用可能です。

```bash
agentcore deploy --local-build
```

### 必要な IAM 権限

実行ロールに以下のポリシーをアタッチしてください:

- `AmazonBedrockFullAccess`（または Bedrock InvokeModel のみに絞った最小権限）
- `s3:GetObject` — 関税データバケットへのアクセス

## モデルの変更

`test_agent.py` および `tariffsearchagent.py` の `BedrockModel(model_id=...)` を変更してください。

```python
from strands.models import BedrockModel

model = BedrockModel(model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0")
```
