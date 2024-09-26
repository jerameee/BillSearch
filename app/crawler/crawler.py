import logging
import xml.etree.ElementTree as ET
import asyncio
import aiohttp
from app.models.bill import Bill, engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch(url, session):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                return None
            return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None


async def parse(xml_content, url):
    if xml_content is None:
        return []

    try:
        root = ET.fromstring(xml_content)

        bills = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find(
                'title') is not None else 'No title'
            description = item.find('description').text if item.find(
                'description') is not None else 'No description'
            link = item.find('link').text if item.find(
                'link') is not None else 'No link'
            pub_date = item.find('pubDate').text if item.find(
                'pubDate') is not None else 'No date'

            # Extract additional fields if they exist
            bill_number = item.find('billNumber').text if item.find(
                'billNumber') is not None else 'No bill number'
            congress = item.find('congress').text if item.find(
                'congress') is not None else 'No congress'
            bill_type = item.find('billType').text if item.find(
                'billType') is not None else 'No bill type'

            # Combine all information into a structured content string
            full_content = f"Title: {title}\n"
            full_content += f"Description: {description}\n"
            full_content += f"Link: {link}\n"
            full_content += f"Published Date: {pub_date}\n"
            full_content += f"Bill Number: {bill_number}\n"
            full_content += f"Congress: {congress}\n"
            full_content += f"Bill Type: {bill_type}\n"
            full_content += f"Source: {url}"

            logger.info(f"Extracted bill: {title}")
            bills.append(Bill(title=title, content=full_content))

        return bills
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML from {url}: {str(e)}")
        return []


async def crawl(urls):
    async with aiohttp.ClientSession() as session:
        all_bills = []
        for url in urls:
            logger.info(f"Fetching URL: {url}")
            xml_content = await fetch(url, session)
            if xml_content:
                logger.info(f"Parsing URL: {url}")
                bills = await parse(xml_content, url)
                all_bills.extend(bills)
            await asyncio.sleep(1)  # Add a delay between requests

        logger.info(f"Total bills extracted: {len(all_bills)}")

        if all_bills:
            Session = sessionmaker(bind=engine)
            with Session() as db_session:
                db_session.add_all(all_bills)
                db_session.commit()
            logger.info("Bills saved to database")
        else:
            logger.warning("No bills extracted, database not updated")

# URLs to crawl
urls = [
    "https://www.govinfo.gov/rss/bills-enr.xml"
]

if __name__ == "__main__":
    asyncio.run(crawl(urls))
