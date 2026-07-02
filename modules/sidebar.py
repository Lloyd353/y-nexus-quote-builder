"""
Sidebar — Zone Cross-Selling
==============================
Rôle : mettre en avant 4 outils de la suite Y-NEXUS pour inciter
les visiteurs de l'outil gratuit à découvrir la boutique payante.
 
Présente en permanence, sur toutes les pages/blocs de l'application.
"""
 
import streamlit as st
 
LIEN_BOUTIQUE = "https://selar.com/m/y-nexus-industrial-group1"
EMAIL_GROUPE = "supportpro.ynexus@gmail.com"
 
# On met ici 4 outils parmi les 14 — vous pouvez facilement changer
# la sélection en modifiant cette liste. J'ai choisi une combinaison
# qui couvre 3 filières différentes (Électrotechnique, Énergie,
# Réseaux, Instrumentation) pour montrer la largeur de votre offre
# plutôt que 4 outils très proches les uns des autres.
OUTILS_MIS_EN_AVANT = [
    {
        "nom": "Power-Supply Designer",
        "description": "Dimensionnement des alimentations à découpage (Buck, Boost, Flyback).",
        "norme": "IEC 61204",
    },
    {
        "nom": "Sun-Gen Designer",
        "description": "Dimensionnement complet de parcs solaires photovoltaïques.",
        "norme": "IEC 62446",
    },
    {
        "nom": "Instrument-Picker",
        "description": "Sélection et calibration des capteurs industriels (Zone ATEX).",
        "norme": "IEC 60079",
    },
    {
        "nom": "Safety-SIL Calculator",
        "description": "Évaluation du niveau de performance de sécurité des machines.",
        "norme": "IEC 61508 / ISO 13849",
    },
]
 
 
def afficher_sidebar():
    with st.sidebar:
        st.markdown("## ⚡ Y-NEXUS INDUSTRIAL GROUP")
        st.markdown(
            "*Y-NEXUS INDUSTRIAL GROUP conçoit des solutions d'ingénierie "
            "chirurgicales pour accélérer vos projets.*"
        )
 
        st.divider()
        st.markdown("### 🛠️ Découvrez notre suite complète")
        st.caption("14 outils de calcul professionnels sur Excel")
 
        for outil in OUTILS_MIS_EN_AVANT:
            with st.container(border=True):
                st.markdown(f"**{outil['nom']}**")
                st.caption(outil["description"])
                st.caption(f"📐 Norme : {outil['norme']}")
 
        st.divider()
 
        # Appel à l'action principal
        st.link_button(
            "🛒 Voir tous les outils sur Selar",
            url=LIEN_BOUTIQUE,
            use_container_width=True,
            type="primary",
        )
 
        st.divider()
        st.caption(f"📧 Contact : {EMAIL_GROUPE}")
 