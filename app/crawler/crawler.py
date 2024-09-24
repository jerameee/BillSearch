import asyncio
import aiohttp
from bs4 import BeautifulSoup
from app.models.bill import Bill, engine
from sqlalchemy.orm import sessionmaker
import re


async def fetch(url, session):
    async with session.get(url) as response:
        return await response.text()


async def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='datatableclass')

    if not table:
        return []

    headers = [header.text.strip() for header in table.find_all('th')]

    bills = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cells = row.find_all('td')
        if len(cells) != len(headers):
            continue

        bill_data = {}
        for header, cell in zip(headers, cells):
            bill_data[header] = cell.text.strip()

        # Extract bill number and title
        bill_number = bill_data.get('Bill Number', '')
        title = bill_data.get('Title', '')

        # Combine all data into content
        content = ' '.join(f"{k}: {v}" for k, v in bill_data.items())

        # Add source URL to content
        content += f" Source: {url}"

        bills.append(Bill(title=f"{bill_number}: {title}", content=content))

    return bills


async def crawl(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(url, session) for url in urls]
        htmls = await asyncio.gather(*tasks)

        all_bills = []
        for html, url in zip(htmls, urls):
            bills = await parse(html, url)
            all_bills.extend(bills)

        Session = sessionmaker(bind=engine)
        with Session() as db_session:
            db_session.add_all(all_bills)
            db_session.commit()

# URL's to crawl
urls = [
    "https://crsreports.congress.gov/AppropriationsStatusTable",
    "https://crsreports.congress.gov/BillStatusTable",
    "https://crsreports.congress.gov/CommitteeStatusTable",
    "https://crsreports.congress.gov/CongressionalReportStatusTable",
    "https://crsreports.congress.gov/CommitteeReportStatusTable"
]

if __name__ == "__main__":
    asyncio.run(crawl(urls))
