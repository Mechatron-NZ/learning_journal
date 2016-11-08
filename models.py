import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *

DATABASE = SqliteDatabase('journal.db')

class User(UserMixin, Model):
    username = CharField(unique=True)
    password = CharField(max_length=100)
    tags = TextField(default="")


    class Meta:
        database = DATABASE
        order_by = ('-username',)

    @classmethod
    def create_user(cls, username, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    password=generate_password_hash(password)
                    )
        except IntegrityError:
            raise ValueError("User already exists")

    def get_journal(self):
        return Journal.select().where(Journal.user == self)

    def get_tagged_journals(self, tag):
        return Journal.select().where((Journal.user == self) &
                                      (Journal.tags.contains(tag)))

class Journal(Model):
    title = CharField(max_length=100)
    tags = CharField(default="")
    date = DateField()
    time_spent = CharField(max_length=100)
    learning = TextField()
    resources = TextField()
    user = ForeignKeyField(
        rel_model=User,
        related_name='journals'
    )

    class Meta:
        database = DATABASE
        order_by =('-date',)

def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Journal], safe=True)
    DATABASE.close()
