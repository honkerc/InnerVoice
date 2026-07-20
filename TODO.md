# 与神对话 · 优化 TODO

> 产品的一句话定位：**用聊天的方式记录自己，并让另一个声音（自己 / AI）回应你。**
> 本清单于 2026-07-19 基于对 backend / frontend 全量代码的实际审查重写，聚焦**已实现但不够稳 / 可优化的地方**，而非新功能。
> 每条尽量给出 `文件:行号`、严重程度与修复方向。功能路线图（语音、心情、PWA 等）见文末「产品路线图」。

---

## 🔴 P0 · 安全（部署前必须处理）

- [ ] **JWT 密钥 / 默认密码硬编码兜底** —— `auth.py:13`、`auth.py:116`
  `JWT_SECRET` 默认 `"yushenduihua-dev-secret-change-me"`，`APP_DEFAULT_PASSWORD` 默认 `"123456"`。一旦部署时没设环境变量，任何人可用已知密钥伪造任意 token，弱口令可直接登录。
  → 启动时若未显式设置 `JWT_SECRET` 则**拒绝启动**（或随机生成并持久化）；首登强制改密。

- [ ] **上传文件同源静态托管 → 存储型 XSS** —— `main.py:447`、`storage.py:56-80`
  `/uploads` 与前端同源经 `StaticFiles` 提供，`detect_kind` 只拦可执行后缀，`.html` / `.svg` 会以 `text/html` / `image/svg+xml` 落盘并被浏览器直接执行，可窃取 localStorage 里的 token。`is_image_file` 仅凭 content-type/后缀，易绕过。
  → 上传目录用独立域名或强制 `Content-Disposition: attachment`；svg/html 拉黑名单；图片做真实内容嗅探。

- [ ] **头像上传无大小限制、后缀未净化** —— `main.py:1087-1093`
  `while chunk := await file.read(...)` 无字节上限，可被超大文件撑爆磁盘；`ext = Path(file.filename).suffix` 沿用原始后缀（可为 `.svg`），叠加上一条成为 XSS 载体。
  → 复用 `save_media_file` 的 `max_bytes` 逻辑 + 后缀白名单。

- [ ] **登录接口无限流 / 无锁定** —— `main.py:450`
  失败无节流，配合弱默认口令可被暴力破解。 → 加失败计数限流 / 递增延迟。

---

## 🟠 P1 · 会导致数据错乱 / 泄漏的 Bug（优先修）

- [ ] **待发送媒体 ObjectURL 内存泄漏** —— `ChatEditor.vue:300-304`
  `onUnmounted` 只清了 observer / 两个 timer，**没 revoke `pendingMedia` 里的 `previewUrl`**。添加图片/视频后点「设置」会卸载整个 ChatView（懒加载路由、无 keep-alive），这些 blob URL 全泄漏。
  → `onUnmounted` 里调用 `revokeAllPendingMedia(pendingMedia.value)`。

- [ ] **分页与整页替换之间的竞态** —— `ChatView.vue:149/171` vs `183/223/345/386`
  `loadOlder`/`loadNewer` 异步返回后 `[...res.items, ...messages.value]`；而 `reloadLatest`/`jumpToMessage`/`handleJumpDate` 会整体替换 `messages.value`。两者交错时旧页数据会拼到新列表上 → 重复/错序消息。目前无任何代际守卫。
  → 引入自增 `loadSeq`，请求回来先比对是否仍是最新一代再写入。

- [ ] **AI 回复竞态：同一触发消息可生成多条回复** —— `main.py:684-689/741-744`、`models.py:14`
  `reply_to_id` **无唯一约束**（对比 `quote_id` 有 `unique=True`），两个并发请求都能通过 `existing` 检查后各自 `create`；后续 `.first()` 无排序，读到哪条不定。
  → 给 `reply_to_id` 加唯一索引，或改 `get_or_create`。

- [ ] **AI 流式响应不可中断** —— `ChatEditor.vue:397-421`、`ai-stream.ts:55`
  `streamAiReply` 支持 `signal` 但调用处从不传。用户在 AI 输出中途离开，reader 仍消费网络流、`aiThinking` 悬挂、emit 打到已卸载组件。
  → 持有 `AbortController`，`onUnmounted` 时 abort。

