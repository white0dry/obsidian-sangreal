<h1 align="center">Sangreal · 圣杯</h1>

<p align="center"><em>一款红、白、金配色的文艺复兴风格 Obsidian 主题，灵感来自《战锤 40K》的圣血天使。</em></p>

<p align="center"><a href="README.md">English</a> · 简体中文</p>

![Sangreal 在 Obsidian 里的预览：左日间、右夜间](docs/images/cover-zh.webp)

## 特点

- 日夜两套配色。
- 兼顾中英文排版，中西文之间自动加间距。
- 西文字体内嵌，离线可用，不发出任何网络请求；中文字体用本机安装的寒蝉活宋体和思源宋体，见[推荐字体](#推荐字体)。
- 35 项 Style Settings 选项，设置页可显示中文或英文，大部分装饰都可以关掉。
- 为桌面端设计，在 Obsidian 1.14.5（Windows）上测试。

## 截图

### 整窗

默认的书签卡片式侧栏：

![日间整窗](docs/images/full-day-zh.webp)

![夜间整窗](docs/images/full-night-zh.webp)

Style Settings「界面 → 侧栏布局」换成简洁：

![简洁侧栏布局，日间整窗](docs/images/full-plain-day-zh.webp)

![简洁侧栏布局，夜间整窗](docs/images/full-plain-night-zh.webp)

### 局部

以下每组左边日间、右边夜间。

![标题、属性框与行内样式](docs/images/note-title-zh.webp)

![标题、引用与列表](docs/images/note-lists-zh.webp)

![包含全部状态的任务清单](docs/images/note-tasks-zh.webp)

![表格与四到六级标题](docs/images/note-table-zh.webp)

![分隔线、代码块、公式与 Mermaid 图](docs/images/note-code-zh.webp)

![图片、嵌入笔记与脚注](docs/images/note-media-zh.webp)

单张图片后面写 `|noframe` 就不加框。

![全部 Callout 类型](docs/images/callouts-zh.webp)

<p align="center"><img src="docs/images/sidebar-zh.webp" width="560" alt="书签卡片式侧栏"></p>

文件列表的动态装饰：日间飘落羽毛，夜间灰烬与火星。

<p align="center"><img src="docs/images/anim-fall-zh.webp" width="560" alt="文件列表的飘落羽毛与灰烬火星"></p>

展开文件夹时空心血滴灌满；悬停当前文件，行尾盖上红蜡封。

<p align="center"><img src="docs/images/anim-folder-zh.webp" width="560" alt="展开文件夹与悬停当前文件"></p>

侧栏按钮行平时收成一对卷翼，悬停时展开。

<p align="center"><img src="docs/images/anim-wings-zh.webp" width="560" alt="侧栏按钮行悬停展开"></p>

<p align="center">
  <img src="docs/images/ribbon-zh.webp" width="300" align="top" alt="功能栏的纯洁印记与提示框">
  &nbsp;&nbsp;
  <img src="docs/images/outline-zh.webp" width="520" align="top" alt="大纲血线">
</p>

大纲跟随鼠标：血线从上级标题流向悬停的标题。

<p align="center"><img src="docs/images/anim-thread-zh.webp" width="600" alt="大纲血线跟随鼠标"></p>

![新标签页](docs/images/empty-zh.webp)

## 安装

**在 Obsidian 里安装**：打开「设置 → 外观 → 主题 → 管理」，搜索 **Sangreal**，点「下载并使用」。

**手动安装**：把 `theme.css` 和 `manifest.json` 复制到 `<你的库>/.obsidian/themes/Sangreal/`，再到「设置 → 外观」里选择本主题。

**建议**：安装 [Style Settings](https://github.com/mgmeyers/obsidian-style-settings) 插件，所有选项都在里面；不装时按默认值显示。

日间或夜间跟随「设置 → 外观 → 基础颜色」。

## 推荐字体

- **中文标题**：[寒蝉活宋体](https://github.com/Warren2060/ChillMovableType/releases/tag/HuoSongv1.000)（寒蝉活字系列）。没有时标题用正文字体。
- **中文正文**：[思源宋体](https://github.com/adobe-fonts/source-han-serif/releases)。没有时用系统宋体。

**不想下载字体**：用仓库里附带的可选片段，各含一套 6763 个常用字的子集：

- 标题：[`snippets/sangreal-chinese-heading-font.css`](snippets/sangreal-chinese-heading-font.css)（寒蝉活宋体，约 10 MB）
- 正文：[`snippets/sangreal-chinese-body-font.css`](snippets/sangreal-chinese-body-font.css)（思源宋体，约 3.4 MB）

下载后放进 `<你的库>/.obsidian/snippets/`，再到「设置 → 外观 → CSS 样式代码片段」刷新列表并打开。

标题字体也可以在 Style Settings「排版 → 标题中文字体」里换成思源宋体或华文宋体。

## Style Settings 选项

设置页最上面的「设置语言」可以切换中文或英文。括号里是默认值。

![Style Settings 设置页](docs/images/settings-zh.webp)

| 分组 | 选项 |
|---|---|
| 氛围 | 羊皮纸纹理浓度（100%）· 四周暗角浓度（100%）· 关闭文件列表动态装饰 · 夜间文件列表动态装饰（灰烬与火星 / 暗色羽毛） |
| 装饰 | 隐藏标题下的战团徽 · 隐藏标题两侧的花边 · 隐藏标题装饰 · 分隔线朴素样式 · 关闭表格隔行底色 · 隐藏 Callout 拉丁铭牌 · Callout 原版图标 · 任务复选框（巴尔宝石 / 蜡封 / 原版）· 图片边框（卡片花边 / 印痕毛边 / 原版）· 属性栏朴素样式 · 粗体用墨色 |
| 代码块 | 代码块样式（红头铭板 / 沉思者）· 显示行号 |
| 排版 | 标题中文字体（寒蝉活宋体 / 思源宋体 / 华文宋体）· 正文行距（1.85）· 正文宽度（46rem，需打开「限制行宽」）· 正文两端对齐 · 关闭中西文自动间距 · 弯引号用西文字形 |
| 界面 | 侧栏布局（书签卡片 / 简洁）· 卡片花边（开）· 卡片间距（8 px）· 滚动条宽度（6 px）· 标题栏 · 仓库栏 · 状态栏 · 自动收起侧栏面板按钮行（开）· 大纲样式（血线 / 金线导轨 / 原版）· 弹窗花边（开）· 功能栏显示方式 · 功能栏样式（纯洁印记 / 普通） |

### 可切换的样式

以下几组样式可以在 Style Settings 里切换，每张上行日间、下行夜间。

**代码块样式**

![代码块样式：红头铭板、沉思者](docs/images/var-code-zh.webp)

**图片边框**

![图片边框：卡片花边、印痕毛边、原版](docs/images/var-image-zh.webp)

**任务复选框**

![任务复选框：巴尔宝石、蜡封、原版](docs/images/var-task-zh.webp)

**大纲样式**

<p align="center"><img src="docs/images/var-outline-zh.webp" width="720" alt="大纲样式：血线、金线导轨、原版"></p>

## 兼容性

- 只支持桌面端，移动端未测试。
- 中文正文用本机安装的思源宋体（Noto Serif SC / Source Han Serif）或正文片段，都没有时用系统宋体。
- 常用的 Mermaid 图会改成主题配色，图里用 `classDef` 或 `style` 自定义的颜色依然优先。
- `theme.css` 约 7 MB，因为西文字体和装饰图全部内嵌。

## 致谢

- **图标**：[game-icons.net](https://game-icons.net)，[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) 授权，有修改。Lorc：bleeding-heart、book-aura、broken-skull、candle-light、chalice-drops、curly-wing、feather、holy-grail、hourglass、laurels、quill、ringing-bell、scroll-unfurled、sundial、two-feathers、winged-sword；Delapouite：notebook、tower-flag。
- **图形素材**：属性框的翅膀描自 Heritage Library（HTC Heritage Type）的公有领域版画；花边与绶带改自 frame-illust.com；Callout 失败图标改自 ICOOON MONO；机械教徽与帝国双头鹰取自社区图标集「wh_icons」。
- **字体**（SIL Open Font License 1.1）：EB Garamond、Cormorant Garamond、IM Fell English SC、Manufacturing Consent、思源宋体 Noto Serif SC（中文标点）；Callout 疑问图标的问号取自 Playfair Display；可选片段里是寒蝉活宋体和思源宋体子集。

## 声明

本主题为非官方同人作品。《战锤 40K》、圣血天使、机械教及其徽记是 Games Workshop Ltd. 的商标。本主题与 Games Workshop 无关，也未经其认可。

## 许可

主题代码以 [MIT 许可证](LICENSE) 发布。第三方素材沿用各自的许可，见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
