from playwright.sync_api import sync_playwright
import re
import time
from urllib.parse import quote_plus


def clean_text(text: str) -> str:
    text = text.replace("See more", "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_job_related_post(content: str, author: str) -> bool:
    """
    Filter to check if post is actually job-related.
    Returns True if post contains hiring keywords, False otherwise.
    """
    if not content:
        return False
    
    content_lower = content.lower()
    
    # Strong hiring indicators
    hiring_keywords = [
        'hiring', 'recruiting', 'looking for', 'seeking', 'hiring for',
        'we are hiring', "we're hiring", 'join our team', 'join us',
        'open position', 'opening', 'opportunity', 'opening for',
        'apply now', 'apply here', 'applications open', 'now hiring',
        'job opening', 'career opportunity', 'careers', 'vacancy',
        'come work', 'work with us', 'join the team', 'we need',
        'position available', 'role available', 'actively hiring',
        'currently hiring', 'internship opening', 'intern position',
        'full-time position', 'part-time position', 'contract position',
        'remote position', 'onsite position', 'hybrid position',
        'send your resume', 'share your cv', 'interested candidates',
        'dm to apply', 'comment to apply', 'link in comments'
    ]
    
    # Check if any hiring keyword exists
    has_hiring_keyword = any(keyword in content_lower for keyword in hiring_keywords)
    
    if not has_hiring_keyword:
        return False
    
    # Additional validation: reject obvious non-job posts
    rejection_keywords = [
        'congratulations', 'congratulation', 'proud to announce',
        'happy to share', 'excited to share', 'thrilled to announce',
        'pleased to announce', 'won the award', 'received the award',
        'launched our', 'released our', 'introducing our new',
        'check out our', 'read our blog', 'watch our', 'article about',
        'speaking at', 'will be speaking', 'attended the conference'
    ]
    
    # If it has rejection keywords at the start, it's likely not a job post
    first_100_chars = content_lower[:100]
    has_rejection = any(keyword in first_100_chars for keyword in rejection_keywords)
    
    if has_rejection and not any(keyword in content_lower[100:] for keyword in hiring_keywords):
        return False
    
    return True


def extract_post_url(post):
    """
    Extract the actual LinkedIn post URL from a post element.
    Tries multiple strategies to find the post link.
    """
    post_url = ""
    
    # Strategy 1: Look for the post link in the post container's data attributes
    try:
        urn = post.get_attribute("data-urn")
        if urn and "activity" in urn:
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


def _scrape_query(page, query: str, limit: int = 5, time_filter: str = "past-week"):
    """
    Scrapes LinkedIn posts for a single search query.
    Now with time filter and job keyword filtering!
    
    time_filter options:
    - "past-24h" (Past 24 hours)
    - "past-week" (Past week) - DEFAULT
    - "past-month" (Past month)
    """
    try:
        print(f"  🔗 Navigating to search results...")
        
        # Build search URL with time filter - EXACT format from LinkedIn
        base_url = f"https://www.linkedin.com/search/results/content/?keywords={quote_plus(query)}"
        
        # Add datePosted parameter with EXACT format: datePosted="past-week"
        if time_filter == "past-24h":
            base_url += '&datePosted=%22past-24h%22'
        elif time_filter == "past-week":
            base_url += '&datePosted=%22past-week%22'
        elif time_filter == "past-month":
            base_url += '&datePosted=%22past-month%22'
        
        search_url = base_url
        print(f"  ⏰ Time filter: {time_filter}")
        print(f"  🔗 URL: {search_url[:100]}...")
        
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  ⚠️ Navigation issue: {e}")
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
        filtered_count = 0

        for i in range(min(limit * 3, post_count)):  # Check more posts to account for filtering
            if len(results) >= limit:  # Stop when we have enough valid posts
                break
                
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
                            if len(content) > 20:
                                break
                    except:
                        continue

                if not content or len(content) < 20:
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

                # 🔥 KEYWORD FILTERING - Check if post is job-related
                if not is_job_related_post(content, author):
                    filtered_count += 1
                    print(f"  ⚠️ Post {i+1}: Filtered out (not job-related)")
                    continue

                # Extract POST URL
                post_url = extract_post_url(post)
                
                if not post_url:
                    print(f"  ⚠️ Post {i+1}: Could not extract post URL")
                
                # Collect links
                links = []
                
                if post_url:
                    links.append(post_url)
                
                try:
                    anchor_selectors = [
                        "a[href*='http']:not([href*='linkedin.com'])",
                        "a.app-aware-link[href*='company']",
                    ]
                    
                    for anchor_selector in anchor_selectors:
                        anchors = post.locator(anchor_selector)
                        for j in range(min(2, anchors.count())):
                            try:
                                href = anchors.nth(j).get_attribute("href")
                                if href and href not in links:
                                    if not href.startswith("http"):
                                        href = f"https://www.linkedin.com{href}"
                                    if "/in/" not in href or len(links) == 0:
                                        links.append(href)
                            except:
                                continue
                except:
                    pass

                result = {
                    "query": query,
                    "author": author,
                    "content": content[:500],
                    "post_url": post_url,
                    "links": links[:4]
                }
                
                results.append(result)
                post_link_status = "✓" if post_url else "✗"
                print(f"  ✅ Post {len(results)}/{limit}: {author[:40]}... ({len(content)} chars) - {post_link_status}")

            except Exception as e:
                print(f"  ⚠️ Error extracting post {i+1}: {str(e)[:100]}")
                continue

        print(f"  📊 Filtered out {filtered_count} non-job posts")
        return results
        
    except Exception as e:
        print(f"  ❌ Error scraping query '{query}': {str(e)[:200]}")
        return []


def scrape_posts(queries, limit_per_query: int = 5, time_filter: str = "past-week"):
    """
    Scrapes LinkedIn posts for multiple queries.
    Now with time filtering and job keyword filtering!
    
    time_filter options: 
    - "past-24h" - Last 24 hours
    - "past-week" - Last week (DEFAULT)
    - "past-month" - Last month
    - None - All time
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
        print(f"⏰ Time Filter: {time_filter or 'None (all posts)'}")
        print(f"🎯 Keyword Filtering: ENABLED (job posts only)")
        print("="*60 + "\n")
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{'─'*60}")
            print(f"📋 Query {idx}/{len(queries)}: '{query}'")
            print(f"{'─'*60}")
            
            posts = _scrape_query(
                page=page,
                query=query,
                limit=limit_per_query,
                time_filter=time_filter
            )
            
            all_results.extend(posts)
            print(f"✅ Collected {len(posts)} job posts for this query\n")
            
            if idx < len(queries):
                wait_time = 4
                print(f"⏳ Waiting {wait_time}s before next query...")
                time.sleep(wait_time)

        print("\n" + "="*60)
        print(f"✅ SCRAPING COMPLETE!")
        print(f"📊 Total posts collected: {len(all_results)}")
        print(f"📊 Posts with URLs: {sum(1 for r in all_results if r.get('post_url'))}")
        print(f"🎯 All posts are job-related (keyword filtered)")
        print(f"⏰ All posts are from: {time_filter or 'all time'}")
        print("="*60 + "\n")

        browser.close()

    return all_results