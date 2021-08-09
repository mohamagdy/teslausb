import sys
import time

from loguru import logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from api_video import ApiVideo


class EventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.api_video = ApiVideo()

    def on_moved(self, event):
        pass

    def on_created(self, event):
        super().on_created(event)

        if event.is_directory:
            pass
        else:
            self.api_video.upload_video(event.src_path)

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        pass


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."

    logger.info(f"Started monitoring {path}")

    event_handler = EventHandler()

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
