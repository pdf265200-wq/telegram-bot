from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from bot.config import Config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    total_requests = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<User {self.user_id} - {self.username}>"

class UsageStat(Base):
    __tablename__ = 'usage_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    command = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UsageStat {self.command} at {self.timestamp}>"

class BroadcastMessage(Base):
    __tablename__ = 'broadcast_messages'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    message_text = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    recipients_count = Column(Integer, default=0)

# Create engine and session
engine = create_engine(Config.DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
