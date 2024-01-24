# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 14:22:57 2024

@author: Hiroshi_Kajiyama
"""

import os
import pandas as pd
import sqlite3
import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import urllib

def load_data():
    # 現在のファイルのディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # データベースファイルへのパスを構築
    db_path = os.path.join(current_dir, 'suumo.db')
    # データベースに接続
    conn = sqlite3.connect(db_path)
    # SQLクエリを実行し、結果をDataFrameに読み込む
    query = "SELECT * FROM suumo"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 国土地理院のAPIを利用して緯度と経度を取得する関数
def get_coordinates(address):
    response = requests.get(f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={urllib.parse.quote(address)}")
    if response.json():
        lon, lat = response.json()[0]["geometry"]["coordinates"]
        return [lat, lon]
    else:
        return [None, None]

df = load_data()

# 希望条件
#区リスト
region_list ={
    "足立区"	,"墨田区","荒川区", "世田谷区","板橋区","台東区",
    "江戸川区","千代田区","大田区","中央区","葛飾区","豊島区","北区",
    "中野区","江東区","練馬区","品川区","文京区","渋谷区","港区",
    "新宿区"	,"目黒区","杉並区"}

#沿線リスト
line_list = list(df["access1_line"].unique())

station_se = pd.Series(index = line_list)

for line in  line_list:
    df_tmp = df[df["access1_line"]==line]
    station_se[line] = list(df_tmp["access1_station"].unique())


# 間取りリスト
madori_list = [
    '2K', '2DK', '2LDK', '2SK', '2SDK', '2SLDK',
    '3K', '3DK', '3LDK', '3SK', '3SDK', '3SLDK',
    '4K', '4LDK', '4SK',  '4SLDK'
    ]

# タイトル
st.title('賃貸物件情報検索')

# アプリ概要説明
st.write('東京23区内の家族で住む交通利便性の高い賃貸物件を、重複なく効率よく探すことができます。')

# 以下、サイドバーで希望の条件を入力する枠を用意
st.sidebar.title('希望条件を入力してください')

# サイドバーで「地域」と「駅」の選択肢を提供
option = st.sidebar.radio("検索条件を選んでください：", ('地域', '駅'))
station_select = []
region_select = []
line_select = []

# 選択肢に応じてセレクトボックスを更新
if option == '地域':
    # 地域の選択肢を提供
    st.sidebar.text('1.地域')
    region_select = st.sidebar.multiselect('希望の地域を選択してください（複数選択可）', region_list)
    # ...
elif option == '駅':
    # 駅の選択肢を提供
    st.sidebar.text('1.最寄駅')
    line_select = st.sidebar.selectbox('希望の沿線を選択してください', line_list)
    station_select = st.sidebar.multiselect('希望の最寄駅を選択してください（複数選択可）', station_se[line_select])


# 賃料
st.sidebar.text('2.賃料')
min_rent, max_rent = st.sidebar.slider(
    '賃料（万円）の範囲を指定してください',
    min_value = 0,
    max_value = 30,
    value = (0, 30))
min_rent_yen = min_rent * 10000
max_rent_yen = max_rent * 10000

# 駅徒歩
st.sidebar.text('3.駅徒歩')
min_walk_time, max_walk_time = st.sidebar.slider(
    '駅徒歩時間（分）の範囲を指定してください',
    min_value = 0,
    max_value = 30,
    value = (0, 30))

# 間取り
st.sidebar.text('4.間取り')
madori_select = st.sidebar.multiselect('希望の間取りを選択してください（複数選択可）', madori_list)

# 築年数
st.sidebar.text('5.築年数')
min_age, max_age = st.sidebar.slider(
    '築年数の範囲を入指定してください',
    min_value = 0,
    max_value = 100,
    value = (0, 50))

# 占有面積
st.sidebar.text('6.占有面積')
min_menseki, max_menseki = st.sidebar.slider(
    '占有面積（m2）の範囲を入指定してください',
    min_value = 0,
    max_value = 150,
    value = (0, 75))

# 検索ボタンを設置
button = st.sidebar.button('検索',type = 'primary')

# 検索条件でデータを絞り込み、結果を df_search に代入
df_search = df.query(
    f'((区 == {region_select}) or (access1_station=={station_select}))  and ({min_rent_yen} <= 家賃 <= {max_rent_yen}) and ({min_walk_time} <= access1_walk <= {max_walk_time}) and (間取り == {madori_select}) and ({min_age} <= 築年数 <= {max_age})  and ({min_menseki} <= 面積 <= {max_menseki})')
# 検索結果のヒット件数を取得
hit = len(df_search)

# map用に緯度, 経度データだけを df_loc に代入。geopyで緯度経度取得できなかった欠損地は削除。
#df_loc = df_search[['lat', 'lon']].dropna()

# df_searchのカラム名を全て日本語に直す
#df_search.columns = ['物件名', '住所', '築年数', '構造', '階数', '賃料', '管理費', '敷金', '礼金', '間取り', '占有面積', '最寄駅路線1', '最寄駅1', '駅徒歩1', '最寄駅路線2', '最寄駅2', '駅徒歩2', '最寄駅路線3', '最寄駅3', '駅徒歩3', '緯度', '経度' ]

df_search = df_search[["マンション名","住所","アクセス1","アクセス2","アクセス3","築年数","構造","階数","間取り","面積","家賃","管理費",'lat','lon']]

# 検索ボタンを押した際に、結果を表示
if button == True:
    st.write('■ 検索結果')
    st.write(f'▼ ヒット件数：{hit}件')
    st.write('▼ 物件一覧：')
    st.dataframe(df_search, width=700, height=300)
    
    # 住所のカラムにジオコーディングを適用
    #df_search['Coordinates'] = df_search['住所'].apply(get_coordinates)
    
    # フィルタリングされた物件の座標の平均を計算
    valid_coords = df_search[['lat','lon']].dropna()
    if len(valid_coords) > 0:
        average_lat = valid_coords["lat"].mean()
        average_lon = valid_coords["lon"].mean()
        map_center = [average_lat, average_lon]
    else:
        # 有効な座標がない場合、デフォルトの中心座標を使用
        map_center = [35.6895, 139.6917]

    # 地図の初期化（平均座標を中心として）
    m = folium.Map(location=map_center, zoom_start=12)

    # 各座標にマーカーをプロットし、物件名をポップアップで表示
    for _, row in df_search.iterrows():
        coord = row[['lat','lon']]
        if coord[0] is not None and coord[1] is not None:
            
            #folium.Circle(
            #location=coord,
            #radius=200,
            #color='blue',
            #fill=True,
            #fill_color='blue'
           #).add_to(m)
            
            folium.Marker(
                location=coord,
                popup=row['マンション名'],
                icon=folium.Icon(icon='info-sign')
            ).add_to(m)

    # Streamlitアプリに地図を表示
    st.title('物件の所在地')
    folium_static(m)
    #st.write("※地図上に表示される物件の位置は付近住所に所在することを表すものであり、実際の物件所在地とは異なる場合がございます。")
    #st.write("正確な物件所在地は、取扱い不動産会社にお問い合わせください。")
    
else:
    st.write("←左の入力欄から条件を設定し、'検索'ボタンを押してください。")

#st.write('▼ マップ：')
#st.map(df_loc)
