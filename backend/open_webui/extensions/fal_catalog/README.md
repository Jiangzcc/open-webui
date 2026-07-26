# fal.ai 模型目录

这里是本项目二开使用的 fal.ai 声明式模型目录。新增同协议模型时，应修改配置文件，而不是继续向
`backend/open_webui/utils/images/fal_models.py` 添加 Python 分支。

## 目录结构

```text
catalog/
└── image/
    ├── manifest.json
    ├── alibaba.json
    ├── google.json
    ├── openai.json
    └── xai.json
```

`manifest.json` 决定默认模型和厂商文件的加载顺序。厂商文件中的顺序就是 API 返回和前端展示的基础顺序。
未来的视频和音频模型应分别放入 `catalog/video/`、`catalog/audio/`，不要混入图片目录。

厂商文件内按以下规则排序：默认或推荐模型优先；同一模型家族放在一起；家族内优先放新版本或高规格版本；
文生图条目后紧跟它的图生图条目。新增模型时应插入所属家族的合理位置，不要简单追加到文件末尾。

## 新增图片模型

1. 在对应厂商 JSON 数组中添加一个模型对象；新厂商还要把文件加入 `manifest.json`。
2. 为模型声明唯一、稳定的 `id`（fal endpoint）和 `public_id`（普通用户可见 ID）。
3. `task` 使用 `text-to-image` 或 `image-to-image`；如有配套模型，用内部 `id` 填写
   `edit_model` 或 `generation_model`。
4. 只声明该模型真实支持的入参，例如 `option_fields`、`boolean_fields`、`integer_fields`、
   `text_fields`、尺寸、比例、数量和参考图上限。
5. 在 credits 定价中继续使用内部 fal endpoint 作为 `resource_id`；价格不复制进模型目录。
6. 运行下方测试。loader 会拒绝未知字段、重复 ID、缺失关系、错误默认模型和非法 endpoint。

最小示例：

```json
{
  "id": "fal-ai/example/text-to-image",
  "public_id": "example",
  "name": "Example / Image Model",
  "provider": "example",
  "task": "text-to-image",
  "edit_model": "fal-ai/example/image-to-image",
  "image_counts": [1, 2, 3, 4],
  "count_field": "num_images",
  "output_formats": ["jpeg", "png", "webp"],
  "default_output_format": "png"
}
```

## 验证

```powershell
$env:PYTHONPATH='backend'
$env:WEBUI_SECRET_KEY='local-test-only-fal-catalog-secret'
python -m pytest backend/open_webui/extensions/fal_catalog/tests backend/open_webui/utils/images/test_fal_models.py -q
python -m pytest backend/open_webui/utils/images/test_fal.py -q
```

上面的 `WEBUI_SECRET_KEY` 只用于本地测试进程，不要把真实生产密钥写入代码或文档。

模型配置由 `schemas.py` 严格校验。不要在 JSON 中加入模板、表达式、任意代码或完整 URL；fal 模型 `id`
只能是相对于已配置 fal API Base URL 的规范化路由。遇到无法用现有字段表达的新入参结构时，应增加一个受控、
可复用的转换能力并补测试，而不是给单个模型增加硬编码分支。

`legacy_builders.py` 只为现有测试和过渡兼容保留，不是新增模型的入口。
