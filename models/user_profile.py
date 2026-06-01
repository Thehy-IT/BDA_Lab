# ============================================================
# models/user_profile.py - Data model cho User Profile
# ============================================================

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class UserProfile:
    """
    Model đại diện cho một User Profile trên mạng xã hội.
    Được lưu vào MongoDB collection: user_profiles
    """
    # ── Định danh ──────────────────────────────────────────
    user_id:      str = field(default_factory=lambda: str(uuid.uuid4()))
    platform:     str = ""          # twitter | facebook | instagram
    platform_uid: str = ""          # ID gốc trên platform

    # ── Thông tin cá nhân ──────────────────────────────────
    username:     str = ""
    display_name: str = ""
    bio:          str = ""
    avatar_url:   str = ""
    website:      str = ""
    location:     str = ""
    birth_date:   Optional[str] = None

    # ── Số liệu thống kê ───────────────────────────────────
    followers_count: int = 0
    following_count: int = 0
    posts_count:     int = 0
    is_verified:     bool = False
    is_private:      bool = False

    # ── Danh sách quan hệ ──────────────────────────────────
    following_ids: List[str] = field(default_factory=list)
    follower_ids:  List[str] = field(default_factory=list)
    interests:     List[str] = field(default_factory=list)   # tag / chủ đề quan tâm

    # ── Metadata ───────────────────────────────────────────
    created_at:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    crawled_at:    str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Chuyển về dict để lưu vào MongoDB"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Khởi tạo từ dict (khi đọc từ MongoDB)"""
        data.pop("_id", None)   # bỏ ObjectId của Mongo
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __repr__(self):
        return (f"<UserProfile user_id={self.user_id} "
                f"username=@{self.username} platform={self.platform} "
                f"followers={self.followers_count}>")
