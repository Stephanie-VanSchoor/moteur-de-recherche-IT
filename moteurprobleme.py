import streamlit as st
import sqlite3
import pandas as pd
import re
import hashlib
from datetime import datetime

# ==================================================
# CONFIGURATION - TOUT EST ICI
# ==================================================

st.set_page_config(
    page_title="Assistant IT - Premium",
    page_icon="💰",
    layout="wide"
)

# ==================================================
# BASE DE DONNÉES
# ==================================================

DB = "assistant.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Table des problèmes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        solution TEXT,
        category TEXT,
        tags TEXT
    )
    ''')
    
    # Table des utilisateurs
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        premium INTEGER DEFAULT 0,
        searches INTEGER DEFAULT 0
    )
    ''')
    
    # Ajouter des données si vide
    cur.execute("SELECT COUNT(*) FROM problems")
    if cur.fetchone()[0] == 0:
        data = [
            ("PC très lent", "L'ordinateur est lent", "Nettoyer le disque, désactiver les programmes au démarrage", "Performance", "lent,pc"),
            ("WiFi ne marche pas", "Pas de connexion WiFi", "Redémarrer la box, vérifier le pilote", "Réseau", "wifi,internet"),
            ("Windows ne démarre pas", "Écran noir au démarrage", "Démarrer en mode sans échec, restaurer le système", "Système", "windows,demarrage"),
            ("Imprimante ne fonctionne pas", "L'imprimante n'imprime pas", "Vérifier l'encre, réinstaller le pilote", "Périphérique", "imprimante"),
            ("Email ne s'envoie pas", "Problème d'envoi d'emails", "Vérifier les paramètres SMTP", "Communication", "email,smtp")
        ]
        cur.executemany(
            "INSERT INTO problems (title, description, solution, category, tags) VALUES (?,?,?,?,?)",
            data
        )
    
    conn.commit()
    conn.close()

# ==================================================
# MOTEUR DE RECHERCHE
# ==================================================

def search_problem(query):
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM problems", conn)
    conn.close()
    
    if df.empty:
        return []
    
    query = query.lower()
    results = []
    
    for _, row in df.iterrows():
        score = 0
        text = f"{row['title']} {row['description']} {row['tags']}".lower()
        
        mots = query.split()
        for mot in mots:
            if len(mot) > 2 and mot in text:
                score += 1
            if mot in row['title'].lower():
                score += 2
        
        if score > 0:
            results.append((dict(row), score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]

# ==================================================
# AUTHENTIFICATION
# ==================================================

def login_user(email, password):
    conn = get_db()
    cur = conn.cursor()
    pwd = hashlib.sha256(password.encode()).hexdigest()
    cur.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, pwd)
    )
    user = cur.fetchone()
    conn.close()
    return user

def create_user(email, password):
    conn = get_db()
    cur = conn.cursor()
    try:
        pwd = hashlib.sha256(password.encode()).hexdigest()
        cur.execute(
            "INSERT INTO users (email, password, premium, searches) VALUES (?, ?, 0, 0)",
            (email, pwd)
        )
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def update_premium(email):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET premium = 1 WHERE email = ?",
        (email,)
    )
    conn.commit()
    conn.close()

# ==================================================
# INTERFACE - MONÉTISATION ÉVIDENTE
# ==================================================

