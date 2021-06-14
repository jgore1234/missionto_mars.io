# Dependencies

from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
from splinter import Browser
import time
import re

# Define a function called `scrape` that will execute all of your scraping code from the `mission_to_mars.ipynb` notebook and return one Python dictionary containing all of the scraped data.
def scrape():

    browser = Browser("chrome", executable_path="chromedriver", headless=True)
    news_title, news_paragraph = mars_news(browser)

    # store the result of the scraping function in dictionary.
    dict = {
        "news_title": news_title,
        "news_paragraph": news_paragraph,
        "featured_image": featured_img(browser),
        "hemispheres": hemispheres(browser),
        "weather": weather_tweet(browser),
        "facts": facts_mars(),
        "last_modified": dt.datetime.now()
    }

    
    browser.quit()
    return dict


def mars_news(browser):
    mars_url = "https://mars.nasa.gov/news/"
    browser.visit(mars_url)

    # Retrieve first list element and pause half a second if not instantly present
    browser.is_element_present_by_css("ul.item_list li.slide", wait_time=0.5)

    html = browser.html
    mars_news_soup = BeautifulSoup(html, "html.parser")

    try:
        slide_elem = mars_news_soup.select_one("ul.item_list li.slide")
        news_title = slide_elem.find("div", class_="content_title").get_text()
        news_p = slide_elem.find(
            "div", class_="article_teaser_body").get_text()

    except AttributeError:
        return None, None

    return news_title, news_p


def featured_img(browser):
    url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"
    browser.visit(url)

    full_img_elem = browser.find_by_id("full_image")
    full_img_elem.click()

    browser.is_element_present_by_text("more info", wait_time=0.5)
    more_info_elem = browser.links.find_by_partial_text("more info")
    more_info_elem.click()

    # read the consequential html with soup
    html = browser.html
    image_soup = BeautifulSoup(html, "html.parser")

    # Get the relative img url
    image = image_soup.select_one("figure.lede a img")

    try:
        image_url_rel = image.get("src")

    except AttributeError:
        return None

    # Use the base url to create an absolute url
    image_url = f"https://www.jpl.nasa.gov{image_url_rel}"

    return image_url


def hemispheres(browser):

    # A way to break up long strings
    hem_url = (
        "https://astrogeology.usgs.gov/search/"
        "results?q=hemisphere+enhanced&k1=target&v1=Mars"
    )

    browser.visit(hem_url)

    # Click the link, find the sample anchor, return the href
    hem_img_urls = []
    for index in range(4):

        # Find the elements on each loop to avoid a stale element exception
        browser.find_by_css("a.product-item h3")[index].click()

        hemi_data = scrape_hemisphere(browser.html)

        # Append hemisphere object to list
        hem_img_urls.append(hemi_data)

        # Finally, we navigate backwards
        browser.back()

    return hem_img_urls


def weather_tweet(browser):
    twitter_url = "https://twitter.com/marswxreport?lang=en"
    browser.visit(twitter_url)

    # halt for 4 seconds to let the Twitter page load before extracting the html
    time.sleep(4)

    html = browser.html
    mars_weather_soup = BeautifulSoup(html, "html.parser")

    # Find a tweet which contains the text `Mars Weather`
    tweet_att = {"class": "tweet", "data-name": "Mars Weather"}
    mars_weather_tweet = mars_weather_soup.find("div", attrs=tweet_att)

    # Look through the tweet for the paragraph tag or span tag containing the tweet text
    # As Tweets changes rgularly the try/except function will spot the tweet
    
    try:
        tweet_mars_weather = mars_weather_tweet.find("p", "tweet-text").get_text()

    except AttributeError:

        pattern = re.compile(r'sol')
        tweet_mars_weather = mars_weather_soup.find('span', text=pattern).text

    return tweet_mars_weather


def scrape_hemisphere(html_text):
    # Soupify the html text
    hemisphere_soup = BeautifulSoup(html_text, "html.parser")

    # Try to get href and text except if error.
    try:
        elem_title = hemisphere_soup.find("h2", class_="title").get_text()
        elem_sample = hemisphere_soup.find("a", text="Sample").get("href")

    except AttributeError:

        # Image error returns None for better front-end handling
        elem_title = None
        elem_sample = None

    hem_dict = {
        "title": elem_title,
        "img_url": elem_sample
    }

    return hem_dict


def facts_mars():
    try:
        facts_df = pd.read_html("http://space-facts.com/mars/")[0]
    except BaseException:
        return None

    facts_df.columns = ["Parameter", "Value"]
    facts_df.set_index("Parameter", inplace=True)

    # Add some bootstrap styling to <table>
    return facts_df.to_html(classes="table table-striped")


if __name__ == "__main__":

    # If running as script, print scraped data
    print(scrape())
