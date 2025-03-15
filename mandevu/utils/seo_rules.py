class SEORuleChecker:
    def __init__(self, seo_data):
        self.seo_data = seo_data
        self.issues = []

    def check_meta_tags(self):
        """Check if meta title and description are missing or not optimal in length."""
        title = self.seo_data.get("meta_title", "")
        if not title or title == "No Title Tag":
            self.issues.append("Missing title tag.")
        elif len(title) < 30 or len(title) > 60:
            self.issues.append("⚠️ Title tag length should be between 30-60 characters.")

        description = self.seo_data.get("meta_description", "")
        if not description or description == "No Description Available":
            self.issues.append("Missing meta description.")
        elif len(description) < 50 or len(description) > 160:
            self.issues.append(f"Meta description length ({len(description)} characters) should be between 50-160 characters.")

    def check_canonical_tag(self):
        """Check if the canonical tag is missing."""
        canonical = self.seo_data.get("canonical", "")
        if not canonical:
            self.issues.append("Missing canonical tag.")

    def check_meta_robots(self):
        """Check if robots meta tag is missing or set to noindex."""
        robots = self.seo_data.get("meta_robots", "")
        if not robots or robots == "No Robots Tag":
            self.issues.append("⚠️ No robots meta tag found.")
        elif "noindex" in robots:
            self.issues.append("Page is set to noindex (won't appear in search results).")

    def check_headings(self):
        """Ensure proper heading hierarchy (H1-H6) and check for missing or multiple H1 tags."""
        headings = {
            "h1": self.seo_data.get("h1_tags", []),
            "h2": self.seo_data.get("h2_tags", []),
            "h3": self.seo_data.get("h3_tags", []),
            "h4": self.seo_data.get("h4_tags", []),
            "h5": self.seo_data.get("h5_tags", []),
            "h6": self.seo_data.get("h6_tags", [])
        }

        h1_count = len(headings["h1"])
        if not headings["h1"]:
            self.issues.append("No H1 tag found on the page. Each page should have one main H1 tag for SEO.")
        elif h1_count > 1:
            self.issues.append(f"Multiple H1 tags found ({h1_count}). Ensure only one main H1 for clarity.")

        heading_order = ["h1", "h2", "h3", "h4", "h5", "h6"]
        last_level = 0

        for level in heading_order:
            if headings[level]:
                if last_level and int(level[1]) > last_level + 1:
                    self.issues.append(f"⚠️ Heading structure issue: Found {level} without an H{last_level} above it.")
                last_level = int(level[1]) if headings[level] else last_level


    def check_internal_links(self):
        """Ensure there are enough internal links."""
        internal_links_count = self.seo_data.get("internal_links_count", 0)
        if internal_links_count < 3:
            self.issues.append("Low internal linking. Consider adding more internal links.")

    def check_external_links(self):
        """Check if there are external links (optional)."""
        external_links_count = self.seo_data.get("external_links_count", 0)
        if external_links_count == 0:
            self.issues.append("No external links found. Consider linking to relevant sources.")

    def check_broken_links(self):
        """Check for broken internal links."""
        for link in self.seo_data.get("internal_links", []):
            if "404" in link:
                self.issues.append(f" Broken internal link found: {link}")

    def check_image_optimization(self):
        """Check for missing, duplicate, or non-descriptive alt text in images."""
        alt_texts = {}

        for img in self.seo_data.get("image_data", []):
            alt_text = img.get("alt", "").strip()
            img_src = img["src"]


            if not alt_text or alt_text.lower() == "no alt text":
                self.issues.append(f"Image missing alt text: {img_src}")
                continue


            generic_terms = {"image", "photo", "screenshot", "picture", "graphic"}
            if alt_text.lower() in generic_terms or alt_text.endswith((".jpg", ".png", ".gif", ".webp")):
                self.issues.append(f"Non-descriptive alt text: '{alt_text}' for {img_src}")


            if alt_text in alt_texts:
                alt_texts[alt_text].append(img_src)
            else:
                alt_texts[alt_text] = [img_src]


        for alt_text, sources in alt_texts.items():
            if len(sources) > 1:
                self.issues.append(f"Duplicate alt text: '{alt_text}' used on {len(sources)} images.")
                print(f"Duplicate alt text detected: '{alt_text}' used on {len(sources)} images.")  # Debug print statement

    def check_large_images(self):
        """Check for large image files."""
        for img in self.seo_data.get("image_data", []):
            if img.get("size", 0) > 100000:
                self.issues.append(f" Large image file: {img['src']} ({img['size']} bytes)")

    def check_broken_images(self):
        """Check for broken images (404s)."""
        for img in self.seo_data.get("image_data", []):
            if img.get("status", 200) == 404:
                self.issues.append(f"Broken image found: {img['src']}")

    def check_https(self):
        """Check if the page is served over HTTPS."""
        if not self.seo_data.get("url", "").startswith("https://"):
            self.issues.append("Page is not served over HTTPS.")

    def check_sitemap(self):
        """Check if a sitemap exists and is referenced in robots.txt."""
        sitemap_url = self.seo_data.get("sitemap_url", "")
        robots_txt = self.seo_data.get("robots_txt", "")

        if not sitemap_url:
            self.issues.append("❌ No sitemap.xml detected. A sitemap helps search engines crawl your site efficiently.")

        if sitemap_url and "Sitemap:" not in robots_txt:
            self.issues.append("⚠️ Sitemap.xml is missing from robots.txt. Consider adding it for better indexing.")


    def check_robots_txt(self):
        """Check if robots.txt exists and has proper directives."""
        robots_txt = self.seo_data.get("robots_txt", "")

        if not robots_txt:
            self.issues.append("❌ No robots.txt file found. This file helps control how search engines crawl your site.")

        if "User-agent: *" not in robots_txt:
            self.issues.append("⚠️ robots.txt is missing a default User-agent directive.")

        if "Disallow: /" in robots_txt:
            self.issues.append("⚠️ robots.txt is blocking all search engines from crawling the site. Review your settings.")


    def check_structured_data(self):
        """Check for the presence of structured data."""
        structured_data = self.seo_data.get("structured_data", [])
        if not structured_data:
            self.issues.append("Missing structured data.")

    def check_open_graph(self):
        """Check for Open Graph metadata."""
        og_data = self.seo_data.get("open_graph_data", {})
        if not og_data.get("og:title"):
            self.issues.append("Missing Open Graph title.")
        if not og_data.get("og:description"):
            self.issues.append("Missing Open Graph description.")
        if not og_data.get("og:image"):
            self.issues.append("Missing Open Graph image.")
        if not og_data.get("og:url"):
            self.issues.append("Missing Open Graph URL.")

    def check_twitter_cards(self):
        """Check for Twitter Card metadata."""
        twitter_data = self.seo_data.get("twitter_card_data", {})
        if not twitter_data.get("twitter:title"):
            self.issues.append("Missing Twitter Card title.")
        if not twitter_data.get("twitter:description"):
            self.issues.append("Missing Twitter Card description.")
        if not twitter_data.get("twitter:image"):
            self.issues.append("Missing Twitter Card image.")
        if not twitter_data.get("twitter:url"):
            self.issues.append("Missing Twitter Card URL.")

    def check_hreflang(self):
        """Check for hreflang tags."""
        hreflang_tags = self.seo_data.get("hreflang_tags", [])
        if not hreflang_tags:
            self.issues.append("Missing hreflang tags.")

    def check_viewport(self):
        """Check for meta viewport tag."""
        viewport = self.seo_data.get("viewport", "")
        if not viewport:
            self.issues.append("Missing meta viewport tag.")

    def check_load_time(self):
        """Check if the page load time is too high."""
        load_time = self.seo_data.get("load_time", 0)
        if load_time > 3:
            self.issues.append(f"Page load time is too high: {load_time:.2f} seconds.")

    def analyze(self):
        """Run all SEO checks and return a list of issues."""
        self.check_meta_tags()
        self.check_canonical_tag()
        self.check_meta_robots()
        self.check_headings()
        self.check_internal_links()
        self.check_external_links()
        self.check_broken_links()
        self.check_image_optimization()
        self.check_large_images()
        self.check_broken_images()
        self.check_sitemap()
        self.check_robots_txt()
        self.check_https()
        self.check_structured_data()
        self.check_open_graph()
        self.check_twitter_cards()
        self.check_hreflang()
        self.check_viewport()
        self.check_load_time()
        return self.issues