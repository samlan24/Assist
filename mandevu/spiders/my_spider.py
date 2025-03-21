import scrapy
import json
from scrapy.linkextractors import LinkExtractor
from mandevu.utils.seo_rules import SEORuleChecker
from mandevu.utils.together_ai import get_recommendations
import time
import os
import subprocess
import requests

class SEOAuditSpider(scrapy.Spider):
    name = "seo_audit"
    allowed_domains = ["allanwanjiku.tech"]
    start_urls = ["https://allanwanjiku.tech/"]

    handle_httpstatus_list = [404]
    visited_links = set()
    all_pages = set()
    linked_pages = set()
    results = []
    seo_data = {"robots_txt": None, "sitemap": None}

    def start_requests(self):
        """Start by requesting robots.txt and sitemap.xml, then proceed to crawl the website."""
        # Request robots.txt
        yield scrapy.Request(
            url=f"{self.start_urls[0]}robots.txt",
            callback=self.parse_robots,
            errback=self.handle_missing_robots,
            dont_filter=True,
        )
        # Request sitemap.xml
        yield scrapy.Request(
            url=f"{self.start_urls[0]}sitemap.xml",
            callback=self.parse_sitemap,
            errback=self.handle_missing_sitemap,
            dont_filter=True,
        )
        # Begin crawling the website
        yield scrapy.Request(
            url=self.start_urls[0], callback=self.parse, dont_filter=True
        )

    def parse_robots(self, response):
        """Parse robots.txt file."""
        if response.status == 200:
            self.seo_data["robots_txt"] = response.text
            self.logger.info("✅ Robots.txt file found and processed.")
        else:
            self.seo_data["robots_txt"] = "Missing"
            self.logger.warning("⚠️ Robots.txt file not found.")

    def handle_missing_robots(self, failure):
        """Handle missing robots.txt gracefully."""
        self.seo_data["robots_txt"] = "Missing"
        self.logger.warning("⚠️ Robots.txt file not found (handled gracefully).")

    def parse_sitemap(self, response):
        """Parse sitemap.xml file."""
        if response.status == 200:
            self.seo_data["sitemap"] = response.text
            self.logger.info("✅ Sitemap.xml file found and processed.")
        else:
            self.seo_data["sitemap"] = "Missing"
            self.logger.warning("⚠️ Sitemap.xml file not found.")

    def handle_missing_sitemap(self, failure):
        """Handle missing sitemap.xml gracefully."""
        self.seo_data["sitemap"] = "Missing"
        self.logger.warning("⚠️ Sitemap.xml file not found (handled gracefully).")

    def parse(self, response):
        """Extracts SEO data and follows internal links."""
        if response.url in self.visited_links:
            return
        self.visited_links.add(response.url)
        self.all_pages.add(response.url)
        self.crawler.stats.inc_value('pages_crawled', 1)

        all_links = set(response.css("a::attr(href)").getall())

        internal_links = {
            response.urljoin(link)
            for link in all_links
            if (link.startswith("/") or link.startswith(self.start_urls[0]) or not link.startswith("http")) and not link.startswith("mailto:")
        }

        external_links = [link for link in all_links if not link.startswith("/") and not link.startswith(self.start_urls[0])]

        self.linked_pages.update(internal_links)

        meta_title = response.xpath("normalize-space(//title/text())").get(default="No Title Tag")
        meta_description = response.xpath("normalize-space(//meta[@name='description']/@content)").get(default="No Description Available")
        canonical = response.xpath("normalize-space(//link[@rel='canonical']/@href)").get(default="No Canonical Tag")
        meta_robots = response.xpath("normalize-space(//meta[@name='robots']/@content)").get(default="No Robots Tag")

        h1_tags = [tag.strip() for tag in response.xpath("//h1//text()").getall()]
        h2_tags = [tag.strip() for tag in response.xpath("//h2//text()").getall()]
        h3_tags = [tag.strip() for tag in response.xpath("//h3//text()").getall()]
        h4_tags = [tag.strip() for tag in response.xpath("//h4//text()").getall()]
        h5_tags = [tag.strip() for tag in response.xpath("//h5//text()").getall()]
        h6_tags = [tag.strip() for tag in response.xpath("//h6//text()").getall()]

        image_data = []
        for img in response.xpath("//img/@src").getall():
            img_url = response.urljoin(img)
            alt_text = response.xpath(f"//img[@src='{img}']/@alt").get(default="No Alt Text")
            status = response.xpath(f"//img[@src='{img}']/@status").get(default=200)


            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                img_size = len(img_response.content)
            except requests.RequestException:
                img_size = 0

            image_data.append({
                "src": img_url,
                "alt": alt_text,
                "size": img_size,
                "status": status
            })


        structured_data = response.xpath("//script[@type='application/ld+json']/text()").getall()
        open_graph_data = {
            "og:title": response.xpath("//meta[@property='og:title']/@content").get(default=""),
            "og:description": response.xpath("//meta[@property='og:description']/@content").get(default=""),
            "og:image": response.xpath("//meta[@property='og:image']/@content").get(default=""),
            "og:url": response.xpath("//meta[@property='og:url']/@content").get(default="")
        }
        twitter_card_data = {
            "twitter:title": response.xpath("//meta[@name='twitter:title']/@content").get(default=""),
            "twitter:description": response.xpath("//meta[@name='twitter:description']/@content").get(default=""),
            "twitter:image": response.xpath("//meta[@name='twitter:image']/@content").get(default=""),
            "twitter:url": response.xpath("//meta[@name='twitter:url']/@content").get(default="")
        }
        hreflang_tags = response.xpath("//link[@rel='alternate']/@hreflang").getall()
        viewport = response.xpath("//meta[@name='viewport']/@content").get(default="")

        start_time = time.time()
        response.follow(response.url)
        load_time = time.time() - start_time

        internal_links_status = self.check_links_status(internal_links)

        seo_data = {
            "url": response.url,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "canonical": canonical,
            "meta_robots": meta_robots,
            "h1_tags": h1_tags,
            "h2_tags": h2_tags,
            "h3_tags": h3_tags,
            "h4_tags": h4_tags,
            "h5_tags": h5_tags,
            "h6_tags": h6_tags,
            "internal_links_count": len(internal_links),
            "internal_links": internal_links_status,
            "external_links_count": len(external_links),
            "external_links": external_links,
            "image_data": image_data,
            "structured_data": structured_data,
            "open_graph_data": open_graph_data,
            "twitter_card_data": twitter_card_data,
            "hreflang_tags": hreflang_tags,
            "viewport": viewport,
            "load_time": load_time,
            "robots_txt": self.seo_data.get("robots_txt", "Unknown"),
            "sitemap": self.seo_data.get("sitemap", "Unknown"),

        }

        rule_checker = SEORuleChecker(seo_data)
        issues = rule_checker.analyze()
        seo_data["issues_detected"] = issues
        seo_data["ai_recommendations"] = get_recommendations(issues)

        self.results.append(seo_data)

        yield seo_data
        for link in internal_links:
            if link not in self.visited_links:
                yield scrapy.Request(link, callback=self.parse)

    def check_links_status(self, links):
        """Check the status of links and return a list with status codes."""
        links_status = []
        for link in links:
            try:
                response = requests.head(link, allow_redirects=True)
                links_status.append({"url": link, "status": response.status_code})
            except requests.RequestException as e:
                links_status.append({"url": link, "status": "error", "error": str(e)})
        return links_status

    def close_spider(self, spider):
        """Runs the report generator after Scrapy finishes crawling."""
        print("✅ Scrapy crawl complete. Generating SEO report...")

        orphan_pages = self.all_pages - self.linked_pages
        if orphan_pages:
            print(f"Orphan pages detected: {orphan_pages}")

        script_dir = os.path.dirname(__file__)
        script_path = os.path.join(script_dir, "..", "utils", "generate_report.py")
        subprocess.run(["python3", script_path])