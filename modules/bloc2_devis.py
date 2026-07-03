"""
BLOC 2 — Moteur Mathématique de Devis
=======================================
Rôle : c'est le cœur de l'outil. L'utilisateur construit son devis
ligne par ligne, et l'application recalcule automatiquement tous
les totaux.
 
CHOIX D'ARCHITECTURE — pourquoi pas de tableau data_editor :
Les deux premières versions de ce module utilisaient st.data_editor
(un vrai DataGrid). Ce composant s'est révélé instable en production
sur cet environnement précis : certaines colonnes de texte refusaient
la saisie de lettres, et les valeurs se réinitialisaient après un
changement de ligne. Deux tentatives de correction ciblée n'ont pas
résolu le problème.
 
Ce module utilise donc une architecture plus simple et plus verbeuse,
mais structurellement fiable : CHAQUE ligne de devis est une série de
champs de saisie individuels (st.text_input, st.number_input,
st.selectbox), chacun avec sa PROPRE clé stable et unique
(ex: "quantite_ligne_2"). Ce sont des composants Streamlit basiques,
avec un comportement extremement previsible et documente.
 
Structure de chaque ligne (dictionnaire), INCHANGEE par rapport aux
versions precedentes — le reste de l'application (Bloc 3, export
JSON, PDF, Excel) n'a donc besoin d'AUCUNE modification :
    {
        "Designation": str,
        "Reference normative": str,
        "Quantite": float,
        "Unite": str,
        "Prix unitaire": float,
    }
 
Chaque ligne possede en interne un identifiant stable unique
("_id_ligne") qui sert de racine aux cles des widgets de cette ligne.
Cet identifiant n'est JAMAIS reindexe (contrairement a la position
dans la liste), ce qui garantit qu'une ligne garde le meme etat meme
si une autre ligne, plus haut dans le tableau, est supprimee.
"""
 
import uuid
 
import streamlit as st
 
UNITES_DISPONIBLES = ["u", "m", "kg", "lot", "forfait"]
DEVISES_DISPONIBLES = ["FCFA (XAF)", "Euro (EUR)", "Dollar US (USD)", "Autre (préciser)"]
 
 
def _valeur_numerique_sure(valeur, defaut: float = 0.0) -> float:
    """
    Convertit une valeur en float de façon robuste, quelle que soit
    sa forme brute : None, chaîne vide "", chaîne non numérique, NaN,
    ou déjà un nombre valide. Conservée depuis les versions précédentes
    car toujours utile pour les calculs de synthèse.
    """
    if valeur is None:
        return defaut
    try:
        nombre = float(valeur)
        if nombre != nombre:  # détection NaN : seule valeur jamais égale à elle-même
            return defaut
        return nombre
    except (ValueError, TypeError):
        return defaut
 
 
def _garantir_id_lignes():
    """
    S'assure que chaque ligne de st.session_state.devis_lignes possède
    un identifiant stable "_id_ligne". Les brouillons importés (JSON)
    ou les données d'une session précédente peuvent ne pas en avoir —
    on les génère alors à la volée, une seule fois.
    """
    for ligne in st.session_state.devis_lignes:
        if "_id_ligne" not in ligne:
            ligne["_id_ligne"] = uuid.uuid4().hex[:8]
 
 
def _ajouter_ligne():
    """Ajoute une nouvelle ligne vide à la fin du devis."""
    st.session_state.devis_lignes.append(
        {
            "_id_ligne": uuid.uuid4().hex[:8],
            "Désignation": "",
            "Référence normative": "",
            "Quantité": 1.0,
            "Unité": "u",
            "Prix unitaire": 0.0,
        }
    )
 
 
