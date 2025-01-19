import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from kafka import KafkaProducer
import json
from datetime import datetime

# Configuration des options pour Selenium Chrome en mode headless
options = webdriver.ChromeOptions()
options.add_argument('--headless')

# Initialisation du service pour le chromedriver
service = Service(r'C:\chromedriver-win64\chromedriver.exe')
driver = webdriver.Chrome(service=service, options=options)

class HespressProducer:
    def __init__(self, server):
        """Initialisation du producteur Kafka."""
        self.server = server
        self.bootstrap_servers = server
        self.topic = 'bigproject'
        self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)

    def hespress_articles(self, mots, rep=20):
        """Collecte les articles correspondant au mot-clé."""
        link = f"https://en.hespress.com/?s={mots}"
        driver.get(link)

        # Attente explicite que la page soit chargée
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'search_results')))

        # Défilement pour charger plus d'articles
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(rep):
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.body.scrollHeight") > last_height)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Récupération du contenu HTML de la page
        src = driver.page_source
        soup = BeautifulSoup(src, 'html.parser')

        # Extraction des articles
        uls = soup.find('div', {'class': 'search_results row'})
        data = []
        for div in uls.findAll('div', {'class': 'col-12 col-sm-6 col-md-4 col-xl-3'}):
            try:
                title = div.find('h3', {'class': 'card-title'}).text.strip()
                link = div.find('a', {'class': 'stretched-link'}).get('href')
                date = div.find('small', {'class': 'text-muted time'}).text.strip()
                data.append({'Title': title, 'Link': link, 'Date': date})
            except AttributeError:
                pass

        df = pd.DataFrame(data)
        return df

    def extract_data(self, url):
        """Extraction des données d'un article spécifique."""
        try:
            driver.get(url)
            time.sleep(1)  # Petite pause pour laisser le temps de charger la page

            # Récupération du contenu HTML
            src = driver.page_source
            soup = BeautifulSoup(src, 'html.parser')

            # Extraction des informations de l'article
            titre = soup.find('h1', {'class': 'post-title'})
            titre = titre.get_text().strip() if titre else "not available"

            date = soup.find('span', {'class': 'date-post'})
            date = date.get_text().strip() if date else "not available"

            sections = soup.find('section', {'class': 'box-tags'})
            tags = ", ".join([section.get_text().strip() for section in sections.findAll('a')]) if sections else ""

            article = soup.find('div', {'class': 'article-content'})
            text = "\n".join([p.get_text().strip() for p in article.findAll('p')]) if article else ""

            # Extraction des commentaires
            comments_area = soup.find('ul', {'class': 'comment-list hide-comments'})
            comments = []
            if comments_area:
                for comment in comments_area.findAll('li', {'class': 'comment even thread-even depth-1 not-reply'}):
                    comment_date = comment.find('div', {'class': 'comment-date'})
                    comment_content = comment.find('div', {'class': 'comment-text'})
                    comment_react = comment.find('span', {'class': 'comment-recat-number'})
                    if comment_date and comment_content and comment_react:
                        comments.append({
                            "comment_date": comment_date.get_text(),
                            "comment_content": comment_content.get_text(),
                            "comment_react": comment_react.get_text()
                        })

            return {'Date': date, 'Titre': titre, 'Tags': tags, 'content': text, 'Comments': comments}
        except Exception as e:
            print(f"Error encountered while processing {url}: {e}")
            return None

    def run(self, keyword):
        """Lance la collecte et l'envoi des données à Kafka."""
        # Collecte des articles en fonction du mot-clé
        articles_df = self.hespress_articles(keyword)
        print("Articles récupérés:")
        print(articles_df)  # Affichage des articles récupérés

        # Collecte des informations supplémentaires pour chaque article
        result_df = pd.DataFrame(columns=['Date', 'Titre', 'Tags', 'Comments'])
        for url in articles_df['Link']:
            extracted_data = self.extract_data(url)
            if extracted_data:
                result_df = pd.concat([result_df, pd.DataFrame([extracted_data])], ignore_index=True)
                result_df['Date'] = pd.to_datetime(result_df['Date'], errors='coerce')
                result_df = result_df.dropna(subset=['Date'])
                result_df['Date'] = result_df['Date'].dt.strftime("%Y-%m-%d %H:%M:%S")

                # Envoi des données à Kafka
                message = {
                    'source': 'Hespress',
                    'date': result_df['Date'].iloc[-1],
                    'videoId': url,
                    'comment': result_df['Titre'].iloc[-1],
                    'topic': keyword
                }
                print(f"Envoi du message : {message}")
                self.producer.send(self.topic, value=json.dumps(message).encode('utf-8'))
                time.sleep(1)  # Petite pause entre les envois

# Assurez-vous que Kafka fonctionne sur localhost:9092
hespress_producer = HespressProducer('127.0.0.1:9092')  # Assurez-vous que Kafka est à cet endroit
hespress_producer.run("maroc")  # Lance la collecte des articles sur le mot-clé "maroc"
