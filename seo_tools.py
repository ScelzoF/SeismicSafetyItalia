
import streamlit as st

def inject_meta_tags():
    st.markdown("""
    <meta name="description" content="Monitoraggio sismico in Campania in tempo reale.">
    <meta name="keywords" content="sisma, campania, terremoti, monitoraggio, realtime, seismic">
    <meta name="author" content="SeismicSafetyItalia">
    """, unsafe_allow_html=True)

def show_robots_txt():
    st.code("""User-agent: *
Disallow:
Sitemap: https://sismocampania.streamlit.app/?page=sitemap
""", language="text")

def show_sitemap_xml():
    st.code("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://sismocampania.streamlit.app</loc>
    <priority>1.00</priority>
  </url>
</urlset>
""", language="xml")
