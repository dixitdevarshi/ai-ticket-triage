from link_checker import extract_urls


def test_extract_urls_finds_a_real_url():
    text = "Please check this link https://www.google.com for more info"
    urls = extract_urls(text)
    assert "https://www.google.com" in urls


def test_extract_urls_returns_empty_when_no_links():
    text = "This message has no links in it at all"
    urls = extract_urls(text)
    assert urls == []