- [ ] **DeepSeek 导入 replace 模式无事务** —— `main.py:1186-1203`
  先删媒体 + 删全表 + 删收藏，再逐条 create；任一步失败则旧数据已丢、新数据不全，无回滚。
  → 用 `in_transaction()` 包裹删除与重建。

- [ ] **引用校验 TOCTOU → 返回 500 而非 409** —— `main.py:331-341`
  `validate_quote` 先查 `already_used` 再创建，并发下靠 `quote_id unique` 兜底但会抛 `IntegrityError` → 500。 → 捕获 `IntegrityError` 转 409。

- [ ] **时区存储不一致** —— `models.py`（未开 `use_tz`）、`main.py:406/825/1145`、`deepseek_share.py:71`
  `datetime.now()`（本地 naive）与 DeepSeek 导入的 UTC-转-naive 混存，`created_at__lt`、按日期定位、游标翻页会错乱。
  → 统一为全 UTC（或统一开 `use_tz`）。

---

## 🟡 P2 · 性能（数据量变大后明显）

- [ ] **消息列表整页渲染 + 数组无限增长** —— `ChatView.vue:16/149/171`
  `MessageRow v-for` 渲染全量 `messages.value`，无虚拟滚动；滚动加载只 concat、**从不裁剪另一端**，长时间上下滑动 DOM 与内存无上限增长。
  → 加载时裁剪反方向超窗条目，或引入虚拟列表。

- [ ] **滚动监听未节流，每次滚动强制回流** —— `ChatView.vue:127-137`
  每次 scroll 同步读 `scrollHeight/scrollTop/clientHeight`（触发 layout）+ `maybeLoadMore`，高频滚动 layout thrashing。 → 用 `requestAnimationFrame` 合并 / 节流。

- [ ] **`to_out` 的 N+1 查询** —— `main.py:170-187`
  每条带 `quote_id` 的消息单独查引用；不传 `favorited_ids` 时每条再 `Favorite.exists()`。`get_message`、`export(json)` 都走此路径。 → 批量预取引用消息与收藏集合。

- [ ] **导出 / AI 回顾全表载入内存** —— `main.py:826/1144`
  `Message.all()` 一次性进内存并逐条 `to_out`（叠加 N+1）；回顾还把整段拼进 prompt，无 token 上限。 → 分批流式处理，回顾内容截断。

- [ ] **检索为多次全表 LIKE 扫描** —— `main.py:126-149/573/581`
  `content__icontains`（`LIKE %kw%`）无法走索引；`find_relevant_history` 对最多 5 个关键词各扫一次全表。 → 升级 SQLite **FTS5** 全文索引（同时获得相关性排序）。

---

## 🟢 P3 · 整洁度 / 死代码 / 可访问性（可批量清理）

- [ ] **删除三个空脚手架目录** —— `src/api/`、`src/composables/`、`src/utils/`（`composables/` 可留作下面抽 hook 用）。
- [ ] **删死代码**：`lib/stream-scheduler.ts`（`createStreamScheduler` 零引用）、`lib/api.ts:182` `requestAiReply`（已被 `streamAiReply` 取代，零引用）。
- [ ] **清理未使用图标** —— `components/icons.ts`：`IconChart` / `IconSearch` / `IconVideo` 零引用（`IconChart` 若要用在 P4 情绪趋势方向可保留）。
- [ ] **抽 `useHoverDropdown` composable** —— `EmojiPicker` / `TemplatePicker` / `AiReviewPicker` 三个 picker 各复制了约 40 行 `open/closeTimer/openPanel/scheduleClose/onPointerDown` 逻辑；`AiReviewPicker` 还沿用了 `template-picker` 的 CSS 类名（复制痕迹）。
- [ ] **修 picker 的 `computed(() => readXxx())` 反应式陷阱** —— `EmojiPicker.vue:23`、`TemplatePicker.vue:26`：computed 包裹纯 localStorage 读取，无依赖 → 只求值一次，改列表后不更新。改普通函数或显式 ref。
- [ ] **拆分 `SettingsView.vue`（826 行）** —— 单文件承担 7 个 tab、有两个独立 `onMounted`（`:560`、`:638`）。按 tab 拆子组件、合并生命周期。
- [ ] **`FavoritesBar.vue` 命名残留** —— 模板混用 `pinned-notice__*` 与 `favorites-bar__*` 两套 BEM（PinnedNotice 改名遗留），依赖旧 CSS 类才显示正常，统一命名。
- [ ] **草稿卸载丢失最后几笔** —— `ChatEditor.vue:300`：`onUnmounted` 只 `clearTimeout(draftTimer)` 不 flush，快速输入后立即切页会丢 <300ms 的输入。卸载前若 timer 存在则同步 `writeDraft`。
- [ ] **图片灯箱无障碍** —— `ChatView.vue:39-42`：裸 `div` 无 `role="dialog"`/`aria-modal`、无 Esc 关闭、无焦点陷阱，`×` 无 `aria-label`。
- [ ] **错误 Toast 不播报** —— `ChatView.vue:37`：无 `role="alert"`/`aria-live`，读屏用户收不到错误。
- [ ] **下拉面板主交互依赖 hover** —— 三个 picker 以 `mouseenter/leave` 为主路径，触屏退化（虽有 click 兜底）。

