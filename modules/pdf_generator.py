"""
Générateur PDF — Y-NEXUS QUOTE BUILDER
=========================================
Construit le devis PDF final avec FPDF2.
 
Structure du document généré :
    1. En-tête avec logo (si fourni)
    2. Titre + informations générales (client, date, secteur...)
    3. Tableau des lignes de devis
    4. Zone de synthèse (Total HT / TVA / TTC)
    5. Zone de signature
    6. Filigrane de bas de page sur CHAQUE page (via footer())
 
FPDF2 fonctionne en coordonnées (x, y) en millimètres, origine en haut
à gauche de la page. C'est différent de la logique HTML/CSS habituelle,
donc chaque positionnement est commenté.
"""
 
import io
import tempfile
import os
 
import qrcode
from fpdf import FPDF
 
# ----------------------------------------------------------------------
# CONSTANTES DE MISE EN PAGE
# ----------------------------------------------------------------------
COULEUR_BLEU_PROFOND = (27, 58, 92)      # #1B3A5C — même bleu que le thème Streamlit
COULEUR_GRIS_ANTHRACITE = (43, 47, 54)    # #2B2F36
COULEUR_GRIS_CLAIR = (247, 248, 250)      # #F7F8FA — fond des en-têtes de tableau
COULEUR_TEXTE_CLAIR = (255, 255, 255)
 
LIEN_BOUTIQUE = "https://selar.com/m/y-nexus-industrial-group1"
EMAIL_GROUPE = "supportpro.ynexus@gmail.com"
NOM_GROUPE = "Y-NEXUS INDUSTRIAL GROUP"
 
 
class DevisPDF(FPDF):
    """
    Sous-classe de FPDF pour injecter automatiquement le filigrane
    en bas de CHAQUE page, sans avoir à y penser manuellement à chaque
    fois qu'on ajoute une page. FPDF2 appelle footer() tout seul.
    """
 
    def footer(self):
        # Se positionne à 15mm du bas de la page, quelle que soit sa hauteur
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 140)  # gris discret, non intrusif
        texte_filigrane = (
            f"Genere via le logiciel d'ingenierie {NOM_GROUPE} - {LIEN_BOUTIQUE}"
        )
        self.cell(0, 10, texte_filigrane, align="C")
 
 
def _sauvegarder_image_temporaire(image_bytes: bytes, suffixe: str) -> str:
    """
    FPDF2 a besoin d'un CHEMIN de fichier pour insérer une image, pas
    directement des bytes en mémoire. On écrit donc un fichier temporaire
    sur disque, dont le chemin est retourné pour être utilisé par pdf.image().
    L'appelant est responsable de supprimer ce fichier après usage.
    """
    fichier_temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffixe)
    fichier_temp.write(image_bytes)
    fichier_temp.close()
    return fichier_temp.name
 
 
