"""
SQLite database layer using SQLAlchemy.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

from .constants import DATABASE_PATH

logger = logging.getLogger(__name__)

Base = declarative_base()


# SQLAlchemy Models

class DownloadTable(Base):
    """Downloads table."""
    __tablename__ = "downloads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    platform = Column(String, nullable=False, default="huggingface")
    repo_type = Column(String, nullable=False, default="model")
    status = Column(String, default="pending")
    save_path = Column(String, nullable=False)
    files_json = Column(Text)  # JSON array of selected files
    total_bytes = Column(Integer, default=0)
    downloaded_bytes = Column(Integer, default=0)
    speed_bps = Column(Float, default=0.0)
    priority = Column(Integer, default=5)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    
    files = relationship("DownloadFileTable", back_populates="download", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_downloads_status", "status"),
        Index("idx_downloads_platform", "platform"),
    )


class DownloadFileTable(Base):
    """Download files table (per-file tracking)."""
    __tablename__ = "download_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    download_id = Column(Integer, ForeignKey("downloads.id", ondelete="CASCADE"))
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    downloaded_bytes = Column(Integer, default=0)
    status = Column(String, default="pending")
    checksum = Column(String)
    verified = Column(Boolean, default=False)
    
    download = relationship("DownloadTable", back_populates="files")


class HistoryTable(Base):
    """Download history table."""
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    repo_type = Column(String, nullable=False)
    save_path = Column(String, nullable=False)
    total_bytes = Column(Integer)
    duration_seconds = Column(Integer)
    completed_at = Column(DateTime, default=datetime.now)
    is_favorite = Column(Boolean, default=False)
    tags = Column(Text)  # JSON array
    
    __table_args__ = (
        Index("idx_history_repo", "repo_id"),
        Index("idx_history_favorite", "is_favorite"),
    )


class ProfileTable(Base):
    """Profiles table."""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    platform = Column(String)
    endpoint = Column(String)
    default_path = Column(String)
    token_id = Column(Integer, ForeignKey("tokens.id"))
    file_filters = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.now)


class TokenTable(Base):
    """Tokens table (encrypted)."""
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    encrypted_value = Column(String, nullable=False)
    scope = Column(String)
    last_validated = Column(DateTime)
    is_valid = Column(Boolean, default=True)


class LocationTable(Base):
    """Named locations table."""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    tool_type = Column(String)
    model_type = Column(String)
    created_at = Column(DateTime, default=datetime.now)


class LocalModelTable(Base):
    """Local models table (scanned)."""
    __tablename__ = "local_models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, nullable=False, unique=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    file_hash = Column(String)
    model_type = Column(String)
    source_repo = Column(String)
    source_platform = Column(String)
    scanned_at = Column(DateTime, default=datetime.now)
    metadata_json = Column(Text)
    
    __table_args__ = (
        Index("idx_local_models_type", "model_type"),
        Index("idx_local_models_hash", "file_hash"),
    )


class SettingsTable(Base):
    """Settings key-value table."""
    __tablename__ = "settings"
    
    key = Column(String, primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.now)


class Database:
    """Database manager singleton."""
    
    _instance = None
    
    def __new__(cls, db_path: Path = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Path = None):
        if self._initialized:
            return
            
        self.db_path = db_path or DATABASE_PATH
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._initialized = True
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def session(self) -> Session:
        """Get a database session context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # Download operations
    
    def add_download(self, download_data: Dict[str, Any]) -> int:
        """Add a new download task."""
        with self.session() as session:
            download = DownloadTable(**download_data)
            session.add(download)
            session.flush()
            return download.id
    
    def get_download(self, download_id: int) -> Optional[DownloadTable]:
        """Get download by ID."""
        with self.session() as session:
            result = session.query(DownloadTable).filter_by(id=download_id).first()
            if result:
                session.expunge(result)
            return result
    
    def get_downloads_by_status(self, status: str) -> List[DownloadTable]:
        """Get all downloads with given status."""
        with self.session() as session:
            results = session.query(DownloadTable).filter_by(status=status).all()
            for r in results:
                session.expunge(r)
            return results
    
    def get_pending_downloads(self) -> List[DownloadTable]:
        """Get all pending/queued downloads ordered by priority."""
        with self.session() as session:
            results = session.query(DownloadTable).filter(
                DownloadTable.status.in_(["pending", "queued"])
            ).order_by(DownloadTable.priority).all()
            for r in results:
                session.expunge(r)
            return results
    
    def update_download(self, download_id: int, **updates) -> bool:
        """Update download fields."""
        with self.session() as session:
            result = session.query(DownloadTable).filter_by(id=download_id).update(updates)
            return result > 0
    
    def delete_download(self, download_id: int) -> bool:
        """Delete a download task."""
        with self.session() as session:
            result = session.query(DownloadTable).filter_by(id=download_id).delete()
            return result > 0
    
    # History operations
    
    def add_to_history(self, history_data: Dict[str, Any]) -> int:
        """Add completed download to history."""
        with self.session() as session:
            history = HistoryTable(**history_data)
            session.add(history)
            session.flush()
            return history.id
    
    def get_history(self, limit: int = 100, favorites_only: bool = False) -> List[HistoryTable]:
        """Get download history."""
        with self.session() as session:
            query = session.query(HistoryTable)
            if favorites_only:
                query = query.filter_by(is_favorite=True)
            results = query.order_by(HistoryTable.completed_at.desc()).limit(limit).all()
            for r in results:
                session.expunge(r)
            return results
    
    def toggle_favorite(self, history_id: int) -> bool:
        """Toggle favorite status."""
        with self.session() as session:
            history = session.query(HistoryTable).filter_by(id=history_id).first()
            if history:
                history.is_favorite = not history.is_favorite
                return True
            return False
    
    # Settings operations
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self.session() as session:
            setting = session.query(SettingsTable).filter_by(key=key).first()
            return setting.value if setting else default
    
    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        with self.session() as session:
            setting = session.query(SettingsTable).filter_by(key=key).first()
            if setting:
                setting.value = value
                setting.updated_at = datetime.now()
            else:
                session.add(SettingsTable(key=key, value=value))
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings as dictionary."""
        with self.session() as session:
            settings = session.query(SettingsTable).all()
            return {s.key: s.value for s in settings}
    
    # Location operations
    
    def add_location(self, location_data: Dict[str, Any]) -> int:
        """Add a named location."""
        with self.session() as session:
            location = LocationTable(**location_data)
            session.add(location)
            session.flush()
            return location.id
    
    def get_locations(self) -> List[LocationTable]:
        """Get all named locations."""
        with self.session() as session:
            results = session.query(LocationTable).order_by(LocationTable.name).all()
            for r in results:
                session.expunge(r)
            return results
    
    def delete_location(self, location_id: int) -> bool:
        """Delete a location."""
        with self.session() as session:
            result = session.query(LocationTable).filter_by(id=location_id).delete()
            return result > 0
    
    # Profile operations
    
    def add_profile(self, profile_data: Dict[str, Any]) -> int:
        """Add a profile."""
        with self.session() as session:
            profile = ProfileTable(**profile_data)
            session.add(profile)
            session.flush()
            return profile.id
    
    def get_profiles(self) -> List[ProfileTable]:
        """Get all profiles."""
        with self.session() as session:
            results = session.query(ProfileTable).order_by(ProfileTable.name).all()
            for r in results:
                session.expunge(r)
            return results
    
    def get_profile(self, profile_id: int) -> Optional[ProfileTable]:
        """Get profile by ID."""
        with self.session() as session:
            result = session.query(ProfileTable).filter_by(id=profile_id).first()
            if result:
                session.expunge(result)
            return result
    
    # Local model operations
    
    def add_local_model(self, model_data: Dict[str, Any]) -> int:
        """Add or update a scanned local model."""
        with self.session() as session:
            existing = session.query(LocalModelTable).filter_by(
                file_path=model_data["file_path"]
            ).first()
            
            if existing:
                for key, value in model_data.items():
                    setattr(existing, key, value)
                return existing.id
            else:
                model = LocalModelTable(**model_data)
                session.add(model)
                session.flush()
                return model.id
    
    def get_local_models(self, model_type: str = None) -> List[LocalModelTable]:
        """Get local models, optionally filtered by type."""
        with self.session() as session:
            query = session.query(LocalModelTable)
            if model_type:
                query = query.filter_by(model_type=model_type)
            results = query.order_by(LocalModelTable.file_name).all()
            for r in results:
                session.expunge(r)
            return results
    
    def find_duplicates(self) -> List[tuple]:
        """Find duplicate models by file hash."""
        with self.session() as session:
            from sqlalchemy import func
            duplicates = session.query(
                LocalModelTable.file_hash,
                func.count(LocalModelTable.id).label('count')
            ).filter(
                LocalModelTable.file_hash.isnot(None)
            ).group_by(
                LocalModelTable.file_hash
            ).having(
                func.count(LocalModelTable.id) > 1
            ).all()
            
            result = []
            for file_hash, count in duplicates:
                models = session.query(LocalModelTable).filter_by(file_hash=file_hash).all()
                result.append((file_hash, models))
            return result


# Convenience functions
_db_instance = None

def get_db() -> Database:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
