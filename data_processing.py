# -*- coding: utf-8 -*-
"""
Created on Sat Dec  9 13:50:42 2023

@author: Hiroshi_Kajiyama
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from sqlalchemy import create_engine

df = pd.read_csv("suumo_data.csv")

#　各物件　の特性の値に　どのような種類の値が含まれるのかを確認し、データクレンジングの必要性、やり方を検討する
columns_prop = ["マンション名", "住所","アクセス","築年数","構造","階数","間取り","面積","家賃","管理費"]
prop_list = []
for prop in  columns_prop:
    tmp =pd.Series(name=prop,data=df[prop].unique())
    prop_list.append(tmp)
    
#################データのクレンジング############################################
"""
各物件情報に含まれる値を調べてた結果は以下
物件名：　物件名称の代わりに　”都営大江戸線 飯田橋駅 15階建 築19年”のように　物件のプロパティを並べて記載してるものがある
⇒物件名に　物件のプロパティがあてられてるものが、実際は既存の物件名があてられるものがないか調べる
アクセス：　いくつの駅からアクセス可能か　カウントする。徒歩10分以内の駅に絞った方がいいかも
住所：見た限り重複らしきもの無し
築年数：新築だけ　データフォーマット違う⇒築0年に変更
構造：地下の階層がついているものもある⇒　地下の階層と地上の階層を足す
階数：　1-2階だけフォーマット違う　⇒ 1.5階に変更
間取り：　間取りを分解して管理？
面積：　これは全て同じフォーマット　
家賃：　これは全て同じフォーマット
管理費：　"-" だけ異なるフォーマット　⇒　0円に変更
"""

#物件名#
#住所が　同じで　違名のものは　実際は　同じ物件とする
# ⇒　同じ住所で違う物件がある？住所だけでは名寄せできない。築年数、構造は少なくとも見ないと 
mansion_id_list = []
dup_list =[]
df["マンション名名寄せ"]=df["住所"]+"_"+df["築年数"]+"_"+df["構造"]
tmp_list = df["マンション名名寄せ"].unique()
for  mansion_id  in tmp_list:
    tmp = df[df["マンション名名寄せ"]==mansion_id]
    mansion_id_list.append(tmp)
    tmp_dup= tmp["マンション名"].unique()
    if len(tmp_dup) > 1: 
        tmp_dup = sorted(tmp_dup, key=len, reverse=False)
        dup_list.append(tmp_dup) #物件名の重複リスト
for  same_mansion  in dup_list:
    df["マンション名"]= df["マンション名"].apply(lambda x: same_mansion[0] if x == same_mansion[1] else x)
#面積#
df["面積"]= df["面積"].apply(lambda x: x.rstrip("m2")).astype("float")
#家賃#
df["家賃"]= df["家賃"].apply(lambda x: x.rstrip("万円")).astype("float")
df["家賃"]= df["家賃"].apply(lambda x: x*10000)
#管理費#
df["管理費"]= df["管理費"].replace("-","0")
df["管理費"]= df["管理費"].apply(lambda x: x.rstrip("円")).astype("int")
#築年数#
df["築年数"]= df["築年数"].replace("新築","築0年")
df["築年数"]= df["築年数"].apply(lambda x: x.replace("築","").replace("年","")).astype("int")
#構造#
df["構造"]= df["構造"].apply(lambda x: sum([int(num) for num in (x.lstrip("地下").rstrip("階建").split("地上"))]) 
                        if x.startswith("地下") else int(x.rstrip("階建")))#階数
df["階数"]= df["階数"].replace("1-2階","1.5階")
df["階数"]= df["階数"].replace("5-6階","5.5階")
df["階数"]= df["階数"].apply(lambda x: x.rstrip("階")).astype("float")
#アクセス#
df["アクセス"]= df["アクセス"].apply(lambda x: x.rstrip().split("分 "))
df["アクセス"]= df["アクセス"].apply(lambda x: [item.rstrip("分") if i == (len(x) - 1) else item for i, item in enumerate(x)])
df["アクセス"]= df["アクセス"].apply(lambda x:  [int(acs[-3:].lstrip(" ").lstrip("歩")) for acs in x])
df["アクセス"]= df["アクセス"].apply(lambda x:  len([num for num in x if num <= 10]))
#間取り
df["間取り"]= df["間取り"].replace("ワンルーム","1R")


################データの重複削除################
check_prop =  ["住所","間取り","階数","面積","家賃"] #重複削除に使う物件情報
df['物件番号'] = df.groupby(check_prop).ngroup() #同一物件に同じ番号をナンバリング
df_unique = df.drop_duplicates(subset='物件番号')

#重複削除した物件データを
df_unique = df.drop(["マンション名名寄せ","物件番号"],axis=1)
df_unique.to_csv("suumo_data_modify.csv")

###### Google Spreadsheet にアップロード　########
# スコープの設定
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
# サービスアカウントキーのファイルを指定
creds = Credentials.from_service_account_file('./innate-benefit-407706-54fee2119a6b.json',scopes=scopes)
client = gspread.authorize(creds)

# スプレッドシートを開く
sheet = client.open('suumo_data').sheet1

# データを書き込む
# DataFrameをスプレッドシートに書き込む
set_with_dataframe(sheet, df_unique)

####### データを RDBMSに書き込む　###############

# データベースの接続情報を設定
username = 'root'
password = 'magu01640703'
host = '127.0.0.1'
database = 'suumo_rental_data'

# SQLAlchemyエンジンを作成
engine = create_engine(f"mysql+mysqlconnector://{username}:{password}@{host}/{database}")

# DataFrameをMySQLデータベースに書き込む
df_unique.to_sql('suumo_data', con=engine, if_exists='replace', index=False)