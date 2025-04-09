import scrapy
import json
from scrapy.linkextractors import LinkExtractor
from mandevu.utils.seo_rules import SEORuleChecker
from mandevu.utils.together_ai import get_recommendations
import time
import os
import subprocess
import requests
import ssl
import socket
from datetime import datetime

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

    def check_ssl_cert(self, url):
        """Check SSL certificate validity."""
        hostname = url.replace("https://", "").replace("http://", "").split("/")[0]

        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()


                    subject = dict(x[0] for x in cert["subject"])
                    issuer = dict(x[0] for x in cert["issuer"])
                    valid_until = cert["notAfter"]


                    expiration_date = datetime.strptime(valid_until, "%b %d %H:%M:%S %Y %Z")
                    if datetime.now() > expiration_date:
                        return {"error": "Certificate is expired."}

                    return {
                        "subject": subject,
                        "issuer": issuer,
                        "valid_until": valid_until,
                        "is_valid": True
                    }
        except ssl.SSLError as e:
            return {"error": f"SSL error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def check_security_headers(self, url):
        """Fetch and filter common security headers."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            headers = response.headers
            common_security_headers = [
                "Content-Security-Policy",
                "Strict-Transport-Security",
                "X-Frame-Options",
                "X-Content-Type-Options",
                "Referrer-Policy",
                "Permissions-Policy",
                "X-XSS-Protection",
                "Expect-CT",
                "Feature-Policy",
            ]


            security_headers = {
                header: headers.get(header, "Not Set")
                for header in common_security_headers
            }

            return security_headers

        except requests.exceptions.RequestException as e:
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def check_securityheaders_io(self, url):
        """Check security headers using SecurityHeaders.io."""
        api_url = f"https://securityheaders.com/?q={url}&followRedirects=on"
        return f"Check security headers report: {api_url}"

    def extract_ssl_issues(self, ssl_result):
        """Extract issues from SSL certificate check."""
        issues = []
        if "error" in ssl_result:
            issues.append(f"SSL Certificate Error: {ssl_result['error']}")
        elif not ssl_result.get("is_valid", False):
            issues.append("SSL Certificate is invalid or expired.")
        return issues

    def extract_security_header_issues(self, security_headers):
        """Extract issues from security headers check."""
        issues = []
        required_headers = {
            "Content-Security-Policy": "Consider adding a Content-Security-Policy to prevent XSS attacks.",
            "Strict-Transport-Security": "Consider adding Strict-Transport-Security to enforce HTTPS.",
            "X-Frame-Options": "Consider adding X-Frame-Options to prevent clickjacking.",
            "X-Content-Type-Options": "Consider adding X-Content-Type-Options to prevent MIME type sniffing.",
            "Referrer-Policy": "Consider adding Referrer-Policy to control referrer information.",
            "Permissions-Policy": "Consider adding Permissions-Policy to restrict browser features.",
        }

        for header, recommendation in required_headers.items():
            if security_headers.get(header, "Not Set") == "Not Set":
                issues.append(f"Missing Security Header: {header}. {recommendation}")

        return issues

    def start_requests(self):
        """Start by checking SSL certificate and security headers, then proceed to crawl the website."""

        ssl_result = self.check_ssl_cert(self.start_urls[0])
        self.seo_data["ssl_cert"] = ssl_result


        if ssl_result.get("is_valid"):
            self.logger.info("SSL certificate is valid.")
        else:
            self.logger.warning(f"SSL certificate issue: {ssl_result.get('error')}")


        security_headers = self.check_security_headers(self.start_urls[0])
        self.seo_data["security_headers"] = security_headers


        if "error" in security_headers:
            self.logger.warning(f"Security headers check failed: {security_headers['error']}")
        else:
            self.logger.info(f"Security headers found: {list(security_headers.keys())}")


        securityheaders_io_report = self.check_securityheaders_io(self.start_urls[0])
        self.seo_data["securityheaders_io_report"] = securityheaders_io_report


        self.logger.info(f"SecurityHeaders.io report: {securityheaders_io_report}")


        yield scrapy.Request(
            url=f"{self.start_urls[0]}robots.txt",
            callback=self.parse_robots,
            errback=self.handle_missing_robots,
            dont_filter=True,
        )

        yield scrapy.Request(
            url=f"{self.start_urls[0]}sitemap.xml",
            callback=self.parse_sitemap,
            errback=self.handle_missing_sitemap,
            dont_filter=True,
        )

        yield scrapy.Request(
            url=self.start_urls[0], callback=self.parse, dont_filter=True
        )

    def parse_robots(self, response):
        """Parse robots.txt file."""
        if response.status == 200:
            self.seo_data["robots_txt"] = response.text
            self.logger.info("Robots.txt file found and processed.")
        else:
            self.seo_data["robots_txt"] = "Missing"
            self.logger.warning("Robots.txt file not found.")

    def handle_missing_robots(self, failure):
        """Handle missing robots.txt gracefully."""
        self.seo_data["robots_txt"] = "Missing"
        self.logger.warning("Robots.txt file not found (handled gracefully).")

    def parse_sitemap(self, response):
        """Parse sitemap.xml file."""
        if response.status == 200:
            self.seo_data["sitemap"] = response.text
            self.logger.info("Sitemap.xml file found and processed.")
        else:
            self.seo_data["sitemap"] = "Missing"
            self.logger.warning("Sitemap.xml file not found.")

    def handle_missing_sitemap(self, failure):
        """Handle missing sitemap.xml gracefully."""
        self.seo_data["sitemap"] = "Missing"
        self.logger.warning("Sitemap.xml file not found (handled gracefully).")

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

        external_links = [
            link for link in all_links
            if not link.startswith("/")
            and not link.startswith(self.start_urls[0])
            and not link.startswith("#")
            and not link.startswith("mailto:")
            and not link.startswith("tel:")
            and link.strip()
            and (link.startswith("http://") or link.startswith("https://"))
        ]

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
                img_type = img_response.headers.get("Content-Type", "unknown").split("/")[-1]  # Extract file type

            except requests.RequestException:
                img_size = 0
                img_type = "unknown"

            image_data.append({
                "src": img_url,
                "alt": alt_text,
                "size": img_size,
                "status": status,
                "type": img_type
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
            "ssl_cert": self.seo_data.get("ssl_cert", "Unknown"),
            "security_headers": self.seo_data.get("security_headers", "Unknown"),
            "securityheaders_io_report": self.seo_data.get("securityheaders_io_report", "Unknown"),
        }

        ssl_issues = self.extract_ssl_issues(self.seo_data.get("ssl_cert", {}))
        security_header_issues = self.extract_security_header_issues(self.seo_data.get("security_headers", {}))


        rule_checker = SEORuleChecker(seo_data)
        seo_issues = rule_checker.analyze()
        all_issues = ssl_issues + security_header_issues + seo_issues


        seo_data["issues_detected"] = all_issues
        seo_data["ai_recommendations"] = get_recommendations(all_issues)

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
        print("Scrapy crawl complete. Generating SEO report...")

        orphan_pages = self.all_pages - self.linked_pages
        if orphan_pages:
            print(f"Orphan pages detected: {orphan_pages}")

        script_dir = os.path.dirname(__file__)
        script_path = os.path.join(script_dir, "..", "utils", "generate_report.py")
        subprocess.run(["python3", script_path])