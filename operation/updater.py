from urllib import request

from apscheduler.schedulers.background import BackgroundScheduler

from operation.views import CronJob


def start():
    schedular = BackgroundScheduler()
    cron = CronJob()

    # schedular.add_job(cron.get, "interval", seconds=5, kwargs={'request': request})

    schedular.start()