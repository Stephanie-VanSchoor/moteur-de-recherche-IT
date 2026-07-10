import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime, timedelta
import stripe  # Ajouter : pip install stripe

# ==================================================
# CONFIGURATION MONÉTISATION
# ==================================================

# Prix (en centimes pour Stripe)
PRIX = {
    "pro_mensuel": 990,  # 9.90€
    "pro_annuel": 7900,  # 79€
    "business_mensuel": 2990,  # 29.90€
    "business_annuel": 24900,  # 249€
    "pack_50": 1500,  # 15€
    "pack_100": 2500,  # 25€
    "consultation": 1990,  # 19.90€
}

# Limites
LIMITES = {
    "gratuit": {"recherches": 5, "historique": 10, "export": False},
    "pro": {"recherches": float('inf'), "historique": float('inf'), "export": True},
    "business": {"recherches": float('inf'), "historique": float('inf'), "export": True},
}

# Configuration Stripe (à remplacer avec vos clés)
STRIPE_PUBLIC_KEY = "pk_test_..."
STRIPE_SECRET_KEY = "sk_test_..."

# ==================================================
# PAGE DE MONÉTISATION
# ==================================================

def page_pricing():
    """Affiche la page des offres"""
    
    st.markdown("## 💰 Offres et Tarifs")
    st.markdown("Choisissez l'offre qui vous convient")
    
    # Layout en colonnes
    col1, col2, col3 = st.columns(3)
    
    # Offre Gratuite
    with col1:
        st.markdown("""
        ### 🆓 Gratuit
        **0€ / mois**
        
        ✅ 5 recherches/jour  
        ✅ Diagnostics basiques  
        ✅ Procédures standards  
        ✅ Historique 10 jours  
        ❌ Pas d'export PDF  
        ❌ Pas de support prioritaire
        """)
        if st.button("🔄 Actuel", key="free_btn", disabled=True):
            pass
    
    # Offre Pro
    with col2:
        st.markdown("""
        ### 🚀 Pro
        **9.90€ / mois**
        ou **79€ / an**
        
        ✅ Recherches illimitées  
        ✅ Diagnostics avancés  
        ✅ Procédures détaillées  
        ✅ Historique illimité  
        ✅ Export PDF  
        ✅ Support prioritaire  
        ✅ Pas de publicité
        """)
        
        col_pro1, col_pro2 = st.columns(2)
        with col_pro1:
            if st.button("📆 Mensuel", key="pro_month"):
                st.session_state.checkout = "pro_mensuel"
                st.rerun()
        with col_pro2:
            if st.button("📅 Annuel (-30%)", key="pro_year"):
                st.session_state.checkout = "pro_annuel"
                st.rerun()
    
    # Offre Business
    with col3:
        st.markdown("""
        ### 🏢 Business
        **29.90€ / mois**
        ou **249€ / an**
        
        ✅ Tout Pro inclus  
        ✅ Accès API  
        ✅ 5 comptes utilisateurs  
        ✅ Statistiques détaillées  
        ✅ Intégration personnalisée  
        ✅ Support 24/7  
        ✅ SLA Garanti
        """)
        
        col_bus1, col_bus2 = st.columns(2)
        with col_bus1:
            if st.button("📆 Mensuel", key="bus_month"):
                st.session_state.checkout = "business_mensuel"
                st.rerun()
        with col_bus2:
            if st.button("📅 Annuel (-25%)", key="bus_year"):
                st.session_state.checkout = "business_annuel"
                st.rerun()

    # Offres spéciales
    st.markdown("---")
    st.markdown("### 🎁 Offres Spéciales")
    
    col_offre1, col_offre2, col_offre3 = st.columns(3)
    
    with col_offre1:
        st.info("""
        #### 🔥 Offre Launch
        -50% sur Pro pendant 3 mois
        
        **4.95€/mois**
        
        Code : `ITLAUNCH50`
        """)
    
    with col_offre2:
        st.success("""
        #### 🎓 Offre Étudiant
        Pro à prix réduit
        
        **5.90€/mois**
        
        Justificatif requis
        """)
    
    with col_offre3:
        st.warning("""
        #### 💼 Packs à la demande
        - 50 recherches : 15€
        - 100 recherches : 25€
        - Consultation : 19.90€
        """)

