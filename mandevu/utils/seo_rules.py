class SEORuleChecker:
    def __init__(self, seo_data):
        self.seo_data = seo_data
        self.issues = []

    def check_meta_tags(self):
        """Check if meta title and description are missing or not optimal in length."""
        title = self.seo_data.get("meta_title", "")
        if not title or title == "No Title Tag":
            self.issues.append("❌ Missing title tag.")
        elif len(title) < 30 or len(title) > 60:
            self.issues.append("⚠️ Title tag length should be between 30-60 characters.")

        description = self.seo_data.get("meta_description", "")
        if not description or description == "No Description Available":
            self.issues.append("❌ Missing meta description.")
        elif len(description) < 50 or len(description) > 160:
            self.issues.append("⚠️ Meta description length should be between 50-160 characters.")

    def check_canonical_tag(self):
        """Check if the canonical tag is missing."""
        canonical = self.seo_data.get("canonical", "")
        if not canonical:
            self.issues.append("❌ Missing canonical tag.")

    def check_meta_robots(self):
        """Check if robots meta tag is missing or set to noindex."""
        robots = self.seo_data.get("meta_robots", "")
        if not robots or robots == "No Robots Tag":
            self.issues.append("⚠️ No robots meta tag found.")
        elif "noindex" in robots:
            self.issues.append("❌ Page is set to noindex (won't appear in search results).")

    def check_headings(self):
        """Ensure proper heading hierarchy (H1-H6) and check for missing or multiple H1 tags."""
        headings = {
            "h1": self.seo_data.get("h1_tags", []),  # Fix: Ensure it matches the key used in parse()
            "h2": self.seo_data.get("h2_tags", []),
            "h3": self.seo_data.get("h3_tags", []),
            "h4": self.seo_data.get("h4_tags", []),
            "h5": self. seo_data.get("h5_tags", []),
            "h6": self. seo_data.get("h6_tags", [])
        }

        # Check if H1 is missing or multiple H1s exist
        h1_count = len(headings["h1"])  # Fix: using corrected key
        if headings["h1"] == []:
            self.issues.append("❌ No H1 tag found on the page. Each page should have one main H1 tag for SEO.")
        elif h1_count > 1:
            self.issues.append(f"⚠️ Multiple H1 tags found ({h1_count}). Ensure only one main H1 for clarity.")

        # Check for heading hierarchy issues (H3 without H2, H4 without H3, etc.)
        heading_order = ["h1", "h2", "h3", "h4", "h5", "h6"]
        last_level = 0  # Track last seen heading level

        for level in heading_order:
            if headings[level]:  # If there are headings at this level
                if last_level and int(level[1]) > last_level + 1:
                    self.issues.append(f"⚠️ Heading structure issue: Found {level} without an H{last_level} above it.")
                last_level = int(level[1]) if headings[level] else last_level

    def check_internal_links(self):
        """Ensure there are enough internal links."""
        internal_links_count = self.seo_data.get("internal_links_count", 0)
        if internal_links_count < 3:
            self.issues.append("⚠️ Low internal linking. Consider adding more internal links.")

    def check_external_links(self):
        """Check if there are external links (optional)."""
        external_links_count = self.seo_data.get("external_links_count", 0)
        if external_links_count == 0:
            self.issues.append("⚠️ No external links found. Consider linking to relevant sources.")

    def check_broken_links(self):
        """Check for broken internal links."""
        for link in self.seo_data.get("internal_links", []):
            if "404" in link:
                self.issues.append(f"❌ Broken internal link found: {link}")

    def check_image_optimization(self):
        """Check for missing alt text in images."""
        for img in self.seo_data.get("image_data", []):
            if img.get("alt") == "No Alt Text":
                self.issues.append(f"⚠️ Image missing alt text: {img['src']}")

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
        return self.issues