def _supprimer_ligne(id_ligne: str):
    """Supprime la ligne correspondant à cet identifiant stable."""
    st.session_state.devis_lignes = [
        ligne for ligne in st.session_state.devis_lignes if ligne.get("_id_ligne") != id_ligne
    ]
    # On garde toujours au moins une ligne pour que le formulaire ne
    # disparaisse jamais complètement.
    if not st.session_state.devis_lignes:
        _ajouter_ligne()
 
 
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
 
    _garantir_id_lignes()
 
    # ------------------------------------------------------------------
    # SÉLECTEUR DE DEVISE
    # ------------------------------------------------------------------
    col_devise, _ = st.columns(2)
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
 
    st.divider()
 
    # ------------------------------------------------------------------
    # EN-TÊTE DES COLONNES (purement visuel, pas de widget ici)
    # ------------------------------------------------------------------
    col_n, col_desig, col_ref, col_qte, col_unite, col_prix, col_total, col_suppr = st.columns(
        [0.4, 2.2, 1.6, 1, 0.9, 1.3, 1.3, 0.5]
    )
    col_n.markdown("**N°**")
    col_desig.markdown("**Désignation**")
    col_ref.markdown("**Réf. normative**")
    col_qte.markdown("**Qté**")
    col_unite.markdown("**Unité**")
    col_prix.markdown("**Prix unit.**")
    col_total.markdown("**Prix Total**")
    col_suppr.markdown("**​**")  # espace réservé, pas de titre nécessaire
 
    # ------------------------------------------------------------------
    # UNE RANGÉE DE CHAMPS DE SAISIE PAR LIGNE DE DEVIS
    # ------------------------------------------------------------------
    # Chaque widget a une clé bâtie sur l'identifiant STABLE de la ligne
    # (ligne["_id_ligne"]), jamais sur sa position dans la liste. C'est
    # ce qui garantit qu'une ligne conserve son état correctement même
    # après suppression d'une autre ligne au-dessus d'elle.
    id_ligne_a_supprimer = None
 
    for numero, ligne in enumerate(st.session_state.devis_lignes, start=1):
        id_ligne = ligne["_id_ligne"]
 
        col_n, col_desig, col_ref, col_qte, col_unite, col_prix, col_total, col_suppr = st.columns(
            [0.4, 2.2, 1.6, 1, 0.9, 1.3, 1.3, 0.5]
        )
 
        col_n.markdown(f"<div style='padding-top: 0.6rem;'>{numero}</div>", unsafe_allow_html=True)
 
        ligne["Désignation"] = col_desig.text_input(
            "Désignation", value=ligne.get("Désignation", ""), key=f"desig_{id_ligne}",
            label_visibility="collapsed", placeholder="Ex : Câble 3G2.5",
        )
        ligne["Référence normative"] = col_ref.text_input(
            "Référence normative", value=ligne.get("Référence normative", ""), key=f"ref_{id_ligne}",
            label_visibility="collapsed", placeholder="Ex : IEC 60364",
        )
        ligne["Quantité"] = col_qte.number_input(
            "Quantité", value=_valeur_numerique_sure(ligne.get("Quantité"), 1.0),
            min_value=0.0, step=1.0, format="%.2f", key=f"qte_{id_ligne}",
            label_visibility="collapsed",
        )
        unite_actuelle = ligne.get("Unité", "u")
        ligne["Unité"] = col_unite.selectbox(
            "Unité", options=UNITES_DISPONIBLES,
            index=UNITES_DISPONIBLES.index(unite_actuelle) if unite_actuelle in UNITES_DISPONIBLES else 0,
            key=f"unite_{id_ligne}", label_visibility="collapsed",
        )
        ligne["Prix unitaire"] = col_prix.number_input(
            "Prix unitaire", value=_valeur_numerique_sure(ligne.get("Prix unitaire")),
            min_value=0.0, step=100.0, format="%.2f", key=f"prix_{id_ligne}",
            label_visibility="collapsed",
        )
 
        # Prix Total : calcul en lecture seule, jamais un widget de saisie
        # (donc aucun risque de conflit d'état ici, c'est du texte statique)
        prix_total_ligne = _valeur_numerique_sure(ligne.get("Quantité")) * _valeur_numerique_sure(
            ligne.get("Prix unitaire")
        )
        col_total.markdown(
            f"<div style='padding-top: 0.6rem; font-weight: 600;'>{prix_total_ligne:,.2f}</div>",
            unsafe_allow_html=True,
        )
 
        # Bouton de suppression — ne supprime pas immédiatement pendant
        # la boucle (modifier une liste qu'on parcourt cause des bugs) ;
        # on mémorise l'identifiant et on supprime après la boucle.
        if col_suppr.button("🗑️", key=f"suppr_{id_ligne}", help="Supprimer cette ligne"):
            id_ligne_a_supprimer = id_ligne
 
    if id_ligne_a_supprimer is not None:
        _supprimer_ligne(id_ligne_a_supprimer)
        st.rerun()
 
    # ------------------------------------------------------------------
    # BOUTON D'AJOUT DE LIGNE
    # ------------------------------------------------------------------
    st.button("➕ Ajouter une ligne", on_click=_ajouter_ligne, use_container_width=False)
 
    st.divider()
 
    # ------------------------------------------------------------------
    # ZONE DE SYNTHÈSE
    # ------------------------------------------------------------------
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
