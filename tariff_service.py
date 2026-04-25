import os
import json
import boto3
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()


class TariffSearchService:
    def __init__(self):
        self._index_data = None
        self.bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("環境変数 S3_BUCKET_NAME が設定されていません")
        self.data_prefix = "tariffdata/"

        self.aws_region = os.environ.get('AWS_REGION', 'us-west-2')
        self.s3_client = boto3.client('s3', region_name=self.aws_region)

    def _load_index_data(self) -> Dict[str, Any]:
        """インデックスデータを読み込む"""
        if self._index_data is None:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key='index.json')
                self._index_data = json.loads(response['Body'].read().decode('utf-8'))
            except Exception:
                raise Exception("インデックスファイルが見つかりません")
        return self._index_data

    def _load_chapter_data(self, chapter: str) -> Optional[List[Dict[str, Any]]]:
        """章データを読み込む"""
        try:
            filename = f"{self.data_prefix}j_{chapter.zfill(2)}_tariff_data.json"
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=filename)
            return json.loads(response['Body'].read().decode('utf-8'))
        except Exception as e:
            print(f"S3ファイル読み込みエラー ({filename}): {type(e).__name__}: {str(e)}")
            return None

    @staticmethod
    def gen_chapters():
        ret = []
        for i in range(1, 98):
            # 欠番
            if i == 77:
                continue
            ret.append(str(i).zfill(2))
        return ret

    def search_tariff_data(self, keywords: List[str]) -> (
            Tuple)[List[Dict[str, Any]], Dict[str, int]]:
        """関税データを検索する（複数キーワード対応）"""
        results = []
        hit_count = defaultdict(int)
        keywords_lower = [keyword.lower() for keyword in keywords]
        for chapter in self.gen_chapters():
            chapter_data = self._load_chapter_data(chapter)
            que = deque(chapter_data)
            if chapter_data:
                while que:
                    item = que.popleft()
                    if item.get('desc'):
                        desc_lower = item['desc'].lower()
                        f = False
                        for keyword in keywords_lower:
                            if keyword in desc_lower:
                                f = True
                                hit_count[keyword] += 1
                        stat_code = item.get('stat_code')
                        for keyword in keywords_lower:
                            if keyword in stat_code:
                                f = True
                                hit_count[keyword] += 1
                        if f:
                            node = {
                                'stat_code': item.get('stat_code'),
                                'hs_code': item.get('hs_code'),
                                'desc': item.get('desc'),
                                'level': item.get('level')
                            }
                            if item.get('rate'):
                                rate_value = {}
                                for k, v in item.get('rate').items():
                                    if v:
                                        rate_value[k] = v
                                node['rate'] = rate_value
                            if item.get('unit'):
                                node['unit'] = item.get('unit')
                            if item.get('law'):
                                node['law'] = item.get('law')
                            results.append(node)

                    if item.get('children'):
                        for elm in item.get('children'):
                            que.append(elm)

        return results, dict(hit_count)
