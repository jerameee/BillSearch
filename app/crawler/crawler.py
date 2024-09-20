import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from app.models.bill import Bill, engine

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.text()


async def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    # This is a placeholder. You'll need to adjust the parsing logic
    # based on the actual structure of the websites you're crawling.
    title = soup.find('h1').text if soup.find('h1') else 'Unknown'
    content = soup.find('div', class_='bill-content').text if soup.find('div',
                                                                        class_='bill-content') else 'No content'
    return Bill(title=title, content=content)


async def crawl(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(url, session) for url in urls]
        htmls = await asyncio.gather(*tasks)
        bills = [await parse(html) for html in htmls]

        Session = sessionmaker(bind=engine)
        with Session() as db_session:
            db_session.add_all(bills)
            db_session.commit()

# Define the URLs to crawl
urls = [
    "https://example.com/bill1",
    "https://example.com/bill2",
]

if __name__ == "__main__":
    asyncio.run(crawl(urls))
