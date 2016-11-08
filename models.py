from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *
import re


DATABASE = SqliteDatabase('journal.db')


class User(UserMixin, Model):
    username = CharField(unique=True)
    password = CharField(max_length=100)
    tags = CharField(default="")

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

    def owner(self, entry):
        """security check that the entry belongs to this user"""
        return entry.user == self

    def get_journal(self):
        """get all the users journal entries"""
        return Journal.select().where(Journal.user == self)

    def get_tagged_journals(self, tag):
        """find entries that contain the tag and belong to the user"""
        tag_search = tag + " "
        return Journal.select().where((Journal.user == self) &
                                      (Journal.tags.contains(tag_search)))


class Journal(Model):
    title = CharField(max_length=100)
    tags = CharField(default="")
    date = DateField()
    time_spent = CharField(max_length=100)
    learning = TextField()
    resources = TextField()
    entry_id = CharField()
    user = ForeignKeyField(
        rel_model=User,
        related_name='journals'
    )

    class Meta:
        database = DATABASE
        order_by = ('-date',)

    @classmethod
    def create_entry(cls, user, title, tags, date, time_spent, learning, resources):
        """creates new entry object"""

        entry_id = None
        count = 1
        while entry_id is None:
            name = title
            try:
                Journal.get(Journal.entry_id**name)
            except DoesNotExist:
                entry_id = name
            else:
                name = title + str(count)
                count += 1

        list_tags = re.findall('#[a-zA-Z0-9\-_]+', tags)
        new_tags = ""
        for tag in list_tags:
            new_tags += tag + " "

        try:
            with DATABASE.transaction():
                cls.create(
                    user=user,
                    title=title,
                    tags=new_tags,
                    date=date,
                    time_spent=time_spent,
                    learning=learning,
                    resources=resources,
                    entry_id=entry_id
                    )
        except IntegrityError:
            raise ValueError("User already exists")


def tags_persist(user):
    """checks that there are still entries for all the tags or removes them"""
    tag_list = ""
    existing_tags = re.findall('#[a-zA-Z0-9\-_]+', user.tags)
    for tag in existing_tags:  # check that all tags still exist
        journal = user.get_tagged_journals(tag)
        try:
            journal[0]
        except IndexError:
            pass
        else:
            tag_list += tag + " "

    user.tags = tag_list
    user.save()


def add_tags(user, tags_field):
    """ adds a new tag if it doesn't exist"""
    list_tags = re.findall('#[a-zA-Z0-9\-_]+', tags_field)
    for tag in list_tags:
        tag += " "
        if tag not in user.tags:
            user.tags += tag + " "
            user.save()


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Journal], safe=True)
    DATABASE.close()
