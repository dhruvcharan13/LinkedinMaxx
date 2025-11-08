"""
Stealth utilities for human-like behavior simulation.
Provides functions to make automation appear as natural human interaction.
"""

import random
import time
import numpy as np
from typing import Optional


def human_delay(min_seconds: float = 3.0, max_seconds: float = 8.0, use_gaussian: bool = True) -> None:
    """
    Human-like delay with Gaussian distribution for natural timing.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
        use_gaussian: Use Gaussian distribution (more natural) vs uniform
    """
    if use_gaussian:
        # Gaussian distribution centered in the middle, with std dev
        mean = (min_seconds + max_seconds) / 2
        std_dev = (max_seconds - min_seconds) / 4
        delay = max(min_seconds, min(max_seconds, np.random.normal(mean, std_dev)))
    else:
        delay = random.uniform(min_seconds, max_seconds)
    
    time.sleep(delay)


def random_mouse_movement(page, min_moves: int = 1, max_moves: int = 3) -> None:
    """
    Simulate random mouse movements on the page.
    
    Args:
        page: Playwright page object
        min_moves: Minimum number of mouse movements
        max_moves: Maximum number of mouse movements
    """
    try:
        viewport = page.viewport_size
        if not viewport:
            return
        
        num_moves = random.randint(min_moves, max_moves)
        for _ in range(num_moves):
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.5))
    except Exception:
        # Silently fail if mouse movement fails
        pass


def human_like_scroll(page, scroll_amount: Optional[int] = None, pause_after: bool = True) -> None:
    """
    Simulate human-like scrolling with variable speed and pauses.
    
    Args:
        page: Playwright page object
        scroll_amount: Pixels to scroll (None for random)
        pause_after: Whether to pause after scrolling
    """
    try:
        if scroll_amount is None:
            # Random scroll amount (small, medium, or large)
            scroll_types = [
                random.randint(100, 300),   # Small scroll
                random.randint(300, 600),   # Medium scroll
                random.randint(600, 1000),  # Large scroll
            ]
            scroll_amount = random.choice(scroll_types)
        
        # Scroll in smaller chunks to simulate smooth scrolling
        chunk_size = scroll_amount // 5
        for i in range(5):
            page.mouse.wheel(0, chunk_size)
            time.sleep(random.uniform(0.05, 0.15))
        
        if pause_after:
            # Random pause after scrolling (simulating reading)
            time.sleep(random.uniform(0.5, 2.0))
    except Exception:
        # Silently fail if scrolling fails
        pass


def scroll_to_load_feed(page, max_scrolls: int = 20, scroll_pause_probability: float = 0.3) -> None:
    """
    Scroll through feed with human-like patterns including random pauses.
    
    Args:
        page: Playwright page object
        max_scrolls: Maximum number of scroll actions
        scroll_pause_probability: Probability of pausing after each scroll (0.0-1.0)
    """
    scroll_count = 0
    consecutive_pauses = 0
    
    while scroll_count < max_scrolls:
        # Occasionally scroll back up slightly (human behavior)
        if random.random() < 0.1 and scroll_count > 3:
            human_like_scroll(page, scroll_amount=random.randint(-200, -50), pause_after=False)
            time.sleep(random.uniform(0.3, 0.8))
        
        # Main scroll down
        human_like_scroll(page, pause_after=False)
        scroll_count += 1
        
        # Random mouse movement every few scrolls
        if random.random() < 0.4:
            random_mouse_movement(page, min_moves=1, max_moves=2)
        
        # Random pause after scroll (simulating reading content)
        if random.random() < scroll_pause_probability:
            pause_duration = random.uniform(2.0, 5.0)
            time.sleep(pause_duration)
            consecutive_pauses += 1
        else:
            consecutive_pauses = 0
        
        # Longer pause every 5-7 scrolls (simulating deeper engagement)
        if scroll_count % random.randint(5, 7) == 0:
            longer_pause = random.uniform(3.0, 8.0)
            time.sleep(longer_pause)
            random_mouse_movement(page, min_moves=2, max_moves=4)
        
        # Small delay between scrolls
        time.sleep(random.uniform(0.3, 1.0))


def simulate_reading_time(content_length: int = 0, base_time: float = 30.0, max_time: float = 120.0) -> float:
    """
    Calculate reading time based on content length.
    
    Args:
        content_length: Length of content (characters)
        base_time: Base time in seconds
        max_time: Maximum time in seconds
    
    Returns:
        Reading time in seconds
    """
    # Estimate reading time: average human reads 200-300 words per minute
    # Rough estimate: 1 character ≈ 0.2 words, so ~1000 chars = 200 words = 1 minute
    reading_time = base_time + (content_length / 1000) * 60
    
    # Add randomness
    reading_time *= random.uniform(0.8, 1.2)
    
    # Cap at max_time
    reading_time = min(reading_time, max_time)
    
    # Ensure minimum base time
    reading_time = max(base_time * 0.7, reading_time)
    
    return reading_time


def simulate_profile_visit(page, min_time: float = 30.0, max_time: float = 120.0) -> None:
    """
    Simulate a human visiting and reading a profile page.
    
    Args:
        page: Playwright page object
        min_time: Minimum time to spend on profile
        max_time: Maximum time to spend on profile
    """
    visit_time = random.uniform(min_time, max_time)
    elapsed_time = 0.0
    
    # Initial page load delay
    time.sleep(random.uniform(2.0, 5.0))
    elapsed_time += random.uniform(2.0, 5.0)
    
    # Random mouse movements while "reading"
    while elapsed_time < visit_time:
        # Scroll down slowly
        if random.random() < 0.7:
            human_like_scroll(page, scroll_amount=random.randint(200, 500), pause_after=True)
            elapsed_time += random.uniform(1.0, 3.0)
        
        # Random mouse movement
        if random.random() < 0.5:
            random_mouse_movement(page, min_moves=1, max_moves=3)
            elapsed_time += random.uniform(0.5, 1.5)
        
        # Pause to "read"
        if random.random() < 0.6:
            pause = random.uniform(2.0, 5.0)
            time.sleep(pause)
            elapsed_time += pause
        
        # Occasionally scroll back up (re-reading)
        if random.random() < 0.2 and elapsed_time > visit_time * 0.3:
            human_like_scroll(page, scroll_amount=random.randint(-300, -100), pause_after=True)
            elapsed_time += random.uniform(1.0, 2.0)
        
        # Small delay
        time.sleep(random.uniform(0.5, 1.5))
        elapsed_time += random.uniform(0.5, 1.5)
    
    # Final random pause before leaving
    time.sleep(random.uniform(1.0, 3.0))


def random_break(min_seconds: float = 30.0, max_seconds: float = 60.0) -> None:
    """
    Take a random break (simulating human behavior).
    
    Args:
        min_seconds: Minimum break duration
        max_seconds: Maximum break duration
    """
    break_time = random.uniform(min_seconds, max_seconds)
    print(f"Taking a break for {break_time:.1f} seconds...")
    time.sleep(break_time)


def longer_break(min_seconds: float = 120.0, max_seconds: float = 300.0) -> None:
    """
    Take a longer break (simulating longer human pauses).
    
    Args:
        min_seconds: Minimum break duration
        max_seconds: Maximum break duration
    """
    break_time = random.uniform(min_seconds, max_seconds)
    print(f"Taking a longer break for {break_time/60:.1f} minutes...")
    time.sleep(break_time)

