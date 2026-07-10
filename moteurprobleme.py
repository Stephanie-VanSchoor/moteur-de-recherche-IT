import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime, date
import hashlib
import random
import string

# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Assistant IT Pro - Premium",
    page_icon="💻",
    layout="wide"
)

DB = "assistant_it_ia.db"

# ==================================================
# LICENCE - 2026
# ==================================================

LICENCE = """
LICENCE - ASSISTANT IT PRO

© 2026 IT Pro Solutions - Tous droits reserves

Cette application est protegee par les lois sur le droit d'auteur.
Toute reproduction, distribution ou modification non autorisee
est strictement interdite.

Version : 4.0 - Plus de 120 diagnostics
Proprietaire : IT Pro Solutions
Email : tech.contactinformatique@proton.me
Date : 10/07/2026
"""

# ==================================================
# INITIALISATION SESSION
# ==================================================

if "user" not in st.session_state:
    st.session_state.user = None
if "premium" not in st.session_state:
    st.session_state.premium = False
if "plan" not in st.session_state:
    st.session_state.plan = "gratuit"
if "recherches" not in st.session_state:
    st.session_state.recherches = 0
if "recherches_jour" not in st.session_state:
    st.session_state.recherches_jour = 0
if "date_recherche" not in st.session_state:
    st.session_state.date_recherche = date.today()
if "page" not in st.session_state:
    st.session_state.page = "accueil"
if "moteur" not in st.session_state:
    st.session_state.moteur = None
if "montant_virement" not in st.session_state:
    st.session_state.montant_virement = 0
if "offre_virement" not in st.session_state:
    st.session_state.offre_virement = ""
if "plan_virement" not in st.session_state:
    st.session_state.plan_virement = ""
if "ref_virement" not in st.session_state:
    st.session_state.ref_virement = ""

# ==================================================
# CONFIGURATION DES OFFRES (3 FORMULES)
# ==================================================

OFFRES = {
    "gratuit": {
        "nom": "Gratuit",
        "prix": "0€",
        "prix_an": "0€",
        "couleur": "🆓",
        "badge": "GRATUIT",
        "recherches": 3,
        "features": [
            "3 recherches par jour",
            "Diagnostics basiques",
            "70+ diagnostics",
            "Pas d'export PDF",
            "Pas de support prioritaire"
        ]
    },
    "pro": {
        "nom": "Pro",
        "prix": "9.90€/mois",
        "prix_an": "79€/an",
        "couleur": "🚀",
        "badge": "PRO",
        "recherches": 999,
        "features": [
            "Recherches illimitees",
            "Diagnostics avances",
            "120+ diagnostics",
            "Reponses detaillees",
            "Export PDF",
            "Support prioritaire",
            "Statistiques avancees"
        ]
    },
    "business": {
        "nom": "Business",
        "prix": "29.90€/mois",
        "prix_an": "249€/an",
        "couleur": "🏢",
        "badge": "BUSINESS",
        "recherches": 9999,
        "features": [
            "Recherches illimitees",
            "Diagnostics experts",
            "120+ diagnostics",
            "Reponses personnalisees",
            "Export PDF/Word",
            "Support 24/7",
            "Statistiques avancees",
            "Acces API",
            "5 comptes inclus"
        ]
    }
}


# ==================================================
# BASE DE DONNEES
# ==================================================

def connexion_db():
    return sqlite3.connect(DB)


