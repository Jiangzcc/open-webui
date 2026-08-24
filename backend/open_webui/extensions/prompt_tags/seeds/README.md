# vipmax 标签库种子

`vipmax_tag_library.json` 是可直接导入的标签库文件（7 个分类、200 个标签）。

- **来源**：移植自 https://vip.vipmax.ai/image 的标签选择面板（2026-08-24 提取）。
- **insert_text 与 label_zh 一致**：源站选中标签后插入的文本即标签中文名。
- **去重**：源站在「艺术家」「元素魔法」分类中重复出现的「蒸汽朋克」只保留「风格修饰」中的一条。
- **英文 label** 为本项目补译，源站没有提供。
- **导入方式**：管理后台「运营中心 → 标签库 → 导入」上传该文件，或
  `POST /api/v1/prompt-tags/admin/import`（body 为文件内容 + `"upsert": true`）。
