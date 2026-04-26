# Tariff Search Agent

日本の関税データを検索する Strands Agent です。
AWS Bedrock AgentCore 上で動作し、商品名や統計コードから関税番号・税率を調べられます。

## 前提条件

- Python 3.12
- AWS 認証情報（Bedrock / S3 へのアクセス権限）
- S3 バケットに関税データが配置済み（`your-bucket-name/tariffdata/j_XX_tariff_data.json`）

## セットアップ

```bash
python -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
```

## AgentCore へのデプロイ

```bash
agentcore configure
agentcore deploy --env=S3_BUCKET_NAME=your-bucket-name
```

### S3読取権限の追加

デプロイ後作成されたロールにS3バケットの読取権限を付与する。

```bash
aws iam put-role-policy \
  --role-name <execution-role-name> \
  --policy-name S3TariffDataAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": [
          "arn:aws:s3:::your-bucket-name",
          "arn:aws:s3:::your-bucket-name/*"
        ]
      }
    ]
  }'
```