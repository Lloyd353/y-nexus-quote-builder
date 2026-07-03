"""
Y-NEXUS QUOTE BUILDER
======================
Point d'entrée principal de l'application.
Ce fichier ne contient AUCUNE logique métier : il orchestre uniquement
la navigation entre les 3 blocs et initialise les données partagées.
 
Pour lancer l'application en local :
    streamlit run app.py
"""
 
import streamlit as st
 
from modules.bloc1_infos import afficher_bloc1
from modules.bloc2_devis import afficher_bloc2
from modules.bloc3_rapport import afficher_bloc3
from modules.sidebar import afficher_sidebar
 
 
# ----------------------------------------------------------------------
# CONFIGURATION DE LA PAGE (doit être le premier appel Streamlit du script)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Y-NEXUS Quote Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
 
# ----------------------------------------------------------------------
# THÈME "INDUSTRIAL PREMIUM" — injection de CSS personnalisé
# ----------------------------------------------------------------------
def injecter_theme_css():
    """
    Applique le thème visuel demandé : fond gris très clair, boutons
    bleu profond / anthracite.
 
    IMPORTANT — Correction mode sombre : Streamlit peut basculer en
    thème sombre selon les préférences système du visiteur. Sans
    forçage explicite, le texte (pensé pour un fond clair) devient
    quasi invisible sur fond noir. On neutralise donc ça avec des
    règles ciblant TOUT le texte de l'app (pas seulement h1-h3), et
    en fixant explicitement les couleurs de fond des zones de saisie.
    """
    st.markdown(
        """
        <style>
        /* Fond général de l'espace de travail — fixe, ignore le mode sombre système */
        .stApp {
            background-color: #F7F8FA;
        }
 
        /* Tout le texte de l'app en anthracite, quel que soit le thème du visiteur */
        .stApp, .stApp p, .stApp span, .stApp label,
        h1, h2, h3, h4, h5, h6,
        .stMarkdown, .stCaption, .stText {
            color: #2B2F36 !important;
        }
 
        /* Champs de saisie : fond blanc explicite + texte lisible,
           pour éviter qu'ils héritent d'un fond sombre système */
        .stTextInput input, .stNumberInput input, .stDateInput input,
        .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            background-color: #FFFFFF !important;
            color: #2B2F36 !important;
        }
 
        /* Boutons principaux : bleu profond (texte toujours blanc, lisible) */
        .stButton > button {
            background-color: #1B3A5C;
            color: #FFFFFF !important;
            border-radius: 6px;
            border: none;
            font-weight: 600;
            padding: 0.5rem 1.2rem;
            transition: background-color 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #142C47;
            color: #FFFFFF !important;
        }
        .stButton > button p {
            color: #FFFFFF !important;
        }
 
        /* Bandeau de progression des blocs */
        .ynexus-stepper {
            display: flex;
            justify-content: space-between;
            margin-bottom: 2rem;
            padding: 0.8rem 1rem;
            background-color: #FFFFFF;
            border-radius: 8px;
            border: 1px solid #E3E6EA;
        }
        .ynexus-step {
            font-weight: 600;
            color: #9AA1AC;
        }
        .ynexus-step-active {
            color: #1B3A5C;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
 
 
# ----------------------------------------------------------------------
# INITIALISATION DU SESSION_STATE
# ----------------------------------------------------------------------
def initialiser_session_state():
    """
    Crée toutes les clés nécessaires dans st.session_state si elles
    n'existent pas encore. C'est l'équivalent d'une "base de données
    en mémoire" propre à la session du visiteur : les valeurs restent
    accessibles tant que l'onglet du navigateur reste ouvert.
 
    IMPORTANT : cette fonction doit être appelée à CHAQUE rerun du script
    (donc à chaque interaction utilisateur), mais elle ne réinitialise
    rien si les clés existent déjà — c'est le rôle du .setdefault().
    """
 
    # --- Navigation ---
    st.session_state.setdefault("bloc_actif", 1)  # 1, 2 ou 3
 
    # --- BLOC 1 : Métadonnées ---
    st.session_state.setdefault("infos_concepteur_prenom", "")
    st.session_state.setdefault("infos_concepteur_nom", "")
    st.session_state.setdefault("infos_client_entreprise", "")
    st.session_state.setdefault("infos_secteur", "Énergie")
    st.session_state.setdefault("infos_pays", "")
    st.session_state.setdefault("infos_date", None)  # sera fixé à today() au 1er rendu
 
    # --- BLOC 2 : Lignes de devis ---
    # On stocke les lignes sous forme de liste de dictionnaires.
    # C'est le format le plus simple à manipuler avec pandas/data_editor.
    if "devis_lignes" not in st.session_state:
        st.session_state.devis_lignes = [
            {
                "Désignation": "",
                "Référence normative": "",
                "Quantité": 1.0,
                "Unité": "u",
                "Prix unitaire": 0.0,
            }
        ]
    st.session_state.setdefault("devis_devise", "FCFA (XAF)")
    st.session_state.setdefault("devis_taux_tva", 19.25)
 
    # --- BLOC 3 : Personnalisation du rapport ---
    st.session_state.setdefault("rapport_logo_bytes", None)
    st.session_state.setdefault("rapport_logo_nom_fichier", None)
    st.session_state.setdefault("rapport_signature_bytes", None)
    st.session_state.setdefault("rapport_signature_nom_fichier", None)
    st.session_state.setdefault("rapport_pdf_bytes", None)  # PDF généré, prêt au téléchargement
 
 
# ----------------------------------------------------------------------
# BANDEAU DE PROGRESSION (stepper visuel en haut de page)
# ----------------------------------------------------------------------
def afficher_stepper():
    """Affiche 'Bloc 1 — Bloc 2 — Bloc 3' avec le bloc actif surligné."""
    bloc_actif = st.session_state.bloc_actif
    noms = {1: "1. Informations générales", 2: "2. Devis", 3: "3. Rapport & Impression"}
 
    cols = st.columns(3)
    for i, col in enumerate(cols, start=1):
        with col:
            classe = "ynexus-step-active" if i == bloc_actif else ""
            icone = "●" if i == bloc_actif else "○"
            col.markdown(
                f'<div class="ynexus-stepper"><span class="ynexus-step {classe}">'
                f'{icone} {noms[i]}</span></div>',
                unsafe_allow_html=True,
            )
 
 
# ----------------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# ----------------------------------------------------------------------
def main():
    initialiser_session_state()
    injecter_theme_css()
 
    # En-tête
    st.title("⚡ Y-NEXUS Quote Builder")
    st.caption(
        "Structurez vos propositions commerciales en énergie, télécoms et automatismes."
    )
 
    # Sidebar (toujours visible, cross-selling)
    afficher_sidebar()
 
    # Stepper visuel
    afficher_stepper()
 
    # Routage vers le bloc actif
    if st.session_state.bloc_actif == 1:
        afficher_bloc1()
    elif st.session_state.bloc_actif == 2:
        afficher_bloc2()
    elif st.session_state.bloc_actif == 3:
        afficher_bloc3()
 
 
if __name__ == "__main__":
    main()
 
