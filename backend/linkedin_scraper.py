from playwright.sync_api import sync_playwright
import re
import time
from urllib.parse import quote_plus


def clean_text(text: str) -> str:
    text = text.replace("See more", "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_post_url(post):
    """
    Extract the actual LinkedIn post URL from a post element.
    Tries multiple strategies to find the post link.
    """
    post_url = ""
    
    # Strategy 1: Look for the post link in the post container's data attributes
    try:
        # Check if the post has a data-urn attribute
        urn = post.get_attribute("data-urn")
        if urn and "activity" in urn:
            # Extract the activity ID from URN like "urn:li:activity:1234567890"
            activity_id = urn.split(":")[-1]
            post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"
            return post_url
    except:
        pass
    
    # Strategy 2: Look for timestamp link (most reliable)
    try:
        timestamp_link = post.locator("a.app-aware-link[href*='/feed/update/']").first
        if timestamp_link.count() > 0:
            href = timestamp_link.get_attribute("href")
            if href:
                post_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                # Clean up the URL (remove query parameters)
                post_url = post_url.split("?")[0]
                return post_url
    except:
        pass
    
    # Strategy 3: Look for any link with activity URN
    try:
        activity_link = post.locator("a[href*='urn:li:activity']").first
        if activity_link.count() > 0:
            href = activity_link.get_attribute("href")
            if href:
                post_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                post_url = post_url.split("?")[0]
                return post_url
    except:
        pass
    
    # Strategy 4: Look in nested feed update links
    try:
        feed_link = post.locator("a[href*='/feed/update/']").first
        if feed_link.count() > 0:
            href = feed_link.get_attribute("href")
            if href and "/feed/update/" in href:
                post_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                post_url = post_url.split("?")[0]
                return post_url
    except:
        pass
    
    # Strategy 5: Look for social detail links
    try:
        social_link = post.locator("a.feed-shared-social-action-bar__action-button[href*='/feed/update/']").first
        if social_link.count() > 0:
            href = social_link.get_attribute("href")
            if href:
                post_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                post_url = post_url.split("?")[0]
                return post_url
    except:
        pass
    
    return post_url


def _scrape_query(page, query: str, limit: int = 5):
    """
    Scrapes LinkedIn posts for a single search query.
    """
    try:
        print(f"  🔗 Navigating to search results...")
        
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={quote_plus(query)}"
        
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  ⚠️ Navigation issue: {e}")
            # Try again with a longer timeout
            time.sleep(2)
            page.goto(search_url, wait_until="networkidle", timeout=40000)
        
        print(f"  ⏳ Waiting for content to load...")
        time.sleep(4)
        
        for i in range(3):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            time.sleep(1)
        
        post_selectors = [
            "div.feed-shared-update-v2",
            "li.reusable-search__result-container",
            "div.search-results-container li",
            "div[data-id*='urn:li:activity']"
        ]
        
        posts = None
        for selector in post_selectors:
            try:
                posts = page.locator(selector)
                if posts.count() > 0:
                    print(f"  ✓ Found {posts.count()} posts using selector: {selector}")
                    break
            except:
                continue
        
        if not posts or posts.count() == 0:
            print(f"  ⚠️ No posts found for query: {query}")
            page.screenshot(path=f"debug_{query[:20].replace(' ', '_')}.png")
            return []

        results = []
        post_count = posts.count()

        for i in range(min(limit, post_count)):
            try:
                post = posts.nth(i)
                
                post.scroll_into_view_if_needed()
                time.sleep(0.5)

                content = ""
                content_selectors = [
                    "span.break-words",
                    "div.update-components-text span",
                    "div.feed-shared-text span",
                    "div.feed-shared-update-v2__description",
                    "span[dir='ltr']",
                    "div.feed-shared-inline-show-more-text"
                ]
                
                for selector in content_selectors:
                    try:
                        content_locator = post.locator(selector).first
                        if content_locator.count() > 0:
                            content = clean_text(content_locator.inner_text())
                            if len(content) > 20:  # Minimum content length
                                break
                    except:
                        continue

                if not content or len(content) < 20:
                    print(f"  ⚠️ Post {i+1}: No content found, skipping")
                    continue

                # Extract author
                author = "Unknown"
                author_selectors = [
                    "span.update-components-actor__name span[aria-hidden='true']",
                    "span.update-components-actor__name",
                    "span[aria-hidden='true']",
                    "div.update-components-actor__meta a span",
                    "a.app-aware-link span[aria-hidden='true']"
                ]
                
                for selector in author_selectors:
                    try:
                        author_locator = post.locator(selector).first
                        if author_locator.count() > 0:
                            author_text = author_locator.inner_text().strip()
                            if author_text and len(author_text) > 1:
                                author = author_text
                                break
                    except:
                        continue

                # Extract POST URL (most important)
                post_url = extract_post_url(post)
                
                if not post_url:
                    print(f"  ⚠️ Post {i+1}: Could not extract post URL")
                
                # Collect all links (post URL first, then others)
                links = []
                
                # Add the main post URL first
                if post_url:
                    links.append(post_url)
                
                # Extract additional links from the post content
                try:
                    # Look for external links in the post
                    anchor_selectors = [
                        "a[href*='http']:not([href*='linkedin.com'])",  # External links
                        "a.app-aware-link[href*='company']",  # Company pages
                    ]
                    
                    for anchor_selector in anchor_selectors:
                        anchors = post.locator(anchor_selector)
                        for j in range(min(2, anchors.count())):  # Limit to 2 additional links
                            try:
                                href = anchors.nth(j).get_attribute("href")
                                if href and href not in links:
                                    if not href.startswith("http"):
                                        href = f"https://www.linkedin.com{href}"
                                    # Avoid author profile links
                                    if "/in/" not in href or len(links) == 0:
                                        links.append(href)
                            except:
                                continue
                except:
                    pass

                result = {
                    "query": query,
                    "author": author,
                    "content": content[:500],  # Limit content length
                    "post_url": post_url,  # Main post URL
                    "links": links[:4]  # Limit to 4 links total
                }
                
                results.append(result)
                post_link_status = "✓" if post_url else "✗"
                print(f"  {post_link_status} Post {i+1}/{limit}: {author[:40]}... ({len(content)} chars) - Link: {post_link_status}")

            except Exception as e:
                print(f"  ⚠️ Error extracting post {i+1}: {str(e)[:100]}")
                continue

        return results
        
    except Exception as e:
        print(f"  ❌ Error scraping query '{query}': {str(e)[:200]}")
        return []


# =========================
# ✅ PUBLIC API (USED BY local_agent.py)
# =========================
def scrape_posts(queries, limit_per_query: int = 5):
    """
    Scrapes LinkedIn posts for multiple queries.
    - Opens browser ONCE
    - Login ONCE
    - Goes directly to search after login
    """

    all_results = []

    with sync_playwright() as p:
        print("\n🌐 Launching browser...")
        
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        
        page = context.new_page()

        print("\n" + "="*60)
        print("🔐 STEP 1: LOGIN TO LINKEDIN")
        print("="*60)
        
        try:
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30000)
        except:
            print("⚠️ Slow connection, trying again...")
            page.goto("https://www.linkedin.com/login", timeout=40000)
        
        print("\n👉 Please log in to LinkedIn in the browser window")
        print("👉 Complete any security checks if prompted")
        print("👉 Once logged in, you'll see the LinkedIn interface")
        
        input("\n✋ Press ENTER after you've successfully logged in...")

        print("\n🔍 Verifying login by testing search...")
        
        try:
            test_url = "https://www.linkedin.com/search/results/content/?keywords=test"
            page.goto(test_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            current_url = page.url
            if "login" in current_url or "checkpoint" in current_url:
                print("❌ Login verification failed - still on login/checkpoint page")
                print(f"Current URL: {current_url}")
                print("⚠️ Please complete the login process and try again")
                browser.close()
                return []
            
            print("✅ Login verified successfully!\n")
            
        except Exception as e:
            print(f"⚠️ Verification issue (but proceeding anyway): {str(e)[:100]}")
            print("   If scraping fails, please try running the script again\n")

        print("\n" + "="*60)
        print("🔍 STEP 2: SCRAPING LINKEDIN POSTS")
        print("="*60 + "\n")
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{'─'*60}")
            print(f"📋 Query {idx}/{len(queries)}: '{query}'")
            print(f"{'─'*60}")
            
            posts = _scrape_query(
                page=page,
                query=query,
                limit=limit_per_query
            )
            
            all_results.extend(posts)
            print(f"✅ Collected {len(posts)} posts for this query\n")
            
            if idx < len(queries):
                wait_time = 4
                print(f"⏳ Waiting {wait_time}s before next query...")
                time.sleep(wait_time)

        print("\n" + "="*60)
        print(f"✅ SCRAPING COMPLETE!")
        print(f"📊 Total posts collected: {len(all_results)}")
        print(f"📊 Posts with URLs: {sum(1 for r in all_results if r.get('post_url'))}")
        print("="*60 + "\n")

        browser.close()

    return all_results