def main():
    # Initialisation
    init_db()
    
    # Session
    if "user" not in st.session_state:
        st.session_state.user = None
    if "premium" not in st.session_state:
        st.session_state.premium = False
    if "searches" not in st.session_state:
        st.session_state.searches = 0
    if "page" not in st.session_state:
        st.session_state.page = "accueil"
    
    # ==================================================
    # SIDEBAR - AUTH ET STATUT
    # ==================================================
    
    with st.sidebar:
        st.markdown("## 👤 Compte")
        
        if st.session_state.user:
            # ==========================================
            # UTILISATEUR CONNECTÉ - STATUT PREMIUM
            # ==========================================
            
            st.success(f"✅ {st.session_state.user}")
            
            # STATUS PREMIUM TRÈS VISIBLE
            if st.session_state.premium:
                st.markdown("""
                <div style='background: #FFD700; padding: 15px; border-radius: 10px; text-align: center;'>
                    <h2 style='color: #000; margin: 0;'>⭐ PREMIUM ⭐</h2>
                    <p style='color: #000; margin: 0;'>Recherches illimitées</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # COMPTEUR POUR GRATUIT
                st.markdown("""
                <div style='background: #FF6B6B; padding: 15px; border-radius: 10px; text-align: center;'>
                    <p style='color: #fff; margin: 0;'>🆓 GRATUIT</p>
                </div>
                """, unsafe_allow_html=True)
                
                restant = max(0, 3 - st.session_state.searches)
                st.progress(st.session_state.searches / 3)
                st.warning(f"⚠️ {restant} recherches restantes")
                
                if restant == 0:
                    st.error("🚨 PLUS DE RECHERCHES !")
            
            # BOUTON PREMIUM
            if not st.session_state.premium:
                if st.button("⭐ PASSER PREMIUM ⭐", type="primary", use_container_width=True):
                    st.session_state.page = "premium"
                    st.rerun()
            
            if st.button("🚪 Déconnexion", use_container_width=True):
                st.session_state.user = None
                st.session_state.premium = False
                st.session_state.searches = 0
                st.rerun()
        
        else:
            # ==========================================
            # PAS CONNECTÉ
            # ==========================================
            
            tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
            
            with tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Mot de passe", type="password", key="login_pass")
                if st.button("Se connecter", use_container_width=True):
                    user = login_user(email, password)
                    if user:
                        st.session_state.user = email
                        st.session_state.premium = bool(user["premium"])
                        st.session_state.searches = user["searches"] if not user["premium"] else 0
                        st.success("✅ Connecté !")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")
            
            with tab2:
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Mot de passe", type="password", key="register_pass")
                if st.button("Créer un compte", use_container_width=True):
                    if create_user(email, password):
                        st.success("✅ Compte créé ! Connectez-vous")
                    else:
                        st.error("❌ Email déjà utilisé")
        
        # ==========================================
        # MENU DE NAVIGATION
        # ==========================================
        
        st.markdown("---")
        menu = ["🏠 Accueil"]
        if st.session_state.user and not st.session_state.premium:
            menu.append("⭐ Premium")
        if st.session_state.user and st.session_state.premium:
            menu.append("📊 Statistiques")
        
        if menu:
            st.session_state.page = st.radio("Navigation", menu)
    
    # ==================================================
    # PAGE PREMIUM - MONÉTISATION
    # ==================================================
    
    if st.session_state.page == "⭐ Premium":
        st.markdown("# 💰 OFFRE PREMIUM")
        st.markdown("---")
        
        # BANNIÈRE
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 40px; border-radius: 20px; text-align: center;'>
            <h1 style='color: white; font-size: 48px;'>🔥 OFFRE SPÉCIALE 🔥</h1>
            <h2 style='color: #FFD700; font-size: 36px;'>-50% sur Premium</h2>
            <h3 style='color: white; font-size: 24px;'>Seulement 4.95€/mois</h3>
            <p style='color: #FFD700; font-size: 18px;'>Code: PREMIUM50</p>
        </div>
        """, unsafe_allow_html=True)
        
        # COMPARAISON
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🆓 GRATUIT
            **0€**
            
            ❌ 3 recherches par jour  
            ❌ Diagnostics basiques  
            ❌ Pas d'export  
            ❌ Support limité  
            ❌ Publicités
            """)
        
        with col2:
            st.markdown("""
            ### ⭐ PREMIUM
            **9.90€/mois**
            
            ✅ Recherches ILLIMITÉES  
            ✅ Diagnostics avancés  
            ✅ Export PDF  
            ✅ Support prioritaire  
            ✅ Pas de publicités  
            ✅ Historique illimité
            """)
        
        # BOUTON D'ACHAT
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⭐ PASSER À PREMIUM ⭐", type="primary", use_container_width=True):
                if st.session_state.user:
                    update_premium(st.session_state.user)
                    st.session_state.premium = True
                    st.success("🎉 Félicitations ! Vous êtes maintenant Premium !")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("Connectez-vous d'abord !")
        
        return
    
    # ==================================================
    # PAGE STATISTIQUES (PREMIUM)
    # ==================================================
    
    if st.session_state.page == "📊 Statistiques":
        st.markdown("# 📊 Vos Statistiques")
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recherches totales", st.session_state.searches)
        with col2:
            st.metric("Statut", "⭐ Premium")
        with col3:
            st.metric("Problèmes résolus", "5")
        
        st.success("⭐ Vous avez accès à toutes les fonctionnalités Premium !")
        return
    
    # ==================================================
    # PAGE ACCUEIL - RECHERCHE
    # ==================================================
    
    st.markdown("# 🤖 Assistant Dépannage IT")
    st.markdown("Décrivez votre problème informatique")
    
    # ==========================================
    # BANNIÈRE PREMIUM (HAUT DE PAGE)
    # ==========================================
    
    if st.session_state.user and not st.session_state.premium:
        st.warning("⚠️ Version gratuite - 3 recherches maximum")
        if st.button("⭐ PASSER PREMIUM ⭐", type="primary"):
            st.session_state.page = "premium"
            st.rerun()
    
    if st.session_state.premium:
        st.success("⭐ Mode Premium - Recherches illimitées !")
    
    # ==========================================
    # ZONE DE RECHERCHE
    # ==========================================
    
    question = st.text_area(
        "Votre problème :",
        height=100,
        placeholder="Ex: mon PC est très lent, le wifi ne marche pas..."
    )
    
    # ==========================================
    # BOUTON DE RECHERCHE AVEC VÉRIFICATION
    # ==========================================
    
    if st.button("🔍 Rechercher", type="primary", use_container_width=True):
        # VÉRIFICATION CONNEXION
        if not st.session_state.user:
            st.error("❌ Connectez-vous pour faire une recherche")
        
        # VÉRIFICATION PREMIUM
        elif not st.session_state.premium and st.session_state.searches >= 3:
            st.error("🚨 LIMITE GRATUITE ATTEINTE ! (3/3)")
            st.info("Passez Premium pour des recherches illimitées")
            if st.button("⭐ PASSER PREMIUM", type="primary"):
                st.session_state.page = "premium"
                st.rerun()
        
        # RECHERCHE
        elif question.strip():
            with st.spinner("Recherche en cours..."):
                # Incrémenter le compteur
                if not st.session_state.premium:
                    st.session_state.searches += 1
                    # Mettre à jour dans la base
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE users SET searches = ? WHERE email = ?",
                        (st.session_state.searches, st.session_state.user)
                    )
                    conn.commit()
                    conn.close()
                
                results = search_problem(question)
                
                if results:
                    st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
                    
                    for problem, score in results:
                        with st.expander(f"📌 {problem['title']} (Pertinence: {score})"):
                            st.markdown(f"**Description:** {problem['description']}")
                            st.markdown(f"**Solution:** {problem['solution']}")
                            st.markdown(f"**Catégorie:** {problem['category']}")
                            st.markdown(f"**Tags:** {problem['tags']}")
                            
                            # Export PDF pour Premium uniquement
                            if st.session_state.premium:
                                if st.button(f"📄 Exporter PDF", key=f"pdf_{problem['id']}"):
                                    st.info("PDF exporté ! (simulation)")
                else:
                    st.warning("Aucun résultat trouvé")
        
        else:
            st.warning("Décrivez votre problème")
    
    # ==========================================
    # LISTE DES PROBLÈMES POPULAIRES
    # ==========================================
    
    with st.expander("📚 Problèmes courants"):
        conn = get_db()
        df = pd.read_sql_query("SELECT title, category FROM problems LIMIT 5", conn)
        conn.close()
        
        for _, row in df.iterrows():
            st.markdown(f"- **{row['title']}** ({row['category']})")
    
    # ==========================================
    # FOOTER
    # ==========================================
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <small>Assistant IT - Version 2.0</small>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# LANCEMENT
# ==================================================

if __name__ == "__main__":
    main()
 
           
