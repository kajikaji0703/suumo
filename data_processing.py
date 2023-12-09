# -*- coding: utf-8 -*-
"""
Created on Sat Dec  9 13:50:42 2023

@author: Hiroshi_Kajiyama
"""

import pandas as pd

df = pd.read_csv("suumo_data.csv")

#　各物件　の特性の値に　どのような種類の値が含まれるのかを確認し、データクレンジングの必要性、やり方を検討する
columns_prop = ["物件名", "住所","アクセス","築年数","構造","階数","間取り","面積","家賃","管理費"]
prop_list = []
for prop in  columns_prop:
    tmp =pd.Series(name=prop,data=df[prop].unique())
    prop_list.append(tmp)
    
"""
各物件情報に含まれる値を調べてた結果は以下
物件名：　物件名称の代わりに　”都営大江戸線 飯田橋駅 15階建 築19年”のように　物件のプロパティを並べて記載してるものがある
⇒物件名に　物件のプロパティがあてられてるものが、実際は既存の物件名があてられるものがないか調べる
アクセス：　いくつの駅にアクセス可能か　カウントする
住所：見た限り重複らしきもの無し
築年数：新築だけ　データフォーマット違う⇒築0年に変更
構造：地下の階層がついているものもある⇒　地下の階層と地上の階層を足す
階数：　1-2階だけフォーマット違う　⇒ 1.5階に変更
間取り：　間取りを分解して管理？
面積：　これは全て同じフォーマット　
家賃：　これは全て同じフォーマット
管理費：　"-" だけ異なるフォーマット　⇒　0円に変更
"""

#物件名を名寄せする
name_list=[]
for  name  in   prop_list[0]:
    tmp = df[df["物件名"]==name]
    name_list.append(tmp)

#住所で名寄せする
#住所が　同じで　違名のものは　実際は　同じ物件とする ⇒　同じ住所で違う物件がある？住所だけでは名寄せできない。築年数、構造は少なくとも見ないと
address_list = []
dup_list =[]
for  address  in   prop_list[1]:
    tmp = df[df["住所"]==address]
    address_list.append(tmp)
    tmp_dup= tmp["物件名"].unique()
    if len(tmp_dup) > 1: 
        tmp_dup = sorted(tmp_dup, key=len, reverse=False)
        dup_list.append(tmp_dup) #物件名の重複リスト

#データのクレンジング

#データの重複削除
check_prop =  ["住所","間取り","階数","面積","家賃"]
df['物件番号'] = df.groupby(check_prop).ngroup()

#面積
df["面積"]= df["面積"].apply(lambda x: x.rstrip("m2")).astype("float")
#家賃
df["家賃"]= df["家賃"].apply(lambda x: x.rstrip("万円")).astype("float")
#管理費
df["管理費"]= df["管理費"].replace("-","0")
df["管理費"]= df["管理費"].apply(lambda x: x.rstrip("円")).astype("int")
#築年数
df["築年数"]= df["築年数"].replace("新築","築0年")
df["築年数"]= df["築年数"].apply(lambda x: x.replace("築","").replace("年","")).astype("int")
#構造
df["構造"]= df["構造"].apply(lambda x: x.replace("築","").replace("年","")).astype("int")

"""
def data_preprocessing(df, prop):
    if prop = 
    
"""



