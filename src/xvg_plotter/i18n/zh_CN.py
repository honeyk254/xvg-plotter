# The zh-CN translation of every user-facing string (C35).
#
# Keys are the English source strings exactly as passed to tr(); values are
# the Chinese UI texts. Untranslated keys simply fall back to English, so a
# missing entry is never a bug — regenerate the key inventory with
# `python tools/i18n_check.py` after adding new strings.
STRINGS: dict[str, str] = {
    # -- menus ----------------------------------------------------------------
    "&File": "文件(&F)",
    "&View": "视图(&V)",
    "&Help": "帮助(&H)",
    "&Theme": "主题(&T)",
    "&Language": "语言(&L)",
    "&Auto (system)": "自动（跟随系统）(&A)",
    "&Light": "浅色(&L)",
    "&Dark": "深色(&D)",
    "System default": "跟随系统",
    "English": "English",
    "中文（简体）": "中文（简体）",
    "Open Folder…": "打开文件夹…",
    "Open Folder in New Window…": "在新窗口中打开文件夹…",
    "Refresh": "刷新",
    "Export…": "导出…",
    "Export all checked files…": "导出全部勾选文件…",
    "Export data (CSV)…": "导出数据（CSV）…",
    "Print…": "打印…",
    "Copy Image": "复制图像",
    "Export Settings…": "导出设置…",
    "Import Settings…": "导入设置…",
    "Quit": "退出",
    "Clear all pins": "清除所有固定曲线",
    "Grid view of checked files": "勾选文件的网格视图",
    "Clear annotations": "清除标注",
    "Focus mode": "专注模式",
    "Keyboard shortcuts…": "键盘快捷键…",
    "Reading the analyses…": "读懂分析结果…",
    "Check for updates…": "检查更新…",
    "Set as default .xvg viewer": "设为默认 .xvg 查看器",
    "About": "关于",
    # -- window / docks ---------------------------------------------------------
    "Files": "文件",
    "Series && analysis": "曲线与分析",
    "Style": "样式",
    "no folder loaded": "未加载文件夹",
    "open a second folder to compare…": "打开第二个文件夹进行对比…",
    "restoring session…": "正在恢复会话…",
    # -- folder bar ---------------------------------------------------------------
    "subfolders": "包含子文件夹",
    "filter…": "筛选…",
    "Current folder; the list holds pinned and recent folders":
        "当前文件夹；列表包含置顶与最近使用的文件夹",
    "Rescan folder (F5)": "重新扫描文件夹（F5）",
    "Pin this folder to the top of the list": "把该文件夹置顶",
    "Unpin this folder": "取消置顶",
    "Include .xvg files in subfolders when scanning":
        "扫描时包含子文件夹中的 .xvg 文件",
    "Filter the list by file name or title (Ctrl+F; Esc clears)":
        "按文件名或标题筛选列表（Ctrl+F；Esc 清除）",
    "Open analysis folder": "打开分析文件夹",
    # -- file table ------------------------------------------------------------------
    "Name": "名称",
    "Title": "标题",
    "Series": "曲线数",
    "Points": "数据点",
    "Size": "大小",
    "Modified": "修改时间",
    "Show in folder": "在文件夹中显示",
    "Copy path": "复制路径",
    "{n} grace directive(s) ignored — in-file styling not applied":
        "已忽略 {n} 条 grace 指令 —— 文件内置样式未应用",
    "cloud-only placeholder — selecting it downloads the file (OneDrive/Dropbox)":
        "仅存于云端 —— 选中后会下载该文件（OneDrive/Dropbox）",
    "no data rows": "没有数据行",
    # -- series dock ---------------------------------------------------------------------
    "Average replicas (mean ± SD)": "副本平均（均值 ± 标准差）",
    "Overlay the mean of matching replicas with a shaded ± SD band":
        "叠加匹配副本的均值，并给出带阴影的 ± 标准差带",
    "select ≥ 2 files with matching column structure":
        "请选择至少 2 个列结构一致的文件",
    "Show member curves": "显示各条副本曲线",
    "Draw each replica faintly under the mean": "在均值下方淡淡地画出每条副本",
    "Common time range": "公共时间范围",
    ("Average only the time span every replica shares — shorter runs no "
     "longer truncate longer ones"):
        "只对每条副本共有的时间段求平均 —— 短的模拟不再截断长的",
    "Smooth overlay": "平滑叠加线",
    "Dashed moving-average overlay on every plotted series":
        "在每个绘制序列上叠加虚线滑动平均",
    "Moving-average window (points)": "滑动平均窗口（点数）",
    "Analysis": "分析",
    "window": "窗口",
    "Normalize": "归一化",
    "off": "关闭",
    "first value": "按首值",
    "max": "按最大值",
    "Normalize every plotted series: divide by its first value or by its maximum":
        "归一化每条曲线：除以它的首个值或最大值",
    "Subtract baseline (first point)": "扣除基线（首点）",
    "Shift each series down by its first value so curves start at zero":
        "把每条曲线减去它的首值，使曲线从零开始",
    "Fit line (least squares)": "拟合直线（最小二乘）",
    ("Dashed y = a·x + b least-squares line over the visible X range, with "
     "the equation in the legend"):
        "在可见 X 范围内画出虚线最小二乘拟合 y = a·x + b，图例中给出方程",
    "dataset {n} ({pts} pts)": "数据集 {n}（{pts} 点）",
    "dataset {n} · {pts} pts": "数据集 {n} · {pts} 点",
    ("Focus dataset for replica averaging; every dataset's series below can "
     "be plotted individually"):
        "副本平均所针对的数据集；下方每个数据集的曲线都可单独勾选绘制",
    ("Click to set this curve's color; right-click to reset to the palette "
     "cycle"):
        "点击设置该曲线的颜色；右键恢复为调色板顺序配色",
    "Reset to palette cycle": "恢复调色板配色",
    "Curve color — {name}": "曲线颜色 —— {name}",
    # -- style dock ---------------------------------------------------------------------------
    "Grid": "网格",
    "Log X": "X 对数",
    "Log Y": "Y 对数",
    "Legend": "图例",
    "Colors": "配色",
    "Line": "线型",
    "Width": "线宽",
    "Fig size (in)": "图尺寸（英寸）",
    "Font": "字体",
    "Title": "标题",
    "X label": "X 轴标签",
    "Y label": "Y 轴标签",
    "X unit": "X 单位",
    "Draw a light grid on the plot": "在图上绘制浅色网格",
    "Logarithmic X axis": "X 轴对数刻度",
    "Logarithmic Y axis": "Y 轴对数刻度",
    "Legend position — 'outside right' keeps it off the data":
        "图例位置 —— “右侧外部”让图例不遮挡数据",
    "Color cycle for overlaid series; Okabe–Ito is colorblind-safe":
        "叠加曲线的取色顺序；Okabe–Ito 对色盲读者友好",
    "Line / marker style for every plotted series": "所有曲线的线型/标记样式",
    "Line width": "线宽",
    "Figure width in inches (auto = fill the window)":
        "图的宽度（英寸）（自动 = 随窗口）",
    "Figure height in inches (auto = fill the window)":
        "图的高度（英寸）（自动 = 随窗口）",
    "Font family for titles, labels and ticks": "标题、轴标签和刻度的字体",
    ("Rescale the time axis (auto picks the largest unit; only applied to "
     "genuine time axes)"):
        "重标定时间轴（自动选择最大单位；仅对真正的时间轴生效）",
    "auto": "自动",
    "Show plot style options": "显示绘图样式选项",
    # -- plot canvas ------------------------------------------------------------------------------
    "✎ Text": "✎ 文字",
    ("Annotate: click the plot to place a text label — drag labels to move "
     "them; included in exports and prints"):
        "标注：在图上点击放置文字标签 —— 拖动标签可移动；导出和打印都会包含",
    ("Open a folder and click a GROMACS .xvg file to plot.\n"
     "Reads .xvg analysis files (RMSD, energy, RDF …).\n"
     "Trajectories (.xtc), maps (.xpm) and .edr files are not supported."):
        "打开文件夹并点击 GROMACS .xvg 文件即可绘图。\n"
        "支持 .xvg 分析文件（RMSD、能量、RDF 等）。\n"
        "不支持轨迹（.xtc）、密度图（.xpm）和 .edr 文件。",
    "plot": "图",
    "grid view": "网格视图",
    "empty plot — no file selected": "空白图 —— 未选择文件",
    # -- main window: plotting status -----------------------------------------------------------------
    "not a folder: {p}": "不是文件夹：{p}",
    "scanning…": "正在扫描…",
    "no file selected": "未选择文件",
    "{n} file(s) plotted": "已绘制 {n} 个文件",
    "grid view: {n} file(s)": "网格视图：{n} 个文件",
    "⚠ {n} more file(s) beyond the {cap}-panel cap — narrow the selection":
        "⚠ 有 {n} 个文件超出 {cap} 格上限 —— 请缩小选择范围",
    "⚠ mixed X axes (time vs other) — check units":
        "⚠ X 轴类型混杂（时间与其他）—— 请检查单位",
    "{n} file(s) · {m} with warnings": "{n} 个文件 · {m} 个有警告",
    "📌 Pin curve": "📌 固定曲线",
    "📌 Unpin curve": "📌 取消固定",
    "New annotation": "新建标注",
    "text at (x = {x}, y = {y}):": "在（x = {x}，y = {y}）处的文字：",
    # -- main window: export / print / copy --------------------------------------------------------------
    "check files to export first": "请先勾选要导出的文件",
    "Export all checked plots to": "导出全部勾选的图到",
    "Exporting {n} plots…": "正在导出 {n} 张图…",
    "Cancel": "取消",
    "Export failed": "导出失败",
    "Could not write {path}:\n{err}": "无法写入 {path}：\n{err}",
    "saved {path}": "已保存 {path}",
    "exported {n} plot(s) to {dir}": "已导出 {n} 张图到 {dir}",
    "nothing plotted to export": "没有可导出的数据",
    "Export data (CSV)": "导出数据（CSV）",
    "CSV (*.csv)": "CSV 文件 (*.csv)",
    "Print": "打印",
    "Could not print:\n{err}": "无法打印：\n{err}",
    "sent to printer": "已发送到打印机",
    "Could not copy the plot: {err}": "无法复制图像：{err}",
    "plot image copied to clipboard": "图像已复制到剪贴板",
    # -- main window: windows / settings / association / updates ---------------------------------------------
    "Open folder in new window": "在新窗口中打开文件夹",
    "Export settings": "导出设置",
    "Import settings": "导入设置",
    "Settings (*.ini)": "设置文件 (*.ini)",
    "exported {n} settings": "已导出 {n} 项设置",
    "Imported {n} settings. Window layout applies after a restart.":
        "已导入 {n} 项设置。窗口布局将在重启后生效。",
    ("This is a development run from source; the file association is "
     "registered by the installed app."):
        "当前是从源码运行的开发版本；文件关联由安装版应用注册。",
    "Register XVG Plotter as an app for .xvg files (current user)?":
        "将 XVG Plotter 注册为 .xvg 文件的应用（当前用户）？",
    "Could not update the registry:\n{err}": "无法更新注册表：\n{err}",
    ("XVG Plotter was registered for .xvg files. If Windows still asks, pick "
     "it in the Open-with dialog or under Settings ▸ Default apps."):
        "XVG Plotter 已注册为 .xvg 文件的处理应用。如果 Windows 仍然询问，"
        "请在“打开方式”或“设置 ▸ 默认应用”中选择它。",
    "checking for updates…": "正在检查更新…",
    "Check for updates": "检查更新",
    "Could not check for updates:\n{err}": "无法检查更新：\n{err}",
    "A new version is available: {latest} (you have {current}).":
        "有新版本可用：{latest}（当前为 {current}）。",
    "Open downloads": "打开下载页",
    "You are up to date (version {current}).": "已是最新版本（{current}）。",
    "Could not check for updates (no connection?).": "无法检查更新（可能没有网络）。",
    # -- main window: language / about --------------------------------------------------------------------------
    "Restart required": "需要重启",
    "The interface language changes after a restart.": "界面语言将在重启后生效。",
    "About XVG Plotter": "关于 XVG Plotter",
    ("<b>XVG Plotter</b> {version}<br><br>Interactive viewer for GROMACS .xvg "
     "analysis files — RMSD, energy, RDF and other .xvg output.<br>Trajectories "
     "(.xtc), maps (.xpm) and .edr files are not supported.<br><br>matplotlib "
     "{mpl} · numpy {np} · PySide6 {pyside}"):
        "<b>XVG Plotter</b> {version}<br><br>交互式 GROMACS .xvg 分析文件查看器"
        " —— 支持 RMSD、能量、RDF 等 .xvg 输出。<br>不支持轨迹（.xtc）、密度图"
        "（.xpm）和 .edr 文件。<br><br>matplotlib {mpl} · numpy {np} · "
        "PySide6 {pyside}",
    # -- export dialog --------------------------------------------------------------------------------------------
    "Export plot": "导出图像",
    "Filename": "文件名",
    "Folder": "文件夹",
    "Format": "格式",
    "DPI (raster: PNG/TIFF)": "DPI（位图：PNG/TIFF）",
    "transparent background": "透明背景",
    "Browse for folder": "浏览文件夹",
    "EPS does not support a transparent background": "EPS 不支持透明背景",
    "Export to folder": "导出到文件夹",
    # -- help dialogs ----------------------------------------------------------------------------------------------
    "Keyboard shortcuts": "键盘快捷键",
    "Shortcut": "快捷键",
    "Action": "作用",
    "Reading the analyses": "读懂分析结果",
    "The jargon, in plain language": "用大白话解释术语",
    # keyboard reference rows (shortcut column stays as-is)
    "Open folder (pane 1)": "打开文件夹（窗格 1）",
    "Open the current folder in a new window": "在新窗口中打开当前文件夹",
    "Refresh scan (Ctrl+R refreshes both panes)": "重新扫描（Ctrl+R 刷新两个窗格）",
    "Jump to the folder filter (Esc clears it)": "跳到筛选框（Esc 清除）",
    "Show or hide the Files / Series panels": "显示/隐藏“文件 / 曲线”面板",
    "Show or hide the Style options": "显示/隐藏样式选项",
    "Focus mode — hide everything except the plot": "专注模式 —— 只显示图",
    "Grid view — one subplot per checked file (small multiples)":
        "网格视图 —— 每个勾选文件一个子图（小倍数图）",
    "Export the current plot…": "导出当前图…",
    "Export every checked file as its own plot…": "把每个勾选文件各导出为一张图…",
    "Export the plotted data as CSV…": "把绘制的数据导出为 CSV…",
    "Print the current plot…": "打印当前图…",
    "Copy the plot image to the clipboard": "把图像复制到剪贴板",
    # glossary: terms
    "RMSD": "RMSD（均方根位移）",
    "Rg (gyrate)": "Rg（回转半径，gmx gyrate）",
    "RDF": "RDF（径向分布函数）",
    "energy.xvg": "energy.xvg（能量文件）",
    "xydy / xydx": "xydy / xydx（误差列）",
    "replica": "副本（replica）",
    "ps / ns": "ps / ns（皮秒 / 纳秒）",
    "moving average": "滑动平均",
    "pin": "固定曲线（pin）",
    "normalize / baseline / fit": "归一化 / 基线 / 拟合",
    "annotation": "标注",
    "grid view": "网格视图",
    "dataset": "数据集",
    # glossary: explanations
    ("Root-mean-square deviation: how far the protein structure has moved "
     "from a reference, in nanometres. A flattening curve means the "
     "simulation is stable."):
        "均方根位移：蛋白结构相对参考结构偏移了多远（单位：纳米）。曲线走平说明"
        "模拟已经稳定。",
    ("Radius of gyration: how compact the molecule is, in nanometres. "
     "Written by gmx gyrate."):
        "回转半径：分子有多紧凑（单位：纳米）。由 gmx gyrate 写出。",
    ("Radial distribution function: how likely two atoms are to be a certain "
     "distance apart. Often has error bars (a ± column)."):
        "径向分布函数：两个原子相隔某一距离的概率。通常带误差棒（± 列）。",
    ("gmx energy output — several series in one file (Potential, Kinetic, "
     "Total, …). Toggle series in the Series panel."):
        "gmx energy 的输出 —— 一个文件里有多个序列（势能、动能、总能量等）。"
        "在“曲线”面板中勾选。",
    ("Grace column types: 'xydy' means the third column is the ± error of Y; "
     "'xydx' the same for X. The app draws error bars automatically."):
        "Grace 列类型：xydy 表示第三列是 Y 的 ± 误差；xydx 是 X 的。"
        "应用会自动画出误差棒。",
    ("An independent repeat of the same simulation. Select ≥ 2 matching files "
     "and tick 'Average replicas' for a mean ± SD band."):
        "同一模拟的独立重复。选择至少 2 个匹配的文件并勾选“副本平均”，"
        "即可得到均值 ± 标准差带。",
    ("Picosecond / nanosecond time units. Use the X unit selector to rescale "
     "the axis (only real time axes are converted)."):
        "皮秒 / 纳秒时间单位。用“X 单位”选择器重标定坐标轴"
        "（仅对真正的时间轴生效）。",
    ("A smoothed overlay that averages a sliding window of points; the label "
     "shows the window in physical time."):
        "对滑动窗口内数据点取平均的平滑叠加线；标签会给出以物理时间表示的窗口宽度。",
    ("Right-click a legend entry to pin a curve — it stays plotted while you "
     "switch files or folders, so you can compare anything with anything."):
        "右键点击图例条目即可固定该曲线 —— 切换文件或文件夹时它仍保留在图上，"
        "任意曲线之间都能对比。",
    ("Analysis-panel helpers. 'Normalize' divides each curve by its first "
     "value or maximum; 'Subtract baseline' shifts curves to start at zero; "
     "'Fit line' draws a dashed least-squares y = a·x + b over the visible "
     "range. Display-only — your files are never changed."):
        "“分析”面板的派生量工具。“归一化”把每条曲线除以它的首值或最大值；"
        "“扣除基线”把曲线平移到从零开始；“拟合直线”在可见范围内画出虚线"
        "最小二乘拟合 y = a·x + b。仅用于显示 —— 不会修改你的文件。",
    ("Click ✎ Text on the plot toolbar, then click the canvas to place a text "
     "label at that data point. Drag labels to move them; they are kept in "
     "exports and prints. View ▸ Clear annotations removes all."):
        "点击绘图工具栏的 ✎ 文字，再在画布上点击即可在该数据位置放置文字标签。"
        "拖动标签可移动；导出和打印都会保留。视图 ▸ 清除标注可全部移除。",
    ("View ▸ Grid view of checked files (Ctrl+G) draws each checked file in "
     "its own small subplot — up to 24 — instead of overlaying them."):
        "视图 ▸ 勾选文件的网格视图（Ctrl+G）会把每个勾选文件画在自己的小"
        "子图里（最多 24 个），而不是叠加在一起。",
    ("A '&' in an .xvg file starts a new dataset. Multi-dataset files list "
     "every dataset's series in the Series panel; tick any of them, also "
     "across files, to overlay."):
        ".xvg 文件中的“&”表示新数据集的开始。多数据集文件会在“曲线”面板中"
        "列出每个数据集的序列；勾选任意序列（包括跨文件）即可叠加显示。",
    # -- first-run intro (two variants: first_run.py and help_dialogs.py) ---------------------------------------------
    ("<h3>Welcome to XVG Plotter</h3><p>The fast way from GROMACS "
     "<code>.xvg</code> files to publication figures:</p><ul><li><b>Open a "
     "folder</b> — every analysis file is listed with title, series and "
     "points; tick <b>subfolders</b> for nested trees.</li><li><b>Click a "
     "file</b> to plot it; <b>tick several</b> to overlay them. The two file "
     "panes can hold <b>two different folders</b> for comparisons.</li>"
     "<li><b>Right-click a legend entry</b> to <b>pin</b> a curve — it "
     "survives file and folder switches.</li><li><b>Average replicas</b> in "
     "the Series panel, rescale time in the Style options, then <b>Export</b> "
     "(PNG/TIFF/PDF/SVG/EPS), <b>print</b>, or <b>copy</b> straight into "
     "slides.</li></ul><p>Help ▸ <i>Reading the analyses</i> explains the "
     "jargon; Help ▸ <i>Keyboard shortcuts</i> lists every shortcut. Drag "
     "files or folders onto the window anytime.</p>"):
        "<h3>欢迎使用 XVG Plotter</h3><p>从 GROMACS <code>.xvg</code> 文件到"
        "出版级图片的最快路径：</p><ul><li><b>打开文件夹</b> —— 每个分析文件都会"
        "列出标题、曲线数和数据点；嵌套目录请勾选<b>包含子文件夹</b>。</li>"
        "<li><b>单击文件</b>即可绘图；<b>勾选多个</b>可叠加对比。两个文件窗格"
        "可以打开<b>两个不同的文件夹</b>。</li><li><b>右键图例条目</b>可"
        "<b>固定</b>曲线 —— 切换文件或文件夹后依然保留。</li><li>在“曲线”面板中"
        "<b>副本平均</b>，在样式选项中换算时间，然后<b>导出</b>"
        "（PNG/TIFF/PDF/SVG/EPS）、<b>打印</b>或直接<b>复制</b>进幻灯片。</li></ul>"
        "<p>帮助 ▸ <i>读懂分析结果</i>解释术语；帮助 ▸ <i>键盘快捷键</i>列出全部"
        "快捷键。随时可以把文件或文件夹拖进窗口。</p>",
    ("<h3>Welcome to XVG Plotter</h3><p>The fast way from GROMACS "
     "<code>.xvg</code> files to publication figures:</p><ul><li><b>Open a "
     "folder</b> — every analysis file is listed with title, series and "
     "points; tick <b>subfolders</b> for nested trees.</li><li><b>Click a "
     "file</b> to plot it; <b>tick several</b> to overlay them. The two file "
     "panes can hold <b>two different folders</b> for comparisons.</li>"
     "<li><b>Right-click a legend entry</b> to <b>pin</b> a curve — it "
     "survives file and folder switches.</li><li><b>Average replicas</b> in "
     "the Series panel, rescale time in the Style options, then <b>Export</b> "
     "(PNG/TIFF/PDF/SVG/EPS), <b>print</b>, or <b>copy</b> straight into "
     "slides.</li></ul><p>Help ▸ <i>Reading the analyses</i> explains the "
     "jargon; Help ▸ <i>Keyboard shortcuts</i> lists every shortcut.</p>"):
        "<h3>欢迎使用 XVG Plotter</h3><p>从 GROMACS <code>.xvg</code> 文件到"
        "出版级图片的最快路径：</p><ul><li><b>打开文件夹</b> —— 每个分析文件都会"
        "列出标题、曲线数和数据点；嵌套目录请勾选<b>包含子文件夹</b>。</li>"
        "<li><b>单击文件</b>即可绘图；<b>勾选多个</b>可叠加对比。两个文件窗格"
        "可以打开<b>两个不同的文件夹</b>。</li><li><b>右键图例条目</b>可"
        "<b>固定</b>曲线 —— 切换文件或文件夹后依然保留。</li><li>在“曲线”面板中"
        "<b>副本平均</b>，在样式选项中换算时间，然后<b>导出</b>"
        "（PNG/TIFF/PDF/SVG/EPS）、<b>打印</b>或直接<b>复制</b>进幻灯片。</li></ul>"
        "<p>帮助 ▸ <i>读懂分析结果</i>解释术语；帮助 ▸ <i>键盘快捷键</i>列出全部"
        "快捷键。</p>",
    "Welcome to XVG Plotter": "欢迎使用 XVG Plotter",
    "Double-click an .xvg, get a proper plot.": "双击 .xvg，立刻得到一张像样的图。",
    "Got it": "知道了",
    # -- app bootstrap (crash dialog; QCoreApplication.translate("app", …)) ---------
    "XVG Plotter — unexpected error": "XVG Plotter —— 未预期的错误",
    ("An unexpected error occurred:\n{err}\n\nA full trace was written to "
     "the log:\n{log}"):
        "发生了一个未预期的错误：\n{err}\n\n完整堆栈已写入日志：\n{log}",
}