def _generer_qrcode_boutique_bytes() -> bytes:
    """
    Génère un QR code pointant vers la boutique Selar et retourne
    directement ses bytes PNG (pas besoin de fichier temporaire séparé
    ici : la lib qrcode sait écrire dans un buffer io.BytesIO).
 
    box_size=6 et border=2 donnent un QR code compact mais net,
    adapté à un espace réduit en bas de PDF (environ 25x25mm à l'impression).
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(LIEN_BOUTIQUE)
    qr.make(fit=True)
 
    image_qr = qr.make_image(fill_color=f"#{COULEUR_BLEU_PROFOND[0]:02x}{COULEUR_BLEU_PROFOND[1]:02x}{COULEUR_BLEU_PROFOND[2]:02x}", back_color="white")
 
    tampon = io.BytesIO()
    image_qr.save(tampon, format="PNG")
    return tampon.getvalue()
 
 
def generer_pdf_devis(
    infos: dict,
    lignes: list[dict],
    totaux: dict,
    devise: str,
    taux_tva: float,
    logo_bytes: bytes | None = None,
    signature_bytes: bytes | None = None,
) -> bytes:
    """
    Fonction principale : construit le PDF complet et retourne les
    bytes finaux, prêts à être servis via st.download_button.
 
    Args:
        infos: dict avec prenom, nom, client, secteur, pays, date
        lignes: liste des lignes de devis (Désignation, Référence normative,
                Quantité, Unité, Prix unitaire)
        totaux: dict avec total_ht, montant_tva, total_ttc
        devise: chaîne de la devise choisie (ex: "FCFA (XAF)")
        taux_tva: taux de TVA en pourcentage
        logo_bytes: bytes de l'image du logo, ou None
        signature_bytes: bytes de l'image de la signature, ou None
 
    Returns:
        bytes du PDF final
    """
    pdf = DevisPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=25)  # 25mm de marge basse pour laisser la place au filigrane
    pdf.add_page()
 
    fichiers_temporaires_a_supprimer = []
 
    try:
        # ------------------------------------------------------------
        # EN-TÊTE : Logo (si fourni) + Titre
        # ------------------------------------------------------------
        if logo_bytes:
            chemin_logo = _sauvegarder_image_temporaire(logo_bytes, ".png")
            fichiers_temporaires_a_supprimer.append(chemin_logo)
            # Logo en haut à droite, taille contenue à 35mm de large
            pdf.image(chemin_logo, x=165, y=10, w=35)
 
        pdf.set_xy(10, 12)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(*COULEUR_BLEU_PROFOND)
        pdf.cell(0, 10, "DEVIS", ln=True)
 
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
        pdf.set_x(10)
        pdf.cell(0, 6, NOM_GROUPE, ln=True)
 
        pdf.ln(8)
 
        # ------------------------------------------------------------
        # BLOC INFORMATIONS GÉNÉRALES
        # ------------------------------------------------------------
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
 
        date_str = infos["date"].strftime("%d/%m/%Y") if infos.get("date") else "-"
 
        lignes_infos = [
            ("Concepteur", f"{infos.get('prenom', '')} {infos.get('nom', '')}".strip() or "-"),
            ("Client", infos.get("client") or "-"),
            ("Secteur d'activité", infos.get("secteur") or "-"),
            ("Pays", infos.get("pays") or "-"),
            ("Date", date_str),
        ]
 
        pdf.set_font("Helvetica", "", 10)
        for etiquette, valeur in lignes_infos:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(45, 7, f"{etiquette} :", border=0)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, str(valeur), ln=True)
 
        pdf.ln(6)
 
        # ------------------------------------------------------------
        # TABLEAU DES LIGNES DE DEVIS
        # ------------------------------------------------------------
        # Largeurs de colonnes (en mm), somme = 190mm (largeur utile A4 avec marges 10mm)
        largeurs_colonnes = {
            "n": 10,
            "designation": 55,
            "reference": 30,
            "quantite": 18,
            "unite": 15,
            "prix_unitaire": 30,
            "prix_total": 32,
        }
 
        def _entete_tableau():
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(*COULEUR_BLEU_PROFOND)
            pdf.set_text_color(*COULEUR_TEXTE_CLAIR)
            pdf.cell(largeurs_colonnes["n"], 8, "N°", border=1, align="C", fill=True)
            pdf.cell(largeurs_colonnes["designation"], 8, "Désignation", border=1, fill=True)
            pdf.cell(largeurs_colonnes["reference"], 8, "Réf. normative", border=1, fill=True)
            pdf.cell(largeurs_colonnes["quantite"], 8, "Qté", border=1, align="C", fill=True)
            pdf.cell(largeurs_colonnes["unite"], 8, "Unité", border=1, align="C", fill=True)
            pdf.cell(largeurs_colonnes["prix_unitaire"], 8, "P.U.", border=1, align="C", fill=True)
            pdf.cell(largeurs_colonnes["prix_total"], 8, "P. Total", border=1, align="C", fill=True)
            pdf.ln()
 
        _entete_tableau()
 
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
 
        for index, ligne in enumerate(lignes, start=1):
            # Si on approche du bas de page, FPDF2 gère le saut de page
            # automatiquement grâce à set_auto_page_break, MAIS l'en-tête
            # du tableau ne se répète pas tout seul : on le vérifie manuellement.
            if pdf.get_y() > 260:
                pdf.add_page()
                _entete_tableau()
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
 
            quantite = float(ligne.get("Quantité", 0) or 0)
            prix_unitaire = float(ligne.get("Prix unitaire", 0) or 0)
            prix_total_ligne = quantite * prix_unitaire
 
            # Couleur de fond alternée pour la lisibilité (zébrage léger)
            fill = index % 2 == 0
            if fill:
                pdf.set_fill_color(*COULEUR_GRIS_CLAIR)
 
            pdf.cell(largeurs_colonnes["n"], 7, str(index), border=1, align="C", fill=fill)
            pdf.cell(
                largeurs_colonnes["designation"], 7,
                str(ligne.get("Désignation", ""))[:35], border=1, fill=fill,
            )
            pdf.cell(
                largeurs_colonnes["reference"], 7,
                str(ligne.get("Référence normative", ""))[:20], border=1, fill=fill,
            )
            pdf.cell(largeurs_colonnes["quantite"], 7, f"{quantite:.2f}", border=1, align="C", fill=fill)
            pdf.cell(largeurs_colonnes["unite"], 7, str(ligne.get("Unité", "")), border=1, align="C", fill=fill)
            pdf.cell(
                largeurs_colonnes["prix_unitaire"], 7,
                f"{prix_unitaire:,.2f}", border=1, align="R", fill=fill,
            )
            pdf.cell(
                largeurs_colonnes["prix_total"], 7,
                f"{prix_total_ligne:,.2f}", border=1, align="R", fill=fill,
            )
            pdf.ln()
 
        pdf.ln(6)
 
        # ------------------------------------------------------------
        # ZONE DE SYNTHÈSE (alignée à droite)
        # ------------------------------------------------------------
        largeur_etiquette = 45
        largeur_valeur = 40
        x_debut_synthese = 210 - 10 - largeur_etiquette - largeur_valeur  # aligné à droite, marge 10mm
 
        def _ligne_synthese(etiquette, valeur, gras=False, encadre=False):
            pdf.set_x(x_debut_synthese)
            if encadre:
                pdf.set_fill_color(*COULEUR_BLEU_PROFOND)
                pdf.set_text_color(*COULEUR_TEXTE_CLAIR)
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
 
            pdf.set_font("Helvetica", "B" if gras else "", 10)
            pdf.cell(largeur_etiquette, 8, etiquette, border=1, fill=encadre)
            pdf.cell(largeur_valeur, 8, valeur, border=1, align="R", fill=encadre)
            pdf.ln()
 
        _ligne_synthese("Total HT", f"{totaux['total_ht']:,.2f} {devise}")
        _ligne_synthese(f"TVA ({taux_tva:.2f}%)", f"{totaux['montant_tva']:,.2f} {devise}")
        _ligne_synthese("TOTAL TTC", f"{totaux['total_ttc']:,.2f} {devise}", gras=True, encadre=True)
 
        pdf.ln(15)
 
        # On mémorise la position verticale de départ pour aligner
        # QR code (gauche) et signature (droite) sur la même ligne.
        y_zone_bas = pdf.get_y()
 
        # ------------------------------------------------------------
        # ZONE QR CODE (gauche) — pont direct vers la boutique Selar
        # ------------------------------------------------------------
        try:
            qr_bytes = _generer_qrcode_boutique_bytes()
            chemin_qr = _sauvegarder_image_temporaire(qr_bytes, ".png")
            fichiers_temporaires_a_supprimer.append(chemin_qr)
 
            pdf.set_xy(10, y_zone_bas)
            pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(50, 6, "Découvrez nos outils :", ln=True)
            pdf.set_x(10)
 
            taille_qr_mm = 25
            pdf.image(chemin_qr, x=10, y=pdf.get_y() + 1, w=taille_qr_mm)
 
            pdf.set_xy(10, pdf.get_y() + taille_qr_mm + 3)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(120, 120, 120)
            pdf.multi_cell(45, 3.5, "Scannez pour explorer la suite complète Y-NEXUS")
        except Exception:
            # Si la génération du QR code échoue pour une raison quelconque
            # (ex: lib manquante côté environnement d'exécution), le PDF
            # doit quand même se générer normalement — le QR code est un
            # bonus, pas un élément critique du document.
            pass
 
        # ------------------------------------------------------------
        # ZONE DE SIGNATURE (droite)
        # ------------------------------------------------------------
        pdf.set_xy(140, y_zone_bas)
        pdf.set_text_color(*COULEUR_GRIS_ANTHRACITE)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(60, 6, "Signature du concepteur :", ln=True)
 
        if signature_bytes:
            chemin_signature = _sauvegarder_image_temporaire(signature_bytes, ".png")
            fichiers_temporaires_a_supprimer.append(chemin_signature)
            pdf.image(chemin_signature, x=140, y=y_zone_bas + 8, w=50)
        else:
            # Zone vide avec une simple ligne, si aucune signature fournie
            y_ligne = y_zone_bas + 23
            pdf.line(140, y_ligne, 195, y_ligne)
 
        # ------------------------------------------------------------
        # SORTIE FINALE — bytes du PDF
        # ------------------------------------------------------------
        # FPDF2 retourne un bytearray avec .output(dest="S") en mode "chaîne".
        pdf_bytes = pdf.output()
        return bytes(pdf_bytes)
 
    finally:
        # Nettoyage systématique des fichiers temporaires, même en cas d'erreur
        for chemin in fichiers_temporaires_a_supprimer:
            if os.path.exists(chemin):
                os.remove(chemin)
 
