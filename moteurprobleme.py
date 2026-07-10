# =====================================================
# ASSISTANT IT PRO - MOTEUR DE RECHERCHE
# PARTIE 1/3
# =====================================================

import streamlit as st
import sqlite3
import pandas as pd
import re


# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Assistant IT Pro",
    page_icon="🤖",
    layout="wide"
)


DB = "assistant_it_ia.db"



# =====================================================
# SUPABASE
# =====================================================

try:

    from supabase import create_client


    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

    SUPABASE_OK = True


except Exception as e:

    supabase = None
    SUPABASE_OK = False

    st.warning(
        "Supabase non disponible : mode local activé"
    )



# =====================================================
# BASE SQLITE
# =====================================================

def connexion():

    return sqlite3.connect(DB)



def init_db():

    con = connexion()

    cur = con.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS pannes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        titre TEXT,

        description TEXT,

        diagnostic TEXT,

        procedure TEXT,

        questions TEXT,

        categorie TEXT,

        niveau INTEGER,

        tags TEXT

    )
    """)


    con.commit()

    con.close()



# =====================================================
# DONNEES DE BASE
# =====================================================

def remplir_base():


    con = connexion()

    cur = con.cursor()


    cur.execute(
        "SELECT COUNT(*) FROM pannes"
    )


    total = cur.fetchone()[0]


    if total > 0:

        con.close()
        return



    donnees = [


        (
        "PC très lent",

        "ordinateur lent rame programmes longs",

        "Manque de ressources, disque lent ou trop de programmes",

        """
1 Vérifier le gestionnaire des tâches
2 Désactiver les programmes inutiles
3 Nettoyer le disque
4 Vérifier la RAM
        """,

        "Depuis quand le problème existe ?",

        "Performance",

        2,

        "lent,rame,ordinateur,performance"
        ),



        (
        "WiFi impossible",

        "wifi internet connexion réseau impossible",

        "Problème réseau, box ou pilote wifi",

        """
1 Redémarrer la box
2 Redémarrer le PC
3 Vérifier le pilote wifi
4 Tester un autre appareil
        """,

        "Les autres appareils ont-ils internet ?",

        "Réseau",

        2,

        "wifi,internet,réseau,connexion"
        ),



        (
        "Ecran noir",

        "ordinateur démarre écran noir aucune image",

        "Problème écran câble RAM ou carte graphique",

        """
1 Vérifier câble HDMI
2 Tester un autre écran
3 Vérifier la RAM
        """,

        "Le PC démarre-t-il ?",

        "Matériel",

        3,

        "écran,noir,image,graphique"
        ),



        (
        "Mot de passe oublié",

        "impossible connexion compte mot passe",

        "Compte utilisateur bloqué",

        """
1 Vérifier le compte
2 Réinitialiser le mot de passe
3 Contacter administrateur
        """,

        "Compte administrateur disponible ?",

        "Sécurité",

        3,

        "motdepasse,connexion,compte"
        )

    ]



    cur.executemany(

    """
    INSERT INTO pannes
    (
    titre,
    description,
    diagnostic,
    procedure,
    questions,
    categorie,
    niveau,
    tags
    )

    VALUES (?,?,?,?,?,?,?,?)

    """,

    donnees

    )



    con.commit()

    con.close()

  
# =====================================================
# ASSISTANT IT PRO
# PARTIE 2/3
# MOTEUR DE RECHERCHE + AUTHENTIFICATION
# =====================================================



# =====================================================
# MOTEUR DE RECHERCHE
# =====================================================

class RechercheIAPro:


    def __init__(self):

        self.df = None



    def charger_base(self):

        if self.df is None:

            con = connexion()

            self.df = pd.read_sql_query(
                "SELECT * FROM pannes",
                con
            )

            con.close()



    def normaliser(self, texte):

        texte = str(texte).lower()


        corrections = {

            "ordi":"ordinateur",
            "pc":"ordinateur",
            "rame":"lent",
            "wiffi":"wifi",
            "wify":"wifi",
            "bloque":"freeze"

        }


        for ancien,nouveau in corrections.items():

            texte = texte.replace(
                ancien,
                nouveau
            )


        return texte



    def rechercher(self, question):


        self.charger_base()


        question = self.normaliser(question)


        mots = re.findall(
            r"\w+",
            question
        )


        resultats=[]



        for _, panne in self.df.iterrows():


            score=0


            champs = [

                panne["titre"],
                panne["description"],
                panne["diagnostic"],
                panne["tags"]

            ]


            texte = self.normaliser(
                " ".join(champs)
            )



            for mot in mots:


                if len(mot)<2:

                    continue



                if mot in texte:

                    score += 5



                if mot in self.normaliser(panne["titre"]):

                    score += 10



            if score>0:

                resultats.append(

                    (
                        dict(panne),
                        score
                    )

                )



        resultats.sort(

            key=lambda x:x[1],

            reverse=True

        )


        return resultats[:10]





# =====================================================
# AUTHENTIFICATION SUPABASE
# =====================================================


def afficher_auth():


    st.sidebar.markdown(
        "## 👤 Compte utilisateur"
    )



    if not SUPABASE_OK:


        st.sidebar.info(
            "Connexion désactivée - mode local"
        )

        return




    if "user" not in st.session_state:

        st.session_state.user=None




    # -----------------------------
    # UTILISATEUR CONNECTE
    # -----------------------------


    if st.session_state.user:


        st.sidebar.success(

            "Connecté : "
            +
            st.session_state.user.email

        )



        if st.sidebar.button(
            "Déconnexion"
        ):


            supabase.auth.sign_out()


            st.session_state.user=None


            st.rerun()



        return




    # -----------------------------
    # FORMULAIRE
    # -----------------------------


    choix = st.sidebar.radio(

        "Action",

        [
            "Connexion",
            "Créer un compte"
        ]

    )



    email = st.sidebar.text_input(
        "Email"
    )


    password = st.sidebar.text_input(

        "Mot de passe",

        type="password"

    )





    if choix=="Créer un compte":


        if st.sidebar.button(
            "Créer mon compte"
        ):


            try:


                supabase.auth.sign_up(

                    {

                    "email":email,

                    "password":password

                    }

                )


                st.sidebar.success(

                    "Compte créé. Vérifiez votre email."

                )


            except Exception as e:


                st.sidebar.error(
                    str(e)
                )






    if choix=="Connexion":


        if st.sidebar.button(
            "Se connecter"
        ):


            try:


                resultat = supabase.auth.sign_in_with_password(

                    {

                    "email":email,

                    "password":password

                    }

                )



                st.session_state.user = resultat.user



                st.sidebar.success(

                    "Connexion réussie"

                )


                st.rerun()



            except Exception as e:


                st.sidebar.error(

                    "Erreur connexion : "
                    +
                    str(e)

                )
# =====================================================
# ASSISTANT IT PRO
# PARTIE 3/3
# INTERFACE STREAMLIT
# =====================================================


# =====================================================
# STYLE
# =====================================================

st.markdown(
"""
<style>

