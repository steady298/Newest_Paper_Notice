"""
arXiv相关工具函数：论文获取、过滤等
"""
import arxiv
from config import TRANSLATION_AVAILABLE, GEMINI_API_KEY
from translation import translate_titles_batch

def get_authors(authors, first_author=False):
    """
    获取作者列表，返回字符串格式
    @param authors: list of Author objects
    @param first_author: bool - 如果为True，只返回第一作者
    @return: str - 作者字符串
    """
    if not authors:
        return ""
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        # 确保转换为字符串
        output = str(authors[0])
    return output

def is_relevant_paper(title, abstract, keywords):
    """
    检查论文是否与cell-free mMIMO领域相关
    @param title: str
    @param abstract: str
    @param keywords: list of str
    @return: bool
    """
    text = (title + " " + abstract).lower()
    
    # 必须包含cell-free相关术语（多种变体）
    cell_free_terms = ["cell-free", "cell free", "cellfree", "cell-free massive", "cell free massive"]
    has_cell_free = any(term in text for term in cell_free_terms)
    
    # 必须包含MIMO相关术语
    mimo_terms = ["massive mimo", "m-mimo", "mmimo", "massive multiple-input", "massive multiple input"]
    has_mimo = any(term in text for term in mimo_terms)
    
    # 无线通信相关术语（如果包含这些，增加相关性权重）
    wireless_terms = ["wireless", "communication", "network", "antenna", "base station", 
                      "access point", "uplink", "downlink", "spectral efficiency", 
                      "energy efficiency", "precoding", "beamforming"]
    has_wireless = any(term in text for term in wireless_terms)
    
    # 排除明显不相关的术语（如果标题/摘要主要讨论这些，则排除）
    exclude_terms = ["biology", "chemistry", "medicine", "protein", "dna", "enzyme",
                     "galaxy", "astronomy", "cosmology", "supernova", "nebula",
                     "molecular", "crystal", "polymer", "quantum computing",
                     "machine learning", "neural network", "deep learning"]
    
    # 如果标题中包含多个排除术语，直接排除
    title_lower = title.lower()
    title_exclude_count = sum(1 for term in exclude_terms if term in title_lower)
    
    # 相关性判断：
    # 1. 必须同时包含cell-free和MIMO，或
    # 2. 包含cell-free且包含无线通信术语（可能是相关研究）
    # 3. 标题中不包含太多排除术语
    is_relevant = (has_cell_free and has_mimo and title_exclude_count == 0) or \
                  (has_cell_free and has_wireless and title_exclude_count == 0)
    
    return is_relevant

def get_daily_papers(topic, query="cell-free", max_results=50, filter_relevant=True, limit=30):
    """
    获取每日论文
    @param topic: str
    @param query: str
    @param max_results: int - 初始搜索的最大结果数（会经过过滤）
    @param filter_relevant: bool - 是否过滤不相关的论文
    @param limit: int - 最终返回的论文数量（默认10篇）
    @return paper_with_code: dict
    """
    # output 
    content = dict() 
    papers_list = []  # 临时存储论文信息
    
    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    relevant_keywords = ["cell-free", "massive MIMO", "mMIMO"]
    
    for result in search_engine.results():
        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id

        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category

        publish_time = result.published.date()

        # 如果启用过滤，检查论文相关性
        if filter_relevant:
            if not is_relevant_paper(paper_title, paper_abstract, relevant_keywords):
                print(f"Filtered out: {paper_title[:60]}...")
                continue

        print("Time = ", publish_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find('v')
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        # 存储论文信息（先不翻译）
        papers_list.append({
            'paper_key': paper_key,
            'date': str(publish_time),
            'title_en': paper_title,
            'author': paper_first_author,
            'paper_id': paper_id,
            'paper_url': paper_url
        })
        
        # 如果已经收集到足够的论文，停止搜索
        if len(papers_list) >= limit:
            break
    
    # 批量翻译所有标题
    if papers_list and TRANSLATION_AVAILABLE and GEMINI_API_KEY:
        print(f"\nTranslating {len(papers_list)} paper titles using Gemini API...")
        titles = [paper['title_en'] for paper in papers_list]
        translations = translate_titles_batch(titles)
        
        # 将翻译结果添加到论文信息中
        for paper in papers_list:
            paper['title_cn'] = translations.get(paper['title_en'], "")
    else:
        # 如果没有翻译功能，设置空翻译
        for paper in papers_list:
            paper['title_cn'] = ""
    
    # 转换为最终格式，确保所有字段都是可序列化的字符串
    for paper in papers_list:
        content[paper['paper_key']] = {
            'date': str(paper['date']),
            'title_en': str(paper['title_en']),
            'title_cn': str(paper['title_cn']) if paper.get('title_cn') else '',
            'author': str(paper['author']),  # 确保author是字符串
            'paper_id': str(paper['paper_id']),
            'paper_url': str(paper['paper_url'])
        }
    
    data = {topic: content}
    
    return data

