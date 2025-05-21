from scrapy import Selector
from urllib.request import urlopen
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Trustpilot Review Analyzer", layout="wide")
st.markdown("""
<h1 style='color:#FFA500; text-align:center;'>Trustpilot Company Review Scraper & Analyzer by Industry</h1>

<p style='font-size:16px; text-align:center;'>
🔗 <b>Enter a Trustpilot search results URL</b> for a specific business category or keyword. <br>
📄 The app will detect the <b>number of available pages</b>, and you can choose how many pages to scrape. <br>
📊 It will then extract detailed information about each listed company — including reviews, services, location, and contact data — and display it in a clean, downloadable table.
</p>

<p style='font-size:14px; text-align:center; color:gray;'>
You can use the extracted data to explore trends in customer reviews by location, service type, and overall trust score.
</p>
""", unsafe_allow_html=True)
st.image('Screenshot 2025-05-16 210109.png')
z=False
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

            file.append({'company_name':f'{name}','count_reviews':f'{num_revew}','review':f'{revew}'\
                         ,'servesis':f'{servesis}','location':f'{loc}','phone_number':f'{phone}',\
                            'email':f'{email}','website':f'{website}'})
    return pd.DataFrame(file)
def clean_df(df):
    df.columns=df.columns.map(lambda col:col.strip())
    df['count_reviews']=df['count_reviews'].str.extract(r'(\d+)')
    df['country']=df['location'].str.split('|').apply(lambda x:x[-1])
    df.count_reviews=df.count_reviews.fillna(0).astype(int)
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
st.markdown("#### 🔍 Enter Trustpilot search URL")
company_url_input = st.text_input(label="", placeholder="Paste the Trustpilot search results URL here...")

start_scrape = False  

if company_url_input:
    if st.button("🔎 Search"):
        st.session_state.company_url = company_url_input
        start_scrape = True
if st.session_state.company_url or start_scrape :
    sel=get_html(st.session_state.company_url)
    try:
        n=sel.xpath('//a[contains(@name,"pagination-button-last")]//text()').extract_first()
        num_pages=int(n)
        st.header(f'you have {num_pages} pages  ')
        st.number_input('',placeholder=f'Enter number of page to scrap.. ',min_value=1,max_value=num_pages,value=None,step=1,key='number_input')
    except Exception as e:
        st.error('❌ No result pages found or this page not contain companys to scrape. Please make sure the URL is valid.')
    
if st.session_state.number_input:
    if st.button("Run"):
        st.session_state.run_scrape = True
    
    if st.session_state.run_scrape:
        with st.spinner("Pleas Waite..."):
            try:
                z=True
                x = scrape_trustpilot(st.session_state.company_url,st.session_state.number_input)
                df=clean_df(x)
                st.success("✅ Done Successfuly!")

                st.subheader("📋 The Extracting Data:")
                st.dataframe(df)

                st.download_button("⬇️  Download The Data", 
                                data=df.to_csv(index=False), 
                                file_name="trustpilot_reviews.csv", 
                                mime="text/csv")
                
                
            except Exception as e:
                z=False
                st.error(f"حدث خطأ أثناء السحب: {e}")
if z:
    st.markdown("""<h3 style='color:#FFA500; text-align:center;'>Top 8 companys per count_reviws </h3>""", unsafe_allow_html=True)
    dfx=df.sort_values('count_reviews',ascending=False).head(8)
    fig=px.bar(data_frame=dfx,x='company_name',y='count_reviews')
    st.plotly_chart(fig)