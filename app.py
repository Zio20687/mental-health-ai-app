import streamlit as st
import mental_health_resources 
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
import time

# 讀取密鑰
gmail_address = st.secrets["gmail_address"]
gmail_password = st.secrets["gmail_app_password"]
counselor_email = st.secrets["counselor_email"]

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

def construct_psych_context():
    if all(k in st.session_state for k in ["level", "age_group", "gender", "responses", "total_score"]):
        intro = (
            f"使用者的心理健康評估結果如下：\n"
            f"- 年齡範圍：{st.session_state['age_group']}\n"
            f"- 性別：{st.session_state['gender']}\n"
            f"- 總分：{st.session_state['total_score']}，建議：{st.session_state['level']}\n\n"
            f"使用者在評估中對情緒問題的回覆如下：\n"
        )
        for q, a in st.session_state['responses'].items():
            intro += f"  - {q}：{a}\n"
        intro += "\n你是一位專業的心理輔導助理，只能針對心理健康、情緒支持、壓力管理等問題提供回應。如果使用者問到無關的問題（例如投資、電影、數學等），請禮貌地回應「請針對心理相關議題發問，我會很樂意協助您。」"
        return intro
    else:
        return (
            "你是一位專業的心理輔導助理。請根據使用者的情緒狀態提供心理健康、壓力釋放、情緒支持等方面的回應。"
            "請避免回答與心理無關的問題，例如財經、遊戲、程式、電腦操作、編寫程式碼等。"
        )

# 分頁
tab1, tab2, tab3 = st.tabs(["📝 心理健康評估", "🤖 AI 心理諮詢", "💖 心衛資源"])

with tab1:
    st.title("📝心理健康評估 及 音樂推薦")

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
        recipient = st.text_input("請輸入您的 Gmail 信箱", placeholder="example@gmail.com")
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
                    
                    
        
        if score_mapping[st.session_state["responses"]["過去一星期，是否有自殺的想法？"]] >= 2 or st.session_state["total_score"] >= 10:
            if st.button("獲取心理資源建議"):
                st.markdown("""
                ### ❤️ 緊急心理資源建議
                我很抱歉，你現在的情況我無法提供足夠的幫助。請撥打下列專線或利用以下資源：

                📞 台灣自殺防治中心：0800-788-995  
                📞 生命線協談專線：1995  
                 
                 #### 🎓 學校心理輔導資源
                 - **僑光科大諮商輔導中心**  
                 僑光科大諮商輔導中心網頁:[https://scc.ocu.edu.tw/index.php?Lang=zh-tw](https://scc.ocu.edu.tw/index.php?Lang=zh-tw)
                 可免費提供學生心理諮詢、情緒調適團體與危機處遇。
  
                 你可以透過以下網址預約心理諮詢服務：  
                 👉[報名預約心理諮商](http://counseling.ocu.edu.tw/index.aspx)     
                                    
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

# 自動傳遞評估摘要給 tab2 輔導開場（只顯示一次）
if "auto_intro_sent" not in st.session_state and "level" in st.session_state:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    intro = (
        "以下是您的心理健康評估結果摘要：\n"
        f"- 年齡範圍：{st.session_state['age_group']}\n"
        f"- 性別：{st.session_state['gender']}\n"
        f"- 總分：{st.session_state['total_score']}，建議：{st.session_state['level']}\n\n"
        f"您在評估中的回答如下：\n"
    )
    for q, a in st.session_state['responses'].items():
        intro += f"  - {q}：{a}\n"

    # 加入第一則系統訊息
    st.session_state.messages.append({
        "role": "assistant", 
        "content": intro
    })

    # 加入模擬使用者訊息，請求 GPT 心理建議
    st.session_state.messages.append({
        "role": "user", 
        "content": "請根據上述心理健康評估結果，給我一些溫柔的心理建議。"
    })

    st.session_state.auto_intro_sent = True

# 若為中度或重度患者，顯示 Gmail 填寫表單並寄信
if "total_score" in st.session_state:
    total_score = st.session_state['total_score']
    suicide_score = score_mapping[st.session_state['responses']["過去一星期，是否有自殺的想法？"]]

    if total_score >= 10 or suicide_score >= 2:
        with st.expander("⚠️ 你有中度以上情緒困擾，是否願意填寫你的 Gmail？系統將匿名寄給輔導員。"):
            user_email = st.text_input("📧 請輸入您的 Gmail（選填）", placeholder="example@gmail.com")
            if st.button("寄送通知給輔導員"):
                if user_email and user_email.endswith("@gmail.com"):
                    body = f"""⚠️ 使用者心理健康評估通知

使用者自行填寫了以下 Gmail：{user_email}

年齡範圍：{st.session_state['age_group']}
性別：{st.session_state['gender']}

填答內容如下：
"""
                    for q, a in st.session_state['responses'].items():
                        body += f"- {q}：{a}\n"
                    body += f"\n總分：{total_score}\n建議：{st.session_state['level']}\n"

                    msg = MIMEText(body, _charset="utf-8")
                    msg["Subject"] = "⚠️ 心理健康評估結果通知（使用者自行填寫Gmail）"
                    msg["From"] = gmail_address
                    msg["To"] = counselor_email

                    try:
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                            server.login(gmail_address, gmail_password)
                            server.send_message(msg)
                        st.success("✅ 已將通知寄出給輔導員。謝謝您的信任。")
                    except Exception as e:
                        st.error(f"❌ 郵件寄送失敗：{e}")
                else:
                    st.warning("請輸入正確的 Gmail。")


# AI 心理諮詢
with tab2:
    st.subheader("🤖 AI 心理諮詢")

    # 顯示訊息
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # ⬇️ 自動觸發 GPT 心理建議
    if (
        "auto_intro_sent" in st.session_state
        and st.session_state.auto_intro_sent
        and not any(m["content"].startswith("根據您的心理健康評估") for m in st.session_state.messages)
    ):
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": construct_psych_context()}
                ] + st.session_state.messages,
                stream=True
            )
            response = st.write_stream(stream)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

    # ⬇️ 使用者輸入處理
    if prompt := st.chat_input("請輸入您的感受..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
               model="gpt-4",
               messages=[
                   {"role": "system", "content": construct_psych_context()}
               ] + st.session_state.messages,
               stream=True
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})


#心衛資源
with tab3:
    st.subheader("💖 心衛資源")
    st.markdown(mental_health_resources.resources_markdown)

# 頁尾
st.markdown("""
---
<div style='text-align: center; color: gray;'>
    。本網頁僅供僑光科大資科系學術研究，結果僅供參考。
</div>
<div style='text-align: center; color: gray;'>
    。表單來源來自社團法人台灣自殺防治學會。
</div>
""", unsafe_allow_html=True)
