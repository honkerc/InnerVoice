"""Demo seed data for 与神对话."""

from datetime import datetime, timedelta

DEMO_IMAGE = "https://picsum.photos/seed/yushen/480/320"
DEMO_IMAGE_2 = "https://picsum.photos/seed/dialogue/480/320"


def _dt(days: int, hour: int, minute: int) -> datetime:
    base = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    return base - timedelta(days=days)


# (id, role, type, content, media_url, created_at, quote_id)
DEMO_MESSAGES: list[tuple] = [
    (
        "demo-001",
        "me",
        "text",
        "你想说什么？",
        None,
        _dt(7, 8, 30),
        None,
    ),
    (
        "demo-002",
        "me",
        "text",
        "#日精进\n早起 6:30\n读了 20 页书\n晚上有点拖延，明天改进",
        None,
        _dt(7, 22, 10),
        None,
    ),
    (
        "demo-003",
        "me",
        "text",
        "最近总在想：我到底在害怕什么？",
        None,
        _dt(6, 21, 45),
        None,
    ),
    (
        "demo-004",
        "me",
        "text",
        "备忘录：把房间收拾一下，断舍离从书桌开始",
        None,
        _dt(5, 12, 0),
        None,
    ),
    (
        "demo-005",
        "me",
        "text",
        "今天走路时突然想通了一件事——不是事件变了，是我愿意承认了",
        None,
        _dt(5, 19, 20),
        None,
    ),
    (
        "demo-006",
        "me",
        "image",
        "傍晚的云，像一封没寄出去的信",
        DEMO_IMAGE,
        _dt(4, 18, 5),
        None,
    ),
    (
        "demo-007",
        "me",
        "text",
        "工作卡在一个 bug 上三小时，越急越乱",
        None,
        _dt(3, 15, 40),
        None,
    ),
    (
        "demo-008",
        "me",
        "text",
        "急的时候先停下来呼吸。乱是因为心比手跑得快。",
        None,
        _dt(3, 15, 55),
        "demo-007",
    ),
    (
        "demo-009",
        "me",
        "text",
        "一句话：允许自己今天只完成 60 分",
        None,
        _dt(2, 9, 15),
        None,
    ),
    (
        "demo-010",
        "me",
        "image",
        "随手拍的路灯",
        DEMO_IMAGE_2,
        _dt(2, 23, 30),
        None,
    ),
    (
        "demo-011",
        "me",
        "text",
        "#日精进\n- 后端接口跑通了\n- 编辑器样式定稿\n- 明天做引用功能",
        None,
        _dt(1, 22, 0),
        None,
    ),
    (
        "demo-012",
        "me",
        "text",
        "活着就是不断和自己的对话。",
        None,
        _dt(1, 23, 10),
        None,
    ),
    (
        "demo-013",
        "me",
        "text",
        "情绪上来录了段视频，发泄完反而清楚了。不发了，留给自己。",
        None,
        _dt(1, 23, 45),
        None,
    ),
    (
        "demo-014",
        "me",
        "text",
        "#日精进\n今天把 FastAPI + SQLite 接好了\n聊天框悬浮在底部，发送即记录",
        None,
        _dt(0, 9, 30),
        None,
    ),
    (
        "demo-015",
        "me",
        "text",
        "编辑器样式我挺喜欢的，就按这个方向继续",
        None,
        _dt(0, 10, 15),
        None,
    ),
    (
        "demo-016",
        "me",
        "text",
        "这句话我想了一整夜。",
        None,
        _dt(0, 11, 0),
        "demo-012",
    ),
    (
        "demo-017",
        "me",
        "text",
        "当天在右，过往在左——像今天的我在回应过去的自己 🌱",
        None,
        _dt(0, 14, 20),
        None,
    ),
]
