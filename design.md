# 设计规范文档 (Design Specification)

## 1. 核心设计哲学

本产品定位为**个人高效桌面开发工具箱**，视觉与交互风格追求 **iOS 的极简克制圆角** 与 **Claude 的高质感暖色调人文极客风**。

### 设计原则

| 原则 | 说明 |
|------|------|
| **高呼吸感** | 拒绝拥挤，通过充足的内边距（Padding）和网格间距（Gap）让界面具备呼吸感 |
| **严谨对齐** | 遵循像素级网格对齐，消除任何视觉上的杂乱与像素偏移 |
| **内容聚焦** | 去除不必要的装饰性高饱和度色块，利用字重、明暗对比和微弱投影拉开层级 |

---

## 2. 色彩系统 (Color Palette)

放弃传统的冷白与纯黑，采用更具质感的**暖调纸张色**与**深炭黑**。

| 变量名 | 颜色值 (Hex) | 适用场景 | 风格映射说明 |
|--------|--------------|----------|--------------|
| `--bg-global` | `#FBF9F6` | 全局大背景 | Claude 标志性纸张暖白 |
| `--bg-surface` | `#FFFFFF` | 核心卡片、左侧边栏、弹窗底色 | iOS 纯白悬浮层质感 |
| `--bg-element` | `#F5F2EB` | 图标背景框、未选中态微调色 | 低饱和度浅暖灰 |
| `--text-primary` | `#222220` | 大标题、正文核心加粗文本 | 优雅的深炭黑，非纯黑 |
| `--text-secondary` | `#8C867E` | 副标题、描述文字、微弱提示 | 暖调中灰 |
| `--border-light` | `#EBE7E0` | 卡片边框、极其隐蔽的分割线 | 代替高饱和度彩色线条 |
| `--theme-accent` | `#635BFF` / `#7C4DFF` | 仅用于局部选中态、核心激活按钮 | 克制的极客紫（不宜大面积使用） |

### 色彩使用规范

```css
:root {
  /* 主背景 */
  --bg-global: #FBF9F6;
  
  /* 表面层 */
  --bg-surface: #FFFFFF;
  
  /* 元素层 */
  --bg-element: #F5F2EB;
  
  /* 文字 */
  --text-primary: #222220;
  --text-secondary: #8C867E;
  
  /* 边框 */
  --border-light: #EBE7E0;
  
  /* 强调色 */
  --theme-accent: #635BFF;
}
```

---

## 3. 布局与间距规范 (Layout & Spacing)

### 3.1 空间布局

**消除重叠原则**：
- 任何卡片、按钮内的图标与文字必须**完全分离**
- 严禁出现背景图标与文字重合、图文堆叠导致的语义模糊

**推荐排版**：
- 卡片内部采用 **左图右文** 或 **上图下文**（纵向流，图标居上且留出 `margin-bottom: 12px`）

### 3.2 尺寸与圆角 (Radii & Padding)

| 元素类型 | 圆角值 | Tailwind 等效 |
|----------|--------|---------------|
| 大卡片 | 16px / 20px | `rounded-2xl` |
| 小元素/图标框 | 10px / 12px | `rounded-xl` |
| 按钮 | 8px / 10px | `rounded-xl` |

**间距规范**：

| 属性 | 值 | 说明 |
|------|-----|------|
| 卡片内边距 (Padding) | ≥ 24px | 确保长文本描述有充足的伸展空间 |
| 网格间距 (Gap) | 24px | 卡片组件网格间距统一 |
| 卡片与边框间距 | 20px | 卡片之间保持呼吸感 |
| 导航栏宽度 | 200px | 左侧导航固定宽度 |
| 内容区边距 | 40px | 右侧内容区内边距 |

---

## 4. 交互与微动效 (Interaction & Motion)

### 4.1 悬浮态 (Hover Effect)

**卡片 Hover**：
```css
.card {
  transition: all 0.3s ease-in-out;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(34, 34, 32, 0.05);
  border-color: #D4CFC7;
}
```

**按钮 Hover**：
```css
.button {
  transition: all 0.2s ease-in-out;
}
.button:hover {
  background-color: darken(currentColor, 5%);
}
```

### 4.2 阴影设计 (Shadows)

避免使用软件默认的浓重黑色阴影，统一使用**极淡的扩散纯单色阴影**：

