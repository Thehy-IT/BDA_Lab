# ============================================================
# models/post.py - Data model cho Post (bài đăng)
# ============================================================

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class MediaItem:
    """Ảnh / Video đính kèm trong bài đăng"""
    media_type: str = "image"   # image | video | gif
    url:        str = ""
    width:      int = 0
    height:     int = 0
    duration_s: Optional[float] = None  # chỉ dùng cho video

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Post:
    """
    Model đại diện cho một bài đăng (post / tweet / status).
    Được lưu vào MongoDB collection: posts
    Chỉ số like được cache thêm ở Redis (post_likes:{post_id})
    """
    # ── Định danh ──────────────────────────────────────────
    post_id:      str = field(default_factory=lambda: str(uuid.uuid4()))
    platform:     str = ""          # twitter | facebook | instagram
    platform_pid: str = ""          # ID bài gốc trên platform

    # ── Nội dung ───────────────────────────────────────────
    author_id:   str = ""
    author_name: str = ""
    content:     str = ""
    language:    str = "vi"
    media:       List[dict] = field(default_factory=list)   # list MediaItem.to_dict()

    # ── Phân loại ──────────────────────────────────────────
    hashtags:    List[str] = field(default_factory=list)
    mentions:    List[str] = field(default_factory=list)    # @username
    urls:        List[str] = field(default_factory=list)

    # ── Tương tác ──────────────────────────────────────────
    likes_count:    int = 0
    comments_count: int = 0
    shares_count:   int = 0
    views_count:    int = 0

    # ── Mối quan hệ ────────────────────────────────────────
    parent_post_id:  Optional[str] = None   # nếu là reply / quote
    is_repost:       bool = False
    original_post_id: Optional[str] = None

    # ── Vị trí ─────────────────────────────────────────────
    location_name: Optional[str] = None
    latitude:      Optional[float] = None
    longitude:     Optional[float] = None

    # ── Metadata ───────────────────────────────────────────
    published_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    crawled_at:   str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_deleted:   bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Post":
        data.pop("_id", None)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __repr__(self):
        preview = self.content[:40].replace("\n", " ")
        return (f"<Post post_id={self.post_id} "
                f"author=@{self.author_name} "
                f"content='{preview}...' "
                f"likes={self.likes_count}>")
