"""
主程序：RIS（智能超表面）论文追踪
"""
import os
import json
from arxiv_utils import get_daily_papers
from data_processing import update_json_file, json_to_md, json_to_html, compare_papers
from push_notification import send_push_notification

if __name__ == "__main__":
    json_file = "cv-arxiv-daily.json"
    
    # 读取上一次的结果用于对比
    old_data = {}
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    old_data = json.loads(content)
        except Exception as e:
            print(f"Warning: Failed to read old data: {e}")
            old_data = {}

    data_collector = []
    keywords = dict()
    # RIS相关查询：匹配智能超表面/智能反射面的各种表达
    keywords["RIS"] = 'all:"reconfigurable intelligent surface" OR all:"intelligent reflecting surface"'

    for topic, keyword in keywords.items():
        print("Keyword: " + topic)
        data = get_daily_papers(topic, query=keyword, max_results=50, filter_relevant=True, limit=30)
        data_collector.append(data)
        print(f"Found {len(data[topic])} relevant papers for {topic}\n")

    # 将data_collector转换为与old_data相同的格式用于对比
    new_data = {}
    for data in data_collector:
        for topic, papers in data.items():
            new_data[topic] = papers

    # 对比新旧数据
    has_new_papers, new_count = compare_papers(old_data, new_data)
    
    if not os.path.exists(json_file):
        with open(json_file, "w", encoding="utf-8") as a:
            print("create " + json_file)
    
    update_json_file(json_file, data_collector)
    json_to_md(json_file)
    json_to_html(json_file)
    
    if has_new_papers:
        send_push_notification("RIS领域论文有更新，请注意查看！")
    else:
        send_push_notification("arxiv检索暂无更新")
