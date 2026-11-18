# ============================================================
# 公開資訊觀測站 開放資料瀏覽器 (Gradio)
# 本機執行：python app.py
# Render 部署：Start Command 使用 python app.py
# ============================================================
import io
import os
import tempfile

import gradio as gr
import pandas as pd
import plotly.express as px
import requests
import urllib3

# 原始腳本使用 verify=False，故關閉憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 可用環境變數 DEFAULT_URL 覆蓋預設資料網址
DEFAULT_URL = os.environ.get(
    "DEFAULT_URL", "https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv"
)


# ------------------------------------------------------------
# 資料處理
# ------------------------------------------------------------
def fetch_data(url: str, drop_na: bool) -> pd.DataFrame:
    """requests.get 下載 CSV -> pandas 讀取 (utf-8-sig) -> 選擇性 dropna"""
    response = requests.get(url, verify=False, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")  # 繁體中文
    if drop_na:
        df = df.dropna()
    return df.reset_index(drop=True)


def to_csv_file(df: pd.DataFrame) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", prefix="mops_")
    df.to_csv(tmp.name, index=False, encoding="utf-8-sig")
    return tmp.name


def stats_html(df: pd.DataFrame) -> str:
    cards = [
        ("📄 資料筆數", f"{len(df):,}"),
        ("🧱 欄位數", f"{df.shape[1]:,}"),
        ("🔢 數值欄位", f"{df.select_dtypes('number').shape[1]:,}"),
        ("⚠️ 缺漏值", f"{int(df.isna().sum().sum()):,}"),
    ]
    items = "".join(
        f"<div class='card'><div class='card-label'>{k}</div>"
        f"<div class='card-value'>{v}</div></div>"
        for k, v in cards
    )
    return f"<div class='cards'>{items}</div>"


EMPTY_STATS = stats_html(pd.DataFrame())


# ------------------------------------------------------------
# 事件函式
# ------------------------------------------------------------
def load_data(url, drop_na):
    try:
        df = fetch_data((url or "").strip(), drop_na)
    except Exception as e:
        raise gr.Error(f"下載或解析失敗：{e}")

    if df.empty:
        raise gr.Error("資料為空。若已勾選「移除缺漏值」，請取消勾選後再試一次。")

    cols = list(df.columns)
    summary = df.describe(include="all").T.reset_index().rename(columns={"index": "欄位"})
    status = f"✅ 載入成功：{len(df):,} 筆、{len(cols)} 欄"
    return (
        df,
        status,
        stats_html(df),
        gr.update(choices=cols, value=cols),
        gr.update(choices=cols, value=cols[0]),
        summary,
    )


def apply_filter(df, keyword, cols):
    if df is None:
        return pd.DataFrame(), "尚未載入資料", None
    view = df
    keyword = (keyword or "").strip()
    if keyword:
        mask = (
            df.astype(str)
            .apply(lambda s: s.str.contains(keyword, case=False, na=False, regex=False))
            .any(axis=1)
        )
        view = df[mask]
    if cols:
        view = view[[c for c in cols if c in view.columns]]
    msg = f"🔎 符合 {len(view):,} / {len(df):,} 筆"
    return view, msg, to_csv_file(view)


def draw_chart(df, col, topn):
    if df is None or not col:
        return None
    topn = int(topn)
    series = df[col]

    if pd.api.types.is_numeric_dtype(series):
        fig = px.histogram(
            df, x=col, nbins=30, template="plotly_white",
            color_discrete_sequence=["#6366f1"], title=f"「{col}」數值分布",
        )
    else:
        vc = series.astype(str).value_counts().head(topn).reset_index()
        vc.columns = [col, "筆數"]
        fig = px.bar(
            vc.iloc[::-1], x="筆數", y=col, orientation="h", text="筆數",
            template="plotly_white", color="筆數",
            color_continuous_scale="Blues", title=f"「{col}」出現次數 Top {topn}",
        )
        fig.update_layout(coloraxis_showscale=False)

    fig.update_layout(
        height=480, margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif"),
    )
    return fig


# ------------------------------------------------------------
# 介面
# ------------------------------------------------------------
CSS = """
.gradio-container {max-width: 1200px !important; margin: auto;}
.hero {
  background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%);
  color: white; padding: 28px 32px; border-radius: 18px; margin-bottom: 8px;
  box-shadow: 0 8px 24px rgba(79,70,229,.25);
}
.hero h1 {margin: 0 0 6px 0; font-size: 28px; color: white;}
.hero p {margin: 0; opacity: .9; font-size: 15px;}
.cards {display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px;}
.card {
  background: var(--background-fill-secondary); border: 1px solid var(--border-color-primary);
  border-radius: 14px; padding: 16px 18px;
}
.card-label {font-size: 13px; opacity: .7; margin-bottom: 6px;}
.card-value {font-size: 26px; font-weight: 700; color: #6366f1;}
"""

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="sky",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Noto Sans TC"), "ui-sans-serif", "sans-serif"],
)

