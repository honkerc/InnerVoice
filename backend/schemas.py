from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


MessageRole = Literal["me", "ai"]
MessageType = Literal["text", "image", "video", "file", "media_group"]
AttachmentType = Literal["image", "video", "file"]


class QuotePreview(BaseModel):
    id: str
    role: MessageRole
    type: MessageType
    content: str
    mediaUrl: str | None = None
    mediaName: str | None = None


class MessageAttachmentOut(BaseModel):
    type: AttachmentType
    url: str
    name: str


class UploadOut(BaseModel):
    url: str
    name: str
    kind: AttachmentType


class MessageCreate(BaseModel):
    role: MessageRole = "me"
    type: MessageType = "text"
    content: str = ""
    quoteId: str | None = None


class MessageUpdate(BaseModel):
    content: str


class AiReplyRequest(BaseModel):
    triggerMessageId: str
    force: bool = False


class MessageOut(BaseModel):
    id: str
    role: MessageRole
    type: MessageType
    content: str
    mediaUrl: str | None = None
    mediaName: str | None = None
    attachments: list[MessageAttachmentOut] | None = None
    tags: list[str] | None = None
    isFavorited: bool = False
    quoteId: str | None = None
    quote: QuotePreview | None = None
    authorAvatarUrl: str | None = None
    authorDisplayName: str | None = None
    createdAt: datetime

    model_config = {"from_attributes": True}


class MessageListOut(BaseModel):
    """分页 / 搜索结果的统一信封。items 始终按 createdAt 升序排列。"""

    items: list[MessageOut]
    hasMoreBefore: bool = False
    hasMoreAfter: bool = False
    total: int | None = None
    anchorId: str | None = None


AiProvider = Literal["deepseek", "openai", "ollama", "custom"]


class SettingsOut(BaseModel):
    displayName: str
    avatarUrl: str | None = None
    aiProvider: AiProvider
    aiModel: str
    aiBaseUrl: str
    hasApiKey: bool
    aiSystemPrompt: str
    aiThinking: bool = True
    avatarTransparent: bool = False
    activePersonaId: str | None = None


class SetActivePersonaRequest(BaseModel):
    personaId: str | None = None


class PersonaOut(BaseModel):
    id: str
    name: str
    icon: str | None = None
    systemPrompt: str
    isBuiltin: bool = False

    model_config = {"from_attributes": True}


class PersonaCreate(BaseModel):
    name: str
    icon: str | None = None
    systemPrompt: str = ""


class PersonaUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    systemPrompt: str | None = None


class AiReviewRequest(BaseModel):
    period: Literal["week", "month"]


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    displayName: str | None = None
    avatarUrl: str | None = None
    aiProvider: AiProvider | None = None
    aiModel: str | None = None
    aiBaseUrl: str | None = None
    aiApiKey: str | None = None
    aiSystemPrompt: str | None = None
    aiThinking: bool | None = None
    avatarTransparent: bool | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refreshToken: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class ChangeUsernameRequest(BaseModel):
    newUsername: str


class DeepSeekShareImportRequest(BaseModel):
    url: str
    mode: Literal["append", "replace"] = "append"


class DeepSeekSharePreviewItem(BaseModel):
    role: MessageRole
    createdAt: str
    content: str


class DeepSeekSharePreviewOut(BaseModel):
    shareId: str
    title: str
    total: int
    meCount: int
    aiCount: int
    rangeFrom: str
    rangeTo: str
    preview: list[DeepSeekSharePreviewItem]


class DeepSeekShareImportOut(BaseModel):
    imported: int
    meCount: int
    aiCount: int
    mode: Literal["append", "replace"]
    shareId: str
    title: str


class AuthTokensOut(BaseModel):
    accessToken: str
    refreshToken: str
    username: str


class AuthUserOut(BaseModel):
    username: str
