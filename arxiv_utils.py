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
    
    cell_free_terms = ["cell-free", "cell free", "cellfree", "cell-free massive", "cell free massive"]
    has_cell_free = any(term in text for term in cell_free_terms)
    
    mimo_terms = ["massive mimo", "m-mimo", "mmimo", "massive multiple-input", "massive multiple input"]
    has_mimo = any(term in text for term in mimo_terms)
    
    wireless_terms = ["wireless", "communication", "network", "antenna", "base station", 
                      "access point", "uplink", "downlink", "spectral efficiency", 
                      "energy efficiency", "precoding", "beamforming"]
    has_wireless = any(term in text for term in wireless_terms)
    
    exclude_terms = ["biology", "chemistry", "medicine", "protein", "dna", "enzyme",
                     "galaxy", "astronomy", "cosmology", "supernova", "nebula",
                     "molecular", "crystal", "polymer", "quantum computing",
                     "machine learning", "neural network", "deep learning"]
    
    title_lower = title.lower()
    title_exclude_count = sum(1 for term in exclude_terms if term in title_lower)
    
    is_relevant = (has_cell_free and has_mimo and title_exclude_count == 0) or \
                  (has_cell_free and has_wireless and title_exclude_count == 0)
    
    return is_relevant

def get_daily_papers(topic, query="cell-free", max_results=50, filter_relevant=True, limit=30):
    """
    获取每日论文
    @param topic: str
    @param query: str
    @param max_results: int
    @param filter_relevant: bool
    @param limit: int - 最终返回的论文数量（默认30篇）
    @return paper_with_code: dict
    """
    content = dict() 
    papers_list = []
    
    # arxiv 2.x API: 使用 Client 对象
    client = arxiv.Client()
    
    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    relevant_keywords = ["cell-free", "massive MIMO", "mMIMO"]
    
    # arxiv 2.x: client.results(search) 替代 search.results()
    for result in client.results(search_engine):
        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id

        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category

        publish_time = result.published.date()

        if filter_relevant:
            if not is_relevant_paper(paper_title, paper_abstract, relevant_keywords):
                print(f"Filtered out: {paper_title[:60]}...")
                continue

        print("Time = ", publish_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

        ver_pos = paper_id.find("v")
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        papers_list.append({
            "paper_key": paper_key,
            "date": str(publish_time),
            "title_en": paper_title,
            "author": paper_first_author,
            "paper_id": paper_id,
            "paper_url": paper_url
        })
        
        if len(papers_list) >= limit:
            break
    
    if papers_list and TRANSLATION_AVAILABLE and GEMINI_API_KEY:
        print(f"\nTranslating {len(papers_list)} paper titles using Gemini API...")
        titles = [paper["title_en"] for paper in papers_list]
        translations = translate_titles_batch(titles)
        
        for paper in papers_list:
            paper["title_cn"] = translations.get(paper["title_en"], "")
    else:
        for paper in papers_list:
            paper["title_cn"] = ""
    
    for paper in papers_list:
        content[paper["paper_key"]] = {
            "date": str(paper["date"]),
            "title_en": str(paper["title_en"]),
            "title_cn": str(paper["title_cn"]) if paper.get("title_cn") else "",
            "author": str(paper["author"]),
            "paper_id": str(paper["paper_id"]),
            "paper_url": str(paper["paper_url"])
        }
    
    data = {topic: content}
    
    return data
