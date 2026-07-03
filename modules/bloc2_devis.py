"""
BLOC 2 — Moteur Mathématique de Devis
=======================================
Rôle : c'est le cœur de l'outil. L'utilisateur construit son devis
ligne par ligne dans un tableau interactif (st.data_editor), et
l'application recalcule automatiquement tous les totaux.

Structure de chaque ligne (dictionnaire) :
    {
        "Désignation": str,
        "Référence normative": str,
        "Quantité": float,
        "Unité": str,
        "Prix unitaire": float,
    }

Le "Prix Total" et le "N°" ne sont PAS stockés dans les données brutes :
ils sont recalculés à l'affichage pour garantir qu'ils sont toujours
exacts, même si l'utilisateur modifie une quantité après coup.
"""

import pandas as pd
import streamlit as st

UNITES_DISPONIBLES = ["u", "m", "kg", "lot", "forfait"]
DEVISES_DISPONIBLES = ["FCFA (XAF)", "Euro (EUR)", "Dollar US (USD)", "Autre (préciser)"]


def _dataframe_vers_lignes(df: pd.DataFrame) -> list[dict]:
    """Reconvertit le DataFrame édité par l'utilisateur en liste de dicts
    propre, en filtrant les lignes totalement vides (résidu de suppression)."""
    lignes = df.to_dict("records")
    lignes_propres = [
        ligne
        for ligne in lignes
        if str(ligne.get("Désignation", "")).strip() != ""
        or float(ligne.get("Quantité", 0) or 0) != 0
        or float(ligne.get("Prix unitaire", 0) or 0) != 0
    ]
    # Toujours garder au moins une ligne, même vide, pour que le tableau
    # ne disparaisse pas complètement si l'utilisateur efface tout.
    return lignes_propres or [
        {"Désignation": "", "Référence normative": "", "Quantité": 1.0, "Unité": "u", "Prix unitaire": 0.0}
    ]


def _calculer_totaux(lignes: list[dict], taux_tva: float) -> dict:
    """Calcule Total HT, Montant TVA et Total TTC à partir des lignes."""
    total_ht = sum(
        float(ligne.get("Quantité", 0) or 0) * float(ligne.get("Prix unitaire", 0) or 0)
        for ligne in lignes
    )
    montant_tva = total_ht * (taux_tva / 100)
    total_ttc = total_ht + montant_tva
    return {"total_ht": total_ht, "montant_tva": montant_tva, "total_ttc": total_ttc}


def afficher_bloc2():
    st.subheader("🟦 Bloc 2 — Moteur de devis")
    st.write(
        "Ajoutez vos lignes de devis. Le prix total par ligne et les totaux "
        "généraux se recalculent automatiquement."
    )

    # ------------------------------------------------------------------
    # SÉLECTEUR DE DEVISE (posé avant le tableau, discret)
    # ------------------------------------------------------------------
    col_devise, col_tva = st.columns(2)
    with col_devise:
        devise_choisie = st.selectbox(
            "Devise du devis",
            options=DEVISES_DISPONIBLES,
            index=DEVISES_DISPONIBLES.index(st.session_state.devis_devise)
            if st.session_state.devis_devise in DEVISES_DISPONIBLES
            else 0,
        )
        if devise_choisie == "Autre (préciser)":
            devise_choisie = st.text_input(
                "Précisez la devise", value="", placeholder="Ex : Franc CFA (XOF)"
            ) or "Autre"
        st.session_state.devis_devise = devise_choisie

    # ------------------------------------------------------------------
    # TABLEAU INTERACTIF (DataGrid)
    # ------------------------------------------------------------------
    df_source = pd.DataFrame(st.session_state.devis_lignes)

    # On ajoute une colonne d'affichage "Prix Total" calculée à la volée,
    # visible mais non éditable (comme demandé dans le cahier des charges).
    df_source["Prix Total"] = (
        df_source["Quantité"].astype(float) * df_source["Prix unitaire"].astype(float)
    )

    df_edite = st.data_editor(
        df_source,
        num_rows="dynamic",  # autorise l'ajout/suppression de lignes directement dans le tableau
        use_container_width=True,
        hide_index=True,
        column_config={
            "Désignation": st.column_config.TextColumn(
                "Désignation", help="Nom du composant ou de l'équipement", width="large"
            ),
            "Référence normative": st.column_config.TextColumn(
                "Référence normative", help="Ex : IEC 60364, IP65", width="medium"
            ),
            "Quantité": st.column_config.NumberColumn(
                "Quantité", min_value=0.0, step=1.0, format="%.2f"
            ),
            "Unité": st.column_config.SelectboxColumn(
                "Unité", options=UNITES_DISPONIBLES
            ),
            "Prix unitaire": st.column_config.NumberColumn(
                "Prix unitaire", min_value=0.0, step=100.0, format="%.2f"
            ),
            "Prix Total": st.column_config.NumberColumn(
                "Prix Total", format="%.2f", disabled=True  # verrouillé, calcul automatique
            ),
        },
        key="editeur_devis",
    )

    # On retire la colonne calculée avant de sauvegarder dans le session_state
    # (elle sera recalculée à chaque rendu, pas besoin de la stocker).
    df_a_sauvegarder = df_edite.drop(columns=["Prix Total"], errors="ignore")
    st.session_state.devis_lignes = _dataframe_vers_lignes(df_a_sauvegarder)

    st.caption(
        "💡 Utilisez le bouton **+** en bas du tableau pour ajouter une ligne, "
        "ou la case à cocher à gauche d'une ligne pour la supprimer."
    )

    # ------------------------------------------------------------------
    # ZONE DE SYNTHÈSE
    # ------------------------------------------------------------------
    st.divider()
    st.markdown("### 📊 Synthèse")

    st.session_state.devis_taux_tva = st.number_input(
        "Taux de TVA (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.devis_taux_tva),
        step=0.25,
        format="%.2f",
    )

    totaux = _calculer_totaux(st.session_state.devis_lignes, st.session_state.devis_taux_tva)
    devise = st.session_state.devis_devise

    col_ht, col_tva_montant, col_ttc = st.columns(3)
    col_ht.metric("Total Hors Taxe", f"{totaux['total_ht']:,.2f} {devise}")
    col_tva_montant.metric(
        f"Montant TVA ({st.session_state.devis_taux_tva:.2f}%)",
        f"{totaux['montant_tva']:,.2f} {devise}",
    )
    col_ttc.metric(
        "TOTAL GÉNÉRAL TTC",
        f"{totaux['total_ttc']:,.2f} {devise}",
    )

    # On stocke les totaux calculés pour que le Bloc 3 puisse les
    # afficher en lecture seule sans tout recalculer.
    st.session_state.devis_totaux = totaux

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------
    st.divider()
    col_precedent, col_suivant, _ = st.columns([1, 1, 2])

    with col_precedent:
        if st.button("⬅ Précédent", use_container_width=True):
            st.session_state.bloc_actif = 1
            st.rerun()

    with col_suivant:
        if st.button("Suivant ➔", use_container_width=True):
            st.session_state.bloc_actif = 3
            st.rerun()
