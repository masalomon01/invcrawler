import csv
import requests
from bs4 import BeautifulSoup
from requests import get
import config
import csv
import unidecode
import os
import time


def get_soup(url):
    response = get(url)
    response = response.text.encode('utf-8')
    html_soup = BeautifulSoup(response, 'html.parser')
    return html_soup


def csv_full_writer(doc, fields, lol):
    with open(doc, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(lol)


def write_to_csv(row):
    fields = ['id', 'sub_topic_id', 'title', 'body', 'author', 'url', 'follow_count', 'datetime', 'vote_count', 'comment_count']
    
    if os.path.isfile('posts_example.csv') == False:
        with open("posts_example.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fields)
            writer.writerow(row)
    else:
        with open(r'posts_example.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            try:
                writer.writerow(row)
            except:
                print (row)
                pass


def get_topics(url, othermainid=None):
    soup = get_soup(url)
    page_topics = soup.find_all('div', class_ = 'large-4 medium-12 small-12 columns text-center pad-top')  # This is hardcoded to fit invision sections
    main_topics, topics_list, id_cnt = {}, [], 0
    for item in page_topics:
        link = item.a.find('a', href=True)  # get the urls for the main topics
        name = item.find('h3', class_ ="homepage-card-titles")
        summary =  item.p.text
        main_topics[name.text] = [link['href'], summary, id_cnt]
        if othermainid != None:
            soup = get_soup(link['href'])
            topic_follows = soup.find('div', class_ = 'topic-subscribe dropdown')
            topic_follows_count = topic_follows.a['data-follower-count']
            topic = [id_cnt, othermainid, name.text, link['href'], summary, topic_follows_count]
            topics_list.append(topic)
        else:
            topic = [id_cnt, name.text, link['href'], summary]
            topics_list.append(topic)
        id_cnt += 1
    return main_topics, topics_list


def get_posts_data_for_page(all_posts, sub_topic_id, id_cnt):
    posts_on_page_list = []
    for post in all_posts:
            link, title = post.a['href'], post.a['title']
            author = post.find('span', class_ = 'post-author').text
            date = post.find('span', class_ = 'post-date')
            date = date.time['datetime']
            comment_count = post.find('div', class_ = 'post-overview-count comments')
            comment_count = comment_count.find('span', class_ = 'count').text
            vote_count = post.find('div', class_ = 'post-overview-count votes')
            vote_count = vote_count.find('span', class_ = 'count').text
            # in here we have to access the actual post and get the following info: body, follows
            soup = get_soup(link)
            article = soup.find('article', class_ = 'post')
            body = article.find('div', class_ = 'post-body')
            string = []
            for item in body:
                try:
                    txt = item.text
                    txt = txt.replace("\n", "")
                    txt = unidecode.unidecode(txt)
                except:
                    txt = None
                    pass
                if txt != None and len(txt)>=1:
                    string.append(txt)
            body = ''.join(string)
            community_follows = soup.find('div', class_ = 'community-follow right')
            community_follows_count = community_follows.a['data-follower-count']
            post_list = [id_cnt, sub_topic_id, title, body, author, link, community_follows_count, date, vote_count, comment_count]
            posts_on_page_list.append(post_list)
            write_to_csv(post_list)
            id_cnt += 1
    return posts_on_page_list, id_cnt


def scrape_community_posts(topics_dict):
    list_of_posts, id_cnt = [], 0
    for topic_name, values in topics_dict.items():
        url, sub_topic_id = values[0], values[2]
        url_stack = [url]
        pagecount = 1
        while url_stack:  # here we are looping until there is not an avaliable next page
            print('posts ', pagecount)
            pagecount += 1
            current_url = url_stack.pop()
            soup = get_soup(current_url)
            page_posts = soup.find_all('div', class_ = "post-overview")
            posts_on_page_list, id_cnt = get_posts_data_for_page(page_posts, sub_topic_id, id_cnt)
            list_of_posts = list_of_posts + posts_on_page_list
            try:
                next_page =  soup.find('li', class_ = 'pagination-next')
                next_page_url = next_page.a['href']
                next_page_url = config.MAIN_URL + next_page_url
            except:
                next_page_url = None

            if next_page is not None:
                url_stack.append(next_page_url)
        # community_dict[topic_name] = {'url': url, 'summary': values[1], 'topic_follows': topic_follows_count, 'posts': posts_dict} 
    return list_of_posts


def scrape_community_comments(posts_lol):
    # here we'll iterate over each post and scrape the comments
    for post in posts_lol:
        post_id, url = post[0], post[5]
        



if __name__ == '__main__':
    print ('starting to crawl!')
    main_topics, main_topics_list = get_topics(config.URL)
    csv_full_writer('main_topics.csv', ['id', 'title', 'url', 'summary'], main_topics_list)
    community_sub_topics, sub_topics_list = get_topics(main_topics['Community'][0], main_topics['Community'][2])
    csv_full_writer('sub_topics.csv', ['id', 'main_id', 'title', 'url', 'summary', 'follow_count'], sub_topics_list)
    posts_lol = scrape_community_posts(community_sub_topics)
    scrape_community_comments(posts_lol)
