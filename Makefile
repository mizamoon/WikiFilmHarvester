run:
	cd movies && uv run scrapy crawl WikiFilmHarvester -O result.csv -s CLOSESPIDER_ITEMCOUNT=5
	uv run python movies/movies/omdb_rating.py movies/result.csv
