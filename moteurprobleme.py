import streamlit as st
import sqlite3
import pandas as pd


DB = "problemes_informatique.db"


# ==========================
# BASE DE DONNEES
# ==========================

def connexion():
    return sqlite3.connect(DB)


def init_db():

    con = connexion()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS problemes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT,
        description TEXT,
        solution TEXT,
        mots_cles TEXT
    )
    """)

    con.commit()

    # Ajout de quelques problèmes de départ
    cur.execute("SELECT COUNT(*) FROM problemes")
    nb = cur.fetchone()[0]

    if nb == 0:

        exemples = [

            (
            "Ecran noir au démarrage",
            "Le PC démarre mais rien ne s'affiche",
            "Vérifier le câble écran, tester un autre écran, démarrer en mode sans échec, vérifier la carte graphique.",
            "écran noir affichage démarrage pc"
            ),

            (
            "Connexion Wifi impossible",
            "Internet ne fonctionne plus",
            "Redémarrer la box, désactiver/réactiver le wifi, vérifier le pilote réseau.",
            "wifi internet réseau connexion"
            ),

            (
            "Ordinateur lent",
            "Le PC est très lent",
            "Supprimer les programmes inutiles, vérifier les virus, nettoyer le disque, ajouter de la RAM.",
            "lent ralentissement performance pc"
            ),

            (
            "Erreur Windows écran bleu",
            "Windows affiche un écran bleu",
            "Noter le code erreur, mettre les pilotes à jour, vérifier la mémoire RAM.",
            "windows bsod erreur bleu"
            )

        ]


        cur.executemany(
            """
            INSERT INTO problemes
            (titre,description,solution,mots_cles)
            VALUES (?,?,?,?)
            """,
            exemples
        )

        con.commit()


    con.close()



def rechercher(texte):

    con = connexion()

    df = pd.read_sql_query(
        """
        SELECT titre,description,solution
        FROM problemes
        WHERE titre LIKE ?
        OR description LIKE ?
        OR mots_cles LIKE ?
        """,
        con,
        params=(
            f"%{texte}%",
            f"%{texte}%",
            f"%{texte}%"
        )
    )

    con.close()

    return df



def ajouter_probleme(
    titre,
    description,
    solution,
    mots
):

    con = connexion()

    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO problemes
        VALUES(NULL,?,?,?,?)
        """,
        (
            titre,
            description,
            solution,
            mots
        )
    )

    con.commit()
    con.close()



# ==========================
# APPLICATION
# ==========================

st.set_page_config(
    page_title="Dépannage Informatique",
    page_icon="🖥️"
)


init_db()


st.title("🖥️ Moteur de recherche de problèmes informatiques")


recherche = st.text_input(
    "Décrivez votre problème informatique"
)


if recherche:


    resultats = rechercher(recherche)


    if resultats.empty:

        st.warning(
            "Aucun problème trouvé."
        )

    else:

        for _, ligne in resultats.iterrows():

            st.subheader(
                "🔧 " + ligne["titre"]
            )

            st.write(
                ligne["description"]
            )

            st.success(
                ligne["solution"]
            )



st.divider()


st.subheader(
    "➕ Ajouter une solution dans la base"
)


titre = st.text_input(
    "Nom du problème"
)

description = st.text_area(
    "Description"
)

solution = st.text_area(
    "Solution"
)

mots = st.text_input(
    "Mots clés"
)


if st.button(
    "Ajouter"
):

    ajouter_probleme(
        titre,
        description,
        solution,
        mots
    )

    st.success(
        "Problème ajouté !"
    )