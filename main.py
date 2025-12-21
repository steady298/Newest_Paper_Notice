"""
主程序：Cell-free Massive MIMO 论文追踪
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
            with open(json_file, "r", encoding='utf-8') as f:
                content = f.read()
                if content:
                    old_data = json.loads(content)
        except Exception as e:
            print(f"Warning: Failed to read old data: {e}")
            old_data = {}

    data_collector = []
    keywords = dict()
    # 使用更精确的查询：必须同时包含cell-free和massive MIMO
    # arXiv查询语法：使用AND连接关键词，all:表示在所有字段搜索
    keywords["Cell-free mMIMO"] = 'all:"cell-free" AND (all:"massive MIMO" OR all:"massive-MIMO" OR all:"mMIMO")'
 
    for topic, keyword in keywords.items():
        print("Keyword: " + topic)
        # 获取最新的10篇论文，批量翻译
        data = get_daily_papers(topic, query=keyword, max_results=50, filter_relevant=True, limit=30)
        data_collector.append(data)
        print(f"Found {len(data[topic])} relevant papers for {topic}\n")

    # 将data_collector转换为与old_data相同的格式用于对比
    # data_collector格式: [{topic: {paper_key: paper_data}}]
    # old_data格式: {topic: {paper_key: paper_data}}
    new_data = {}
    for data in data_collector:
        # data 是一个字典，键是topic，值是论文字典
        for topic, papers in data.items():
            new_data[topic] = papers

    # 对比新旧数据
    has_new_papers, new_count = compare_papers(old_data, new_data)
    
    # update README.md file
    if not os.path.exists(json_file):
        with open(json_file, 'w', encoding='utf-8') as a:
            print("create " + json_file)
    
    # update json data
    update_json_file(json_file, data_collector)
    # json data to markdown
    json_to_md(json_file)
    # json data to html
    json_to_html(json_file)
    
    # 根据对比结果发送推送通知
    if has_new_papers:
        send_push_notification("领域论文有更新，请注意查看！")
    else:
        send_push_notification("arxiv检索暂无更新")
