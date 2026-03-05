import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# ================= 1. 核心功能函数区 (和之前一样) =================

def scrape_real_estate_news(url):
    """爬虫模块"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
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
            return f"抓取失败，网页返回状态码: {response.status_code}"
    except Exception as e:
        return f"抓取发生异常，错误信息: {e}"


def analyze_with_ai(text_content):
    """AI 分析模块"""
    # 让代码去 Streamlit 的“保险箱”里读取密码
    client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )
    system_prompt = """你是一位顶级的宏观房地产金融分析师。
    请基于用户提供的国家统计局房价数据新闻稿，输出一份专业且结构清晰的快评报告。报告必须包含以下三部分：
    1. 【总体趋势判断】：精准概括一二三线城市商品住宅销售价格的环比与同比变动分化情况。
    2. 【市场情绪与供需分析】：透过数据分析当前市场的购房者情绪、去库存压力及政策面的实际效用。
    3. 【前瞻与投资组合建议】：从金融机构的视角，给出针对房地产板块（含股票及REITs）的短期风险提示与潜在机会挖掘。"""

    try:
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下国家统计局发布的最新房价变动数据：\n\n{text_content}"}
            ],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI 分析失败，错误信息: {e}"


# ================= 2. 网页界面构建区 (Streamlit 魔力所在) =================

# 设置网页的标题和图标
st.set_page_config(page_title="房地产金融宏观分析智能体", page_icon="🏢", layout="wide")

# 网页主标题
st.title("🏢 房地产金融宏观分析智能体")
st.markdown("输入国家统计局或其他宏观数据的网页链接，AI 智能体将自动抓取并生成专业的金融快评报告。")

# 创建一个输入框，让用户粘贴网址
default_url = "https://www.stats.gov.cn/sj/zxfb/202602/t20260213_1962617.html"
target_url = st.text_input("🔗 请在此粘贴数据源网址：", value=default_url)

# 创建一个按钮，点击后开始执行
if st.button("🚀 开始抓取并生成报告"):
    if target_url:
        # 使用进度提示，让等待过程不枯燥
        with st.spinner('🕵️ 智能体正在潜入网页抓取数据...'):
            scraped_data = scrape_real_estate_news(target_url)

        if "抓取失败" not in scraped_data and "异常" not in scraped_data and len(scraped_data) > 50:
            st.success("✅ 网页数据抓取成功！")

            # 使用折叠面板展示抓取到的生肉数据（显得很专业）
            with st.expander("点击查看抓取到的原始网页文本 (前500字)"):
                st.write(scraped_data[:500] + "...")

            st.markdown("---")

            with st.spinner('🧠 AI 首席分析师正在生成研报，请稍候...'):
                analysis_result = analyze_with_ai(scraped_data)

            # 展示最终报告
            st.subheader("📊 智能体分析报告")
            st.info(analysis_result)
        else:
            st.error(f"❌ 数据获取失败。\n\n详细信息：{scraped_data}")
    else:
        st.warning("请先输入网址！")