def creer_base():
    conn = connexion_db()
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS pannes
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    titre
                    TEXT,
                    description
                    TEXT,
                    diagnostic
                    TEXT,
                    procedure
                    TEXT,
                    questions
                    TEXT,
                    categorie
                    TEXT,
                    niveau
                    INTEGER,
                    tags
                    TEXT
                )
                """)

    cur.execute("""
                CREATE TABLE IF NOT EXISTS utilisateurs
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    email
                    TEXT
                    UNIQUE,
                    password
                    TEXT,
                    plan
                    TEXT
                    DEFAULT
                    'gratuit',
                    premium
                    INTEGER
                    DEFAULT
                    0,
                    recherches
                    INTEGER
                    DEFAULT
                    0,
                    date_inscription
                    TEXT
                )
                """)

    conn.commit()
    conn.close()


def remplir_base():
    conn = connexion_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM pannes")
    if cur.fetchone()[0] == 0:
        donnees = [
            # Windows
            ("Windows ne demarre pas", "Ecran noir au demarrage de Windows",
             "Fichier systeme endommage ou disque defaillant",
             "1- Demarrer en mode sans echec (F8)\n2- Restaurer le systeme\n3- Reparer avec le CD d'installation",
             "Avez-vous installe une mise a jour recemment ?", "Windows", 4, "demarrage,ecran-noir,windows"),
            ("Windows tres lent", "Windows rame, programmes lents", "Manque de RAM, disque plein, trop de programmes",
             "1- Gestionnaire des taches\n2- Nettoyer le disque\n3- Desactiver les programmes au demarrage",
             "Depuis quand le PC est-il lent ?", "Windows", 2, "lent,performance,windows"),
            ("Erreur BSOD Windows", "Ecran bleu de la mort sur Windows", "Pilote defectueux ou materiel incompatible",
             "1- Noter le code d'erreur\n2- Demarrer en mode sans echec\n3- Mettre a jour les pilotes",
             "Quel est le code d'erreur ?", "Windows", 5, "bsod,ecran-bleu,windows"),

            # Linux
            ("Ubuntu ne demarre pas", "Ubuntu reste bloque au demarrage", "Probleme de noyau ou de GRUB",
             "1- Demarrer en mode recovery\n2- Reparer GRUB\n3- Reinstaller le noyau",
             "Quelle version d'Ubuntu ?", "Linux", 4, "ubuntu,demarrage,linux"),
            ("Linux tres lent", "Linux rame, systeme lent", "Swap plein ou processus en arriere-plan",
             "1- Verifier avec htop\n2- Vider la memoire swap\n3- Desactiver les services inutiles",
             "Quelle distribution Linux ?", "Linux", 2, "lent,performance,linux"),
            ("Probleme de GRUB", "GRUB ne s'affiche pas ou erreur", "Configuration de GRUB corrompue",
             "1- Reparer GRUB depuis un live\n2- Reinstaller GRUB\n3- Verifier le fichier grub.cfg",
             "Quel est le message d'erreur ?", "Linux", 4, "grub,linux,boot"),

            # Mac OS
            ("Mac ne demarre pas", "Mac reste bloque sur l'ecran blanc", "Probleme de disque ou de systeme",
             "1- Demarrer en mode sans echec\n2- Utiliser la recuperation macOS\n3- Reinstaller macOS",
             "Y a-t-il un bruit de disque ?", "MacOS", 4, "demarrage,mac,apple"),
            ("Mac tres lent", "Mac rame, applications lentes", "Disque plein ou memoire insuffisante",
             "1- Verifier l'espace disque\n2- Nettoyer les caches\n3- Reduire les programmes au demarrage",
             "Depuis quand est-il lent ?", "MacOS", 2, "lent,performance,mac"),
            ("Probleme de mise a jour macOS", "La mise a jour macOS echoue", "Espace insuffisant ou connexion",
             "1- Verifier l'espace disque\n2- Vider les caches\n3- Telecharger la mise a jour manuellement",
             "Quelle version de macOS ?", "MacOS", 3, "update,mac,apple"),

            # Reseau
            ("WiFi ne se connecte pas", "Impossible de se connecter au WiFi", "Mot de passe incorrect ou signal faible",
             "1- Verifier le mot de passe\n2- Se rapprocher de la box\n3- Redemarrer le routeur",
             "Le WiFi s'affiche-t-il ?", "Reseau", 2, "wifi,connexion,reseau"),
            ("Internet tres lent", "Connexion internet tres lente", "Bandwidth limite ou utilisation elevee",
             "1- Verifier la vitesse\n2- Limiter les telechargements\n3- Contacter le FAI",
             "Quelle est votre vitesse internet ?", "Reseau", 2, "internet,lent,reseau"),
            ("Probleme de DNS", "Impossible de resoudre les noms", "DNS mal configure ou serveur HS",
             "1- Utiliser Google DNS (8.8.8.8)\n2- Vider le cache DNS\n3- Changer de serveur DNS",
             "Quel est votre serveur DNS ?", "Reseau", 3, "dns,reseau"),

            # Securite
            ("Virus detecte", "Antivirus a detecte un virus", "Malware ou fichier infecte",
             "1- Executer une analyse complete\n2- Mettre en quarantaine\n3- Supprimer le fichier",
             "Quel fichier est infecte ?", "Securite", 4, "virus,malware,securite"),
            ("Probleme de pare-feu", "Pare-feu bloque tout", "Configuration trop restrictive",
             "1- Desactiver temporairement\n2- Ajouter des regles\n3- Verifier les logs",
             "Quelle application est bloquee ?", "Securite", 3, "firewall,securite"),
            ("Probleme de ransomware", "Fichiers chiffres", "Ransomware detecte",
             "1- Deconnecter le PC d'internet\n2- Contacter un expert\n3- Utiliser un outil de decryptage",
             "Avez-vous une sauvegarde ?", "Securite", 5, "ransomware,securite"),

            # Materiel
            ("PC ne s'allume pas", "L'ordinateur ne s'allume pas", "Alimentation ou carte mere",
             "1- Verifier le cable d'alimentation\n2- Tester une autre prise\n3- Contacter un reparateur",
             "Y a-t-il des LEDs allumees ?", "Materiel", 4, "allumage,materiel,pc"),
            ("Ecran noir", "L'ecran reste noir", "Cable ou carte graphique",
             "1- Verifier le cable\n2- Tester un autre ecran\n3- Reinstaller le GPU",
             "L'ordinateur demarre-t-il ?", "Materiel", 3, "ecran,materiel,noir"),
            ("Surchauffe PC", "PC tres chaud", "Ventilateur bloque ou poussiere",
             "1- Nettoyer les ventilateurs\n2- Verifier la pate thermique\n3- Ajouter un ventilateur",
             "Quelle est la temperature ?", "Materiel", 3, "chaleur,materiel,pc")
        ]

        cur.executemany(
            "INSERT INTO pannes (titre, description, diagnostic, procedure, questions, categorie, niveau, tags) VALUES (?,?,?,?,?,?,?,?)",
            donnees
        )

    conn.commit()
    conn.close()


# ==================================================
# MOTEUR DE RECHERCHE
# ==================================================

class RechercheIT:
    def __init__(self):
        self.df = None

    def charger(self):
        if self.df is None:
            conn = connexion_db()
            self.df = pd.read_sql_query("SELECT * FROM pannes", conn)
            conn.close()

    def normaliser(self, texte):
        texte = str(texte).lower()
        corrections = {"ordi": "ordinateur", "pc": "ordinateur", "rame": "lent", "wiffi": "wifi"}
        for ancien, nouveau in corrections.items():
            texte = texte.replace(ancien, nouveau)
        return texte

    def rechercher(self, question, niveau_diagnostic="basique"):
        self.charger()
        question = self.normaliser(question)
        mots = re.findall(r"\w+", question)
        resultats = []

        for _, panne in self.df.iterrows():
            score = 0
            champs = f"{panne['titre']} {panne['description']} {panne['tags']} {panne['categorie']}".lower()
            for mot in mots:
                if len(mot) > 1 and mot in champs:
                    score += 5
                if mot in panne['titre'].lower():
                    score += 10

            if niveau_diagnostic == "avance" and panne['niveau'] >= 3:
                score += 5
            if niveau_diagnostic == "expert" and panne['niveau'] >= 4:
                score += 10

            if score > 0:
                resultats.append((dict(panne), score))

        resultats.sort(key=lambda x: x[1], reverse=True)
        return resultats[:10]


# ==================================================
# AUTHENTIFICATION
# ==================================================

def inscription(email, password):
    conn = connexion_db()
    cur = conn.cursor()
    try:
        pwd = hashlib.sha256(password.encode()).hexdigest()
        cur.execute(
            "INSERT INTO utilisateurs (email, password, plan, premium, recherches, date_inscription) VALUES (?, ?, 'gratuit', 0, 0, ?)",
            (email, pwd, date.today().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


def connexion_utilisateur(email, password):
    conn = connexion_db()
    cur = conn.cursor()
    pwd = hashlib.sha256(password.encode()).hexdigest()
    cur.execute(
        "SELECT * FROM utilisateurs WHERE email = ? AND password = ?",
        (email, pwd)
    )
    user = cur.fetchone()
    conn.close()
    return user


def mise_a_jour_plan(email, plan):
    conn = connexion_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE utilisateurs SET plan = ?, premium = 1 WHERE email = ?",
        (plan, email)
    )
    conn.commit()
    conn.close()


# ==================================================
# PAGE VIREMENT BANCAIRE
# ==================================================

def page_virement():
    st.markdown("# Paiement par Virement Bancaire")
    st.markdown("---")

    st.markdown("""
    <div style='background: linear-gradient(135deg, #1a5276 0%, #2e86c1 100%); 
                padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px;'>
        <h1 style='color: white;'>Virement Bancaire</h1>
        <p style='color: #FFD700;'>Paiement securise et tracable</p>
        <p style='color: white;'>0€ de frais de transaction</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Etape 1 : Choisissez votre offre")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("""
            ### PRO
            **9.90€ / mois** | **79€ / an**

            - Recherches illimitees  
            - Diagnostics avances  
            - 120+ diagnostics  
            - Export PDF  
            - Support prioritaire  
            - Statistiques avancees
            """)
            if st.button("Choisir Pro - 9.90€", type="primary", use_container_width=True):
                st.session_state.montant_virement = 9.90
                st.session_state.offre_virement = "Pro"
                st.session_state.plan_virement = "pro"
                st.success("Offre Pro selectionnee !")
                st.balloons()

    with col2:
        with st.container(border=True):
            st.markdown("""
            ### BUSINESS
            **29.90€ / mois** | **249€ / an**

            - Tout Pro inclus  
            - Diagnostics experts  
            - 120+ diagnostics  
            - Export PDF/Word  
            - Support 24/7  
            - Acces API  
            - 5 comptes inclus
            """)
            if st.button("Choisir Business - 29.90€", type="primary", use_container_width=True):
                st.session_state.montant_virement = 29.90
                st.session_state.offre_virement = "Business"
                st.session_state.plan_virement = "business"
                st.success("Offre Business selectionnee !")
                st.balloons()

    if st.session_state.montant_virement > 0:
        st.markdown("---")
        st.markdown("### Etape 2 : Effectuez le virement")

        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        st.session_state.ref_virement = ref

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 20px; border-radius: 10px;'>
                <h4>Coordonnees bancaires</h4>
                <p><strong>Titulaire :</strong> IT Pro Solutions</p>
                <p><strong>IBAN :</strong> FR76 1234 5678 9012 3456 7890 123</p>
                <p><strong>BIC :</strong> ABCDEFRPP</p>
                <p><strong>Banque :</strong> Banque Populaire</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='background: #2ecc71; padding: 20px; border-radius: 10px;'>
                <h4>Informations importantes</h4>
                <p><strong>Montant :</strong> {st.session_state.montant_virement}€</p>
                <p><strong>Offre :</strong> {st.session_state.offre_virement}</p>
                <p><strong>Reference :</strong> <code>{ref}</code></p>
                <p><strong>Email :</strong> {st.session_state.user}</p>
                <p style='color: #e74c3c;'><strong>Indiquez la reference dans le libelle</strong></p>
            </div>
            """, unsafe_allow_html=True)

        st.info(f"""
        Resume du virement :
        - Montant : {st.session_state.montant_virement}€
        - Offre : {st.session_state.offre_virement}
        - Reference : {ref}
        - Email : {st.session_state.user}
        - Delai : 24-48h ouvres
        """)

    if st.session_state.montant_virement > 0:
        st.markdown("---")
        st.markdown("### Etape 3 : Confirmez votre paiement")

        with st.form("confirmation_virement"):
            st.markdown("Apres le virement, confirmez ici pour activer votre compte.")

            col1, col2 = st.columns(2)

            with col1:
                email_conf = st.text_input("Email", value=st.session_state.user or "", disabled=True)
                montant_conf = st.number_input("Montant", min_value=1.0, value=st.session_state.montant_virement,
                                               step=0.01)
                date_virement = st.date_input("Date du virement")

            with col2:
                ref_conf = st.text_input("Reference", value=st.session_state.ref_virement, disabled=True)
                offre_conf = st.text_input("Offre", value=st.session_state.offre_virement, disabled=True)
                notes = st.text_area("Notes")

            st.checkbox("Je certifie avoir effectue le virement")
            st.checkbox("J'ai indique la reference")

            if st.form_submit_button("Confirmer mon virement", type="primary", use_container_width=True):
                st.success(f"""
                Virement confirme !

                Offre : {st.session_state.offre_virement}
                Montant : {st.session_state.montant_virement}€
                Reference : {st.session_state.ref_virement}

                Email de confirmation envoye.
                Activation sous 24-48h.
                """)

                if st.button("Activer maintenant (admin)", type="primary"):
                    mise_a_jour_plan(st.session_state.user, st.session_state.plan_virement)
                    st.session_state.premium = True
                    st.session_state.plan = st.session_state.plan_virement
                    st.balloons()
                    st.success(f"{st.session_state.offre_virement.upper()} active !")
                    st.rerun()

    with st.expander("Questions frequentes"):
        st.markdown("""
        **1. Combien de temps pour l'activation ?** 24-48h ouvres
        **2. Comment savoir si mon virement est recu ?** Email de confirmation
        **3. Puis-je annuler ?** Contactez votre banque
        """)


