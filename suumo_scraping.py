# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 15:41:47 2023

@author: tyoka
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep

#東京都の　文京区に絞って物件表示
#url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13105&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="
#東京23区全部
url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&sc=13106&sc=13107&sc=13108&sc=13118&sc=13121&sc=13122&sc=13123&sc=13109&sc=13110&sc=13111&sc=13112&sc=13114&sc=13115&sc=13120&sc=13116&sc=13117&sc=13119&cb=0.0&ct=9999999&mb=0&mt=9999999&et=9999999&cn=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&sngz=&po1=25&pc=50"

#情報格納用の　DFを作成する
#columns_prop = ["物件名", "住所","間取り","家賃","階数"]
columns_prop = ["マンション名", "住所","アクセス","アクセス1","アクセス2","アクセス3","築年数","構造","階数","間取り","面積","家賃","管理費"]
df = pd.DataFrame(columns= columns_prop)

n=0

page_num = 2525

# 1ページから114ページまでスクレイピング
for page_num in range(1, page_num):
    # ページ番号をURLに組み込む
    url = f"{url}&page={page_num}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sleep(1)

    #同一ページ内の各物件の情報をループ
    for property_row in soup.find_all('div', class_='cassetteitem'):
        property_name = property_row.find('div', class_='cassetteitem_content-title').text.strip()  # 物件名
        address = property_row.find('li', class_='cassetteitem_detail-col1').text.strip()  # 住所
        access = ' '.join([div.text.strip() for div in property_row.find_all('div', class_='cassetteitem_detail-text')])  # アクセス
        # アクセス分解
        access1 = property_row.find_all('div', class_='cassetteitem_detail-text')[0].text
        access2 = property_row.find_all('div', class_='cassetteitem_detail-text')[1].text
        access3 = property_row.find_all('div', class_='cassetteitem_detail-text')[2].text
        age = property_row.find('li', class_='cassetteitem_detail-col3').div.text.strip()  # 築年数
        structure = [div.text.strip() for div in property_row.find('li', class_='cassetteitem_detail-col3').find_all('div')][1]
        
        
        # 同じ物件の異なる部屋情報を取得
        #for room_row in property_row.find_all('tbody')[0].find_all('tr'):
        for room_row in property_row.find_all('tbody'):
            floor = room_row.find_all('td')[2].text.strip()  # 階数
            layout = room_row.find_all('td')[5].text.strip().split()[0]  # 間取り
            size = room_row.find_all('td')[5].text.strip().split()[1]   # 広さ
            rent = room_row.find_all('td')[3].text.strip().split()[0]  # 家賃
            management_fee = room_row.find_all('td')[3].text.strip().split()[1] #管理費            
            #management_fee = room_row.find_all('td')[4].text.strip() if room_row.find_all('td')[4].text.strip() != '-' else '0円'  # 管理費
            
            # 新しい行を作成してまとめ用のDataFrameに追加
            data= [property_name, address,access,access1,access2,access3,age,structure,floor,layout,size,rent,management_fee]
            tmp = pd.DataFrame([data],columns=columns_prop)
            df = pd.concat([df, tmp], ignore_index=True)

    n+=1
    print(n)
       
    
# DataFrameをCSVファイルに出力
df.to_csv('suumo_data_all.csv' , index=False, encoding='utf-8-sig')