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
 
 
def _valeur_numerique_sure(valeur, defaut: float = 0.0) -> float:
    """
    Convertit une valeur en float de façon robuste, quelle que soit
    sa forme brute en provenance du DataGrid : None, chaîne vide "",
    chaîne non numérique, NaN (pandas), ou déjà un nombre valide.
 
    C'est le point de correction central du bug "None / nan" observé
    en production : une nouvelle ligne ajoutée au tableau est vide
    jusqu'à saisie de l'utilisateur, et cette vacuité peut prendre
    plusieurs formes selon le moment exact du rendu Streamlit. Un
    simple `float(x or 0)` ne couvre pas tous ces cas — celui-ci si.
    """
    if valeur is None:
        return defaut
    try:
        nombre = float(valeur)
        # pandas peut produire NaN (Not a Number) pour une cellule vide ;
        # float('nan') est un float VALIDE au sens Python, donc le try
        # ci-dessus ne l'intercepte pas — on le détecte explicitement.
        if nombre != nombre:  # une égalité fausse avec soi-même est LA signature de NaN
            return defaut
        return nombre
    except (ValueError, TypeError):
        # Chaîne vide "", texte non numérique, ou tout autre cas imprévu
        return defaut
 
 
def _dataframe_vers_lignes(df: pd.DataFrame) -> list[dict]:
    """Reconvertit le DataFrame édité par l'utilisateur en liste de dicts
    propre, en filtrant les lignes totalement vides (résidu de suppression)."""
    lignes = df.to_dict("records")
    lignes_propres = [
        ligne
        for ligne in lignes
        if str(ligne.get("Désignation", "") or "").strip() != ""
        or _valeur_numerique_sure(ligne.get("Quantité")) != 0
        or _valeur_numerique_sure(ligne.get("Prix unitaire")) != 0
    ]
    # Toujours garder au moins une ligne, même vide, pour que le tableau
    # ne disparaisse pas complètement si l'utilisateur efface tout.
    return lignes_propres or [
        {"Désignation": "", "Référence normative": "", "Quantité": 1.0, "Unité": "u", "Prix unitaire": 0.0}
    ]
 
 
def _calculer_totaux(lignes: list[dict], taux_tva: float) -> dict:
    """Calcule Total HT, Montant TVA et Total TTC à partir des lignes."""
    total_ht = sum(
        _valeur_numerique_sure(ligne.get("Quantité")) * _valeur_numerique_sure(ligne.get("Prix unitaire"))
        for ligne in lignes
    )
    taux_tva_sur = _valeur_numerique_sure(taux_tva)
    montant_tva = total_ht * (taux_tva_sur / 100)
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
    # CORRECTIF CRITIQUE v2 — cycle de vie du data_editor :
    #
    # PROBLÈME persistant malgré la v1 : repasser un DataFrame reconstruit
    # (même stocké dans notre propre session_state) en ARGUMENT à
    # st.data_editor à chaque rerun peut entrer en conflit avec l'état
    # interne que Streamlit garde sous la `key` fixe "editeur_devis" —
    # chaque objet DataFrame recréé a une identité Python différente
    # même à contenu égal, ce qui peut suffire à perturber la
    # persistance de la saisie (texte refusé, valeurs qui sautent).
    #
    # CORRECTIF v2 : on initialise les données UNE SEULE FOIS au tout
    # premier rendu, puis on n'appelle plus JAMAIS st.data_editor avec
    # un DataFrame explicite après coup — Streamlit gère alors l'état
    # entièrement lui-même via la clé, sans qu'on interfère à chaque
    # rerun. La colonne "Prix Total" est retirée du tableau éditable
    # (elle causait aussi une réinjection à chaque rerun) et affichée
    # séparément juste en dessous, en lecture seule.
    if "df_devis_source" not in st.session_state:
        df_init = pd.DataFrame(st.session_state.devis_lignes)
 
        # Typage explicite forcé : évite l'inférence ambiguë de pandas
        # quand une colonne texte ne contient au départ qu'une chaîne vide.
        for colonne_texte in ["Désignation", "Référence normative", "Unité"]:
            if colonne_texte in df_init.columns:
                df_init[colonne_texte] = df_init[colonne_texte].astype(str).replace("nan", "")
        for colonne_numerique in ["Quantité", "Prix unitaire"]:
            if colonne_numerique in df_init.columns:
                df_init[colonne_numerique] = df_init[colonne_numerique].apply(_valeur_numerique_sure)
 
        st.session_state.df_devis_source = df_init
 
    # IMPORTANT : à partir d'ici, on ne touche plus jamais
    # st.session_state.df_devis_source avant l'appel au widget.
    # st.data_editor lit son état interne via la clé "editeur_devis" ;
    # le paramètre positionnel n'est utilisé QUE lors du tout premier
    # rendu (quand aucun état n'existe encore sous cette clé).
    df_edite = st.data_editor(
        st.session_state.df_devis_source,
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
        },
        key="editeur_devis",
    )
 
    # On NE réécrit PLUS st.session_state.df_devis_source ici (c'était
    # la source du conflit). Streamlit maintient déjà l'état à jour en
    # interne sous la clé "editeur_devis" — df_edite, retourné par
    # l'appel ci-dessus, reflète toujours la dernière saisie de
    # l'utilisateur, sans qu'on ait besoin de le réinjecter nous-mêmes.
 
    # Calcul du Prix Total par ligne, affiché séparément en lecture
    # seule (retiré du tableau éditable pour éliminer tout risque de
    # conflit de state lié à cette colonne recalculée à chaque rerun).
    df_edite = df_edite.copy()
    df_edite["Prix Total"] = df_edite.apply(
        lambda ligne: _valeur_numerique_sure(ligne.get("Quantité"))
        * _valeur_numerique_sure(ligne.get("Prix unitaire")),
        axis=1,
    )
 
    with st.expander("📋 Aperçu des prix totaux par ligne", expanded=True):
        st.dataframe(
            df_edite[["Désignation", "Quantité", "Prix unitaire", "Prix Total"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prix Total": st.column_config.NumberColumn("Prix Total", format="%.2f"),
                "Prix unitaire": st.column_config.NumberColumn("Prix unitaire", format="%.2f"),
                "Quantité": st.column_config.NumberColumn("Quantité", format="%.2f"),
            },
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
 
