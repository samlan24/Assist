import scrapy
import json
from scrapy.linkextractors import LinkExtractor
from mandevu.utils.seo_rules import SEORuleChecker

class SEOAuditSpider(scrapy.Spider):
    name = "seo_audit"
    allowed_domains = ["allanwanjiku.tech"]
    start_urls = ["https://allanwanjiku.tech/"]

    handle_httpstatus_list = [404]
    visited_links = set()

    def parse(self, response):
        """Extracts SEO data and follows internal links."""
        if response.url in self.visited_links:
            return
        self.visited_links.add(response.url)
        self.crawler.stats.inc_value('pages_crawled', 1)

        all_links = set(response.css("a::attr(href)").getall())


        internal_links = {
            response.urljoin(link)
            for link in all_links
            if link.startswith("/") or link.startswith(self.start_urls[0]) or not link.startswith("http")
        }

        external_links = [link for link in all_links if not link.startswith("/") and not link.startswith(self.start_urls[0])]


        meta_title = response.xpath("normalize-space(//title/text())").get(default="No Title Tag")
        meta_description = response.xpath("normalize-space(//meta[@name='description']/@content)").get(default="No Description Available")
        canonical = response.xpath("normalize-space(//link[@rel='canonical']/@href)").get(default="No Canonical Tag")
        meta_robots = response.xpath("normalize-space(//meta[@name='robots']/@content)").get(default="No Robots Tag")

        h1_tags = response.xpath("//h1//text()").getall()
        image_data = [
            {"src": response.urljoin(img), "alt": response.xpath(f"//img[@src='{img}']/@alt").get(default="No Alt Text")}
            for img in response.xpath("//img/@src").getall()
        ]

        seo_data = {
            "url": response.url,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "canonical": canonical,
            "meta_robots": meta_robots,
            "h1_tags": h1_tags,
            "internal_links_count": len(internal_links),
            "internal_links": list(internal_links),
            "external_links_count": len(external_links),
            "external_links": external_links,
            "image_data": image_data,
        }

        rule_checker = SEORuleChecker(seo_data)
        issues = rule_checker.analyze()
        seo_data["issues_detected"] = issues

        yield seo_data
        for link in internal_links:
            if link not in self.visited_links:
                yield response.follow(link, callback=self.parse)