---

## 🔵 P4 · 架构 / 长期技术债

- [ ] **用户资产分裂在 localStorage 与后端两处** —— 模板 / 表情 / 草稿 / 主题 / AI 开关全在 localStorage，换设备即丢；模板、表情属明显的用户资产，建议迁到后端 settings 同步。
- [ ] **localStorage key 命名不统一** —— 部分用 `yushenduihua-` 前缀，`custom_templates` / `custom_emoji_list` 却无前缀，易冲突难清理。统一前缀。
- [ ] **启动期手工 PRAGMA 迁移无并发保护** —— `main.py:235-328/418-432`：`ensure_*_columns` / `migrate_legacy_*` 每次启动跑，多 worker 并发 `ALTER TABLE`/建索引会冲突；`migrate_legacy_god_role` 每次无条件全表 UPDATE。→ 迁移加锁或改用 aerich。
- [ ] **鉴权逻辑双份实现** —— `auth.py:57-78` 与 `131-163`：`get_current_user` 与 `auth_middleware` 重复解析校验 token，中间件已把 user 放 `request.state.user` 却仍每端点再查一次库。去重复用。
- [ ] **API Key 明文存库** —— `models.py:31`：`ai_api_key` 明文存 SQLite。本地单机风险有限，仍建议加密或仅走环境变量。
- [ ] **`update_settings` 无法清空字段** —— `settings_store.py:48-53`：`if value is not None` 使显式置 null（如移除 `avatarUrl`）被忽略。
- [ ] **撤销删除 / 回收站** —— `DELETE /api/messages/{id}` 为硬删除并立即清理媒体，无撤销窗口。改软删除 + 回收站。
- [ ] **多用户数据未隔离**（当前为单用户设计，标注技术债）—— `UserSettings` 固定 `id="default"`，消息/收藏/设置全局，未来若多用户会串号。

---

## 产品路线图（新功能，非本轮优化重点）

> 以下为尚未实现的功能项，保留自上版路线图。是否要做仍以「是否服务主线」判断。

- **输入体验**：语音输入 / 语音消息（前端无 `MediaRecorder`）、全局快捷键（`↑` 编辑上一条、快速聚焦输入框）。
- **情绪与洞察**：心情标记 + 趋势图、活跃度热力图 / 关键词云。
- **长期体验**：PWA / 离线（无 manifest、无 service worker）、隐私锁（内容加密 / 二次验证）、每日记录提醒。

---

## 备注：技术债速记

- 全文搜索是 SQLite `LIKE` 非 FTS5，量大后需升级（见 P2）。
- 导入 DeepSeek 分享是直接爬 `chat.deepseek.com` 内部接口，无鉴权/限流，上游变动即失效。
- `backend/scripts/export_deepseek_share.py` 是独立脚本，不读本应用消息库，与「导出」需求无关。
- `frontend-next/` 为归档旧版前端，不再维护。
