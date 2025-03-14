import scrapy
import json
from scrapy.linkextractors import LinkExtractor
from mandevu.utils.seo_rules import SEORuleChecker
from mandevu.utils.content_analyzer import analyze_content
import time

class SEOAuditSpider(scrapy.Spider):
    name = "seo_audit"
    allowed_domains = ["allanwanjiku.tech"]
    start_urls = ["https://allanwanjiku.tech/"]

    handle_httpstatus_list = [404]
    visited_links = set()
    results = []

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

        h1_tags = [tag.strip() for tag in response.xpath("//h1//text()").getall()]
        h2_tags = [tag.strip() for tag in response.xpath("//h2//text()").getall()]
        h3_tags = [tag.strip() for tag in response.xpath("//h3//text()").getall()]
        h4_tags = [tag.strip() for tag in response.xpath("//h4//text()").getall()]
        h5_tags = [tag.strip() for tag in response.xpath("//h5//text()").getall()]
        h6_tags = [tag.strip() for tag in response.xpath("//h6//text()").getall()]

        image_data = [
            {
                "src": response.urljoin(img),
                "alt": response.xpath(f"//img[@src='{img}']/@alt").get(default="No Alt Text"),
                "size": response.xpath(f"//img[@src='{img}']/@size").get(default=0),
                "status": response.xpath(f"//img[@src='{img}']/@status").get(default=200)
            }
            for img in response.xpath("//img/@src").getall()
        ]

        # Extract additional elements
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

        # Measure page load time
        start_time = time.time()
        response.follow(response.url)
        load_time = time.time() - start_time

        content = response.xpath("//body//text()").getall()
        content = " ".join(content).strip()

        content_analysis = analyze_content(content)

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
            "internal_links": list(internal_links),
            "external_links_count": len(external_links),
            "external_links": external_links,
            "image_data": image_data,
            "structured_data": structured_data,
            "open_graph_data": open_graph_data,
            "twitter_card_data": twitter_card_data,
            "hreflang_tags": hreflang_tags,
            "viewport": viewport,
            "load_time": load_time,
            "content_analysis": content_analysis,
        }

        rule_checker = SEORuleChecker(seo_data)
        issues = rule_checker.analyze()
        seo_data["issues_detected"] = issues

        self.results.append(seo_data)

        yield seo_data
        for link in internal_links:
            if link not in self.visited_links:
                yield response.follow(link, callback=self.parse)
