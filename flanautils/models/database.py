import os

import pymongo

from flanautils.models import MongoBase

mongo_client = None
database = None


def init_database(reload=False):
    global mongo_client
    global database

    if mongo_client and not reload:
        return

    mongo_client = pymongo.MongoClient(
        host=os.environ.get('MONGO_HOST'),
        port=int(port) if (port := os.environ.get('MONGO_PORT')) else None,
        username=os.environ.get('MONGO_USER'),
        password=os.environ.get('MONGO_PASSWORD'),
        tz_aware=True
    )

    if database_name := os.environ.get('DATABASE_NAME'):
        database = mongo_client[database_name]
        MongoBase.init_database_attributes(database)
