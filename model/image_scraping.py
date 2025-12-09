#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code credit:
https://towardsdatascience.com/image-scraping-with-python-a96feda8af2d
"""

import time
import requests 
import io
import hashlib
import os
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image

def fetch_image_urls(
    query: str, 
    max_links_to_fetch: int, 
    wd, 
    sleep_between_interactions: int = 1,
    driver_path = None, 
    target_path = None, 
    search_term = None):
    """
    Fetch image URLs from Google Images search results.
    
    Args:
        query: Search term to query Google Images
        max_links_to_fetch: Maximum number of image URLs to collect
        wd: Selenium WebDriver instance
        sleep_between_interactions: Delay between scrolls (in seconds)
        driver_path: Path to chromedriver executable
        target_path: Directory to save images
        search_term: Original search term for folder naming
    
    Returns:
        Set of image URLs found in the search results
    """
    
    def scroll_to_end(wd):
        """Scroll to the bottom of the page to trigger lazy-loading of more images."""
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)    
    
    # Build the Google Images search URL with the query parameter
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # Navigate to the Google Images search page
    wd.get(search_url.format(q=query))
    
    print("Waiting for page to load...")
    time.sleep(2)  # Give the page time to fully render

    # Store unique image URLs in a set to avoid duplicates
    image_urls = set()
    last_height = 0  # Track page height to detect when we've reached the bottom
    scroll_attempts = 0  # Count consecutive scrolls without new content
    max_scroll_attempts = 10  # Stop if we can't find new content after 10 scrolls
    
    # Keep scrolling and extracting URLs until we have enough or can't scroll further
    iteration = 0
    while len(image_urls) < max_links_to_fetch and scroll_attempts < max_scroll_attempts:
        iteration += 1
        print(f"\n[Iteration {iteration}] Starting scroll/extraction cycle...")
        
        # Scroll down to trigger lazy-loading of more images
        print(f"[Iteration {iteration}] Scrolling to bottom...")
        scroll_to_end(wd)
        time.sleep(sleep_between_interactions)
        
        # Get the entire HTML source of the page
        print(f"[Iteration {iteration}] Extracting page source...")
        page_source = wd.page_source
        print(f"[Iteration {iteration}] Page source length: {len(page_source)} characters")
        
        # Regex pattern to find image URLs embedded in the HTML source
        # Matches: http(s)://...anything...(jpg|jpeg|png|gif|webp)...more chars
        url_pattern = r'https?://[^"\s<>]+?\.(?:jpg|jpeg|png|gif|webp)[^"\s<>]*'
        found_urls = re.findall(url_pattern, page_source, re.IGNORECASE)
        print(f"[Iteration {iteration}] Found {len(found_urls)} total URLs in page source")
        
        # Filter out low-quality thumbnails and keep only full-size image URLs
        before_count = len(image_urls)
        for url in found_urls:
            # Skip Google's thumbnail images (encrypted-tbn) and very short URLs
            if 'encrypted-tbn' not in url and len(url) > 50:
                # Clean up HTML-escaped characters in the URL
                url = url.replace('\\u003d', '=').replace('\\/', '/')
                image_urls.add(url)  # Set automatically handles duplicates
        
        new_urls_added = len(image_urls) - before_count
        print(f"[Iteration {iteration}] Added {new_urls_added} new URLs (total: {len(image_urls)}/{max_links_to_fetch})")
        
        # Check if the page height changed (indicates new content loaded)
        new_height = wd.execute_script("return document.body.scrollHeight")
        print(f"[Iteration {iteration}] Page height: {new_height} (previous: {last_height})")
        
        if new_height == last_height:
            # Page didn't grow - we might be at the bottom
            scroll_attempts += 1
            print(f"[Iteration {iteration}] ⚠ No height change detected (attempt {scroll_attempts}/{max_scroll_attempts})")
            
            # Try to find and click the "Show more results" button
            try:
                # Multiple selectors for the load-more button (Google changes these)
                print(f"[Iteration {iteration}] Searching for 'Show more' button...")
                load_more = wd.find_element(By.CSS_SELECTOR, "input.mye4qd, .YstHxe input")
                wd.execute_script("arguments[0].click();", load_more)
                print(f"[Iteration {iteration}] ✓ Clicked 'Show more results' button")
                time.sleep(2)  # Wait for new images to load
                scroll_attempts = 0  # Reset counter since we found new content
            except Exception as e:
                # Button not found or not clickable - continue scrolling
                print(f"[Iteration {iteration}] ✗ Load-more button not found: {str(e)[:100]}")
        else:
            # Page grew - new content loaded successfully
            print(f"[Iteration {iteration}] ✓ Page height increased by {new_height - last_height}px")
            scroll_attempts = 0
            last_height = new_height
        
        # Stop early if we've collected enough URLs
        if len(image_urls) >= max_links_to_fetch:
            print(f"[Iteration {iteration}] ✓ Target reached! Stopping search.")
            break
    
    # Log why the loop ended
    if scroll_attempts >= max_scroll_attempts:
        print(f"\n⚠ Stopped: Reached max scroll attempts ({max_scroll_attempts})")
    elif len(image_urls) >= max_links_to_fetch:
        print(f"\n✓ Success: Collected enough URLs ({len(image_urls)})")
    else:
        print(f"\n⚠ Loop ended unexpectedly")
    
    # Convert set to list and slice to get exactly the number requested
    # (we might have collected more than needed)
    result_urls = list(image_urls)[:max_links_to_fetch]
    print(f"Total collected: {len(result_urls)} image URLs")
    return set(result_urls)  # Return as set for consistency

def persist_image(folder_path: str, url: str):
    """
    Download an image from a URL and save it to disk.
    
    Args:
        folder_path: Directory where the image will be saved
        url: URL of the image to download
    
    Returns:
        True if successful, False if failed
    """
    try:
        # Download the image content from the URL with timeout
        print(f"  → Downloading...")
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()  # Raise error for bad status codes
        image_content = response.content
        
        # Validate file size (skip tiny files that are likely error pages)
        if len(image_content) < 5000:  # Less than 5KB is suspicious
            print(f"  ⚠ SKIPPED - File too small ({len(image_content)} bytes) - likely an error page")
            return False
        
        print(f"  → Downloaded {len(image_content)} bytes")

    except requests.exceptions.Timeout:
        print(f"  ❌ ERROR - Timeout after 15 seconds")
        return False
    except Exception as e:
        print(f"  ❌ ERROR - Could not download {url[:80]}...")
        print(f"     Reason: {e}")
        return False

    try:
        # Load the image data into a PIL Image object
        print(f"  → Opening image...")
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')  # Convert to RGB (removes alpha channel)
        
        # Validate minimum image dimensions
        width, height = image.size
        if width < 100 or height < 100:
            print(f"  ⚠ SKIPPED - Image too small ({width}x{height}px)")
            return False
        
        # Create a unique filename using SHA1 hash of the image content
        # This prevents duplicate downloads and handles URL encoding issues
        filename = hashlib.sha1(image_content).hexdigest()[:10] + '.jpg'
        file_path = os.path.join(folder_path, filename)
        
        # Save the image as JPEG with 85% quality (good balance of size/quality)
        print(f"  → Saving as {filename}...")
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=85)
        print(f"  ✓ SUCCESS - Saved to {file_path}")
        return True
    except Exception as e:
        print(f"  ❌ ERROR - Could not save {url[:80]}...")
        print(f"     Reason: {e}")
        return False
    
def search_and_download(search_term: str, driver_path: str, target_path='./datasets', number_images=50):
    """
    Main function to search Google Images and download results.
    
    Args:
        search_term: Query to search for (e.g., "Serena Williams")
        driver_path: Path to the ChromeDriver executable
        target_path: Base directory for saving images (default: './datasets')
        number_images: Number of images to download (default: 50)
    """
    print(f"\n\n{'#'*60}")
    print(f"# Starting search for: '{search_term}'")
    print(f"# Target: {number_images} images")
    print(f"{'#'*60}\n")
    
    # Create a folder for this search term (spaces replaced with underscores)
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))
    print(f"Target folder: {target_folder}")

    # Create the directory if it doesn't exist
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # Configure Chrome options to avoid bot detection
    print("\nConfiguring Chrome browser...")
    options = Options()
    # Disable the "Chrome is being controlled by automated software" banner
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Set a realistic user-agent string to mimic a normal browser
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    # Initialize Chrome WebDriver with the configured options
    print(f"Launching Chrome with driver: {driver_path}")
    service = Service(driver_path)
    with webdriver.Chrome(service=service, options=options) as wd:
        print("Browser launched successfully\n")
        # Fetch image URLs from Google Images
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5, 
                               driver_path=driver_path, target_path=target_path, search_term=search_term)
        print(f"\nBrowser session ended. Collected {len(res)} URLs.")
    
    # Download and save each image
    print(f"\n{'='*60}")
    print(f"Starting download of {len(res)} images...")
    print(f"{'='*60}\n")
    
    download_count = 0
    error_count = 0
    skipped_count = 0
    
    try:    
        for idx, elem in enumerate(res, 1):
            print(f"\n[{idx}/{len(res)}] Processing: {elem[:80]}...")
            result = persist_image(target_folder, elem)
            if result is True:
                download_count += 1
            elif result is False:
                error_count += 1
            print(f"Progress: {download_count} successful, {error_count} failed")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during download loop: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Download complete: {download_count}/{len(res)} successful")
    if error_count > 0:
        print(f"Failed/Skipped: {error_count} (small files, timeouts, or invalid images)")
    print(f"{'='*60}")
    
def scraping_images(query: list, number_images:int):
    # List of search queries - add or modify as needed
    # Images will be saved to ./datasets/<query_name>/ for each query
    
    # Process each query: search Google Images and download results
    for q in query:
        search_and_download(q, r"./chromedriver.exe", number_images=number_images)