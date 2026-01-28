import scrapy
import re

class WikiFilmsSpider(scrapy.Spider):
    name = "п"
    allowed_domains = ["ru.wikipedia.org"]
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]

    custom_settings = {
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "DOWNLOAD_DELAY": 0.6,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "RETRY_ENABLED": True,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504],
        "RETRY_TIMES": 8,
        "COOKIES_ENABLED": False,
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {"User-Agent": "Mozilla/5.0 (compatible; WikiFilmHarvester/1.0; author=mizamoon)"},
    }

    bad_ns = {"Категория","Служебная","Википедия","Портал","Файл","Шаблон","Справка","Участник","Обсуждение","MediaWiki","Special","Help","Template","User"}
    year_re = re.compile(r"(18\d{2}|19\d{2}|20\d{2})")
    ref_re = re.compile(r"\[\d+\]")
    lang_re = re.compile(r"^(рус|англ|фр|нем|исп|ит|яп)\.\s*", re.I)
    ext_re = re.compile(r"\s*Внешние\s+видеофайлы.*$", re.I)

    def parse(self, r):
        for href in r.css("#mw-pages .mw-category-group li a::attr(href)").getall():
            if not href.startswith("/wiki/"):
                continue
            t = href[6:]
            if ":" in t and t.split(":", 1)[0] in self.bad_ns:
                continue
            yield r.follow(href, self.parse_film)

        nxt = r.xpath('//div[@id="mw-pages"]//a[normalize-space()="Следующая страница"]/@href').get()
        if nxt:
            yield r.follow(nxt, self.parse, dont_filter=True)

    def clean(self, s):
        return " ".join(self.ref_re.sub("", (s or "").replace("\xa0"," ")).split())

    def get_title(self, r):
        t = self.clean(" ".join(r.css("table.infobox .infobox-above").xpath(".//text()").getall()))
        t = self.ext_re.sub("", self.lang_re.sub("", t)).strip()
        return t or self.clean(r.css("#firstHeading .mw-page-title-main::text").get())

    def get_value(self, row):
        links = [self.clean(x) for x in row.xpath(".//td//a/text()").getall()]
        links = [x for x in links if x and not x.isdigit()]
        if links:
            return ", ".join(links)
        txt = [self.clean(x) for x in row.xpath('.//td//text()[not(ancestor::sup)]').getall()]
        return " ".join(x for x in txt if x)

    def parse_film(self, r):
        title = self.get_title(r)
        genre = director = country = year = ""

        for row in r.css("table.infobox tr"):
            key = self.clean(" ".join(row.xpath(".//th//text()").getall()))
            if not key:
                continue
            val = self.get_value(row)
            if "Жанр" in key:
                genre = val.lower()
            elif "Режисс" in key:
                director = self.clean(re.sub(r"\b\d+\b", "", val))
            elif "Стран" in key:
                country = self.clean(re.sub(r"\b\d+\b", "", val))
            elif "Год" in key:
                m = self.year_re.search(val or "")
                year = m.group(1) if m else ""

        yield {"Название": title, "Жанр": genre, "Режиссер": director, "Страна": country, "Год": year}