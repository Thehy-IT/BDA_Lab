# ============================================================
# utils/mock_generator.py - Tạo dữ liệu giả lập
# ============================================================

import random
import uuid
from datetime import datetime, timedelta
from typing import List

from models.user_profile import UserProfile
from models.post import Post, MediaItem
from models.feed import FeedItem, TrendingTag

# ── Dữ liệu mẫu tiếng Việt ────────────────────────────────
SAMPLE_USERNAMES = [
    "nguyen_anh_tu", "tran_minh_khoa", "le_bao_chau",
    "pham_hong_nhung", "hoang_duc_manh", "do_thu_hang",
    "bui_van_long", "vo_thi_mai", "dang_quoc_khanh",
    "truong_ngoc_linh", "ngo_bich_van", "dinh_xuan_hoa",
]

SAMPLE_BIOS = [
    "Lập trình viên | Coffee addict ☕ | Yêu công nghệ",
    "Sinh viên CNTT | Đam mê AI & Machine Learning",
    "Nhiếp ảnh gia nghiệp dư | Du lịch | Ăn uống 🍜",
    "Marketing digital | Content creator | Blogger",
    "Kỹ sư phần mềm tại FPT | Open source contributor",
    "Yêu sách 📚 | Review phim | Triết học",
]

SAMPLE_CONTENTS = [
    "Hôm nay học được thuật toán mới về xử lý đồ thị, thật sự rất thú vị! "
    "Ai quan tâm đến Graph Neural Network thì cùng thảo luận nhé 🚀 #AI #MachineLearning",

    "Quán cà phê mới mở gần nhà, không gian cực chill, wifi tốt, giá hợp lý. "
    "Dân dev mà chưa ghé thì phí lắm đó 😄 #Hanoi #CafeReview",

    "Vừa hoàn thành bài tập lớn môn Hệ quản trị CSDL. "
    "Thiết kế NoSQL cho mạng xã hội thật sự thách thức! "
    "#MongoDB #Redis #Database #HUST",

    "Chia sẻ tài liệu học Python miễn phí cho anh em: "
    "link dưới đây nhé. Từ cơ bản đến nâng cao đều có 📖 #Python #LapTrinh",

    "Hà Nội mưa cả ngày rồi... Ngồi code mà nghe mưa rơi thật bình yên ❤️ "
    "#HaNoi #Rainy",

    "Thảo luận: MongoDB vs PostgreSQL cho hệ thống social media? "
    "Ý kiến của mọi người thế nào? #Database #Backend",

    "Vừa deploy ứng dụng lên production thành công! "
    "Mất 3 ngày debug cái lỗi Redis connection timeout mà 😭😂 #DevLife",

    "Đọc paper về Transformer architecture xong não tôi mụ hết 🤯 "
    "Nhưng mà hiểu rồi thì cảm giác amazing lắm! #DeepLearning #AI",
]

SAMPLE_HASHTAGS = [
    ["AI", "MachineLearning", "Technology"],
    ["MongoDB", "Redis", "NoSQL", "Database"],
    ["Python", "LapTrinh", "Programming"],
    ["HaNoi", "SaiGon", "Vietnam"],
    ["CafeReview", "Food", "Travel"],
    ["Backend", "DevLife", "SoftwareEngineering"],
    ["HUST", "UET", "SinhVien"],
    ["OpenSource", "GitHub", "Tech"],
]

SAMPLE_PLATFORMS = ["twitter", "facebook", "instagram"]

SAMPLE_LOCATIONS = [
    "Hà Nội, Việt Nam", "TP. Hồ Chí Minh, Việt Nam",
    "Đà Nẵng, Việt Nam", "Hải Phòng, Việt Nam",
]


def _random_date(days_back: int = 365) -> str:
    delta = timedelta(days=random.randint(0, days_back),
                      hours=random.randint(0, 23),
                      minutes=random.randint(0, 59))
    return (datetime.utcnow() - delta).isoformat()