.main-title {

font-size:40px;
font-weight:bold;
text-align:center;

}


.result {

padding:20px;
border-radius:15px;
background:#f5f5f5;
margin-bottom:15px;

}

</style>

""",

unsafe_allow_html=True
)




# =====================================================
# INTERFACE PRINCIPALE
# =====================================================


def main():


    # création base

    init_db()

    remplir_base()



    # connexion utilisateur

    afficher_auth()



    # moteur recherche

    if "moteur" not in st.session_state:

        st.session_state.moteur = RechercheIAPro()





    # TITRE


    st.markdown(

        '<div class="main-title">'
        '🤖 Assistant Dépannage IT'
        '</div>',

        unsafe_allow_html=True

    )



    st.write(
        ""
    )



    # statistiques


    con = connexion()


    total = pd.read_sql_query(

        "SELECT COUNT(*) as total FROM pannes",

        con

    ).iloc[0]["total"]



    con.close()



    st.sidebar.metric(

        "📚 Diagnostics disponibles",

        total

    )





    # ONGLET


    tab1, tab2 = st.tabs(

        [
            "🔍 Recherche IT",

            "🌐 Recherche Web"

        ]

    )





    # =============================
    # RECHERCHE IA
    # =============================


    with tab1:


        question = st.text_area(

            "Décrivez votre problème informatique :",

            placeholder=

            "Exemple : mon ordinateur est lent",

            height=120

        )



        bouton = st.button(

            "🔍 Analyser",

            type="primary",

            use_container_width=True

        )





        if bouton and question:



            resultats = (

                st.session_state.moteur
                .rechercher(question)

            )



            if not resultats:


                st.error(

                    "Aucun diagnostic trouvé"

                )


            else:


                st.success(

                    f"{len(resultats)} problème(s) trouvé(s)"

                )



                for panne, score in resultats:



                    with st.expander(

                        panne["titre"]

                        +

                        f"  ⭐ {score}"

                    ):



                        st.write(

                            "**Catégorie :**",

                            panne["categorie"]

                        )


                        st.write(

                            "**Diagnostic :**"

                        )


                        st.info(

                            panne["diagnostic"]

                        )



                        st.write(

                            "**Procédure :**"

                        )


                        st.write(

                            panne["procedure"]

                        )



                        st.write(

                            "**Questions :**",

                            panne["questions"]

                        )


                        st.caption(

                            "Tags : "

                            +

                            panne["tags"]

                        )






    # =============================
    # GOOGLE SEARCH
    # =============================


    with tab2:


        st.markdown(

        """

        ### 🌐 Recherche Internet

        Vous pouvez rechercher une solution complémentaire :

        """

        )



        recherche = st.text_input(

            "Recherche Google"

        )



        if recherche:


            url = (

            "https://www.google.com/search?q="

            +

            recherche.replace(

                " ",

                "+"

            )

            )


            st.markdown(

                f"[🔎 Ouvrir Google]({url})"

            )





# =====================================================
# LANCEMENT
# =====================================================


if __name__ == "__main__":


    main()
    def verifier_plan():

    if "user" not in st.session_state:
        return "gratuit"


    user = st.session_state.user


    resultat = supabase.table(
        "profiles"
    ).select(
        "plan"
    ).eq(
        "id",
        user.id
    ).execute()


    if resultat.data:

        return resultat.data[0]["plan"]


    return "gratuit"
    plan = verifier_plan()


if plan != "premium":

    st.warning(
        "Version gratuite : 5 diagnostics par jour. Passez Premium pour un accès complet."
    )
    supabase.auth.sign_in_with_password(
{
"email":email,
"password":password
}
)
