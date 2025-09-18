import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import pandas as pd
import json

st.set_page_config(page_title="コメントランキングアプリ", layout="wide")
st.title("🎯 コメントランキングアプリ（初心者向けWeb版）")

# --- 1. スプレッドシートURL入力 ---
sheet_url = st.text_input("GoogleスプレッドシートのURLを入力してください")

if sheet_url:
    try:
        # URLからスプレッドシートIDを抽出
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]

        # --- 2. Google認証 (Secrets対応) ---
        creds_dict = json.loads(st.secrets["GSPREAD_CREDS"])
        with open("temp_credentials.json", "w") as f:
            json.dump(creds_dict, f)

        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("temp_credentials.json", scope)
        client = gspread.authorize(creds)

        # コメント取得
        sheet = client.open_by_key(sheet_id).sheet1
        comments = sheet.col_values(1)

        # --- セッション管理 ---
        if "points" not in st.session_state:
            st.session_state.points = {c:0 for c in comments}
            st.session_state.round = 0
            st.session_state.options = random.sample(comments, 3)
            st.session_state.sub_round = 0
            st.session_state.history = []

        remaining = 50 - st.session_state.round
        col1, col2 = st.columns([3,1])

        with col1:
            st.write(f"ラウンド: {st.session_state.round + 1} / 50 (残り {remaining})")

            # --- ランダム3択 ---
            if st.session_state.sub_round == 0:
                st.write("一番好きなコメントを選んでください👇")
                for c in st.session_state.options:
                    if st.button(c):
                        st.session_state.selected = c
                        st.session_state.sub_round = 1
                        st.experimental_rerun()

            else:
                st.write("さらに一番好きなものを選んでください👇")
                sub_options = [st.session_state.selected] + [c for c in st.session_state.options if c != st.session_state.selected]
                for c in sub_options:
                    if st.button(c):
                        st.session_state.points[c] += 1
                        st.session_state.round += 1
                        st.session_state.history.append(c)
                        st.session_state.sub_round = 0
                        st.session_state.options = random.sample(comments, 3)

                        if st.session_state.round >= 50:
                            # --- ランキング表示 ---
                            st.success("🎉 選択完了！最終ランキング")
                            ranked = sorted(st.session_state.points.items(), key=lambda x:x[1], reverse=True)
                            df = pd.DataFrame(ranked, columns=["コメント","ポイント"])
                            st.dataframe(df)
                            st.bar_chart(df.set_index("コメント")["ポイント"])
                        else:
                            st.experimental_rerun()

        with col2:
            st.write("📝 選択履歴（直近10件）")
            if st.session_state.history:
                for i, h in enumerate(st.session_state.history[-10:], 1):
                    st.write(f"{i}. {h}")
            else:
                st.write("まだ選択はありません。")

    except Exception as e:
        st.error(f"接続エラー: {e}")
