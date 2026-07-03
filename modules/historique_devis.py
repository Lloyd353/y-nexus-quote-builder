"""
Historique des Devis (Session)
=================================
Conserve un historique des 5 derniers devis générés au cours de la
session en cours, pour permettre une comparaison rapide sans avoir
à ressaisir les informations.
 
IMPORTANT — Portée de cette fonctionnalité : l'historique vit UNIQUEMENT
dans st.session_state, donc UNIQUEMENT en mémoire, pour la durée de vie
de l'onglet du navigateur. Si l'utilisateur ferme l'onglet, rafraîchit
la page (F5), ou change d'appareil, l'historique est définitivement
perdu. Ce n'est PAS une base de données persistante — pour une vraie
persistance inter-session, il faudrait une base de données côté serveur
(hors périmètre de cette V1, mais mentionné en piste d'évolution).
"""
 
import datetime
 
import streamlit as st
 
NOMBRE_MAX_HISTORIQUE = 5
 
 
def enregistrer_devis_dans_historique(
    infos: dict, totaux: dict, devise: str, nb_lignes: int
):
    """
    Ajoute une entrée à l'historique de la session, après chaque
    génération réussie de PDF ou Excel. Appelée depuis bloc3_rapport.py.
 
    On ne stocke qu'un RÉSUMÉ (pas les lignes complètes du devis, pas
    le logo, pas la signature) pour garder l'historique léger — son
    seul but est la comparaison rapide, pas la régénération de documents.
    """
    st.session_state.setdefault("historique_devis", [])
 
    entree = {
        "horodatage": datetime.datetime.now().strftime("%H:%M:%S"),
        "client": infos.get("client") or "Client non renseigné",
        "secteur": infos.get("secteur", "—"),
        "nb_lignes": nb_lignes,
        "total_ht": totaux.get("total_ht", 0.0),
        "total_ttc": totaux.get("total_ttc", 0.0),
        "devise": devise,
    }
 
    # On insère en tête de liste (le plus récent en premier)
    st.session_state.historique_devis.insert(0, entree)
 
    # On garde uniquement les N plus récents, pour éviter que l'historique
    # ne grossisse indéfiniment au fil d'une longue session de travail.
    st.session_state.historique_devis = st.session_state.historique_devis[:NOMBRE_MAX_HISTORIQUE]
 
 
def afficher_historique():
    """
    Affiche l'historique sous forme de tableau comparatif compact.
    Conçu pour être appelé depuis le Bloc 3, après la zone de génération.
    N'affiche rien si l'historique est vide (premier devis de la session).
    """
    historique = st.session_state.get("historique_devis", [])
 
    if not historique:
        return  # Rien à afficher — pas la peine de montrer une section vide
 
    st.divider()
    with st.expander(f"🕒 Historique de cette session ({len(historique)} devis)", expanded=False):
        st.caption(
            "⚠️ Cet historique est temporaire : il est perdu si vous fermez "
            "l'onglet ou rafraîchissez la page. Utilisez l'export JSON "
            "(Bloc 1) pour une sauvegarde durable."
        )
 
        for i, entree in enumerate(historique):
            libelle_position = "Devis actuel" if i == 0 else f"Devis n°{len(historique) - i}"
            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 2])
                col_a.markdown(f"**{libelle_position}**")
                col_a.caption(f"🕒 {entree['horodatage']}")
                col_b.markdown(f"**{entree['client']}**")
                col_b.caption(f"{entree['secteur']} · {entree['nb_lignes']} ligne(s)")
                col_c.metric("Total HT", f"{entree['total_ht']:,.0f} {entree['devise']}", label_visibility="visible")
                col_d.metric("Total TTC", f"{entree['total_ttc']:,.0f} {entree['devise']}", label_visibility="visible")
 
