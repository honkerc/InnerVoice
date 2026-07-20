from tortoise import fields, models


class Message(models.Model):
    id = fields.CharField(pk=True, max_length=64)
    role = fields.CharField(max_length=8, default="me")
    type = fields.CharField(max_length=16, default="text")
    content = fields.TextField(default="")
    media_url = fields.CharField(max_length=512, null=True)
    media_name = fields.CharField(max_length=255, null=True)
    attachments = fields.TextField(null=True)
    tags = fields.TextField(null=True)
    quote_id = fields.CharField(max_length=64, null=True, unique=True)
    reply_to_id = fields.CharField(max_length=64, null=True)
    author_avatar_url = fields.CharField(max_length=512, null=True)
    author_display_name = fields.CharField(max_length=64, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "messages"
        ordering = ["created_at"]


class UserSettings(models.Model):
    id = fields.CharField(pk=True, max_length=32, default="default")
    display_name = fields.CharField(max_length=64, default="我")
    avatar_url = fields.CharField(max_length=512, null=True)
    ai_provider = fields.CharField(max_length=32, default="deepseek")
    ai_model = fields.CharField(max_length=128, default="deepseek-v4-pro")
    ai_base_url = fields.CharField(max_length=512, default="https://api.deepseek.com")
    ai_api_key = fields.TextField(default="")
    ai_system_prompt = fields.TextField(default="")
    ai_thinking = fields.BooleanField(default=True)
    avatar_transparent = fields.BooleanField(default=False)
    active_persona_id = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "user_settings"


class User(models.Model):
    id = fields.CharField(pk=True, max_length=64)
    username = fields.CharField(max_length=64, unique=True)
    password_hash = fields.CharField(max_length=255)
    refresh_token_version = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"


class Persona(models.Model):
    id = fields.CharField(pk=True, max_length=64)
    name = fields.CharField(max_length=64)
    icon = fields.CharField(max_length=16, null=True)
    system_prompt = fields.TextField(default="")
    is_builtin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "personas"
        ordering = ["created_at"]


class Favorite(models.Model):
    id = fields.CharField(pk=True, max_length=64)
    message_id = fields.CharField(max_length=64, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "favorites"
        ordering = ["-created_at"]