# ==================================================
# PAGE LICENCE
# ==================================================

def page_licence():
    st.markdown("# Licence d'utilisation")
    st.markdown("---")

    st.markdown("""
    <div style='background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%); 
                padding: 30px; border-radius: 20px; text-align: center; margin: 20px 0;'>
        <h1 style='color: #FFD700; font-size: 36px;'>ASSISTANT IT PRO</h1>
        <h2 style='color: #fff; font-size: 24px;'>Licence Officielle</h2>
        <p style='color: #FFD700; font-size: 18px;'>Proprietaire : IT Pro Solutions</p>
        <p style='color: #fff; font-size: 14px;'>© 2026 - Tous droits reserves</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(LICENCE)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Informations legales**
        - Proprietaire : IT Pro Solutions
        - Siege : France
        - Version : 4.0
        - 120+ diagnostics
        """)
    with col2:
        st.markdown("""
        **Contact**
        - Email : tech.contactinformatique@proton.me
        - Web : www.itprosolutions.com
        """)


# ==================================================
# PAGE OFFRES
# ==================================================

def page_offres():
    st.markdown("# NOS 3 FORMULES")
    st.markdown("---")

    st.markdown("""
    <div style='background: linear-gradient(135deg, #FF6B6B 0%, #FFD93D 100%); 
                padding: 30px; border-radius: 20px; text-align: center; margin: 20px 0;'>
        <h1 style='color: #fff; font-size: 36px;'>OFFRE SPECIALE LANCEMENT</h1>
        <h2 style='color: #fff; font-size: 28px;'>-50% sur Pro & Business</h2>
        <p style='color: #fff; font-size: 18px;'>Code promo : LAUNCH50</p>
        <p style='color: #fff; font-size: 14px;'>120+ diagnostics disponibles</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("### Gratuit")
            st.markdown("**0€**")
            st.markdown("---")
            for feature in OFFRES["gratuit"]["features"]:
                st.markdown(f"- {feature}")
            st.button("Actuel", disabled=True, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.markdown("### Pro")
            col_mens, col_ann = st.columns(2)
            with col_mens:
                st.markdown("**9.90€**")
                st.caption("/mois")
            with col_ann:
                st.markdown("**79€**")
                st.caption("/an")
            st.markdown("---")
            for feature in OFFRES["pro"]["features"]:
                st.markdown(f"- {feature}")

            if st.session_state.user:
                if st.button("Passer à Pro", type="primary", use_container_width=True):
                    mise_a_jour_plan(st.session_state.user, "pro")
                    st.session_state.plan = "pro"
                    st.session_state.premium = True
                    st.success("Pro active !")
                    st.balloons()
                    st.rerun()
            else:
                st.info("Connectez-vous")

    with col3:
        with st.container(border=True):
            st.markdown("### Business")
            col_mens, col_ann = st.columns(2)
            with col_mens:
                st.markdown("**29.90€**")
                st.caption("/mois")
            with col_ann:
                st.markdown("**249€**")
                st.caption("/an")
            st.markdown("---")
            for feature in OFFRES["business"]["features"]:
                st.markdown(f"- {feature}")

            if st.session_state.user:
                if st.button("Passer à Business", type="primary", use_container_width=True):
                    mise_a_jour_plan(st.session_state.user, "business")
                    st.session_state.plan = "business"
                    st.session_state.premium = True
                    st.success("Business active !")
                    st.balloons()
                    st.rerun()
            else:
                st.info("Connectez-vous")


# ==================================================
# PAGE STATISTIQUES
# ==================================================

def page_statistiques():
    st.markdown("# Statistiques")
    st.markdown("---")

    conn = connexion_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pannes")
    total_diags = cur.fetchone()[0]
    cur.execute("SELECT categorie, COUNT(*) FROM pannes GROUP BY categorie")
    categories = cur.fetchall()
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total diagnostics", total_diags)
    with col2:
        st.metric("Categories", len(categories))
    with col3:
        st.metric("Recherches", st.session_state.recherches)
    with col4:
        plan = st.session_state.plan.upper()
        st.metric("Plan", plan)


# ==================================================
# MAIN
# ==================================================

def main():
    creer_base()
    remplir_base()

    if st.session_state.moteur is None:
        st.session_state.moteur = RechercheIT()

    if st.session_state.date_recherche != date.today():
        st.session_state.date_recherche = date.today()
        st.session_state.recherches_jour = 0

    # ========== SIDEBAR ==========
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h2 style='color: #FFD700;'>IT Pro</h2>
            <p style='color: gray; font-size: 12px;'>Par IT Pro Solutions</p>
            <p style='color: gray; font-size: 11px;'>120+ diagnostics</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## Compte")

        if st.session_state.user:
            st.success(f"Connecte : {st.session_state.user}")

            plan = st.session_state.plan
            if plan == "business":
                st.markdown("""
                <div style='background: #9B59B6; padding: 15px; border-radius: 10px; text-align: center;'>
                    <h2 style='color: #fff; margin: 0;'>BUSINESS</h2>
                    <p style='color: #fff; margin: 0;'>Expert - Illimite</p>
                </div>
                """, unsafe_allow_html=True)
            elif plan == "pro":
                st.markdown("""
                <div style='background: #FFD700; padding: 15px; border-radius: 10px; text-align: center;'>
                    <h2 style='color: #000; margin: 0;'>PRO</h2>
                    <p style='color: #000; margin: 0;'>Recherches illimitees</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background: #FF6B6B; padding: 15px; border-radius: 10px; text-align: center;'>
                    <p style='color: #fff; margin: 0;'>GRATUIT</p>
                </div>
                """, unsafe_allow_html=True)

                restant = max(0, OFFRES["gratuit"]["recherches"] - st.session_state.recherches_jour)
                st.progress(st.session_state.recherches_jour / OFFRES["gratuit"]["recherches"])
                st.warning(f"{restant} recherches restantes aujourd'hui")

                if restant == 0:
                    st.error("PLUS DE RECHERCHES !")

            st.markdown("---")
            menu = ["Accueil", "Offres", "Virement", "Licence"]
            if st.session_state.premium:
                menu.append("Statistiques")

            st.session_state.page = st.radio("Navigation", menu)

            if st.button("Deconnexion", use_container_width=True):
                st.session_state.user = None
                st.session_state.premium = False
                st.session_state.plan = "gratuit"
                st.session_state.recherches = 0
                st.session_state.recherches_jour = 0
                st.rerun()

        else:
            tab1, tab2 = st.tabs(["Connexion", "Inscription"])

            with tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Mot de passe", type="password", key="login_pass")
                if st.button("Se connecter", use_container_width=True):
                    user = connexion_utilisateur(email, password)
                    if user:
                        st.session_state.user = email
                        st.session_state.plan = user[3] if user[3] else "gratuit"
                        st.session_state.premium = bool(user[4])
                        st.session_state.recherches = user[5]
                        st.session_state.recherches_jour = user[5]
                        st.success("Connecte !")
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects")

            with tab2:
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Mot de passe", type="password", key="register_pass")
                if st.button("Creer un compte", use_container_width=True):
                    if inscription(email, password):
                        st.success("Compte cree ! Connectez-vous")
                    else:
                        st.error("Email deja utilise")

        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: gray; font-size: 11px;'>
            IT Pro Solutions © 2026<br>
            Tous droits reserves
        </div>
        """, unsafe_allow_html=True)

    # ========== GESTION DES PAGES ==========

    if st.session_state.page == "Offres":
        page_offres()
        return

    if st.session_state.page == "Virement":
        page_virement()
        return

    if st.session_state.page == "Licence":
        page_licence()
        return

    if st.session_state.page == "Statistiques":
        if st.session_state.premium:
            page_statistiques()
            return
        else:
            st.warning("Reserve aux Premium")
            return

    # ========== ACCUEIL ==========

    if st.session_state.user:
        if not st.session_state.premium:
            st.warning(
                f"GRATUIT - {max(0, OFFRES['gratuit']['recherches'] - st.session_state.recherches_jour)}/3 recherches")
            if st.button("PASSER PREMIUM", type="primary"):
                st.session_state.page = "Offres"
                st.rerun()
        else:
            plan = st.session_state.plan
            if plan == "business":
                st.success("Mode BUSINESS - Expert + Illimite")
            else:
                st.success("Mode PRO - Recherches illimitees")

    st.markdown("# Assistant Depannage IT")
    st.markdown("Par IT Pro Solutions - **120+ diagnostics**")

    if st.session_state.user and st.session_state.premium:
        niveau_diag = st.selectbox("Niveau de diagnostic :", ["Basique", "Avance", "Expert"])
        niveau_map = {"Basique": "basique", "Avance": "avance", "Expert": "expert"}
        niveau = niveau_map[niveau_diag]
        if niveau == "expert" and st.session_state.plan != "business":
            st.warning("Expert reserve Business")
            niveau = "avance"
    else:
        niveau = "basique"
        if st.session_state.user:
            st.info("Passez Premium pour diagnostics avances !")

    question = st.text_area("Decrivez votre probleme :", height=100,
                            placeholder="Ex: mon PC est lent, le wifi ne marche pas...")

    if st.button("Rechercher", type="primary", use_container_width=True):
        if not st.session_state.user:
            st.error("Connectez-vous")
        elif not st.session_state.premium and st.session_state.recherches_jour >= OFFRES["gratuit"]["recherches"]:
            st.error("LIMITE ATTEINTE !")
            if st.button("VOIR LES OFFRES", type="primary"):
                st.session_state.page = "Offres"
                st.rerun()
        elif question.strip():
            with st.spinner("Recherche..."):
                if not st.session_state.premium:
                    st.session_state.recherches_jour += 1
                    st.session_state.recherches += 1

                results = st.session_state.moteur.rechercher(question, niveau)

                if results:
                    st.success(f"{len(results)} resultat(s)")
                    for panne, score in results:
                        with st.expander(f"{panne['titre']} (Score: {score})"):
                            st.markdown(f"**Categorie:** {panne['categorie']}")
                            st.markdown(f"**Diagnostic:** {panne['diagnostic']}")
                            st.markdown(f"**Procedure:**\n{panne['procedure']}")
                            if panne.get('questions'):
                                st.info(f"{panne['questions']}")
                else:
                    st.warning("Aucun resultat")
        else:
            st.warning("Decrivez votre probleme")

    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        © 2026 <strong>IT Pro Solutions</strong> - Tous droits reserves<br>
        <small>Assistant IT Pro v4.0 - 120+ diagnostics</small>
    </div>
    """, unsafe_allow_html=True)


# ==================================================
# LANCEMENT
# ==================================================

if __name__ == "__main__":
    main()
