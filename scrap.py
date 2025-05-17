from scrapy import Selector
from urllib.request import urlopen
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Trustpilot Review Analyzer", layout="wide")
html_title = """<h1 style="color:orange;text-align:center;"> Trustpilot Review Scraper & Analyzer </h1>"""
st.markdown(html_title, unsafe_allow_html=True)
st.image('Screenshot 2025-05-16 210109.png')
st.header('showe data')

def get_html(url):
    clint=urlopen(url)
    html=clint.read()
    clint.close()
    return Selector(text=html)

@st.cache_data(show_spinner=False)
def scrape_trustpilot(url,num_p):
    file=[]
    base='https://www.trustpilot.com'
    sel=get_html(url)
    for j in range(num_p):
        next_page=sel.xpath('//a[contains(@name,"pagination-button-next")]//@href').extract_first()
        if j==0:
            ref=sel.xpath('//div[contains(@class,"styles_wrapper__Jg8fe")]//@href').extract()
        else:
            url_pages=f'{base}{next_page}'
            sel=get_html(url_pages)
            ref=sel.xpath('//div[contains(@class,"styles_wrapper__Jg8fe")]//@href').extract()
        for i in ref:
            url_itme=f'{base}{i}'
            product=get_html(url_itme)

            name=product.xpath('//h1//text()').extract_first()
            num_revew=product.xpath('//span[contains(@class,"typography_body-l")]//text()').extract()
            if len(num_revew)>0:
                num_revew=' '.join(num_revew).replace(',','')
            revew=product.xpath('//div[contains(@class,"styles_rating__kLMDv styles")]//text()').extract_first()
            servesis=product.xpath('//ol[contains(@class,"styles_flexRow__eqdt3")]//text()').extract()
            if len(servesis)>0:
                servesis="|".join(servesis).replace('"',' ')
            loc=product.xpath('//li[.//path[contains(@d, "M3.404 1.904A6.5")]]//text()').extract()
            if len(loc)>0:
                loc=loc[0].replace(',','|')
            phone=product.xpath('//li[.//path[contains(@d, "m4.622.933")]]//text()').extract_first()
            email=product.xpath('//li[.//path[contains(@d, "2.5h16v11H0v-11Zm1.789")]]//text()').extract_first()
            website=product.xpath('//li[.//path[contains(@d, "M10.694 1.537c.217")]]//text()').extract_first()

            file.append({'company_name':f'\"{name}\"','num_reviews':f'\"{num_revew}\"','review':f'\"{revew}\"'\
                         ,'servesis':f'\"{servesis}\"','location':f'\"{loc}\"','phone_number':f'\"{phone}\"',\
                            'email':f'\"{email}\"','website':f'\"{website}\"'})
    return pd.DataFrame(file)
def clean_df(df):
    df.columns=df.columns.map(lambda col:col.strip())
    df['num_reviews']=df['num_reviews'].str.extract(r'(\d+)')
    df['country']=df['location'].str.split('|').apply(lambda x:x[-1])
    for col in df.select_dtypes(include='object').columns:
        df[col]=df[col].str.replace('\"','')
    df.num_reviews=df.num_reviews.fillna(0).astype(int)
    df.review=df.review.replace({'None':np.nan}).astype(float)
    df.servesis=df.servesis.replace({' [] ':np.nan})
    df['location']=df['location'].replace({'[]':np.nan}) 
    df['phone_number']=df['phone_number'].replace({' None ':np.nan})
    df['email']=df['email'].replace({' None ':np.nan})
    df['country']=df['country'].replace({'[]':np.nan}).str.strip()
    df.drop_duplicates(inplace=True)
    return df

if "run_scrape" not in st.session_state:
    st.session_state.run_scrape = False
if 'number_input' not in st.session_state:
    st.session_state.number_input = None
if 'company_url' not in st.session_state:
    st.session_state.company_url = None

st.session_state.company_url = st.text_input("Input url for this site Trustpilot:")
if st.session_state.company_url :
    sel=get_html(st.session_state.company_url)
    num_pages=int(sel.xpath('//a[contains(@name,"pagination-button-last")]//text()').extract_first())
    st.number_input(f'you have {num_pages} Enter number of page to scrap :',min_value=1,max_value=num_pages,value=None,step=1,key='number_input')
if st.session_state.number_input:
    if st.button("ابدأ السحب"):
        st.session_state.run_scrape = True

    if st.session_state.run_scrape:
        with st.spinner("جاري استخراج البيانات من Trustpilot..."):
            try:
                x = scrape_trustpilot(st.session_state.company_url,st.session_state.number_input)
                df=clean_df(x)
                st.success("✅ تم سحب البيانات بنجاح!")

                st.subheader("📋 البيانات المستخرجة:")
                st.dataframe(df)

                st.download_button("⬇️ تحميل البيانات", 
                                data=df.to_csv(index=False), 
                                file_name="trustpilot_reviews.csv", 
                                mime="text/csv")

                # تحليل بسيط
            except Exception as e:
                st.error(f"حدث خطأ أثناء السحب: {e}")