with gr.Blocks(theme=theme, css=CSS, title="公開資訊觀測站 開放資料瀏覽器") as demo:
    state = gr.State(None)

    gr.HTML(
        "<div class='hero'><h1>📊 公開資訊觀測站 開放資料瀏覽器</h1>"
        "<p>下載 MOPS 開放資料 CSV，快速搜尋、篩選欄位、視覺化並匯出結果</p></div>"
    )

    with gr.Row():
        url_box = gr.Textbox(label="資料網址 (CSV)", value=DEFAULT_URL, scale=5)
        drop_na = gr.Checkbox(label="移除缺漏值 (dropna)", value=True, scale=1)
        load_btn = gr.Button("🚀 載入資料", variant="primary", scale=1)

    status = gr.Markdown("尚未載入資料")
    stats = gr.HTML(EMPTY_STATS)

    with gr.Tabs():
        with gr.Tab("📋 資料表"):
            with gr.Row():
                keyword = gr.Textbox(
                    label="關鍵字搜尋（搜尋所有欄位）",
                    placeholder="例如：公司代號、公司名稱…", scale=3,
                )
                cols_sel = gr.Dropdown(
                    label="顯示欄位", choices=[], value=[], multiselect=True, scale=4
                )
            with gr.Row():
                filter_msg = gr.Markdown("")
                dl_file = gr.File(label="下載目前結果 (CSV)", scale=1)
            table = gr.Dataframe(interactive=False, wrap=True)

        with gr.Tab("📈 圖表分析"):
            with gr.Row():
                chart_col = gr.Dropdown(label="選擇欄位", choices=[], scale=3)
                topn = gr.Slider(5, 30, value=15, step=1, label="Top N（文字欄位）", scale=2)
            plot = gr.Plot()

        with gr.Tab("🧮 欄位摘要"):
            summary_tbl = gr.Dataframe(interactive=False, wrap=True)

    # ---- 事件綁定 ----
    load_outputs = [state, status, stats, cols_sel, chart_col, summary_tbl]
    filter_inputs = [state, keyword, cols_sel]
    filter_outputs = [table, filter_msg, dl_file]

    load_btn.click(load_data, [url_box, drop_na], load_outputs).then(
        apply_filter, filter_inputs, filter_outputs
    ).then(draw_chart, [state, chart_col, topn], plot)

    keyword.submit(apply_filter, filter_inputs, filter_outputs)
    keyword.change(apply_filter, filter_inputs, filter_outputs)
    cols_sel.change(apply_filter, filter_inputs, filter_outputs)
    chart_col.change(draw_chart, [state, chart_col, topn], plot)
    topn.release(draw_chart, [state, chart_col, topn], plot)

    # 開啟頁面時自動載入資料
    demo.load(load_data, [url_box, drop_na], load_outputs).then(
        apply_filter, filter_inputs, filter_outputs
    ).then(draw_chart, [state, chart_col, topn], plot)


if __name__ == "__main__":
    # Render 會提供 PORT 環境變數，且必須綁定 0.0.0.0
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )
