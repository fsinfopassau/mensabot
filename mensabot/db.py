from sqlalchemy import *

SQL_ENGINE = create_engine('sqlite:///mensabot.sqlite', echo=True)

metadata = MetaData()
CHATS = Table(
    'chats', metadata,
    Column('id', Integer, primary_key=True),
    Column('price_category', Integer, default=0),
    Column('template', String, default=None),
    Column('locale', String, default=None),
    Column('notification_time', Time, default=None),
)

metadata.create_all(SQL_ENGINE)
