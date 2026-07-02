"""
BLOC 1 — Tableau de Bord & Informations Générales
====================================================
Rôle : collecter les métadonnées du document (qui rédige, pour qui,
quel secteur, quand). Ces informations réapparaîtront en page de garde
du PDF final.
 
Toutes les valeurs sont lues/écrites directement dans st.session_state
pour survivre à la navigation entre blocs.
"""
 
import datetime
import streamlit as st
 
from modules.gestion_brouillon import afficher_widget_export_import
 
SECTEURS_DISPONIBLES = ["Énergie", "Télécoms", "Automatisme", "BTP", "Autre"]
 
 
def _champs_obligatoires_remplis() -> bool:
    """
    Retourne True si tous les champs obligatoires du Bloc 1 sont remplis.
    Centraliser cette vérification ici évite de dupliquer la logique
    entre le bouton 'Suivant' et le bouton 'Passer à la configuration'.
    """
    return all(
        [
            st.session_state.infos_concepteur_prenom.strip() != "",
            st.session_state.infos_concepteur_nom.strip() != "",
            st.session_state.infos_client_entreprise.strip() != "",
            st.session_state.infos_pays.strip() != "",
        ]
    )
 
 
def afficher_bloc1():
    st.subheader("🟦 Bloc 1 — Informations générales")
    st.write(
        "Ces informations apparaîtront sur la page de garde de votre devis PDF."
    )
 
    # Widget de reprise de brouillon — placé en tout premier pour qu'un
    # utilisateur revenant sur l'app puisse immédiatement recharger son travail.
    afficher_widget_export_import()
 
    st.divider()
 
    # ------------------------------------------------------------------
    # FORMULAIRE — deux colonnes pour un rendu compact
    # ------------------------------------------------------------------
    col_gauche, col_droite = st.columns(2)
 
    with col_gauche:
        st.session_state.infos_concepteur_prenom = st.text_input(
            "Prénom du concepteur *",
            value=st.session_state.infos_concepteur_prenom,
            placeholder="Ex : Jean",
        )
        st.session_state.infos_client_entreprise = st.text_input(
            "Nom de l'Entreprise / Client cible *",
            value=st.session_state.infos_client_entreprise,
            placeholder="Ex : SONATEL SA",
        )
        st.session_state.infos_pays = st.text_input(
            "Pays *",
            value=st.session_state.infos_pays,
            placeholder="Ex : Cameroun",
        )
 
    with col_droite:
        st.session_state.infos_concepteur_nom = st.text_input(
            "Nom du concepteur *",
            value=st.session_state.infos_concepteur_nom,
            placeholder="Ex : Dupont",
        )
        st.session_state.infos_secteur = st.selectbox(
            "Secteur d'activité *",
            options=SECTEURS_DISPONIBLES,
            index=SECTEURS_DISPONIBLES.index(st.session_state.infos_secteur),
        )
 
        # Date : par défaut sur aujourd'hui au tout premier rendu
        valeur_date_defaut = st.session_state.infos_date or datetime.date.today()
        st.session_state.infos_date = st.date_input(
            "Date *",
            value=valeur_date_defaut,
        )
 
    st.caption("* Champs obligatoires")
 
    # ------------------------------------------------------------------
    # VALIDATION + NAVIGATION
    # ------------------------------------------------------------------
    st.divider()
 
    champs_ok = _champs_obligatoires_remplis()
 
    if not champs_ok:
        st.warning(
            "⚠️ Veuillez remplir tous les champs obligatoires (*) avant de continuer.",
            icon="⚠️",
        )
 
    col_suivant, col_skip, _ = st.columns([1, 1.4, 2])
 
    with col_suivant:
        if st.button("Suivant ➔", disabled=not champs_ok, use_container_width=True):
            st.session_state.bloc_actif = 2
            st.rerun()
 
    with col_skip:
        if st.button(
            "Passer à la configuration ➔",
            disabled=not champs_ok,
            use_container_width=True,
            help="Aller directement au Bloc 3 (utile si vous voulez d'abord configurer le logo).",
        ):
            st.session_state.bloc_actif = 3
            st.rerun()
 