def generate_users(n: int = 20, platform: str = None) -> List[UserProfile]:
    """Tạo n user giả lập"""
    users = []
    used_names = set()

    for _ in range(n):
        platform_chosen = platform or random.choice(SAMPLE_PLATFORMS)
        username = random.choice(SAMPLE_USERNAMES)
        # tránh trùng trong cùng platform
        suffix = random.randint(1, 9999)
        if username in used_names:
            username = f"{username}_{suffix}"
        used_names.add(username)

        followers = random.randint(50, 50_000)
        following = random.randint(10, min(followers, 2000))

        user = UserProfile(
            platform=platform_chosen,
            platform_uid=str(uuid.uuid4().int)[:12],
            username=username,
            display_name=username.replace("_", " ").title(),
            bio=random.choice(SAMPLE_BIOS),
            avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
            location=random.choice(SAMPLE_LOCATIONS),
            followers_count=followers,
            following_count=following,
            posts_count=random.randint(10, 3000),
            is_verified=random.random() < 0.05,
            interests=random.sample(
                ["AI", "Music", "Travel", "Food", "Tech", "Sport", "Book", "Movie"],
                k=random.randint(2, 5)
            ),
            created_at=_random_date(730),
        )
        users.append(user)

    return users


def generate_posts(users: List[UserProfile],
                   n_per_user: int = 5) -> List[Post]:
    """Tạo bài đăng giả lập cho danh sách users"""
    posts = []
    for user in users:
        count = random.randint(1, n_per_user)
        for _ in range(count):
            content = random.choice(SAMPLE_CONTENTS)
            tags    = random.choice(SAMPLE_HASHTAGS)
            has_media = random.random() < 0.4

            media = []
            if has_media:
                media.append(MediaItem(
                    media_type="image",
                    url=f"https://picsum.photos/seed/{uuid.uuid4().hex[:8]}/800/600",
                    width=800,
                    height=600,
                ).to_dict())

            post = Post(
                platform=user.platform,
                platform_pid=str(uuid.uuid4().int)[:14],
                author_id=user.user_id,
                author_name=user.username,
                content=content,
                hashtags=tags,
                media=media,
                likes_count=random.randint(0, 5000),
                comments_count=random.randint(0, 500),
                shares_count=random.randint(0, 200),
                views_count=random.randint(0, 100_000),
                published_at=_random_date(30),
                language="vi",
            )
            posts.append(post)

    return posts


def generate_feed_items(users: List[UserProfile],
                        posts: List[Post],
                        items_per_user: int = 20) -> List[FeedItem]:
    """Tạo feed giả lập"""
    items = []
    source_types = ["following", "trending", "recommended"]

    for user in users:
        sample_posts = random.sample(posts, min(items_per_user, len(posts)))
        for post in sample_posts:
            recency  = random.uniform(0.1, 1.0)
            relevance = random.uniform(0.1, 1.0)
            final    = 0.6 * relevance + 0.4 * recency

            item = FeedItem(
                user_id=user.user_id,
                post_id=post.post_id,
                source_type=random.choice(source_types),
                author_id=post.author_id,
                author_name=post.author_name,
                content_preview=post.content[:200],
                media_url=post.media[0]["url"] if post.media else None,
                likes_count=post.likes_count,
                comments_count=post.comments_count,
                relevance_score=round(relevance, 4),
                recency_score=round(recency, 4),
                final_score=round(final, 4),
            )
            items.append(item)

    return items


def generate_trending_tags(posts: List[Post]) -> List[TrendingTag]:
    """Đếm hashtag và tạo trending list"""
    counter: dict = {}
    for post in posts:
        for tag in post.hashtags:
            counter[tag] = counter.get(tag, 0) + 1

    return [
        TrendingTag(tag=tag, score=float(score), platform="all")
        for tag, score in sorted(counter.items(), key=lambda x: -x[1])
    ]
