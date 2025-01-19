import time
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

class YoutubeProducer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.processed_comment_ids = set()

    def scrape_comments(self, video_id, keyword):
        print(f"Scraping comments for video ID: {video_id}")
        request = self.youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="time",
            maxResults=2
        )
        response = request.execute()

        for item in response['items']:
            comment_id = item['snippet']['topLevelComment']['id']
            if comment_id not in self.processed_comment_ids:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comment_time = item['snippet']['topLevelComment']['snippet']['publishedAt']
                comment_time = datetime.strptime(comment_time, "%Y-%m-%dT%H:%M:%SZ")
                one_minute_ago = datetime.utcnow() - timedelta(minutes=5)
                if comment_time >= one_minute_ago:
                    message = {
                        'source': 'youtube',
                        'date': comment_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'videoId': video_id,
                        'comment': comment,
                        'topic': keyword
                    }
                    # Display the comment data in the console
                    print(f"Extracted comment: {json.dumps(message, indent=4)}")
                    self.processed_comment_ids.add(comment_id)

    def run(self, video_id, keyword):
        while True:
            self.scrape_comments(video_id, keyword)
            time.sleep(1)

if __name__ == "__main__":
    api_key = "AIzaSyBxwIjmxrzb26rRs_ms4FJ2S-3R8PdV7b0"  # replace with your YouTube API key
    video_id = "Kp5t_Ljdm2g"  # replace with your video ID
    keyword = "sentiment"  # replace with the relevant keyword for your topic

    youtube_producer = YoutubeProducer(api_key)
    youtube_producer.run(video_id, keyword)
