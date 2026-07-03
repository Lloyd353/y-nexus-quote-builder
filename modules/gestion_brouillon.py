"""
Gestion du Brouillon — Export / Import JSON
==============================================
Remplace l'usage de streamlit-local-storage (composant tiers peu
maintenu) par une solution 100% native : l'utilisateur télécharge
un fichier .json contenant l'état complet de son devis, qu'il peut
ensuite réimporter pour reprendre exactement là où il s'était arrêté.
 
Aucune dépendance externe : uniquement la librairie standard `json`.
 
Le fichier JSON généré contient TOUTES les données des 3 blocs
(métadonnées, lignes de devis, devise, TVA). Les images (logo,
signature) ne sont PAS incluses dans le JSON — elles sont trop
volumineuses pour ce format et doivent être réimportées séparément
si besoin (voir note dans importer_brouillon).
"""
 
import json
import datetime
 
import streamlit as st
 
 
def _convertir_pour_json(valeur):
    """
    json.dumps() ne sait pas sérialiser un objet datetime.date nativement.
    Cette fonction convertit les types non supportés en chaînes de
    caractères ISO (format universel, facile à reconvertir ensuite).
    """
    if isinstance(valeur, (datetime.date, datetime.datetime)):
        return valeur.isoformat()
    return valeur
 
 
def construire_brouillon_dict() -> dict:
    """
    Rassemble toutes les données du session_state pertinentes pour
    un brouillon, dans un dictionnaire propre et versionné.
 
    Le champ 'version_format' permet, si un jour la structure du
    brouillon change, de détecter et gérer d'anciens fichiers exportés
    par une version antérieure de l'application.
    """
    return {
        "version_format": "1.0",
        "date_export": datetime.datetime.now().isoformat(),
        "infos": {
            "prenom": st.session_state.infos_concepteur_prenom,
            "nom": st.session_state.infos_concepteur_nom,
            "client": st.session_state.infos_client_entreprise,
            "secteur": st.session_state.infos_secteur,
            "pays": st.session_state.infos_pays,
            "date": _convertir_pour_json(st.session_state.infos_date),
        },
        "devis": {
            # On retire le champ technique "_id_ligne" (identifiant
            # interne utilisé par bloc2_devis.py pour la stabilité des
            # widgets) avant export — il n'a aucune utilité pour
            # l'utilisateur et n'a pas besoin d'être dans le brouillon.
            "lignes": [
                {cle: valeur for cle, valeur in ligne.items() if cle != "_id_ligne"}
                for ligne in st.session_state.devis_lignes
            ],
            "devise": st.session_state.devis_devise,
            "taux_tva": st.session_state.devis_taux_tva,
        },
    }
 
 
def exporter_brouillon_json() -> str:
    """Retourne le brouillon actuel sous forme de chaîne JSON indentée
    (lisible si quelqu'un l'ouvre dans un éditeur de texte)."""
    brouillon = construire_brouillon_dict()
    return json.dumps(brouillon, indent=2, ensure_ascii=False)
 
 
def importer_brouillon(fichier_json_bytes: bytes) -> tuple[bool, str]:
    """
    Charge un brouillon depuis des bytes JSON et remplit le session_state.
 
    Retourne un tuple (succes: bool, message: str) pour que l'appelant
    (bloc1_infos.py) puisse afficher un message clair à l'utilisateur,
    que l'import réussisse ou échoue.
    """
    try:
        brouillon = json.loads(fichier_json_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "❌ Fichier invalide : ce n'est pas un brouillon Y-NEXUS valide (JSON illisible)."
 
    # Vérification minimale de structure — évite un plantage si quelqu'un
    # importe un JSON qui n'a rien à voir avec un brouillon de devis.
    if "infos" not in brouillon or "devis" not in brouillon:
        return False, "❌ Fichier invalide : structure de brouillon non reconnue."
 
    try:
        infos = brouillon["infos"]
        st.session_state.infos_concepteur_prenom = infos.get("prenom", "")
        st.session_state.infos_concepteur_nom = infos.get("nom", "")
        st.session_state.infos_client_entreprise = infos.get("client", "")
        st.session_state.infos_secteur = infos.get("secteur", "Énergie")
        st.session_state.infos_pays = infos.get("pays", "")
 
        # Reconversion de la date : elle a été stockée en texte ISO
        # (ex: "2026-07-01"), on la reconvertit en objet date réel
        # pour que st.date_input puisse l'utiliser directement.
        date_str = infos.get("date")
        if date_str:
            st.session_state.infos_date = datetime.date.fromisoformat(date_str)
 
        devis = brouillon["devis"]
        st.session_state.devis_lignes = devis.get("lignes", [])
        st.session_state.devis_devise = devis.get("devise", "FCFA (XAF)")
        st.session_state.devis_taux_tva = devis.get("taux_tva", 19.25)
 
        # IMPORTANT : on efface le tableau mis en cache du Bloc 2 (s'il
        # existe) pour forcer sa reconstruction à partir des données
        # fraîchement importées ci-dessus. Sans cette ligne, un import
        # de brouillon après une première visite du Bloc 2 laisserait
        # l'ancien tableau affiché, ignorant silencieusement l'import.
        st.session_state.pop("df_devis_source", None)
 
        return True, "✅ Brouillon importé avec succès ! Vos données ont été restaurées."
 
    except (KeyError, ValueError, TypeError) as erreur:
        # Filet de sécurité : si la structure interne est corrompue
        # d'une façon imprévue, on informe plutôt que de faire planter l'app.
        return False, f"❌ Erreur lors de la lecture du brouillon : {erreur}"
 
 
def afficher_widget_export_import():
    """
    Composant réutilisable affichant les boutons d'export et d'import
    du brouillon. Conçu pour être appelé depuis le Bloc 1 (en haut de
    parcours, pour que l'utilisateur puisse reprendre un devis dès
    l'ouverture de l'app) ET optionnellement ailleurs si besoin.
    """
    with st.expander("💾 Sauvegarder / Reprendre un brouillon", expanded=False):
        st.caption(
            "Téléchargez votre devis en cours pour le reprendre plus tard, "
            "ou réimportez un brouillon précédemment sauvegardé. "
            "⚠️ Le logo et la signature ne sont pas inclus dans le brouillon : "
            "vous devrez les réimporter manuellement au Bloc 3."
        )
 
        col_export, col_import = st.columns(2)
 
        with col_export:
            nom_fichier_export = (
                f"brouillon_devis_{st.session_state.infos_client_entreprise or 'sans_nom'}"
                f".json".replace(" ", "_")
            )
            st.download_button(
                label="⬇️ Exporter le brouillon",
                data=exporter_brouillon_json(),
                file_name=nom_fichier_export,
                mime="application/json",
                use_container_width=True,
            )
 
        with col_import:
            fichier_importe = st.file_uploader(
                "Réimporter un brouillon (.json)",
                type=["json"],
                key="uploader_brouillon",
                label_visibility="collapsed",
            )
            if fichier_importe is not None:
                # On utilise une clé de session pour éviter de réimporter
                # en boucle le même fichier à chaque rerun de Streamlit.
                cle_dernier_import = "dernier_brouillon_importe_nom"
                if st.session_state.get(cle_dernier_import) != fichier_importe.name:
                    succes, message = importer_brouillon(fichier_importe.getvalue())
                    st.session_state[cle_dernier_import] = fichier_importe.name
                    if succes:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
