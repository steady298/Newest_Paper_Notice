"""
数据处理模块：JSON和Markdown转换
"""
import datetime
import json
import os

def sort_papers(papers):
    """
    对论文按日期排序
    @param papers: dict
    @return: dict - 排序后的论文字典
    """
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output

def update_json_file(filename, data_all):
    """
    更新JSON文件
    @param filename: str - JSON文件名
    @param data_all: list - 数据列表
    """
    with open(filename, "r", encoding='utf-8') as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)
            
    json_data = m.copy()
    
    # update papers in each keywords
    for data in data_all:
        for keyword in data.keys():
            papers = data[keyword]

            if keyword in json_data.keys():
                json_data[keyword].update(papers)
            else:
                json_data[keyword] = papers

    with open(filename, "w", encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def group_papers_by_month(papers):
    """
    按月份分组论文
    @param papers: dict - 论文数据字典
    @return: dict with month-year as key
    """
    grouped = {}
    for paper_key, paper_data in papers.items():
        # 兼容旧格式（字符串）和新格式（字典）
        if isinstance(paper_data, dict):
            try:
                date_str = paper_data.get('date', '')
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                month_key = date_obj.strftime('%Y-%m')
                if month_key not in grouped:
                    grouped[month_key] = []
                grouped[month_key].append((date_str, paper_data))
            except Exception as e:
                if 'Other' not in grouped:
                    grouped['Other'] = []
                grouped['Other'].append(('Unknown', paper_data))
        else:
            # 旧格式兼容：字符串格式
            try:
                parts = paper_data.split('|')
                if len(parts) >= 2:
                    date_str = parts[1].strip()
                    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    month_key = date_obj.strftime('%Y-%m')
                    if month_key not in grouped:
                        grouped[month_key] = []
                    grouped[month_key].append((date_str, paper_data))
                else:
                    raise ValueError("Invalid format")
            except Exception as e:
                if 'Other' not in grouped:
                    grouped['Other'] = []
                grouped['Other'].append(('Unknown', paper_data))
    
    # 对每个月的论文按日期排序（降序）
    for month_key in grouped:
        if month_key != 'Other':
            grouped[month_key].sort(key=lambda x: x[0], reverse=True)
    
    return grouped

def json_to_md(filename):
    """
    将JSON数据转换为Markdown格式
    @param filename: str - JSON文件名
    @return None
    """
    DateNow = datetime.date.today()
    DateNow_str = DateNow.strftime('%Y-%m-%d')
    DateNow_display = DateNow.strftime('%Y年%m月%d日')
    
    with open(filename, "r", encoding='utf-8') as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    md_filename = "README.md"
    
    # clean README.md if daily already exist else create it
    with open(md_filename, "w+", encoding='utf-8') as f:
        # 写入标题和介绍
        f.write("# Cell-free Massive MIMO 论文追踪\n\n")
        f.write(f"**最后更新**: {DateNow_display}\n\n")
        f.write("本文档自动追踪 arXiv 上关于无蜂窝式大规模 MIMO (Cell-free Massive MIMO) 领域的最新论文。\n\n")
        f.write("---\n\n")
    
    # write data into README.md
    with open(md_filename, "a+", encoding='utf-8') as f:
        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            
            # 统计信息
            total_papers = len(day_content)
            f.write(f"## {keyword}\n\n")
            f.write(f"**总计**: {total_papers} 篇论文\n\n")
            
            # 按月份分组
            grouped_papers = group_papers_by_month(day_content)
            
            # 按月份排序（降序）
            sorted_months = sorted(grouped_papers.keys(), reverse=True)
            
            for month_key in sorted_months:
                if month_key == 'Other':
                    continue
                    
                month_papers = grouped_papers[month_key]
                month_name = datetime.datetime.strptime(month_key, '%Y-%m').strftime('%Y年%m月')
                
                f.write(f"### {month_name}\n\n")
                f.write("| 发布日期 | 论文标题 | 第一作者 | PDF链接 |\n")
                f.write("|:--------|:---------|:---------|:--------|\n")
                
                for date_str, paper_data in month_papers:
                    # 处理新格式（字典）或旧格式（字符串）
                    if isinstance(paper_data, dict):
                        title_en = paper_data.get('title_en', '')
                        title_cn = paper_data.get('title_cn', '')
                        author = paper_data.get('author', 'Unknown')
                        paper_id = paper_data.get('paper_id', '')
                        paper_url = paper_data.get('paper_url', '')
                        
                        # 格式化标题：英文标题 + 中文翻译（如果有）
                        if title_cn:
                            title_display = f"[{title_en}]({paper_url})<br/>*{title_cn}*"
                        else:
                            title_display = f"[{title_en}]({paper_url})"
                        
                        f.write(f"|{date_str}|{title_display}|{author} et.al.|[{paper_id}]({paper_url})|\n")
                    else:
                        # 旧格式兼容
                        f.write(paper_data)
                
                f.write("\n")
            
            # 如果有Other类别的论文，单独显示
            if 'Other' in grouped_papers and grouped_papers['Other']:
                f.write("### 其他\n\n")
                f.write("| 发布日期 | 论文标题 | 第一作者 | PDF链接 |\n")
                f.write("|:--------|:---------|:---------|:--------|\n")
                for date_str, paper_data in grouped_papers['Other']:
                    if isinstance(paper_data, dict):
                        title_en = paper_data.get('title_en', '')
                        title_cn = paper_data.get('title_cn', '')
                        author = paper_data.get('author', 'Unknown')
                        paper_id = paper_data.get('paper_id', '')
                        paper_url = paper_data.get('paper_url', '')
                        
                        # 格式化标题：英文标题 + 中文翻译（如果有）
                        if title_cn:
                            title_display = f"[{title_en}]({paper_url})<br/>*{title_cn}*"
                        else:
                            title_display = f"[{title_en}]({paper_url})"
                        
                        f.write(f"|{date_str}|{title_display}|{author} et.al.|[{paper_id}]({paper_url})|\n")
                    else:
                        f.write(paper_data)
                f.write("\n")
            
            f.write("---\n\n")
    
    print("finished")

def json_to_html(filename):
    """
    将JSON数据转换为美观的HTML网页
    @param filename: str - JSON文件名
    @return None
    """
    DateNow = datetime.date.today()
    DateNow_display = DateNow.strftime('%Y年%m月%d日')
    
    with open(filename, "r", encoding='utf-8') as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    html_filename = "index.html"
    
    # 创建HTML内容
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cell-free Massive MIMO 论文追踪</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.95;
            margin-top: 10px;
        }}
        
        .header .update-time {{
            font-size: 0.95em;
            opacity: 0.9;
            margin-top: 15px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-weight: 600;
        }}
        
        .section-stats {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
            font-weight: 500;
        }}
        
        .month-section {{
            margin-bottom: 40px;
        }}
        
        .month-title {{
            font-size: 1.4em;
            color: #764ba2;
            margin-bottom: 20px;
            padding: 10px 15px;
            background: #f5f5f5;
            border-left: 4px solid #764ba2;
            border-radius: 4px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 1em;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background-color: #f8f9ff;
            transition: background-color 0.2s;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .paper-title {{
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .paper-title a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .paper-title a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .paper-title-cn {{
            font-style: italic;
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
            display: block;
        }}
        
        .author {{
            color: #555;
        }}
        
        .pdf-link {{
            display: inline-block;
            padding: 5px 12px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            transition: background 0.2s;
        }}
        
        .pdf-link:hover {{
            background: #764ba2;
        }}
        
        .date {{
            color: #888;
            font-size: 0.95em;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            table {{
                font-size: 0.9em;
            }}
            
            th, td {{
                padding: 10px;
            }}
            
            .paper-title-cn {{
                font-size: 0.85em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Cell-free Massive MIMO 论文追踪</h1>
            <div class="subtitle">自动追踪 arXiv 上关于无蜂窝式大规模 MIMO 领域的最新论文</div>
            <div class="update-time">最后更新: {DateNow_display}</div>
        </div>
        
        <div class="content">
"""
    
    # 处理每个主题的数据
    for keyword in data.keys():
        day_content = data[keyword]
        if not day_content:
            continue
        
        # 统计信息
        total_papers = len(day_content)
        html_content += f"""
            <div class="section">
                <h2 class="section-title">{keyword}</h2>
                <div class="section-stats">总计: <strong>{total_papers}</strong> 篇论文</div>
"""
        
        # 按月份分组
        grouped_papers = group_papers_by_month(day_content)
        
        # 按月份排序（降序）
        sorted_months = sorted(grouped_papers.keys(), reverse=True)
        
        for month_key in sorted_months:
            if month_key == 'Other':
                continue
                
            month_papers = grouped_papers[month_key]
            month_name = datetime.datetime.strptime(month_key, '%Y-%m').strftime('%Y年%m月')
            
            html_content += f"""
                <div class="month-section">
                    <h3 class="month-title">{month_name}</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>发布日期</th>
                                <th>论文标题</th>
                                <th>第一作者</th>
                                <th>PDF链接</th>
                            </tr>
                        </thead>
                        <tbody>
"""
            
            for date_str, paper_data in month_papers:
                # 处理新格式（字典）或旧格式（字符串）
                if isinstance(paper_data, dict):
                    title_en = paper_data.get('title_en', '')
                    title_cn = paper_data.get('title_cn', '')
                    author = paper_data.get('author', 'Unknown')
                    paper_id = paper_data.get('paper_id', '')
                    paper_url = paper_data.get('paper_url', '')
                    
                    # 转义HTML特殊字符
                    title_en_escaped = title_en.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    title_cn_escaped = title_cn.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if title_cn else ''
                    author_escaped = author.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    html_content += f"""
                            <tr>
                                <td class="date">{date_str}</td>
                                <td>
                                    <div class="paper-title">
                                        <a href="{paper_url}" target="_blank">{title_en_escaped}</a>
                                    </div>
                                    {f'<div class="paper-title-cn">{title_cn_escaped}</div>' if title_cn_escaped else ''}
                                </td>
                                <td class="author">{author_escaped} et.al.</td>
                                <td><a href="{paper_url}" class="pdf-link" target="_blank">{paper_id}</a></td>
                            </tr>
"""
                else:
                    # 旧格式兼容（跳过，因为已经是字符串格式）
                    pass
            
            html_content += """
                        </tbody>
                    </table>
                </div>
"""
        
        # 如果有Other类别的论文，单独显示
        if 'Other' in grouped_papers and grouped_papers['Other']:
            html_content += """
                <div class="month-section">
                    <h3 class="month-title">其他</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>发布日期</th>
                                <th>论文标题</th>
                                <th>第一作者</th>
                                <th>PDF链接</th>
                            </tr>
                        </thead>
                        <tbody>
"""
            for date_str, paper_data in grouped_papers['Other']:
                if isinstance(paper_data, dict):
                    title_en = paper_data.get('title_en', '')
                    title_cn = paper_data.get('title_cn', '')
                    author = paper_data.get('author', 'Unknown')
                    paper_id = paper_data.get('paper_id', '')
                    paper_url = paper_data.get('paper_url', '')
                    
                    # 转义HTML特殊字符
                    title_en_escaped = title_en.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    title_cn_escaped = title_cn.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if title_cn else ''
                    author_escaped = author.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    html_content += f"""
                            <tr>
                                <td class="date">{date_str}</td>
                                <td>
                                    <div class="paper-title">
                                        <a href="{paper_url}" target="_blank">{title_en_escaped}</a>
                                    </div>
                                    {f'<div class="paper-title-cn">{title_cn_escaped}</div>' if title_cn_escaped else ''}
                                </td>
                                <td class="author">{author_escaped} et.al.</td>
                                <td><a href="{paper_url}" class="pdf-link" target="_blank">{paper_id}</a></td>
                            </tr>
"""
            
            html_content += """
                        </tbody>
                    </table>
                </div>
"""
        
        html_content += """
            </div>
"""
    
    # 添加页脚
    html_content += """
        </div>
        
        <div class="footer">
            <p>自动生成于 {}</p>
            <p>数据来源: <a href="https://arxiv.org" target="_blank">arXiv</a></p>
        </div>
    </div>
</body>
</html>
""".format(DateNow_display)
    
    # 写入HTML文件
    with open(html_filename, "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML file generated: {html_filename}")

def compare_papers(old_data, new_data):
    """
    比较新旧论文数据，找出新增的论文
    @param old_data: dict - 旧的数据
    @param new_data: dict - 新的数据
    @return: tuple - (has_new_papers: bool, new_count: int)
    """
    if not old_data:
        # 如果没有旧数据，认为有新论文（首次运行）
        total_new = sum(len(papers) for papers in new_data.values())
        return (total_new > 0, total_new)
    
    new_count = 0
    for topic in new_data.keys():
        new_papers = new_data.get(topic, {})
        old_papers = old_data.get(topic, {})
        
        # 找出新论文（在新的数据中存在但在旧数据中不存在的）
        for paper_key in new_papers.keys():
            if paper_key not in old_papers:
                new_count += 1
    
    return (new_count > 0, new_count)

