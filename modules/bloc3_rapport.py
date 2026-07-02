"""
BLOC 3 — Configuration du Rapport & Impression
=================================================
Rôle : personnalisation visuelle (logo, signature) et déclenchement
de la génération du PDF final.
 
Ce module NE CONTIENT PAS la logique de construction du PDF elle-même
(voir modules/pdf_generator.py) — il se contente de collecter les
éléments visuels et d'appeler le générateur.
"""
 
import streamlit as st
 
from modules.pdf_generator import generer_pdf_devis
from modules.excel_generator import generer_excel_devis
from modules.historique_devis import enregistrer_devis_dans_historique, afficher_historique
 
FORMATS_IMAGE_ACCEPTES = ["png", "jpg", "jpeg"]
 
 
def afficher_bloc3():
    st.subheader("🟦 Bloc 3 — Configuration du rapport")
 
    # ------------------------------------------------------------------
    # RÉSUMÉ EN LECTURE SEULE (transfert automatique des blocs 1 et 2)
    # ------------------------------------------------------------------
    st.markdown("### 📋 Résumé du devis")
 
    totaux = st.session_state.get(
        "devis_totaux",
        {"total_ht": 0.0, "montant_tva": 0.0, "total_ttc": 0.0},
    )
    devise = st.session_state.devis_devise
 
    col_a, col_b, col_c = st.columns(3)
    col_a.info(f"**Client**\n\n{st.session_state.infos_client_entreprise or '—'}")
    col_b.info(f"**Date**\n\n{st.session_state.infos_date or '—'}")
    col_c.info(f"**Total TTC**\n\n{totaux['total_ttc']:,.2f} {devise}")
 
    st.divider()
 
    # ------------------------------------------------------------------
    # PERSONNALISATION — LOGO
    # ------------------------------------------------------------------
    st.markdown("### 🖼️ Logo de l'entreprise")
    fichier_logo = st.file_uploader(
        "Insérez le logo de votre entreprise (PNG/JPG)",
        type=FORMATS_IMAGE_ACCEPTES,
        key="uploader_logo",
    )
    if fichier_logo is not None:
        st.session_state.rapport_logo_bytes = fichier_logo.getvalue()
        st.session_state.rapport_logo_nom_fichier = fichier_logo.name
        st.image(fichier_logo, caption="Aperçu du logo", width=150)
    elif st.session_state.rapport_logo_bytes is not None:
        st.image(
            st.session_state.rapport_logo_bytes,
            caption=f"Logo actuel : {st.session_state.rapport_logo_nom_fichier}",
            width=150,
        )
 
    st.divider()
 
    # ------------------------------------------------------------------
    # PERSONNALISATION — SIGNATURE
    # ------------------------------------------------------------------
    st.markdown("### ✍️ Signature")
    st.caption(
        "Pour cette version, importez une image de votre signature scannée "
        "ou photographiée (fond blanc de préférence)."
    )
    fichier_signature = st.file_uploader(
        "Importez votre signature (PNG/JPG)",
        type=FORMATS_IMAGE_ACCEPTES,
        key="uploader_signature",
    )
    if fichier_signature is not None:
        st.session_state.rapport_signature_bytes = fichier_signature.getvalue()
        st.session_state.rapport_signature_nom_fichier = fichier_signature.name
        st.image(fichier_signature, caption="Aperçu de la signature", width=200)
    elif st.session_state.rapport_signature_bytes is not None:
        st.image(
            st.session_state.rapport_signature_bytes,
            caption=f"Signature actuelle : {st.session_state.rapport_signature_nom_fichier}",
            width=200,
        )
 
    st.divider()
 
    # ------------------------------------------------------------------
    # GÉNÉRATION DU RAPPORT — PDF et Excel côte à côte
    # ------------------------------------------------------------------
    st.markdown("### 📄 Génération du rapport")
 
    # Dictionnaire d'infos partagé entre les deux générateurs, construit
    # une seule fois pour éviter la duplication.
    infos_devis = {
        "prenom": st.session_state.infos_concepteur_prenom,
        "nom": st.session_state.infos_concepteur_nom,
        "client": st.session_state.infos_client_entreprise,
        "secteur": st.session_state.infos_secteur,
        "pays": st.session_state.infos_pays,
        "date": st.session_state.infos_date,
    }
 
    col_pdf, col_excel = st.columns(2)
 
    with col_pdf:
        if st.button("🖨️ GÉNÉRER LE PDF", use_container_width=True, type="primary"):
            with st.spinner("Génération du PDF en cours..."):
                pdf_bytes = generer_pdf_devis(
                    infos=infos_devis,
                    lignes=st.session_state.devis_lignes,
                    totaux=totaux,
                    devise=devise,
                    taux_tva=st.session_state.devis_taux_tva,
                    logo_bytes=st.session_state.rapport_logo_bytes,
                    signature_bytes=st.session_state.rapport_signature_bytes,
                )
                st.session_state.rapport_pdf_bytes = pdf_bytes
            st.success("✅ PDF généré !")
            enregistrer_devis_dans_historique(
                infos=infos_devis,
                totaux=totaux,
                devise=devise,
                nb_lignes=len(st.session_state.devis_lignes),
            )
 
        if st.session_state.rapport_pdf_bytes is not None:
            nom_fichier_pdf = (
                f"Devis_{st.session_state.infos_client_entreprise or 'client'}"
                f"_{st.session_state.infos_date}.pdf".replace(" ", "_")
            )
            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=st.session_state.rapport_pdf_bytes,
                file_name=nom_fichier_pdf,
                mime="application/pdf",
                use_container_width=True,
            )
 
    with col_excel:
        if st.button("📊 GÉNÉRER L'EXCEL", use_container_width=True):
            with st.spinner("Génération de l'Excel en cours..."):
                excel_bytes = generer_excel_devis(
                    infos=infos_devis,
                    lignes=st.session_state.devis_lignes,
                    totaux=totaux,
                    devise=devise,
                    taux_tva=st.session_state.devis_taux_tva,
                )
                st.session_state.rapport_excel_bytes = excel_bytes
            st.success("✅ Excel généré !")
            enregistrer_devis_dans_historique(
                infos=infos_devis,
                totaux=totaux,
                devise=devise,
                nb_lignes=len(st.session_state.devis_lignes),
            )
 
        if st.session_state.get("rapport_excel_bytes") is not None:
            nom_fichier_excel = (
                f"Devis_{st.session_state.infos_client_entreprise or 'client'}"
                f"_{st.session_state.infos_date}.xlsx".replace(" ", "_")
            )
            st.download_button(
                label="⬇️ Télécharger l'Excel",
                data=st.session_state.rapport_excel_bytes,
                file_name=nom_fichier_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
 
    # ------------------------------------------------------------------
    # HISTORIQUE DE SESSION (comparaison rapide des derniers devis)
    # ------------------------------------------------------------------
    afficher_historique()
 
    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------
    st.divider()
    col_precedent, _ = st.columns([1, 3])
    with col_precedent:
        if st.button("⬅ Précédent", use_container_width=True):
            st.session_state.bloc_actif = 2
            st.rerun()
 