# ==================================================
# INTÉGRATION STRIPE (Paiement)
# ==================================================

def stripe_checkout(plan, email):
    """Crée une session de paiement Stripe"""
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        # Créer la session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Assistant IT Pro - {plan}',
                    },
                    'unit_amount': PRIX[plan],
                },
                'quantity': 1,
            }],
            mode='subscription' if 'mensuel' in plan or 'annuel' in plan else 'payment',
            success_url='https://votre-site.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://votre-site.com/cancel',
            customer_email=email,
        )
        return session.url
    except Exception as e:
        st.error(f"Erreur de paiement : {e}")
        return None

# ==================================================
# COMPTEUR ET LIMITES
# ==================================================

def verifier_limites():
    """Vérifie si l'utilisateur a dépassé les limites"""
    if not st.session_state.user:
        return True  # Non connecté = limité
    
    plan = st.session_state.get("plan", "gratuit")
    limite = LIMITES[plan]["recherches"]
    
    if limite == float('inf'):
        return True
    
    return st.session_state.recherches < limite

def afficher_compteur():
    """Affiche le compteur de recherches restantes"""
    if not st.session_state.user:
        return
    
    plan = st.session_state.get("plan", "gratuit")
    limite = LIMITES[plan]["recherches"]
    
    if limite == float('inf'):
        st.sidebar.success("♾️ Recherches illimitées")
    else:
        restant = max(0, limite - st.session_state.recherches)
        st.sidebar.info(f"📊 Restant : {restant} recherches aujourd'hui")
        
        if restant <= 2:
            st.sidebar.warning("⚠️ Plus que quelques recherches !")
            if st.sidebar.button("🚀 Passer Pro"):
                st.session_state.page = "pricing"
                st.rerun()

# ==================================================
# MODIFICATION DE LA FONCTION MAIN
# ==================================================

def main():
    """Fonction principale avec monétisation"""
    
    init_session()
    creer_base()
    remplir_base()
    
    # Sidebar avec authentification
    authentification()
    afficher_profil()
    afficher_compteur()  # Afficher le compteur
    
    # Navigation
    menu = ["🏠 Accueil", "💰 Tarifs", "📊 Statistiques"]
    if st.session_state.user:
        menu.append("👤 Mon Compte")
    
    choice = st.sidebar.radio("Navigation", menu)
    
    if choice == "💰 Tarifs":
        page_pricing()
        return
    
    if choice == "📊 Statistiques" and st.session_state.user:
        # Afficher les statistiques
        st.markdown("## 📊 Vos Statistiques")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recherches totales", st.session_state.recherches)
        with col2:
            st.metric("Problèmes résolus", st.session_state.get("resolus", 0))
        with col3:
            st.metric("Temps économisé", "2h 15min")
        
        # Graphique simple (à améliorer)
        st.line_chart([1, 2, 3, 5, 8, 13])  # Exemple
        return
    
    # Page principale avec recherche
    st.markdown("# 🤖 Assistant Dépannage IT")
    
    # Vérifier les limites avant de permettre la recherche
    if not verifier_limites():
        st.warning("""
        ⚠️ **Limite gratuite atteinte !**
        
        Passez à Pro pour continuer :
        - Recherches illimitées
        - Diagnostics avancés
        - Export PDF
        """)
        if st.button("🚀 Passer Pro maintenant"):
            st.session_state.page = "pricing"
            st.rerun()
        return
    
    # Reste de votre code de recherche...
    # ... (votre code existant)