| 状态 | 阴影值 |
|------|--------|
| Base 阴影 | `box-shadow: 0 4px 20px rgba(34, 34, 32, 0.02)` |
| Hover 阴影 | `box-shadow: 0 10px 30px rgba(34, 34, 32, 0.05)` |

### 4.3 过渡时间

| 属性 | 时长 | 缓动函数 |
|------|------|----------|
| 悬浮效果 | 300ms | ease-in-out |
| 点击反馈 | 150ms | ease-out |
| 页面切换 | 250ms | ease-in-out |

---

## 5. 标题栏与系统级规范 (Window Chrome)

### 5.1 无边框架构 (Frameless)

- 隐藏操作系统原生标题栏
- 自定义绘制窗口控制区域

### 5.2 iOS 控制按钮

在**左上角**（或根据习惯右上角）自定义标准的 iOS 软糖三色键：

| 按钮 | 颜色 | 功能 |
|------|------|------|
| 关闭 | `#FF5F56` | 关闭窗口 |
| 最小化 | `#FFBD2E` | 最小化到任务栏 |
| 最大化 | `#27C93F` | 切换最大化/还原 |

```css
.window-control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}
.window-close { background-color: #FF5F56; }
.window-minimize { background-color: #FFBD2E; }
.window-maximize { background-color: #27C93F; }
```

### 5.3 拖拽区

- 顶部预留 **32px** 高度的区域支持软件窗口整体拖拽
- 内部的按钮需排除拖拽属性 (`no-drag`)

```css
.window-header {
  height: 32px;
  -webkit-app-region: drag;
}

.window-header button {
  -webkit-app-region: no-drag;
}
```

---

## 6. 字体规范 (Typography)

### 6.1 字体族

```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### 6.2 字号与字重

| 用途 | 字号 | 字重 | 颜色 |
|------|------|------|------|
| 窗口标题 | 17px | 600 | `--text-primary` |
| 区块标题 | 26px | 600 | `--text-primary` |
| 卡片标题 | 15px | 600 | `--text-primary` |
| 描述文字 | 13-14px | 400 | `--text-secondary` |
| 辅助信息 | 12px | 400 | `--text-secondary` |

---

## 7. 组件规范 (Components)

### 7.1 工具卡片

```
┌─────────────────────────────────────┐
│  ↑                                  │  ← 图标 (32x32)
│                                     │
│  上传 Jar 包                        │  ← 标题 (15px, 600)
│                                     │
│  将本地 Jar 包上传到远程服务器      │  ← 描述 (13px, 400)
│                                     │
└─────────────────────────────────────┘
  ↑ 24px padding
```

**属性**：
- 尺寸：280px × 160px
- 圆角：16px
- 内边距：24px
- 背景：`--bg-surface`
- 边框：1px solid `--border-light`
- 阴影：`0 4px 20px rgba(34, 34, 32, 0.02)`

### 7.2 导航项

```
┌─────────────────────────────┐
│  🚀  部署工具               │  ← 图标 + 文字
└─────────────────────────────┘
```

**属性**：
- 高度：40px
- 圆角：10px
- 内边距：12px 16px
- 选中态背景：`#F5F3F0`
- 选中态文字：`--text-primary`, 600
- 未选中态文字：`--text-secondary`, 500

---

## 8. 实现参考

### PySide6 实现示例

```python
# 配色常量
COLORS = {
    "bg": "#FBF9F6",
    "card": "#FFFFFF",
    "card_border": "#EBE7E0",
    "title": "#222220",
    "desc": "#8C867E",
    "nav_active": "#222220",
    "nav_inactive": "#8C867E",
    "nav_hover": "#F5F3F0",
}

# 卡片样式
card_style = f"""
    ToolCard {{
        background-color: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 16px;
    }}
    ToolCard:hover {{
        border-color: #D4CFC7;
    }}
"""

# 阴影效果
shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(24)
shadow.setXOffset(0)
shadow.setYOffset(4)
shadow.setColor(QColor(0, 0, 0, 12))
```

---

## 9. 更新日志

### v1.0.0 (2026-06-28)

- ✅ 完成色彩系统定义
- ✅ 完成布局间距规范
- ✅ 完成交互动效规范
- ✅ 完成标题栏规范
- ✅ 工具箱界面重构完成

---

*文档版本: 1.0.0 | 最后更新: 2026-06-28*
