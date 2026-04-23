#!/usr/bin/env python3
"""
WordPress XML to HTML/Markdown Converter
Converts WordPress XML export files to HTML or Markdown with index

Usage:
    python3 wp-exporter.py input.xml output.html
"""

import sys
import xml.etree.ElementTree as ET
import re
import requests
import cloudscraper
import json
import base64
from pathlib import Path

def validate_files(input_file, output_file, export_format='html'):
    """Validate input and output files"""
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' does not exist", file=sys.stderr)
        return False
    
    if not input_file.lower().endswith('.xml'):
        print(f"Error: Input file must be .xml", file=sys.stderr)
        return False
    
    if export_format == 'markdown':
        if not output_file.lower().endswith('.md'):
            print(f"Error: Output file must be .md for Markdown format", file=sys.stderr)
            return False
    else:
        if not output_file.lower().endswith('.html'):
            print(f"Error: Output file must be .html", file=sys.stderr)
            return False
    
    return True

def clean_article_content(content, clean_shortcodes=False):
    """Clean HTML while preserving basic structure"""
    clean_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    clean_content = re.sub(r'<style[^>]*>.*?</style>', '', clean_content, flags=re.DOTALL)
    
    # Clean plugin shortcodes if requested
    if clean_shortcodes:
        # Clean fusion_builder shortcodes
        clean_content = re.sub(r'\[fusion_builder_[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[/fusion_builder_[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[fusion_builder_[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[fusion_content_boxes[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[fusion_content_box[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[fusion_builder_row[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[fusion_builder_column[^\]]*\]', '', clean_content)
        clean_content = re.sub(r'\[/fusion_content_boxes\]', '', clean_content)
        clean_content = re.sub(r'\[/fusion_content_box\]', '', clean_content)
        clean_content = re.sub(r'\[/fusion_builder_row\]', '', clean_content)
        clean_content = re.sub(r'\[/fusion_builder_column\]', '', clean_content)
        
        # Clean other common shortcodes
        clean_content = re.sub(r'\[[^\]]*\]', '', clean_content)
    
    # Convert heading tags
    clean_content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'<h4>\1</h4>', clean_content, flags=re.DOTALL)
    
    # Preserve paragraphs
    clean_content = re.sub(r'<p[^>]*>(.*?)</p>', r'<p>\1</p>', clean_content, flags=re.DOTALL)
    
    # Convert line breaks to paragraphs
    clean_content = re.sub(r'\n\n+', '</p><p>', clean_content)
    clean_content = re.sub(r'\n', '<br>', clean_content)
    
    # Clean remaining tags
    clean_content = re.sub(r'<(?!p|/p|h[1-6]|/h[1-6]|br)[^>]*>', '', clean_content)
    
    # Clean multiple spaces
    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
    
    # Wrap in paragraph if not already
    if not clean_content.startswith('<p>'):
        clean_content = f'<p>{clean_content}</p>'
    
    return clean_content

