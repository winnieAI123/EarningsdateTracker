"""
Substack Search Collector
Adapted for AI News Pipeline
"""

import requests
import json
import csv
import time
import re
import os
import sys
import random
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote
from pathlib import Path

try:
    import cloudscraper
    # CLOUD_SCRAPER_AVAILABLE = True
    CLOUD_SCRAPER_AVAILABLE = False # Proven: Requests+Cookie works better than Cloudscraper here
except ImportError:
    CLOUD_SCRAPER_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# --- Inline Helpers to replace missing deps ---

class Logger:
    def __init__(self, name):
        self.name = name
    def info(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}][INFO][{self.name}] {msg}")
    def warning(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}][WARN][{self.name}] {msg}")
    def error(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}][ERR][{self.name}] {msg}")
    def section(self, msg):
        print(f"\n=== {msg} ===\n")

def get_output_filename(base_name, ext, output_dir=None):
    if not output_dir:
        output_dir = Path("data")
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{base_name}_{timestamp}.{ext}"

def save_to_csv(data, filename):
    if not data:
        return

    fieldnames = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} items to {filename}")

# --- Config Placeholder ---
class Config:
    PROXIES = {} # Add proxies here if needed

# ---------------------------------------------

class SubstackCollector:
    """Substack 数据采集器"""

    def __init__(self, use_proxy: bool = True):
        """
        初始化采集器

        Args:
            use_proxy: 是否使用代理
        """
        self.logger = Logger("SubstackCollector")
        self.base_url = "https://substack.com/api/v1/top/search"
        self.use_proxy = use_proxy
        self.proxies = {}  # Initialize proxies dictionary

        # Initial headers - will be rotated per request
        self.headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }

        # 1. Search Session (Always use Requests + Cookie)
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # 2. Content Scraper (Use Cloudscraper if available)
        self.scraper = None
        if CLOUD_SCRAPER_AVAILABLE:
            try:
                self.scraper = cloudscraper.create_scraper(
                    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
                )
                self.logger.info("已启用 Cloudscraper (仅用于文章内容抓取)")
            except Exception as e:
                self.logger.warning(f"Cloudscraper 初始化失败: {e}")
        else:
            self.logger.warning("未安装 cloudscraper，建议安装以绕过 Cloudflare (pip install cloudscraper)")

        # Load Cookies from config/api_keys.json
        try:
            # Locate api_keys.json relative to this script
            # Path: .../ai-news/sources/substack/substack_collector.py
            # Config: .../ai-news/config/api_keys.json
            current_dir = Path(__file__).parent.absolute()
            project_root = current_dir.parent.parent
            config_path = project_root / "config" / "api_keys.json"

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
                    cookie_str = keys.get("substack_cookie", "")

                    if cookie_str:
                        # Parse cookie string into dict
                        cookie_dict = {}
                        for item in cookie_str.split(';'):
                            if '=' in item:
                                k, v = item.strip().split('=', 1)
                                cookie_dict[k] = v.strip('"') # Strip quotes if present

                        # Apply to Search Session
                        self.session.cookies.update(cookie_dict)
                        # Apply to Scraper (if exists)
                        if self.scraper:
                            self.scraper.cookies.update(cookie_dict)

                        self.logger.info("已加载 Substack Cookie")
        except Exception as e:
            self.logger.warning(f"加载 Cookie 失败: {e}")

        # Proxy setup (if needed, cloudscraper handles proxies slightly differently but session.proxies works usually)
        if use_proxy and Config.PROXIES:
            self.proxies = Config.PROXIES
            self.session.proxies.update(self.proxies)
            if self.scraper:
                self.scraper.proxies.update(self.proxies)

        if not BS4_AVAILABLE:
            self.logger.warning("未安装 beautifulsoup4，无法解析文章内容")
            self.logger.info("安装命令: pip install beautifulsoup4")

    def _get_random_headers(self, url: str) -> Dict:
        """Generate headers to mimic browser behavior"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        return {
            'User-Agent': random.choice(user_agents),
            'Referer': 'https://substack.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def search(self, query: str, page: int = 0) -> Dict:
        """
        执行搜索请求
        """
        params = {
            'query': query,
            'fromSuggestedSearch': 'false'
        }

        if page > 0:
            params['page'] = page

        encoded_query = quote(query)
        self.session.headers['referer'] = f'https://substack.com/search/{encoded_query}?searching=top'

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                proxies=self.proxies,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            return {}

    def extract_comments(self, items: List[Dict]) -> List[Dict]:
        """从 items 中提取评论数据"""
        comments = []
        for item in items:
            if item.get('type') == 'comment' and 'comment' in item:
                comment_data = item['comment']
                comments.append({
                    'id': comment_data.get('id', ''),
                    'name': comment_data.get('name', ''),
                    'body': comment_data.get('body', ''),
                    'date': comment_data.get('date', ''),
                    'user_id': comment_data.get('user_id', ''),
                    'reactions': json.dumps(comment_data.get('reactions', {}), ensure_ascii=False),
                })
        return comments

    def extract_posts(self, items: List[Dict]) -> List[Dict]:
        """从 items 中提取文章数据，尽可能提取搜索结果中的内容"""
        posts = []
        for item in items:
            if item.get('type') == 'post' and 'post' in item:
                post_data = item['post']

                # 提取作者
                author = ''
                if post_data.get('publishedBylines'):
                    author = post_data['publishedBylines'][0].get('name', '')

                # 尝试从搜索结果中提取内容
                # 搜索 API 可能返回: body_html, truncated_body_text, description
                content = ''
                body_html = post_data.get('body_html', '')
                if body_html:
                    if BS4_AVAILABLE:
                        try:
                            soup = BeautifulSoup(body_html, 'html.parser')
                            content = soup.get_text(separator='\n', strip=True)
                        except:
                            content = re.sub(r'<[^>]+>', '', body_html)
                    else:
                        content = re.sub(r'<[^>]+>', '', body_html)

                # 如果没有 body_html，尝试其他字段
                if not content:
                    content = post_data.get('truncated_body_text', '')
                if not content:
                    content = post_data.get('body_text', '')

                posts.append({
                    'title': post_data.get('title', ''),
                    'subtitle': post_data.get('subtitle', ''),
                    'description': post_data.get('description', ''),
                    'canonical_url': post_data.get('canonical_url', ''),
                    'post_date': post_data.get('post_date', ''),
                    'publishedBylines': json.dumps(post_data.get('publishedBylines', []), ensure_ascii=False),
                    'publication_name': post_data.get('publishedBylines', [{}])[0].get('name', '') if post_data.get('publishedBylines') else '',
                    'author': author,
                    'content': content,
                    'word_count': post_data.get('wordcount', 0),
                    'is_paid': post_data.get('audience', '') == 'only_paid',
                })
        return posts

    def search_and_collect(
        self,
        query: str,
        target_comments: int = 20,
        target_posts: int = 20,
        max_pages: int = 10
    ) -> tuple:
        """
        搜索并收集数据
        """
        all_comments = []
        all_posts = []
        page = 0

        self.logger.info(f"搜索关键词: '{query}'")

        while page < max_pages:
            if len(all_comments) >= target_comments and len(all_posts) >= target_posts:
                break

            response_data = self.search(query, page)

            if not response_data or 'items' not in response_data:
                break

            items = response_data['items']
            if not items:
                break

            comments = self.extract_comments(items)
            posts = self.extract_posts(items)

            remaining_comments = target_comments - len(all_comments)
            remaining_posts = target_posts - len(all_posts)

            all_comments.extend(comments[:remaining_comments])
            all_posts.extend(posts[:remaining_posts])

            self.logger.info(f"  第 {page + 1} 页: 评论 {len(comments)}, 文章 {len(posts)} "
                           f"(累计: {len(all_comments)}/{target_comments}, {len(all_posts)}/{target_posts})")

            page += 1
            time.sleep(1)

        return all_comments[:target_comments], all_posts[:target_posts]

    def _parse_substack_url(self, url: str) -> Optional[Dict]:
        """
        解析 Substack URL，提取 subdomain 和 slug
        支持格式:
        - https://example.substack.com/p/article-slug
        - https://www.example.com/p/article-slug (自定义域名)
        """
        # Pattern for substack.com subdomain
        substack_pattern = r'https?://([^.]+)\.substack\.com/p/([^/?#]+)'
        # Pattern for custom domain
        custom_pattern = r'https?://(?:www\.)?([^/]+)/p/([^/?#]+)'

        match = re.match(substack_pattern, url)
        if match:
            return {
                'subdomain': match.group(1),
                'slug': match.group(2),
                'base_url': f"https://{match.group(1)}.substack.com"
            }

        match = re.match(custom_pattern, url)
        if match:
            return {
                'subdomain': None,  # Custom domain
                'slug': match.group(2),
                'base_url': f"https://{match.group(1)}"
            }

        return None

    def _fetch_via_api(self, url: str) -> Optional[Dict]:
        """
        通过 Substack API 获取文章内容
        API 端点: {base_url}/api/v1/posts/{slug}
        """
        parsed = self._parse_substack_url(url)
        if not parsed:
            return None

        api_url = f"{parsed['base_url']}/api/v1/posts/{parsed['slug']}"

        try:
            headers = {
                'Accept': 'application/json',
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                ]),
                'Referer': url,
            }

            response = self.session.get(api_url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # 提取作者
                author = ""
                if 'publishedBylines' in data and data['publishedBylines']:
                    author = data['publishedBylines'][0].get('name', '')

                # 提取内容 - API 返回 body_html
                content = ""
                body_html = data.get('body_html', '')
                if body_html and BS4_AVAILABLE:
                    soup = BeautifulSoup(body_html, 'html.parser')
                    content = soup.get_text(separator='\n', strip=True)
                elif body_html:
                    # 简单去除 HTML 标签
                    content = re.sub(r'<[^>]+>', '', body_html)
                    content = re.sub(r'\s+', ' ', content).strip()

                # 如果没有 body_html，尝试 truncated_body_text
                if not content:
                    content = data.get('truncated_body_text', '')

                self.logger.info(f"  [API] 成功获取: {len(content)} 字符")
                return {'author': author, 'content': content}

            return None

        except Exception as e:
            self.logger.warning(f"[API] 请求失败: {e}")
            return None

    def _fetch_via_embedded_json(self, html: str, url: str) -> Optional[Dict]:
        """
        从 HTML 中提取嵌入的 JSON 数据
        Substack 页面包含 window.__PRELOADED_STATE__ 或 JSON-LD
        """
        # 方法1: 尝试提取 JSON-LD (schema.org)
        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(html, 'html.parser')
                json_ld = soup.find('script', type='application/ld+json')
                if json_ld:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):
                        data = data[0]

                    content = data.get('articleBody', '')
                    author = ''
                    if 'author' in data:
                        author_data = data['author']
                        if isinstance(author_data, list) and author_data:
                            author = author_data[0].get('name', '')
                        elif isinstance(author_data, dict):
                            author = author_data.get('name', '')

                    if content:
                        self.logger.info(f"  [JSON-LD] 成功获取: {len(content)} 字符")
                        return {'author': author, 'content': content}
            except Exception as e:
                pass

        # 方法2: 尝试提取 window.__PRELOADED_STATE__
        try:
            pattern = r'window\.__PRELOADED_STATE__\s*=\s*({.*?});?\s*</script>'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                state_json = match.group(1)
                # 这个 JSON 可能很大，尝试提取文章部分
                state = json.loads(state_json)

                # 查找 post 数据
                post_data = None
                if 'post' in state:
                    post_data = state['post']
                elif 'posts' in state and state['posts']:
                    post_data = list(state['posts'].values())[0] if isinstance(state['posts'], dict) else state['posts'][0]

                if post_data:
                    content = ''
                    body_html = post_data.get('body_html', '')
                    if body_html and BS4_AVAILABLE:
                        soup = BeautifulSoup(body_html, 'html.parser')
                        content = soup.get_text(separator='\n', strip=True)
                    elif body_html:
                        content = re.sub(r'<[^>]+>', '', body_html)

                    author = ''
                    if 'publishedBylines' in post_data and post_data['publishedBylines']:
                        author = post_data['publishedBylines'][0].get('name', '')

                    if content:
                        self.logger.info(f"  [PRELOADED] 成功获取: {len(content)} 字符")
                        return {'author': author, 'content': content}
        except Exception as e:
            pass

        return None

    def _fetch_via_html_parsing(self, html: str) -> Optional[Dict]:
        """
        传统 HTML 解析方法（备用）
        """
        if not BS4_AVAILABLE:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 提取作者 - 更新选择器
            author = ""
            author_selectors = [
                'div.byline-wrapper a[href*="@"]',
                'a.pencraft[href*="substack.com/@"]',
                '.post-header a[href*="@"]',
                'a[data-testid="post-author-link"]',
                '.author-name',
                'meta[name="author"]',
            ]
            for selector in author_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        author = meta.get('content', '')
                        break
                else:
                    author_links = soup.select(selector)
                    for author_link in author_links:
                        author_text = author_link.get_text(strip=True)
                        if author_text and author_text not in ['', 'View profile', 'Subscribe']:
                            author = author_text
                            break
                if author:
                    break

            # 提取正文 - 更新选择器
            content = ""
            body_selectors = [
                'div.body.markup',
                'div.post-content',
                'article.post',
                'div[class*="body"]',
                '.available-content',
                'div.post',
            ]
            for selector in body_selectors:
                body_elem = soup.select_one(selector)
                if body_elem:
                    # 移除不需要的元素
                    for unwanted in body_elem.select('script, style, nav, footer, .subscription-widget'):
                        unwanted.decompose()
                    content = body_elem.get_text(separator='\n', strip=True)
                    if len(content) > 100:  # 确保有足够内容
                        break

            if content:
                self.logger.info(f"  [HTML] 成功获取: {len(content)} 字符")
                return {'author': author, 'content': content}

        except Exception as e:
            pass

        return None

    def fetch_post_content(self, url: str) -> Optional[Dict]:
        """
        获取文章内容 - 多策略尝试
        优先级: API > 嵌入JSON > HTML解析
        """
        # 策略1: 尝试 API (最可靠，不需要 JS 渲染)
        result = self._fetch_via_api(url)
        if result and result.get('content'):
            return result

        # 策略2 & 3: 需要先获取 HTML
        client = self.scraper if self.scraper else self.session
        client_name = "Cloudscraper" if self.scraper else "Requests"

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                headers = self._get_random_headers(url)
                response = client.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                html = response.text

                # 策略2: 从嵌入的 JSON 提取
                result = self._fetch_via_embedded_json(html, url)
                if result and result.get('content'):
                    return result

                # 策略3: 传统 HTML 解析
                result = self._fetch_via_html_parsing(html)
                if result and result.get('content'):
                    return result

                # 如果都失败了，可能是付费内容
                self.logger.warning(f"  无法提取内容（可能是付费文章）: {url}")
                return {'author': '', 'content': ''}

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    self.logger.warning(f"  [403] 被反爬虫拦截: {url}")
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 5
                        self.logger.info(f"  等待 {wait_time}s 后重试...")
                        time.sleep(wait_time)
                        continue
                else:
                    self.logger.warning(f"  [{client_name}] HTTP错误 {e.response.status_code}: {url}")
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"  [{client_name}] 错误: {e}, 重试中...")
                    time.sleep(3)
                else:
                    self.logger.warning(f"  [{client_name}] 获取失败: {e}")

        return None

    def fetch_all_posts_content(self, posts: List[Dict], min_content_length: int = 200) -> List[Dict]:
        """
        批量获取文章内容
        只获取内容为空或太短的文章（搜索结果可能已包含部分内容）

        Args:
            posts: 文章列表
            min_content_length: 最小内容长度阈值，低于此值会重新获取
        """
        # 统计需要获取的文章数
        posts_to_fetch = [
            p for p in posts
            if len(p.get('content', '')) < min_content_length and not p.get('is_paid', False)
        ]

        if not posts_to_fetch:
            self.logger.info(f"所有 {len(posts)} 篇文章已有足够内容，无需额外获取")
            return posts

        self.logger.info(f"需要获取 {len(posts_to_fetch)}/{len(posts)} 篇文章的完整内容...")

        fetched_count = 0
        for i, post in enumerate(posts, 1):
            url = post.get('canonical_url', '')
            if not url:
                continue

            # 跳过已有足够内容的文章
            current_content_len = len(post.get('content', ''))
            if current_content_len >= min_content_length:
                self.logger.info(f"  [{i}/{len(posts)}] 跳过 (已有 {current_content_len} 字符): {post.get('title', '')[:40]}...")
                continue

            # 跳过付费文章
            if post.get('is_paid', False):
                self.logger.info(f"  [{i}/{len(posts)}] 跳过付费文章: {post.get('title', '')[:40]}...")
                continue

            self.logger.info(f"  [{i}/{len(posts)}] 获取: {post.get('title', '')[:50]}...")

            content_data = self.fetch_post_content(url)
            if content_data:
                # 只在获取到更多内容时更新
                new_content = content_data.get('content', '')
                if len(new_content) > current_content_len:
                    post['content'] = new_content
                if content_data.get('author') and not post.get('author'):
                    post['author'] = content_data.get('author', '')
                fetched_count += 1

            # 添加随机延迟
            time.sleep(random.uniform(1.5, 4))

        self.logger.info(f"完成! 成功获取 {fetched_count} 篇文章内容")
        return posts

    def collect_by_keywords(
        self,
        keywords: List[str],
        domain: str = "AI",
        comments_per_keyword: int = 20,
        posts_per_keyword: int = 20,
        fetch_content: bool = True,
        output_dir: Optional[Path] = None
    ) -> tuple:
        """
        Standalone collection method used when running this script directly
        """
        # ... logic if needed, or simply map to search_and_collect ...
        # For pipeline usage, search_and_collect + fetch_all_posts_content is enough.
        pass

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "large language model training"  # Default query

    print(f"=" * 60)
    print(f"Testing SubstackCollector")
    print(f"Query: {query}")
    print(f"=" * 60)

    collector = SubstackCollector(use_proxy=False)  # Disable proxy for testing

    # 1. Search
    print("\n[Step 1] Searching...")
    comments, posts = collector.search_and_collect(query, target_posts=5, target_comments=0)
    print(f"Found {len(posts)} posts from search.")

    # Show initial content status
    print("\n[Step 2] Initial content status from search API:")
    for i, p in enumerate(posts, 1):
        content_len = len(p.get('content', ''))
        status = "Has content" if content_len > 100 else "Needs fetch"
        print(f"  {i}. [{status}] ({content_len} chars) {p.get('title', '')[:50]}...")

    # 2. Fetch Content for posts without enough content
    if posts:
        print("\n[Step 3] Fetching full content for articles without enough content...")
        posts = collector.fetch_all_posts_content(posts, min_content_length=200)

        # 3. Final Verification
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        success_count = 0
        for i, p in enumerate(posts, 1):
            content_len = len(p.get('content', ''))
            is_paid = p.get('is_paid', False)

            if content_len > 100:
                status = "OK"
                success_count += 1
            elif is_paid:
                status = "PAID"
            else:
                status = "FAIL"

            print(f"\n{i}. [{status}] {p.get('title', '')}")
            print(f"   Author: {p.get('author', 'N/A')}")
            print(f"   URL: {p.get('canonical_url', 'N/A')}")
            print(f"   Content: {content_len} characters")
            if content_len > 0:
                preview = p.get('content', '')[:150].replace('\n', ' ')
                print(f"   Preview: {preview}...")

        print(f"\n{'=' * 60}")
        print(f"Summary: {success_count}/{len(posts)} articles fetched successfully")
        print(f"{'=' * 60}")
