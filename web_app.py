import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# ================= 1. 核心功能函数区 =================

def scrape_real_estate_news(url):
    """爬虫模块：负责去网站抓取数据"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            article_text = "\n".join([p.text.strip() for p in paragraphs if p.text.strip() != ""])
            return article_text[:2000]
        else:
            return f"抓取失败，状态码: {response.status_code}"
    except Exception as e:
        return f"抓取异常: {e}"


def get_ai_response(messages):
    """通用的 AI 调用模块"""
    client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )
    try:
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI 响应失败: {e}"


# ================= 2. 网页界面与逻辑控制区 =================

st.set_page_config(page_title="房地产金融宏观分析智能体", page_icon="🏢", layout="wide")
st.title("🏢 房地产金融宏观分析智能体")
st.markdown("不仅能自动生成研报，还能针对房地产数据进行深度问答。")

# --- 状态管理 (赋予网页记忆功能) ---
# 初始化爬取的数据和分析报告的状态
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = ""
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = ""
# 初始化聊天记录列表
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 第一部分：数据抓取与研报生成 ---
st.header("1. 宏观数据提取与分析")
default_url = "https://www.stats.gov.cn/sj/zxfb/202602/t20260213_1962617.html"
target_url = st.text_input("🔗 请在此粘贴数据源网址：", value=default_url)

if st.button("🚀 开始抓取并生成报告"):
    if target_url:
        with st.spinner('🕵️ 智能体正在潜入网页抓取数据...'):
            data = scrape_real_estate_news(target_url)
            st.session_state.scraped_data = data  # 将抓取的数据存入记忆

        if "失败" not in data and "异常" not in data and len(data) > 50:
            st.success("✅ 数据提取成功！")
            with st.expander("点击查看原始网页文本"):
                st.write(data[:500] + "...")

            with st.spinner('🧠 正在生成专业研报...'):
                # 构建生成研报的专属 Prompt
                report_prompt = [
                    {"role": "system",
                     "content": "你是一位顶级的宏观房地产金融分析师。请基于用户提供的数据输出包含趋势判断、市场情绪、投资组合建议三部分的快评。"},
                    {"role": "user", "content": f"请分析以下数据：\n\n{data}"}
                ]
                report = get_ai_response(report_prompt)
                st.session_state.analysis_report = report  # 将报告存入记忆

                # 研报生成后，自动将背景知识加入聊天记录的 System Prompt 中，让 AI 知道我们在聊什么
                st.session_state.chat_history = [
                    {"role": "system",
                     "content": f"你是一位房地产金融助教。请基于以下背景数据回答用户的问题。\n\n背景数据：{data[:1000]}"}
                ]
        else:
            st.error("❌ 获取失败，请检查网址。")

# 如果已经生成了报告，就展示出来
if st.session_state.analysis_report:
    st.subheader("📊 智能体分析报告")
    st.info(st.session_state.analysis_report)

    # ====== 👇 升级版的完整文档导出功能 👇 ======
    st.markdown("<br>", unsafe_allow_html=True)

    # 1. 先把核心研报放入我们要导出的文本中
    export_text = f"# 📊 房地产宏观数据 AI 分析报告\n\n{st.session_state.analysis_report}\n\n"

    # 2. 智能筛选并拼接聊天记录
    # (过滤掉 role 为 'system' 的后台提示词，只保留你和 AI 的真实对话)
    chat_records = [msg for msg in st.session_state.chat_history if msg["role"] != "system"]

    if chat_records:
        export_text += "---\n\n## 💬 深度互动问答 (Q&A) 实录\n\n"
        for msg in chat_records:
            if msg["role"] == "user":
                export_text += f"**🗣️ 提问：** {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                export_text += f"**🤖 AI 专家：** {msg['content']}\n\n"

    # 3. 生成终极下载按钮
    st.download_button(
        label="📥 一键下载完整报告 & Q&A 问答记录",
        data=export_text,
        file_name="房地产宏观深度分析与问答实录_AI生成.md",
        mime="text/markdown",
        help="点击即可将研报正文与下方的深度追问记录一并保存本地"
    )
    # =====================================

    # 接收用户的提问
    if user_question := st.chat_input("例如：这份数据对公募 REITs 的底层资产估值有什么影响？"):
        # 1. 把用户的问题显示在界面上并加入记忆
        with st.chat_message("user"):
            st.markdown(user_question)
        st.session_state.chat_history.append({"role": "user", "content": user_question})

        # 2. 呼叫 AI 进行回答
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                # 将完整的历史记录发给 AI，确保它有上下文
                ai_answer = get_ai_response(st.session_state.chat_history)
                st.markdown(ai_answer)
        # 3. 把 AI 的回答加入记忆
        st.session_state.chat_history.append({"role": "assistant", "content": ai_answer})
else:
    st.warning("⚠️ 请先在上方执行【数据抓取与生成报告】，然后才能开启问答功能。")