def extract_articles(xml_file, clean_shortcodes=False):
    """Extract articles from WordPress XML"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        namespace = {
            'wp': 'http://wordpress.org/export/1.2/', 
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        articles = []
        
        for item in root.findall('.//item'):
            # Only published posts
            status = item.find('wp:status', namespace)
            if status is None or status.text != 'publish':
                continue
                
            post_type = item.find('wp:post_type', namespace)
            if post_type is None or post_type.text != 'post':
                continue
            
            # Extract title
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else 'Untitled'
            
            # Extract content
            content_elem = item.find('content:encoded', namespace)
            content = content_elem.text if content_elem is not None else ''
            
            # Extract categories and tags
            categories = []
            tags = []
            for cat in item.findall('category'):
                domain = cat.get('domain')
                cat_name = cat.text
                if cat_name:
                    if domain == 'category':
                        categories.append(cat_name)
                    elif domain == 'post_tag':
                        tags.append(cat_name)
            
            # Extract additional metadata
            pub_date_elem = item.find('pubDate')
            pub_date = pub_date_elem.text if pub_date_elem is not None else ''
            
            author_elem = item.find('dc:creator', {'dc': 'http://purl.org/dc/elements/1.1/'})
            author = author_elem.text if author_elem is not None else ''
            
            # Extract excerpt/description
            excerpt_elem = item.find('excerpt:encoded', namespace)
            excerpt = excerpt_elem.text if excerpt_elem is not None else ''
            
            # Extract meta description (first 160 characters of content)
            content_text = re.sub(r'<[^>]+>', '', content).strip()
            meta_description = content_text[:160] + '...' if len(content_text) > 160 else content_text
            
            clean_content = clean_article_content(content, clean_shortcodes)
            
            articles.append({
                'title': title,
                'content': clean_content,
                'original_content': content,
                'categories': categories,
                'tags': tags,
                'pub_date': pub_date,
                'author': author,
                'excerpt': excerpt,
                'meta_description': meta_description,
                'word_count': len(content_text.split())
            })
        
        return articles
        
    except Exception as e:
        print(f"Error processing XML: {e}", file=sys.stderr)
        return []

def categorize_articles(articles, num_categories):
    """Organize articles into detected categories"""
    # Collect all unique categories
    all_categories = set()
    for article in articles:
        for cat in article['categories']:
            all_categories.add(cat)
    
    # If no categories, return uncategorized articles
    if not all_categories:
        return {'Uncategorized': articles}
    
    # Convert to list and sort by frequency
    category_counts = {}
    for cat in all_categories:
        category_counts[cat] = 0
    
    for article in articles:
        for cat in article['categories']:
            category_counts[cat] += 1
    
    # Sort categories by number of articles
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Take the n most common categories
    top_categories = [cat[0] for cat in sorted_categories[:num_categories]]
    
    # Group articles by categories
    categorized_articles = {}
    
    # Initialize selected categories
    for cat in top_categories:
        categorized_articles[cat] = []
    
    # Category for articles without category or with non-selected categories
    categorized_articles['Other'] = []
    
    for article in articles:
        placed = False
        # If article has categories, try to place it in first selected category
        for cat in article['categories']:
            if cat in top_categories:
                categorized_articles[cat].append(article)
                placed = True
                break
        
        # If not placed, goes to "Other"
        if not placed:
            categorized_articles['Other'].append(article)
    
    # Remove empty categories
    categorized_articles = {k: v for k, v in categorized_articles.items() if v}
    
    return categorized_articles

def filter_articles(articles, filters):
    """Filter articles according to specified criteria"""
    filtered_articles = []
    
    for article in articles:
        include = True
        
        # Filter by date range
        if filters.get('date_start') or filters.get('date_end'):
            pub_date = article.get('pub_date', '')
            if pub_date:
                try:
                    # Parse date (typical format: Wed, 15 Mar 2023 10:30:00 +0000)
                    import datetime
                    date_obj = datetime.datetime.strptime(pub_date[:25], '%a, %d %b %Y %H:%M:%S')
                    
                    if filters.get('date_start'):
                        start_date = datetime.datetime.strptime(filters['date_start'], '%Y-%m-%d')
                        if date_obj.date() < start_date.date():
                            include = False
                    
                    if filters.get('date_end'):
                        end_date = datetime.datetime.strptime(filters['date_end'], '%Y-%m-%d')
                        if date_obj.date() > end_date.date():
                            include = False
                except:
                    pass  # If can't parse date, include article
        
        # Filter by author
        if filters.get('author') and article.get('author', '').lower() != filters['author'].lower():
            include = False
        
        # Filter by tags
        if filters.get('tags'):
            article_tags = [tag.lower() for tag in article.get('tags', [])]
            filter_tags = [tag.lower() for tag in filters['tags']]
            if not any(tag in article_tags for tag in filter_tags):
                include = False
        
        # Filter by categories
        if filters.get('categories'):
            article_categories = [cat.lower() for cat in article.get('categories', [])]
            filter_categories = [cat.lower() for cat in filters['categories']]
            if not any(cat in article_categories for cat in filter_categories):
                include = False
        
        # Filter by minimum length
        if filters.get('min_length'):
            word_count = article.get('word_count', 0)
            if word_count < filters['min_length']:
                include = False
        
        if include:
            filtered_articles.append(article)
    
    return filtered_articles

class WordPressAPIClient:
    """WordPress REST API client for live content extraction"""
    
    def __init__(self, domain, username=None, password=None, use_cloudscraper=True):
        self.domain = domain.rstrip('/')
        self.username = username
        self.password = password
        self.use_cloudscraper = use_cloudscraper
        
        if use_cloudscraper:
            try:
                self.session = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'desktop': True
                    },
                    delay=10
                )
                print("🔧 Using cloudscraper for Cloudflare bypass")
            except Exception as e:
                print(f"⚠️ Cloudscraper failed, falling back to requests: {e}")
                self.session = requests.Session()
                self.use_cloudscraper = False
        else:
            self.session = requests.Session()
            print("🔧 Using standard requests (no Cloudflare bypass)")
            
        self.api_base = f"{self.domain}/wp-json/wp/v2"
        
        # Add headers with Cloudflare rule
        headers = {
            'User-Agent': 'wp-exporter',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session.headers.update(headers)
        
    def authenticate(self):
        """Authenticate with WordPress REST API using HTTP Basic Auth"""
        if not self.username or not self.password:
            raise ValueError("Username and password required for authentication")
        
        # Use HTTP Basic Authentication (same as curl -u)
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        # Set authorization header for Basic Auth
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}'
        })
        
        try:
            response = self.session.get(f"{self.api_base}/users/me", timeout=10)
            if response.status_code == 200:
                print(f"✅ Successfully authenticated with {self.domain}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_cloudflare_cookies(self):
        """Get Cloudflare cookies by visiting main page first"""
        try:
            response = self.session.get(self.domain, timeout=15)
            
            # If we get a challenge page, cloudscraper should handle it
            if response.status_code == 200:
                return True
            else:
                if response.status_code == 403:
                    print(f"🛡️ Cloudflare protection detected on {self.domain}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error accessing {self.domain}: {e}")
            return False
    
    def test_connection(self):
        """Test if WordPress REST API is available"""
        # First try to get Cloudflare cookies
        if not self.get_cloudflare_cookies():
            return False
            
        try:
            response = self.session.get(f"{self.api_base}", timeout=10)
            if response.status_code == 200:
                print(f"✅ WordPress REST API available at {self.domain}")
                return True
            else:
                print(f"❌ WordPress REST API not available (HTTP {response.status_code})")
                if response.status_code == 403:
                    print("🛡️ This may be due to Cloudflare protection or access restrictions")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to {self.domain}: {e}")
            return False
    
    def get_posts(self, per_page=100, page=1, status='publish'):
        """Get posts from WordPress API"""
        try:
            params = {
                'per_page': per_page,
                'page': page,
                'status': status,
                '_embed': True  # Include embedded data like author, categories
            }
            
            response = self.session.get(f"{self.api_base}/posts", params=params)
            
            if response.status_code == 200:
                posts = response.json()
                print(f"📥 Retrieved {len(posts)} posts from page {page}")
                return posts
            else:
                print(f"❌ Error fetching posts: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching posts: {e}")
            return []
    
    def get_all_posts(self, status='publish'):
        """Get all posts with pagination"""
        all_posts = []
        page = 1
        per_page = 100
        
        while True:
            posts = self.get_posts(per_page=per_page, page=page, status=status)
            if not posts:
                break
            
            all_posts.extend(posts)
            
            # Check if we got all posts (less than per_page means last page)
            if len(posts) < per_page:
                break
                
            page += 1
            
            # Safety check to prevent infinite loops
            if page > 1000:
                print("⚠️  Reached page limit, stopping pagination")
                break
        
        print(f"✅ Total posts retrieved: {len(all_posts)}")
        return all_posts
    
    def get_categories(self):
        """Get all categories"""
        try:
            response = self.session.get(f"{self.api_base}/categories", params={'per_page': 100})
            if response.status_code == 200:
                categories = response.json()
                return categories
            else:
                print(f"❌ Error fetching categories: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching categories: {e}")
            return []
    
    def get_tags(self):
        """Get all tags"""
        try:
            response = self.session.get(f"{self.api_base}/tags", params={'per_page': 100})
            if response.status_code == 200:
                tags = response.json()
                return tags
            else:
                print(f"❌ Error fetching tags: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching tags: {e}")
            return []
    
    def convert_api_post_to_article(self, post):
        """Convert WordPress API post to article format"""
        # Extract categories
        categories = []
        if 'categories' in post and post['categories']:
            for cat in post['categories']:
                categories.append(cat['name'])
        
        # Extract tags
        tags = []
        if 'tags' in post and post['tags']:
            for tag in post['tags']:
                tags.append(tag['name'])
        
        # Extract author
        author = ''
        if 'author' in post and post['author']:
            author = post['author']['name']
        
        # Extract content
        content = post['content']['rendered'] if 'content' in post else ''
        title = post['title']['rendered'] if 'title' in post else 'Untitled'
        
        # Extract date
        pub_date = post['date'] if 'date' in post else ''
        
        # Extract excerpt
        excerpt = post['excerpt']['rendered'] if 'excerpt' in post else ''
        
        # Generate meta description
        content_text = re.sub(r'<[^>]+>', '', content).strip()
        meta_description = content_text[:160] + '...' if len(content_text) > 160 else content_text
        
        return {
            'title': title,
            'content': content,
            'original_content': content,
            'categories': categories,
            'tags': tags,
            'pub_date': pub_date,
            'author': author,
            'excerpt': excerpt,
            'meta_description': meta_description,
            'word_count': len(content_text.split())
        }

def extract_from_web(domain, auth_credentials, list_categories=False):
    """Extract articles from WordPress REST API"""
    # Parse authentication credentials
    if ':' not in auth_credentials:
        print("Error: --auth format should be username:password", file=sys.stderr)
        print("For application passwords, use: username:'app password with spaces'", file=sys.stderr)
        return None, None
    
    # Handle application passwords with spaces (enclosed in quotes)
    if "'" in auth_credentials or '"' in auth_credentials:
        # Handle quoted application passwords
        if "'" in auth_credentials:
            username, password = auth_credentials.split("'", 1)
            username = username.rstrip(':')
            password = password.rstrip("'")
        else:
            username, password = auth_credentials.split('"', 1)
            username = username.rstrip(':')
            password = password.rstrip('"')
    else:
        # Handle regular passwords
        username, password = auth_credentials.split(':', 1)
    
    # Create WordPress API client
    wp_client = WordPressAPIClient(domain, username, password)
    
    # Test connection
    if not wp_client.test_connection():
        return None, None
    
    # For public sites, authentication may not be required
    # Try to access posts first, then authenticate if needed
    try:
        posts = wp_client.get_posts(per_page=1)  # Try to get one post
        if posts:
            print(f"✅ Public access available - no authentication needed")
        else:
            print(f"🔐 Authentication required for this site")
            if not wp_client.authenticate():
                return None, None
    except:
        # If posts access fails, try authentication
        print(f"🔐 Authentication required for this site")
        if not wp_client.authenticate():
            return None, None
    
    # Handle category listing for API
    if list_categories:
        print(f"📖 Analyzing categories from: {domain}")
        categories = wp_client.get_categories()
        if categories:
            print("\n" + "="*60)
            print("📂 AVAILABLE CATEGORIES")
            print("="*60)
            print(f"Total unique categories: {len(categories)}")
            print("\nCategories (sorted by name):")
            print("-" * 60)
            
            for i, category in enumerate(sorted(categories, key=lambda x: x['count'], reverse=True), 1):
                print(f"{i:2d}. {category['name']:<30} ({category['count']} posts)")
            
            print("-" * 60)
            print("\n💡 Usage suggestions:")
            print("   • To extract top 5 categories: --cat 5")
            print("   • To extract specific categories: --categories \"Insurance,Financial\"")
            print("   • To filter by one category: --categories \"Insurance\"")
            print("="*60)
        else:
            print("❌ No categories found")
        return None, "categories_listed"
    
    # Extract articles from API
    print(f"📥 Extracting articles from: {domain}")
    api_posts = wp_client.get_all_posts()
    
    if not api_posts:
        return None, None
    
    # Convert API posts to article format
    articles = []
    for post in api_posts:
        article = wp_client.convert_api_post_to_article(post)
        articles.append(article)
    
    print(f"✅ Successfully extracted {len(articles)} articles")
    return articles, "web"

def extract_from_file(input_file, clean_shortcodes=False, list_categories=False):
    """Extract articles from XML file"""
    if list_categories:
        print(f"📖 Analyzing categories in: {input_file}")
        list_all_categories(input_file)
        return None, "categories_listed"
    
    print(f"📖 Processing file: {input_file}")
    
    if clean_shortcodes:
        print("🧹 Cleaning plugin shortcodes...")
    
    # Extraer artículos
    articles = extract_articles(input_file, clean_shortcodes)
    return articles, "file"

def process_articles(articles, filters, num_categories, show_stats, clean_shortcodes=False):
    """Common processing logic for articles from any source"""
    if not articles:
        return None
    
    print(f"✅ Found {len(articles)} articles")
    
    # Apply filters if requested
    if filters:
        original_count = len(articles)
        articles = filter_articles(articles, filters)
        print(f"🎯 Articles after filtering: {len(articles)} (removed {original_count - len(articles)})")
    
    # Show statistics if requested
    if show_stats:
        stats = generate_statistics(articles)
        print_statistics(stats)
    
    # Categorize articles if requested
    categorized_articles = None
    if num_categories:
        categorized_articles = categorize_articles(articles, num_categories)
        print(f"📋 Categories found: {list(categorized_articles.keys())}")
    
    return articles, categorized_articles

def list_all_categories(xml_file):
    """Lista todas las categorías disponibles en el XML"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        namespace = {
            'wp': 'http://wordpress.org/export/1.2/', 
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        from collections import Counter
        all_categories = []
        category_counts = Counter()
        
        for item in root.findall('.//item'):
            # Solo posts publicados
            status = item.find('wp:status', namespace)
            if status is None or status.text != 'publish':
                continue
                
            post_type = item.find('wp:post_type', namespace)
            if post_type is None or post_type.text != 'post':
                continue
            
            # Extraer categorías
            for cat in item.findall('category'):
                domain = cat.get('domain')
                if domain == 'category':
                    cat_name = cat.text
                    if cat_name:
                        all_categories.append(cat_name)
                        category_counts[cat_name] += 1
        
        if not all_categories:
            print("❌ No se encontraron categorías en el archivo XML", file=sys.stderr)
            return
        
        # Ordenar por frecuencia
        sorted_categories = category_counts.most_common()
        
        print("\n" + "="*60)
        print("📂 CATEGORÍAS DISPONIBLES")
        print("="*60)
        print(f"Total de categorías únicas: {len(sorted_categories)}")
        print(f"Total de artículos categorizados: {sum(count for _, count in sorted_categories)}")
        print("\nCategorías (ordenadas por número de artículos):")
        print("-" * 60)
        
        for i, (category, count) in enumerate(sorted_categories, 1):
            print(f"{i:2d}. {category:<30} ({count} artículos)")
        
        print("-" * 60)
        print("\n💡 Sugerencias de uso:")
        print("   • Para extraer las 5 categorías principales: --cat 5")
        print("   • Para extraer categorías específicas: --categories \"Seguros,Insurance\"")
        print("   • Para filtrar por una categoría: --categories \"Seguros\"")
        print("="*60)
        
    except Exception as e:
        print(f"Error processing XML: {e}", file=sys.stderr)

def generate_statistics(articles):
    """Genera estadísticas detalladas del contenido"""
    import json
    from collections import Counter
    
    stats = {
        'total_articles': len(articles),
        'word_count_stats': {},
        'categories': {},
        'tags': {},
        'authors': {},
        'publication_dates': {},
        'content_analysis': {}
    }
    
    if not articles:
        return stats
    
    # Análisis de conteo de palabras
    word_counts = [article.get('word_count', 0) for article in articles]
    stats['word_count_stats'] = {
        'total_words': sum(word_counts),
        'average_words': sum(word_counts) / len(word_counts),
        'min_words': min(word_counts),
        'max_words': max(word_counts),
        'median_words': sorted(word_counts)[len(word_counts) // 2]
    }
    
    # Análisis de categorías
    all_categories = []
    for article in articles:
        all_categories.extend(article.get('categories', []))
    category_counts = Counter(all_categories)
    stats['categories'] = {
        'total_unique': len(category_counts),
        'most_common': category_counts.most_common(10),
        'distribution': dict(category_counts)
    }
    
    # Análisis de tags
    all_tags = []
    for article in articles:
        all_tags.extend(article.get('tags', []))
    tag_counts = Counter(all_tags)
    stats['tags'] = {
        'total_unique': len(tag_counts),
        'most_common': tag_counts.most_common(15),
        'distribution': dict(tag_counts)
    }
    
    # Análisis de autores
    authors = [article.get('author', 'Desconocido') for article in articles]
    author_counts = Counter(authors)
    stats['authors'] = {
        'total_unique': len(author_counts),
        'most_common': author_counts.most_common(),
        'distribution': dict(author_counts)
    }
    
    # Análisis de fechas de publicación
    dates = [article.get('pub_date', '') for article in articles if article.get('pub_date')]
    if dates:
        try:
            import datetime
            date_objects = []
            for date_str in dates:
                try:
                    date_obj = datetime.datetime.strptime(date_str[:25], '%a, %d %b %Y %H:%M:%S')
                    date_objects.append(date_obj)
                except:
                    continue
            
            if date_objects:
                years = [d.year for d in date_objects]
                year_counts = Counter(years)
                stats['publication_dates'] = {
                    'date_range': {
                        'earliest': min(date_objects).strftime('%Y-%m-%d'),
                        'latest': max(date_objects).strftime('%Y-%m-%d')
                    },
                    'total_with_dates': len(date_objects),
                    'by_year': dict(year_counts)
                }
        except:
            stats['publication_dates'] = {'error': 'Could not parse dates'}
    
    # Análisis de contenido
    stats['content_analysis'] = {
        'avg_reading_time_minutes': round(stats['word_count_stats']['average_words'] / 200, 1),  # 200 WPM average
        'total_reading_time_hours': round(stats['word_count_stats']['total_words'] / 200 / 60, 1),
        'articles_with_categories': len([a for a in articles if a.get('categories')]),
        'articles_with_tags': len([a for a in articles if a.get('tags')]),
        'articles_with_author': len([a for a in articles if a.get('author')]),
        'articles_with_dates': len([a for a in articles if a.get('pub_date')])
    }
    
    return stats

def print_statistics(stats):
    """Imprime estadísticas de forma legible"""
    print("\n" + "="*50)
    print("📊 ESTADÍSTICAS DEL CONTENIDO")
    print("="*50)
    
    print(f"📝 Total de artículos: {stats['total_articles']}")
    
    if stats['word_count_stats']:
        wcs = stats['word_count_stats']
        print(f"\n📈 Análisis de palabras:")
        print(f"   Total palabras: {wcs['total_words']:,}")
        print(f"   Promedio por artículo: {wcs['average_words']:.0f}")
        print(f"   Artículo más corto: {wcs['min_words']} palabras")
        print(f"   Artículo más largo: {wcs['max_words']} palabras")
        print(f"   Tiempo lectura total: {stats['content_analysis']['total_reading_time_hours']} horas")
    
    if stats['categories']['most_common']:
        print(f"\n📂 Categorías principales:")
        for cat, count in stats['categories']['most_common'][:5]:
            print(f"   {cat}: {count} artículos")
    
    if stats['tags']['most_common']:
        print(f"\n🏷️  Tags principales:")
        for tag, count in stats['tags']['most_common'][:5]:
            print(f"   {tag}: {count} artículos")
    
    if stats['authors']['most_common']:
        print(f"\n✍️  Autores:")
        for author, count in stats['authors']['most_common']:
            print(f"   {author}: {count} artículos")
    
    if stats['publication_dates'].get('date_range'):
        dr = stats['publication_dates']['date_range']
        print(f"\n📅 Rango de fechas:")
        print(f"   Desde: {dr['earliest']}")
        print(f"   Hasta: {dr['latest']}")
    
    print("="*50)

def generate_html(articles, output_file, categorized_articles=None, template_file=None, css_file=None, branding_text=None):
    """Genera HTML con índice y contenido"""
    
    # Cargar CSS personalizado si se especifica
    custom_css = ""
    if css_file:
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                custom_css = f.read()
            print(f"✅ CSS cargado: {css_file}")
        except Exception as e:
            print(f"⚠️  No se pudo cargar CSS: {e}")
    
    # Determinar texto de marca
    site_title = branding_text if branding_text else "WordPress Export"
    
    if categorized_articles:
        # Generar índice categorizado
        index_html = ""
        article_counter = 0
        
        for category, category_articles in categorized_articles.items():
            index_html += f'        <li><strong>{category} ({len(category_articles)})</strong></li>\n'
            index_html += f'        <ul class="subcategory">\n'
            
            for article in category_articles:
                article_id = f"articulo_{article_counter}"
                index_html += f'            <li><a href="#{article_id}">{article["title"]}</a></li>\n'
                article_counter += 1
            
            index_html += f'        </ul>\n'
        
        # Generar contenido categorizado
        content_html = ""
        article_counter = 0
        
        for category, category_articles in categorized_articles.items():
            content_html += f'    <section class="category-section">\n'
            content_html += f'        <h2 class="category-title">{category} <span class="article-count">({len(category_articles)})</span></h2>\n'
            
            for article in category_articles:
                article_id = f"articulo_{article_counter}"
                content_html += f'        <article id="{article_id}">\n'
                content_html += f'            <h3>{article["title"]}</h3>\n'
                content_html += f'            <div class="contenido">\n'
                content_html += f'                {article["content"]}\n'
                content_html += f'            </div>\n'
                content_html += f'            <div class="volver-indice">\n'
                content_html += f'                <a href="#indice" title="Volver al índice">←</a>\n'
                content_html += f'            </div>\n'
                content_html += f'        </article>\n\n'
                article_counter += 1
            
            content_html += f'    </section>\n\n'
    else:
        # Generar índice normal
        index_html = ""
        for i, article in enumerate(articles):
            article_id = f"articulo_{i}"
            index_html += f'        <li><a href="#{article_id}">{article["title"]}</a></li>\n'
        
        # Generar contenido normal
        content_html = ""
        for i, article in enumerate(articles):
            article_id = f"articulo_{i}"
            content_html += f'    <article id="{article_id}">\n'
            content_html += f'        <h2>{article["title"]}</h2>\n'
            content_html += f'        <div class="contenido">\n'
            content_html += f'            {article["content"]}\n'
            content_html += f'        </div>\n'
            content_html += f'        <div class="volver-indice">\n'
            content_html += f'            <a href="#indice" title="Volver al índice">←</a>\n'
            content_html += f'        </div>\n'
            content_html += f'    </article>\n\n'
    
    # HTML completo
    if custom_css:
        css_content = custom_css
    else:
        # CSS por defecto
        css_content = f"""
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        h1 {{
            margin: 0 0 20px 0;
            font-size: 2.5em;
        }}
        
        #indice {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        #indice h2 {{
            color: #333;
            margin-top: 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        #indice ul {{
            list-style: none;
            padding: 0;
            columns: 2;
            column-gap: 30px;
        }}
        
        #indice ul.subcategory {{
            margin-left: 20px;
            margin-top: 5px;
            margin-bottom: 10px;
            columns: 1;
        }}
        
        #indice li {{
            margin-bottom: 8px;
            break-inside: avoid;
        }}
        
        #indice a {{
            color: #667eea;
            text-decoration: none;
            display: block;
            padding: 5px 10px;
            border-radius: 5px;
            transition: background-color 0.3s;
        }}
        
        #indice a:hover {{
            background-color: #f0f0f0;
            color: #764ba2;
        }}
        
        article {{
            background: white;
            margin-bottom: 30px;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            page-break-before: always;
            break-before: page;
        }}
        
        article:first-of-type {{
            page-break-before: auto;
            break-before: auto;
        }}
        
        .category-section {{
            margin-bottom: 50px;
            page-break-inside: avoid;
        }}
        
        .category-title {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 25px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            page-break-after: avoid;
        }}
        
        .article-count {{
            color: #999;
            font-size: 0.8em;
            font-weight: normal;
        }}
        
        article h2 {{
            color: #333;
            margin-top: 0;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        
        article h3 {{
            color: #333;
            margin-top: 0;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            font-size: 1.3em;
        }}
        
        .contenido {{
            text-align: justify;
            margin: 20px 0;
        }}
        
        .contenido p {{
            margin-bottom: 15px;
            line-height: 1.8;
        }}
        
        .contenido h4 {{
            color: #555;
            margin: 20px 0 10px 0;
            font-size: 1.1em;
            font-weight: 600;
            border-left: 3px solid #667eea;
            padding-left: 10px;
        }}
        
        .volver-indice {{
            text-align: right;
            margin-top: 15px;
            opacity: 0.6;
        }}
        
        .volver-indice a {{
            color: #999;
            text-decoration: none;
            font-size: 1.5em;
            transition: all 0.3s;
            padding: 5px;
        }}
        
        .volver-indice a:hover {{
            color: #667eea;
            opacity: 1;
        }}
        
        .stats {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            #indice ul {{
                columns: 1;
            }}
            
            h1 {{
                font-size: 2em;
            }}
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .volver-indice {{
                display: none;
            }}
        }}
        """
    
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title} - {Path(output_file).stem}</title>
    <style>
{css_content}
    </style>
</head>
<body>
    <header>
        <h1>📚 {site_title}</h1>
        <p>Contenido convertido desde XML de WordPress</p>
    </header>
    
    <div class="stats">
        <strong>Total de artículos:</strong> {len(articles)}
    </div>
    
    <section id="indice">
        <h2>📋 Índice de Contenido</h2>
        <ul>
{index_html}        </ul>
    </section>
    
    <main>
{content_html}    </main>
    
    <footer style="text-align: center; margin-top: 50px; padding: 20px; color: #666;">
        <p>Generado con wp-x2h.py desde archivo XML de WordPress</p>
    </footer>
</body>
</html>"""
    
    return html_template

def generate_markdown(articles, output_file, categorized_articles=None, branding_text=None):
    """Genera Markdown con índice y contenido"""
    
    site_title = branding_text if branding_text else "WordPress Export"
    
    markdown_content = f"# {site_title}\n\n"
    markdown_content += f"Contenido convertido desde XML de WordPress\n\n"
    markdown_content += f"**Total de artículos:** {len(articles)}\n\n"
    
    # Generar índice
    markdown_content += "## 📋 Índice de Contenido\n\n"
    
    if categorized_articles:
        article_counter = 0
        for category, category_articles in categorized_articles.items():
            markdown_content += f"### {category} ({len(category_articles)})\n\n"
            
            for article in category_articles:
                article_id = f"articulo_{article_counter}"
                title = article['title'].replace('[', '\\[').replace(']', '\\]')
                markdown_content += f"- [{title}](#{article_id})\n"
                article_counter += 1
            
            markdown_content += "\n"
    else:
        for i, article in enumerate(articles):
            article_id = f"articulo_{i}"
            title = article['title'].replace('[', '\\[').replace(']', '\\]')
            markdown_content += f"- [{title}](#{article_id})\n"
        
        markdown_content += "\n"
    
    markdown_content += "---\n\n"
    
    # Generar contenido
    if categorized_articles:
        article_counter = 0
        for category, category_articles in categorized_articles.items():
            markdown_content += f"## {category}\n\n"
            
            for article in category_articles:
                article_id = f"articulo_{article_counter}"
                title = article['title'].replace('[', '\\[').replace(']', '\\]')
                markdown_content += f"### {title} {article_id}\n\n"
                
                # Limpiar contenido para Markdown
                content = article['content']
                # Convertir HTML a Markdown básico
                content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'### \1', content, flags=re.DOTALL)
                content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
                content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
                content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
                content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
                content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)
                content = re.sub(r'<br[^>]*>', '\n', content)
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'\n+', '\n\n', content).strip()
                
                markdown_content += f"{content}\n\n"
                markdown_content += "---\n\n"
                article_counter += 1
    else:
        for i, article in enumerate(articles):
            article_id = f"articulo_{i}"
            title = article['title'].replace('[', '\\[').replace(']', '\\]')
            markdown_content += f"## {title} {article_id}\n\n"
            
            # Limpiar contenido para Markdown
            content = article['content']
            # Convertir HTML a Markdown básico
            content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'### \1', content, flags=re.DOTALL)
            content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
            content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
            content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
            content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
            content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)
            content = re.sub(r'<br[^>]*>', '\n', content)
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\n+', '\n\n', content).strip()
            
            markdown_content += f"{content}\n\n"
            markdown_content += "---\n\n"
    
    return markdown_content

def main():
    """Función principal"""
    # 1. Recepción de argumentos
    if len(sys.argv) < 2:
        print("Usage: python3 wp-exporter.py input.xml [output.html] [options]", file=sys.stderr)
        print("       python3 wp-exporter.py --domain <url> --auth <user:pass> [options]", file=sys.stderr)
        print("Options:", file=sys.stderr)
        print("  --clean, -c           : Remove plugin shortcodes", file=sys.stderr)
        print("  --list-categories     : List all available categories", file=sys.stderr)
        print("  --format markdown     : Export to Markdown format", file=sys.stderr)
        print("  --stats               : Show detailed content statistics", file=sys.stderr)
        print("  --template <file>     : Use custom HTML template", file=sys.stderr)
        print("  --css <file>          : Use custom CSS file", file=sys.stderr)
        print("  --branding <text>     : Custom branding text", file=sys.stderr)
        print("  --domain <url>        : WordPress site domain (live connection)", file=sys.stderr)
        print("  --auth <user:pass>    : Authentication credentials", file=sys.stderr)
        print("                        For app passwords: user:'abcd efgh ijkl mnop qrst uvwx'", file=sys.stderr)
        sys.exit(1)
    
    # Parse arguments
    clean_shortcodes = False
    output_file = None
    num_categories = None
    filters = {}
    show_stats = False
    template_file = None
    css_file = None
    branding_text = None
    export_format = None
    list_categories = False
    domain = None
    auth_credentials = None
    input_file = None
    
    # Check if using domain mode or file mode
    if '--domain' in sys.argv:
        domain = None  # Will be set during argument parsing
        input_file = None
        start_index = 1  # Start from --domain
    else:
        input_file = sys.argv[1]
        domain = None
        start_index = 2  # Skip input file
    
    # Parsear argumentos
    i = start_index
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['--clean', '-c']:
            clean_shortcodes = True
        elif arg == '--list-categories':
            list_categories = True
        elif arg == '--format':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                export_format = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --format requires a format (html/markdown)", file=sys.stderr)
                sys.exit(1)
        elif arg == '--template':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                template_file = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --template requires a file", file=sys.stderr)
                sys.exit(1)
        elif arg == '--css':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                css_file = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --css requires a file", file=sys.stderr)
                sys.exit(1)
        elif arg == '--branding':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                branding_text = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --branding requires text", file=sys.stderr)
                sys.exit(1)
        elif arg == '--domain':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                domain = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --domain requires a URL", file=sys.stderr)
                sys.exit(1)
        elif arg == '--auth':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                auth_credentials = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --auth requires credentials (user:password)", file=sys.stderr)
                sys.exit(1)
        elif arg == '--cat':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                try:
                    num_categories = int(sys.argv[i + 1])
                    i += 1
                except ValueError:
                    print("Error: --cat requires a valid number", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Error: --cat requires a number", file=sys.stderr)
                sys.exit(1)
        elif arg == '--date-range':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                date_range = sys.argv[i + 1]
                try:
                    start_date, end_date = date_range.split(',')
                    filters['start_date'] = start_date.strip()
                    filters['end_date'] = end_date.strip()
                    i += 1
                except ValueError:
                    print("Error: --date-range requires format YYYY-MM-DD,YYYY-MM-DD", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Error: --date-range requires a date range", file=sys.stderr)
                sys.exit(1)
        elif arg == '--author':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                filters['author'] = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --author requires an author name", file=sys.stderr)
                sys.exit(1)
        elif arg == '--tags':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                tags = sys.argv[i + 1]
                filters['tags'] = [tag.strip() for tag in tags.split(',')]
                i += 1
            else:
                print("Error: --tags requires tags (comma-separated)", file=sys.stderr)
                sys.exit(1)
        elif arg == '--categories':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                categories = sys.argv[i + 1]
                filters['categories'] = [cat.strip() for cat in categories.split(',')]
                i += 1
            else:
                print("Error: --categories requires categories (comma-separated)", file=sys.stderr)
                sys.exit(1)
        elif arg == '--min-length':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('-'):
                try:
                    filters['min_length'] = int(sys.argv[i + 1])
                    i += 1
                except ValueError:
                    print("Error: --min-length requires a number", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Error: --min-length requires a number", file=sys.stderr)
                sys.exit(1)
        elif arg == '--stats':
            show_stats = True
        elif not arg.startswith('-') and output_file is None:
            output_file = arg
        i += 1
    
    # 2. Fase de Ingesta (Obtención del dato)
    articles = None
    source_type = None
    
    if domain:
        # Modo web: extraer desde WordPress API
        if not auth_credentials:
            print("Error: --domain requires --auth for authentication", file=sys.stderr)
            sys.exit(1)
        
        articles, source_type = extract_from_web(domain, auth_credentials, list_categories)
        
        if source_type == "categories_listed":
            return  # Task completed (categories listed)
        
        if not articles:
            print("❌ No articles found on the WordPress site", file=sys.stderr)
            sys.exit(1)
            
    else:
        # Modo archivo: validar y extraer desde XML
        if not input_file:
            print("Error: No input file specified", file=sys.stderr)
            sys.exit(1)
        if not Path(input_file).exists():
            print(f"Error: File '{input_file}' does not exist", file=sys.stderr)
            sys.exit(1)
        if not input_file.lower().endswith('.xml'):
            print(f"Error: Input file must be .xml", file=sys.stderr)
            sys.exit(1)
        
        articles, source_type = extract_from_file(input_file, clean_shortcodes, list_categories)
        
        if source_type == "categories_listed":
            return  # Task completed (categories listed)
        
        if not articles:
            print("❌ No articles found in the XML file", file=sys.stderr)
            sys.exit(1)
    
    # 3. Fase de Procesamiento (Lógica común)
    # En este punto, no importa el origen, solo que 'articles' tiene datos
    processed_result = process_articles(articles, filters, num_categories, show_stats, clean_shortcodes)
    
    if not processed_result:
        print("❌ No articles to process", file=sys.stderr)
        sys.exit(1)
    
    articles, categorized_articles = processed_result
    
    # 4. Generación de salida
    # Determinar archivo de salida si no se especificó
    if output_file is None:
        if domain:
            # Generate output filename from domain
            domain_name = domain.replace('https://', '').replace('http://', '').replace('/', '_')
            if export_format == 'markdown':
                output_file = f"{domain_name}.md"
            else:
                output_file = f"{domain_name}.html"
        else:
            # Generate output filename from input file
            input_path = Path(input_file)
            if export_format == 'markdown':
                output_file = input_path.stem + '.md'
            else:
                output_file = input_path.stem + '.html'
    
    # Validar archivos (solo para modo XML)
    if not domain:
        if not validate_files(input_file, output_file, export_format):
            sys.exit(1)
    
    # Generate content according to format
    if export_format == 'markdown':
        print(f"📝 Generating Markdown: {output_file}")
        content = generate_markdown(articles, output_file, categorized_articles, branding_text)
    else:
        print(f"🎨 Generating HTML: {output_file}")
        content = generate_html(articles, output_file, categorized_articles, template_file, css_file, branding_text)
        format_type = "HTML"
    
    # Save file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_size = len(content) / 1024
        print(f"✅ {format_type} file generated successfully: {output_file}")
        print(f"📊 Size: {file_size:.1f} KB")
        if format_type == "HTML":
            print(f"🌐 Open the file in your web browser")
        else:
            print(f"📄 Open the file in your Markdown editor")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
