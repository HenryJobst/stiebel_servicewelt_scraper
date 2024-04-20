docker run -d --name stiebel-scraper \
  -e DB_HOST=localhost \
  -e DB_NAME=stiebelwp \
  -e DB_USER=stiebelwp \
  -e DB_PASSWORD=stiebelwp \
  -e DB_PORT=5432 \
  stiebel-servicewelt-scraper
