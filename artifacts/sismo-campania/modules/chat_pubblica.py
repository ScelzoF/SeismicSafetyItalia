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
                raw_ts = r.get("inviato_il", "")
                try:
                    ts_fmt = datetime.fromisoformat(raw_ts.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    ts_fmt = raw_ts[:16].replace('T', ' ') if raw_ts else "🕒"
                st.markdown(f"**{r['utente']}** _({ts_fmt})_: {r['messaggio']}")
    except Exception as e:
        st.error(f"Errore nel caricamento messaggi: {e}")