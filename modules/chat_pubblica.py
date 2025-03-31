def chat_pubblica(sb_client):
    import streamlit as st
    from datetime import datetime
    import pytz

    st.title("💬 Chat Pubblica")

    user = st.text_input("👤 Il tuo nome", max_chars=20)
    msg = st.text_area("✍️ Scrivi un messaggio")

    if st.button("📨 Invia messaggio"):
        if user.strip() == "" or msg.strip() == "":
            st.warning("Inserisci nome e messaggio.")
        else:
            try:
                rome_time = datetime.now(pytz.timezone("Europe/Rome")).isoformat()
                data = {
                    "utente": user.strip(),
                    "messaggio": msg.strip(),
                    "inviato_il": rome_time
                }
                res = sb_client.table("chat").insert(data).execute()
                if res.data:
                    st.success("Messaggio inviato!")
                    st.rerun()
                else:
                    st.error("Errore durante l'invio del messaggio.")
            except Exception as e:
                st.error(f"Errore: {e}")

    st.markdown("---")
    st.subheader("📜 Messaggi recenti:")

    try:
        result = sb_client.table("chat").select("*").order("inviato_il", desc=True).limit(30).execute()
        chat_data = result.data
        if not chat_data:
            st.info("Nessun messaggio ancora.")
        else:
            for r in reversed(chat_data):
                timestamp = r.get("inviato_il", "🕒")
                st.markdown(f"**{r['utente']}** _({timestamp[:19].replace('T',' ')})_: {r['messaggio']}")
    except Exception as e:
        st.error(f"Errore nel caricamento messaggi: {e}")