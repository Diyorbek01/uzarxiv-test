import json
import time
from random import randint

from channels.generic.websocket import WebsocketConsumer

from main.models import Exam


class WSConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        number = 0
        while True:
            exams = Exam.objects.all()
            exams_number = Exam.objects.all().count()
            if number != exams_number:
                number = exams_number
                for i in exams:
                    self.send(json.dumps({
                        "id": i.id,
                        "group_name": i.group.name,
                        "variant_id": i.variant.id,
                        "variant_name": i.variant.name,
                        'start_date': str(i.start_date),
                        'finish_date': str(i.finish_date),
                        "duration": i.duration,
                        "is_retry": i.is_retry,
                    }))
            time.sleep(1)
