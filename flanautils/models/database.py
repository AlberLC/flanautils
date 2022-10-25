import os

import pymongo

from flanautils.models import MongoBase

mongo_client = None
db = None


def init_db():
    global mongo_client
    global db

    mongo_client = pymongo.MongoClient(
        host=os.environ.get('MONGO_HOST'),
        port=int(port) if (port := os.environ.get('MONGO_PORT')) else None,
        username=os.environ.get('MONGO_USER'),
        password=os.environ.get('MONGO_PASSWORD'),
        tz_aware=True
    )

    db = mongo_client[os.environ['DATABASE_NAME']]
    MongoBase.init_database_attributes(db)
