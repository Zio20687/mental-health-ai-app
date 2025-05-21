import streamlit as st
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
import time

# 讀取密鑰
gmail_address = st.secrets["gmail_address"]
gmail_password = st.secrets["gmail_app_password"]

@st.cache_resource
def get_openai_client():
    return OpenAI(
        api_key=st.secrets["openai_api_key"],
        organization="org-GnOIuRNbbIp6l80TftYOup4A"
    )
client = get_openai_client()

# 音樂推薦函數
def recommend_music(level, age_group, gender):
    with st.spinner("正在搜尋適合的歌曲，請稍候..."):
        try:
            time.sleep(2)
            prompt = f"請根據{level}的情緒狀態、{age_group}的年齡範圍與{gender}的性別，以繁體中文推薦 5 首適合的中文歌曲，並附上歌手名稱。"
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一位音樂推薦專家及心情輔導專家，請以繁體中文回答。"},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            recommendations = [song.strip() for song in content.split("\n") if song.strip()]
            st.subheader("🎵 根據您的狀態，推薦以下歌曲：")
            for song in recommendations:
                st.write(f"- {song}")
        except Exception as e:
            st.error(f"發生錯誤：{e}")
            raise

# 分頁
tab1, tab2, tab3 = st.tabs(["📝 心理健康評估", "🤖 AI 心理諮詢", "📷 臉部辨識評估"])

with tab1:
    st.title("心理健康評估音樂推薦 與 AI 心理諮詢")

    age_group = st.selectbox("請選擇您的年齡範圍：", ["請選擇", "14歲(含)以下", "15~24歲", "25~44歲", "45~64歲", "65歲(含)以上"])
    gender = st.selectbox("請選擇您的性別：", ["請選擇", "男", "女"])

    questions = {
        "在過去一星期中，是否有睡眠困難譬如難以入睡、易醒或早醒？": ["請選擇", "完全沒有", "輕微", "中等程度", "厲害", "非常厲害"],
        "過去一星期中，是否有感覺緊張不安？": ["請選擇", "完全沒有", "輕微", "中等程度", "厲害", "非常厲害"],
        "過去一星期，是否有感覺憂鬱、心情低落？": ["請選擇", "完全沒有", "輕微", "中等程度", "厲害", "非常厲害"],
        "過去一星期，是否有感覺自己比不上別人？": ["請選擇", "完全沒有", "輕微", "中等程度", "厲害", "非常厲害"],
        "過去一星期，是否有自殺的想法？": ["請選擇", "完全沒有", "輕微", "中等程度", "厲害", "非常厲害"]
    }
    score_mapping = {"完全沒有": 0, "輕微": 1, "中等程度": 2, "厲害": 3, "非常厲害": 4}

    if st.session_state.get("reset_flag", False):
        for idx in range(len(questions)):
            st.session_state[f"q_{idx}"] = "請選擇"
        st.session_state.clear()
        st.rerun()

    responses = {}
    for idx, (q, options) in enumerate(questions.items()):
        key = f"q_{idx}"
        default = st.session_state.get(key, "請選擇")
        responses[q] = st.selectbox(q, options, index=options.index(default), key=key)

    if st.button("送出評估"):
        if age_group == "請選擇" or gender == "請選擇" or "請選擇" in responses.values():
            st.warning("請完整填寫所有問題與基本資料後再送出。")
        else:
            total_score = sum(score_mapping[responses[q]] for q in responses)
            suicide_score = score_mapping[responses["過去一星期，是否有自殺的想法？"]]

            if suicide_score >= 2:
                level = "⚠️ 您在自殺想法的評分達到中等程度以上，建議立即尋求精神醫療專業諮詢。"
            elif total_score <= 5:
                level = "0~5分，一般正常範圍。"
            elif total_score <= 9:
                level = "6~9分，輕度情緒困擾: 建議找朋友或家人談談，抒發情緒。"
            elif total_score <= 14:
                level = "10~14分，中度情緒困擾: 建議尋求紓壓管道或心理專業指導。"
            else:
                level = "15分以上，重度情緒困擾: 建議諮詢輔導老師或精神科醫師。"

            st.session_state.update({
                "level": level,
                "age_group": age_group,
                "gender": gender,
                "responses": responses,
                "total_score": total_score
            })

            st.markdown(f"### 您的總分為：**{total_score}**")
            st.markdown(f"### 狀態建議：**{level}**")

    if "level" in st.session_state:
        st.markdown("---")
        st.subheader("📩 將結果寄到您的 Gmail")
        recipient = st.text_input("請輸入您的 Gmail 信箱")
        if st.button("將結果寄到 Gmail"):
            if not recipient or "@gmail.com" not in recipient:
                st.error("請輸入正確的 Gmail 地址")
            else:
                try:
                    body = f"""您好，

這是您在心理健康評估系統中的結果：

年齡範圍：{st.session_state['age_group']}
性別：{st.session_state['gender']}

填答內容：
"""
                    for q, a in st.session_state['responses'].items():
                        body += f"- {q}：{a}\n"
                    body += f"\n總分：{st.session_state['total_score']}\n結果及建議：{st.session_state['level']}\n\n"
                    body += """---
請記得，這個系統僅供輔助用途。如有急迫需求請聯繫心理專業人士。
祝您平安。心理輔導 AI 系統 敬上"""

                    msg = MIMEText(body, _charset="utf-8")
                    msg["Subject"] = "心理健康評估結果"
                    msg["From"] = gmail_address
                    msg["To"] = recipient

                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(gmail_address, gmail_password)
                        server.send_message(msg)

                    st.success("✅ 結果已寄出！請到您的 Gmail 查收。")
                except Exception as e:
                    st.error(f"❌ 郵件寄送失敗：{e}")
                    raise

        if score_mapping[st.session_state["responses"]["過去一星期，是否有自殺的想法？"]] >= 2:
            if st.button("獲取心理資源建議"):
                st.markdown("""
                ### ❤️ 緊急心理資源建議
                我很抱歉，你現在的情況我無法提供足夠的幫助。請撥打下列專線：

                📞 台灣自殺防治中心：0800-788-995  
                📞 生命線協談專線：1995  

                請記得：你並不孤單，很多人願意幫助你。
                """)
        else:
            if st.button("獲取音樂推薦"):
                recommend_music(
                    st.session_state["level"],
                    st.session_state["age_group"],
                    st.session_state["gender"]
                )

        if st.button("重新開始評估"):
            st.session_state.reset_flag = True
            st.rerun()

# AI 心理諮詢
with tab2:
    st.subheader("🤖 AI 心理諮詢")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    if prompt := st.chat_input("請輸入您的感受..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages,
                stream=True
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

# 頁尾
st.markdown("""
---
<div style='text-align: center; color: gray;'>
    本網頁僅供學術研究
</div>
""", unsafe_allow_html=True)