import mimetypes
from datetime import datetime

import requests
import os

from loguru import logger


class ApiVideo:
    DATE_TIME_FORMAT = "%Y-%M-%d %H:%M:%S"
    CHUNK_SIZE = 6000000

    # Set up variables for endpoints (we will create the third URL programmatically later)
    AUTH_URL = "https://ws.api.video/auth/api-key"
    CREATE_URL = "https://ws.api.video/videos"

    # Set up headers and payload for first authentication request
    HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    PAYLOAD = {"apiKey": os.environ["API_VIDEO_API_KEY"]}

    def __init__(self):
        self.token = None

    def get_token(self):
        # Send the first authentication request to get a token.
        # The token can be used for one hour with the rest of the API endpoints.
        response = requests.request("POST", self.AUTH_URL, json=self.PAYLOAD, headers=self.HEADERS)
        response = response.json()
        return response.get("access_token")

    def create_video(self):
        # Set up headers for authentication - the rest of the endpoints use Bearer authentication.

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.__auth_token()
        }

        # Create the video container payload, you can add more parameters if you like,
        # check out the docs at https://docs.api.video
        payload = {
            "title": f"Tesla Video {datetime.now().strftime(self.DATE_TIME_FORMAT)}",
            "description": f"Tesla video captured at {datetime.now().strftime(self.DATE_TIME_FORMAT)}"
        }

        # Send the request to create the container, and retrieve the videoId from the response.
        response = requests.request("POST", self.CREATE_URL, json=payload, headers=headers)
        response = response.json()
        return response["videoId"]

    def upload_video(self, file_path: str):
        # Set up the chunk size. This is how much you want to read from the file every time you grab a new chunk of
        # your file to read. If you're doing a big upload, the recommendation is 50 - 80 MB (50000000-80000000 bytes).
        # It's listed at 6MB (6000000 bytes) because then you can try this sample code with a small file just to see how
        # it will work.  The minimum size for a chunk is 5 MB.

        logger.info(f"Uploading {file_path} to api.video")

        if self.__is_video(file_path):
            # This is our chunk reader. This is what gets the next chunk of data ready to send.
            def read_in_chunks(file_object):
                while True:
                    data = file_object.read(self.CHUNK_SIZE)
                    if not data:
                        break
                    yield data

            # Create endpoint to upload video to - you have to add the videoId into the URL
            video_id = self.create_video()
            upload_url = f"{self.CREATE_URL}/{video_id}/source"

            content_size = os.stat(file_path).st_size

            logger.info(f"{file_path} {content_size / 1024 / 1024} MB")

            file = open(file_path, "rb")
            index = 0
            headers = {}
            for chunk in read_in_chunks(file):
                offset = index + len(chunk)
                headers["Content-Range"] = "bytes %s-%s/%s" % (index, offset - 1, content_size)
                headers["Authorization"] = self.__auth_token()
                index = offset
                try:
                    file = {"file": chunk}
                    requests.post(upload_url, files=file, headers=headers)
                except Exception as e:
                    logger.error(e)

            logger.info(f"Finished uploading {file_path} to api.video")
        else:
            logger.debug("Skipping uploading non video file!")

    def __auth_token(self):
        if not self.token:
            self.token = self.get_token()

        return "Bearer " + self.get_token()

    @staticmethod
    def __is_video(file_path):
        file_type = mimetypes.guess_type(file_path)[0]

        if file_type is not None and file_type.split("/")[0] == "video":
            return True
        else:
            return False
