# =============================================================================
#  quality_attributaire.py — Contrôles de qualité attributaire — V20
#
#  CORRECTIONS V20 :
#    - Champ commentaire retiré de mapping.py — plus de filtre nécessaire
#    - Tous les champs définis dans mapping.py s'affichent en 2.3, même
#      absents des données client (100% non renseigné)
#    - arrondi_pct() : un pourcentage réel < 100% n'affiche jamais 100%,
#      même après arrondi — appliqué à tous les taux du rapport
#
#  CORRECTIONS V17 :
#    - Contraintes conditionnelles appliquées EN DERNIER et prioritaires
#      sur les résultats du contrôle standard (plus d'écrasement involontaire)
#    - Calcul des stats conditionnelles basé sur les champs _qualif du GDF
#      enrichi (taux de conformité réel, pas juste le remplissage)
#    - Champ diametre_regard affiché même si nom_client = None (0% absent)
#    - Score attributaire corrigé — collecte cohérente des objets en erreur
#
#  ORDRE D'EXÉCUTION :
#    1. Contrôles standards par champ (texte, numérique, mixte)
#    2. Contraintes conditionnelles (Vision 1 — prioritaires, en dernier)
#    3. Cohérence inter-champs (cote TN > radier)
#    4. Calculs de synthèse (complétude, taux de conformité, stats 2.4)
# =============================================================================

import pandas as pd
import numpy as np
import re
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SPECIAL_CHARS, ACCENT_CHARS


def arrondi_pct(valeur, decimales=1):
    """
    Arrondit un pourcentage sans jamais afficher 100% si la valeur réelle
    est strictement inférieure à 100%.

    Un arrondi mathématique classique peut transformer 99.9953% en 100.0%,
    donnant l'illusion d'une complétude parfaite alors qu'il manque des
    objets. On tronque (arrondi vers le bas) dès que la valeur réelle est
    < 100 mais que l'arrondi classique atteindrait 100.

    Exemples :
      arrondi_pct(99.9953) → 99.9   (pas 100.0)
      arrondi_pct(99.8)    → 99.8   (inchangé, déjà < 100 après arrondi)
      arrondi_pct(100.0)   → 100.0  (vraie complétude, inchangé)
      arrondi_pct(0.0)     → 0.0
    """
    if valeur is None:
        return 0.0
    arrondi_classique = round(valeur, decimales)
    if valeur < 100.0 and arrondi_classique >= 100.0:
        facteur = 10 ** decimales
        return math.floor(valeur * facteur) / facteur
    return arrondi_classique


def _contient_caractere_interdit(valeur):
    """Retourne True si la valeur contient un caractère spécial ou accent."""
    texte = str(valeur)
    if any(c in texte for c in SPECIAL_CHARS):
        return True
    if any(c in texte for c in ACCENT_CHARS):
        return True
    return False


def _est_valide(val, config_champ):
    """
    Vérifie si une valeur respecte la règle du champ.
    Contrôles supportés : "numerique", "texte", "mixte".
    Retourne (bool_valide, str_probleme_ou_None).
    """
    controle = config_champ.get("controle", "")

    if controle == "numerique":
        try:
            num = float(str(val).replace(",", "."))
        except (ValueError, TypeError):
            return False, f"Type attendu : numérique — valeur reçue : '{val}'"
        if "min" in config_champ and num < config_champ["min"]:
            return False, f"Valeur {num} < minimum autorisé ({config_champ['min']})"
        if "max" in config_champ and num > config_champ["max"]:
            return False, f"Valeur {num} > maximum autorisé ({config_champ['max']})"
        if "multiple_of" in config_champ and num % config_champ["multiple_of"] != 0:
            return False, f"Doit être multiple de {config_champ['multiple_of']} — reçu : {num}"
        if config_champ.get("warn_zero") and num == 0:
            return False, "Valeur = 0 (point d'attention — à vérifier)"
        return True, None

    elif controle == "texte":
        if _contient_caractere_interdit(val):
            return False, "Caractères spéciaux ou accents détectés"
        return True, None

    elif controle == "mixte":
        # Accepte Integer OU texte alphanumérique (tirets et underscores autorisés)
        # Refuse les caractères spéciaux et accents
        texte = str(val).strip()
        if _contient_caractere_interdit(texte):
            return False, "Caractères spéciaux ou accents dans l'identifiant"
        if not re.match(r'^[a-zA-Z0-9_\-]+$', texte):
            return False, f"Identifiant non conforme : '{val}'"
        return True, None

    return True, None


def _null_mask(serie):
    """Masque booléen True si valeur nulle/vide."""
    return serie.isna() | serie.astype(str).str.strip().isin(
        ["", "None", "nan", "NaN"]
    )


def controler_champ(serie, config_champ, nom_champ_client):
    """
    Contrôle une colonne entière.
    Retourne résultats statistiques + série "oui"/"non" par objet.
    """
    label  = config_champ.get("label", nom_champ_client)
    total  = len(serie)
    nulls  = _null_mask(serie)
    n_null = int(nulls.sum())
    n_present = total - n_null
    completude = arrondi_pct(n_present / total * 100) if total > 0 else 0.0

    details     = []
    n_invalides = 0
    qualif = pd.Series("non", index=serie.index, dtype=str)

    for idx, val in serie[~nulls].items():
        valide, probleme = _est_valide(val, config_champ)
        if valide:
            qualif.at[idx] = "oui"
        else:
            qualif.at[idx] = "non"
            n_invalides += 1
            details.append({
                "index":        idx,
                "valeur":       str(val),
                "probleme":     probleme,
                "label":        label,
                "champ_client": nom_champ_client,
            })

    return {
        "label":        label,
        "champ_client": nom_champ_client,
        "n_total":      total,
        "n_null":       n_null,
        "n_present":    n_present,
        "completude":   completude,
        "n_invalides":  n_invalides,
        "details":      details,
        "qualif_serie": qualif,
    }


def _appliquer_contraintes_conditionnelles(gdf, champs_config, gdf_enrichi):
    """
    Applique les contraintes conditionnelles sur la couche tronçon.
    PRIORITAIRES — s'exécute APRÈS les contrôles standards et les écrase.
    VERSION VECTORISÉE pour la performance sur grands volumes.

    RÈGLES Vision 1 :
      Canalisation/branchement/raccordement (TYPES_AVEC_DIAMETRE) :
        - Diamètre absent          → "non"
        - Hauteur remplie          → "non" (non attendu)
        - Hauteur absente          → "oui" (normal)
        - Matériau = herbe         → "non"

      Fossé (TYPES_FOSSE) :
        - Hauteur absente          → "non"
        - Diamètre rempli          → "non" (non attendu)
        - Diamètre absent          → "oui" (normal)
        - Matériau ≠ herbe         → "non"

      Autre type :
        - Diamètre rempli          → "non" (non attendu)
        - Diamètre absent          → "oui" (normal)
        - Hauteur remplie          → "non" (non attendu)
        - Hauteur absente          → "oui" (normal)
        - Matériau rempli          → "non" (non attendu)
        - Matériau absent          → "oui" (normal)

    Retourne la liste des erreurs conditionnelles détectées.
    """
    from mapping import TYPES_AVEC_DIAMETRE, TYPES_FOSSE, MATERIAU_HERBE

    details_cond = []

    nom_type     = champs_config.get("type_troncon", {}).get("nom_client")
    nom_diametre = champs_config.get("diametre",      {}).get("nom_client")
    nom_hauteur  = champs_config.get("hauteur",       {}).get("nom_client")
    nom_materiau = champs_config.get("materiau",      {}).get("nom_client")

    # Impossible d'appliquer les contraintes sans le champ type
    if not nom_type or nom_type not in gdf.columns:
        return details_cond

    # Masques vectorisés par catégorie de type
    type_serie   = gdf[nom_type].astype(str).str.strip()
    m_cana       = type_serie.isin(TYPES_AVEC_DIAMETRE)
    m_fosse      = type_serie.isin(TYPES_FOSSE)
    m_autre      = ~m_cana & ~m_fosse

    # ── CAS 1 : CANALISATION ──────────────────────────────────────────────────

    if nom_diametre and nom_diametre in gdf.columns:
        null_d = _null_mask(gdf[nom_diametre])
        # Diamètre absent pour canalisation → "non" PRIORITAIRE
        idx_ko = gdf.index[m_cana & null_d]
        gdf_enrichi.loc[idx_ko, "diametre_qualif"] = "non"
        for idx in idx_ko:
            details_cond.append({
                "index": idx, "valeur": None,
                "probleme": "Diamètre obligatoire pour canalisation — valeur absente",
                "label": "Diamètre (mm)", "champ_client": nom_diametre,
            })

    if nom_hauteur and nom_hauteur in gdf.columns:
        null_h = _null_mask(gdf[nom_hauteur])
        # Hauteur remplie pour canalisation → "non" PRIORITAIRE (non attendu)
        idx_ko = gdf.index[m_cana & ~null_h]
        gdf_enrichi.loc[idx_ko, "hauteur_qualif"] = "non"
        for idx in idx_ko:
            details_cond.append({
                "index": idx,
                "valeur": str(gdf.at[idx, nom_hauteur]),
                "probleme": "Hauteur renseignée pour canalisation — information non attendue",
                "label": "Hauteur (m)", "champ_client": nom_hauteur,
            })
        # Hauteur absente pour canalisation → "oui" (normal, pas d'obligation)
        gdf_enrichi.loc[gdf.index[m_cana & null_h], "hauteur_qualif"] = "oui"

    if nom_materiau and nom_materiau in gdf.columns:
        null_m    = _null_mask(gdf[nom_materiau])
        mat_herbe = gdf[nom_materiau].astype(str).str.strip().isin(MATERIAU_HERBE)
        # Matériau = herbe pour canalisation → "non" PRIORITAIRE
        idx_ko = gdf.index[m_cana & ~null_m & mat_herbe]
        gdf_enrichi.loc[idx_ko, "materiau_qualif"] = "non"
        for idx in idx_ko:
            details_cond.append({
                "index": idx,
                "valeur": str(gdf.at[idx, nom_materiau]),
                "probleme": "Matériau 'herbe' incohérent avec le type canalisation",
                "label": "Matériau", "champ_client": nom_materiau,
            })

    # ── CAS 2 : FOSSÉ ─────────────────────────────────────────────────────────

    if nom_hauteur and nom_hauteur in gdf.columns:
        null_h = _null_mask(gdf[nom_hauteur])
        # Hauteur absente pour fossé → "non" PRIORITAIRE
        idx_ko = gdf.index[m_fosse & null_h]
        gdf_enrichi.loc[idx_ko, "hauteur_qualif"] = "non"
        for idx in idx_ko:
            details_cond.append({
                "index": idx, "valeur": None,
                "probleme": "Hauteur obligatoire pour fossé — valeur absente",
                "label": "Hauteur (m)", "champ_client": nom_hauteur,
            })

    if nom_diametre and nom_diametre in gdf.columns:
        null_d = _null_mask(gdf[nom_diametre])
        # Diamètre rempli pour fossé → "non" PRIORITAIRE (non attendu)
        idx_ko = gdf.index[m_fosse & ~null_d]
        gdf_enrichi.loc[idx_ko, "diametre_qualif"] = "non"
        for idx in idx_ko:
            details_cond.append({
                "index": idx,
                "valeur": str(gdf.at[idx, nom_diametre]),
                "probleme": "Diamètre renseigné pour fossé — information non attendue",
                "label": "Diamètre (mm)", "champ_client": nom_diametre,
            })
        # Diamètre absent pour fossé → "oui" (normal)
        gdf_enrichi.loc[gdf.index[m_fosse & null_d], "diametre_qualif"] = "oui"

    if nom_materiau and nom_materiau in gdf.columns:
        null_m    = _null_mask(gdf[nom_materiau])
        mat_herbe = gdf[nom_materiau].astype(str).str.strip().isin(MATERIAU_HERBE)
        # Matériau présent et ≠ herbe pour fossé → "non" PRIORITAIRE
        idx_ko = gdf.index[m_fosse & ~null_m & ~mat_herbe]
        gdf_enrichi.loc[idx_ko, "materiau_qualif"] = "non"
        for idx in idx_ko:
            details_cond.append({
                "index": idx,
                "valeur": str(gdf.at[idx, nom_materiau]),
                "probleme": "Matériau incohérent avec fossé — attendu : herbe",
                "label": "Matériau", "champ_client": nom_materiau,
            })

    # ── CAS 3 : AUTRE TYPE ────────────────────────────────────────────────────

    for nom_champ, cle_qualif, label_ch in [
        (nom_diametre, "diametre_qualif", "Diamètre (mm)"),
        (nom_hauteur,  "hauteur_qualif",  "Hauteur (m)"),
        (nom_materiau, "materiau_qualif", "Matériau"),
    ]:
        if nom_champ and nom_champ in gdf.columns:
            null_c = _null_mask(gdf[nom_champ])
            # Rempli pour autre type → "non" PRIORITAIRE
            idx_ko = gdf.index[m_autre & ~null_c]
            gdf_enrichi.loc[idx_ko, cle_qualif] = "non"
            for idx in idx_ko:
                details_cond.append({
                    "index": idx,
                    "valeur": str(gdf.at[idx, nom_champ]),
                    "probleme": f"{label_ch} renseigné pour un type sans contrainte — information non attendue",
                    "label": label_ch, "champ_client": nom_champ,
                })
            # Absent pour autre type → "oui" PRIORITAIRE (normal)
            gdf_enrichi.loc[gdf.index[m_autre & null_c], cle_qualif] = "oui"

    return details_cond


def _appliquer_coherence_cotes(gdf, champs_config, gdf_enrichi):
    """
    Vérifie cote TN > cote radier. Vectorisé.
    """
    details = []
    nom_tn  = champs_config.get("cote_tn",  {}).get("nom_client")
    nom_rad = champs_config.get("cote_rad", {}).get("nom_client")

    if (not nom_tn  or nom_tn  not in gdf.columns or
        not nom_rad or nom_rad not in gdf.columns):
        return details

    tn_num  = pd.to_numeric(
        gdf[nom_tn].astype(str).str.replace(",", "."), errors="coerce"
    )
    rad_num = pd.to_numeric(
        gdf[nom_rad].astype(str).str.replace(",", "."), errors="coerce"
    )

    masque = tn_num.notna() & rad_num.notna() & (tn_num <= rad_num)
    idx_ko = gdf.index[masque]

    # Marquer les deux champs comme non conformes PRIORITAIREMENT
    gdf_enrichi.loc[idx_ko, "cote_tn_qualif"]  = "non"
    gdf_enrichi.loc[idx_ko, "cote_rad_qualif"] = "non"

    for idx in idx_ko:
        details.append({
            "index":        idx,
            "valeur":       f"TN={tn_num.at[idx]} / Rad={rad_num.at[idx]}",
            "probleme":     f"Cote TN ({tn_num.at[idx]}) ≤ cote radier ({rad_num.at[idx]}) — incohérence",
            "label":        "Cote TN vs Radier",
            "champ_client": f"{nom_tn} / {nom_rad}",
        })
    return details


def _appliquer_diametre_regard(gdf, champs_config, gdf_enrichi):
    """Contrôle diamètre uniquement pour les nœuds de type regard."""
    from mapping import TYPES_REGARD

    details  = []
    config_d = champs_config.get("diametre_regard", {})
    nom_diam = config_d.get("nom_client")
    nom_type = champs_config.get("type_noeud", {}).get("nom_client")

    if not nom_diam or nom_diam not in gdf.columns:
        return details
    if not nom_type or nom_type not in gdf.columns:
        return details

    type_s = gdf[nom_type].astype(str).str.strip()
    m_reg  = type_s.isin(TYPES_REGARD)

    # Non-regards → "nd" (non applicable)
    gdf_enrichi.loc[gdf.index[~m_reg], "diametre_regard_qualif"] = "nd"

    null_d = _null_mask(gdf[nom_diam])
    # Regards sans diamètre → "non"
    idx_absent = gdf.index[m_reg & null_d]
    gdf_enrichi.loc[idx_absent, "diametre_regard_qualif"] = "non"
    for idx in idx_absent:
        details.append({
            "index": idx, "valeur": None,
            "probleme": "Diamètre regard obligatoire (min 600 mm) — valeur absente",
            "label": "Diamètre regard (mm)", "champ_client": nom_diam,
        })

    # Regards avec diamètre → vérifier min et multiple
    d_num = pd.to_numeric(
        gdf[nom_diam].astype(str).str.replace(",", "."), errors="coerce"
    )
    min_d = config_d.get("min", 600)
    mul_d = config_d.get("multiple_of", 100)

    for idx in gdf.index[m_reg & ~null_d]:
        d = d_num.at[idx]
        if pd.isna(d):
            gdf_enrichi.at[idx, "diametre_regard_qualif"] = "non"
            details.append({
                "index": idx,
                "valeur": str(gdf.at[idx, nom_diam]),
                "probleme": "Diamètre regard : valeur non numérique",
                "label": "Diamètre regard (mm)", "champ_client": nom_diam,
            })
            continue
        errs = []
        if d < min_d:
            errs.append(f"Diamètre {d} mm < minimum ({min_d} mm)")
        if d % mul_d != 0:
            errs.append(f"Doit être multiple de {mul_d}")
        if errs:
            gdf_enrichi.at[idx, "diametre_regard_qualif"] = "non"
            details.append({
                "index": idx,
                "valeur": str(gdf.at[idx, nom_diam]),
                "probleme": " | ".join(errs),
                "label": "Diamètre regard (mm)", "champ_client": nom_diam,
            })
        else:
            gdf_enrichi.at[idx, "diametre_regard_qualif"] = "oui"
    return details


def _calculer_completude_conditionnelle(gdf, champs_config, layer_name):
    """
    Ajuste la complétude des champs conditionnels :
    - Diamètre : dénominateur = canalisations uniquement
    - Hauteur  : dénominateur = fossés uniquement
    """
    if layer_name != "Tronçon":
        return {}
    try:
        from mapping import TYPES_AVEC_DIAMETRE, TYPES_FOSSE
    except ImportError:
        return {}

    result   = {}
    nom_type = champs_config.get("type_troncon", {}).get("nom_client")
    if not nom_type or nom_type not in gdf.columns:
        return {}

    nom_d = champs_config.get("diametre", {}).get("nom_client")
    if nom_d and nom_d in gdf.columns:
        sous = gdf[gdf[nom_type].isin(TYPES_AVEC_DIAMETRE)]
        if len(sous) > 0:
            result["diametre"] = arrondi_pct(
                (1 - _null_mask(sous[nom_d]).mean()) * 100
            )

    nom_h = champs_config.get("hauteur", {}).get("nom_client")
    if nom_h and nom_h in gdf.columns:
        sous = gdf[gdf[nom_type].isin(TYPES_FOSSE)]
        if len(sous) > 0:
            result["hauteur"] = arrondi_pct(
                (1 - _null_mask(sous[nom_h]).mean()) * 100
            )

    return result


def _preparer_stats_conditionnelles(gdf, gdf_enrichi, champs_config, layer_name):
    """
    Prépare les statistiques pour le tableau 2.4.
    Basé sur les champs _qualif du GDF enrichi (taux de conformité réel).

    Pour chaque type de tronçon :
      - diametre : % de diametre_qualif = "oui" parmi les canalisations
      - hauteur  : % de hauteur_qualif = "oui" parmi les fossés
      - materiau : % de materiau_qualif = "oui" (tous types)

    Retourne aussi les stats par type de matériau.
    """
    if layer_name != "Tronçon":
        return [], []

    try:
        from mapping import TYPES_AVEC_DIAMETRE, TYPES_FOSSE
    except ImportError:
        return [], []

    nom_type     = champs_config.get("type_troncon", {}).get("nom_client")
    nom_materiau = champs_config.get("materiau",      {}).get("nom_client")

    # ── Stats par type de tronçon ──
    stats_type = []
    if nom_type and nom_type in gdf.columns:
        types_uniques = sorted(gdf[nom_type].dropna().astype(str).str.strip().unique())
        for tv in types_uniques:
            m     = gdf[nom_type].astype(str).str.strip() == tv
            sous  = gdf_enrichi[m]
            nb    = int(m.sum())

            def _pct_oui(col):
                if col not in sous.columns or len(sous) == 0:
                    return None
                return arrondi_pct((sous[col] == "oui").mean() * 100)

            if tv in TYPES_AVEC_DIAMETRE:
                stats_type.append({
                    "type": tv, "nb": nb,
                    "diametre": _pct_oui("diametre_qualif"),
                    "hauteur":  None,
                    "materiau": _pct_oui("materiau_qualif"),
                })
            elif tv in TYPES_FOSSE:
                stats_type.append({
                    "type": tv, "nb": nb,
                    "diametre": None,
                    "hauteur":  _pct_oui("hauteur_qualif"),
                    "materiau": _pct_oui("materiau_qualif"),
                })
            else:
                stats_type.append({
                    "type": tv, "nb": nb,
                    "diametre": None, "hauteur": None, "materiau": None,
                })

    # ── Stats par type de matériau ──
    stats_mat = []
    if nom_materiau and nom_materiau in gdf.columns:
        mats_uniques = sorted(
            gdf[nom_materiau].dropna().astype(str).str.strip().unique()
        )
        for mv in mats_uniques:
            m    = gdf[nom_materiau].astype(str).str.strip() == mv
            sous = gdf_enrichi[m]
            nb   = int(m.sum())
            pct  = arrondi_pct((sous.get("materiau_qualif", pd.Series()) == "oui").mean() * 100) if len(sous) > 0 else 0.0
            stats_mat.append({"materiau": mv, "nb": nb, "conformite": pct})

    return stats_type, stats_mat


def _preparer_icgp(qa_tr, qa_nd, qt):
    """
    Calcule l'indice de connaissance patrimoniale SIG (inspiré ICGP) sur 40 pts.
    Basé uniquement sur ce que les couches SIG permettent de mesurer.
    """
    def _taux(qa, cle_qualif):
        """% de "oui" dans un champ _qualif."""
        gdf = qa.get("gdf_enrichi")
        if gdf is None or cle_qualif not in gdf.columns:
            return 0.0
        total = len(gdf)
        if total == 0:
            return 0.0
        return arrondi_pct((gdf[cle_qualif] == "oui").sum() / total * 100)

    criteres = [
        {
            "label":      "Diamètre tronçon conforme",
            "points_max": 8,
            "taux":       _taux(qa_tr, "diametre_qualif"),
        },
        {
            "label":      "Matériau tronçon conforme",
            "points_max": 8,
            "taux":       _taux(qa_tr, "materiau_qualif"),
        },
        {
            "label":      "Type tronçon renseigné et conforme",
            "points_max": 4,
            "taux":       _taux(qa_tr, "type_troncon_qualif"),
        },
        {
            "label":      "Cote TN nœud conforme",
            "points_max": 6,
            "taux":       _taux(qa_nd, "cote_tn_qualif"),
        },
        {
            "label":      "Cote radier nœud conforme",
            "points_max": 6,
            "taux":       _taux(qa_nd, "cote_rad_qualif"),
        },
        {
            "label":      "Connectivité topologique",
            "points_max": 8,
            "taux":       qt.get("taux_conformite_topo", 0.0),
        },
    ]

    for c in criteres:
        c["score"] = round(c["points_max"] * c["taux"] / 100, 1)
        if c["taux"] >= 80:
            c["niveau"] = "Satisfaisant"
        elif c["taux"] >= 40:
            c["niveau"] = "Partiel"
        else:
            c["niveau"] = "Insuffisant"

    total_score = round(sum(c["score"] for c in criteres), 1)

    if total_score >= 30:
        niveau_global = "Satisfaisant"
    elif total_score >= 15:
        niveau_global = "Partiel"
    else:
        niveau_global = "Insuffisant"

    return {
        "criteres":      criteres,
        "total_score":   total_score,
        "total_max":     40,
        "niveau_global": niveau_global,
    }


def _preparer_stats_classe(gdf, champs_config, layer_name):
    """
    Prépare les statistiques de répartition par classe de précision pour 4.3.

    Pour la couche tronçon : % basé sur la longueur linéaire (geometry.length)
    Pour la couche nœud   : % basé sur le nombre d'objets

    CORRECTION V19 : certains objets peuvent avoir une géométrie vide ou
    absente dans les données transmises (tracé manquant dans le SIG source,
    bien que toutes les informations attributaires soient renseignées).
    Pour la couche tronçon, ces objets ont une longueur NaN qui, si elle
    n'est pas neutralisée, contamine la somme de toute leur classe et
    produit un résultat NaN sur l'ensemble de la classe concernée.
    On les exclut donc explicitement du calcul de longueur et on les
    compte à part pour signalement dans la note de bas de tableau (4.3).

    Retourne un dict :
      {
        "disponible"          : True/False,
        "stats"                : [ {"classe": "A", "valeur": 12450.0, "pct": 45.2}, ... ],
        "total"                : 27550.0,
        "unite"                : "m" ou "objets",
        "n_geom_invalide"      : 3,
        "geom_invalide_qualif" : Series ou None
      }
    """
    try:
        from mapping import normaliser_classe
    except ImportError:
        return {"disponible": False, "stats": [], "total": 0, "unite": "",
                "n_geom_invalide": 0, "geom_invalide_qualif": None}

    config_classe = champs_config.get("classe", {})
    nom_client    = config_classe.get("nom_client")

    if not nom_client or nom_client not in gdf.columns:
        return {"disponible": False, "stats": [], "total": 0,
                "unite": "m" if layer_name == "Tronçon" else "objets",
                "n_geom_invalide": 0, "geom_invalide_qualif": None}

    use_length  = (layer_name == "Tronçon")
    valeurs_ref = None
    if use_length:
        try:
            valeurs_ref = gdf.geometry.length
        except Exception:
            valeurs_ref = None
            use_length  = False

    # Géométrie vide/absente (tronçon) — exclue du calcul de longueur
    masque_geom_invalide = pd.Series(False, index=gdf.index)
    if use_length and valeurs_ref is not None:
        masque_geom_invalide = (
            valeurs_ref.isna() | gdf.geometry.isna() | gdf.geometry.is_empty
        )
    n_geom_invalide = int(masque_geom_invalide.sum())

    classes_norm = gdf[nom_client].apply(normaliser_classe)

    comptages  = {}
    n_non_rens = 0.0
    for idx, classe in classes_norm.items():
        if use_length and masque_geom_invalide.at[idx]:
            continue
        poids = float(valeurs_ref.at[idx]) if (use_length and valeurs_ref is not None) else 1.0
        if classe is None:
            n_non_rens += poids
        else:
            comptages[classe] = comptages.get(classe, 0.0) + poids

    total = sum(comptages.values()) + n_non_rens

    geom_invalide_qualif = None
    if n_geom_invalide > 0:
        geom_invalide_qualif = masque_geom_invalide.map(lambda x: "non" if x else "oui")

    if total == 0:
        return {"disponible": True, "stats": [], "total": 0,
                "unite": "m" if use_length else "objets",
                "n_geom_invalide": n_geom_invalide,
                "geom_invalide_qualif": geom_invalide_qualif}

    stats = []
    for classe in sorted(comptages.keys()):
        val = round(comptages[classe], 1)
        pct = arrondi_pct(val / total * 100)
        stats.append({"classe": classe, "valeur": val, "pct": pct})

    if n_non_rens > 0:
        stats.append({
            "classe": "Non renseigné",
            "valeur": round(n_non_rens, 1),
            "pct":    arrondi_pct(n_non_rens / total * 100),
        })

    return {
        "disponible":           True,
        "stats":                stats,
        "total":                round(total, 1),
        "unite":                "m" if use_length else "objets",
        "n_geom_invalide":      n_geom_invalide,
        "geom_invalide_qualif": geom_invalide_qualif,
    }


def _preparer_synthese_4_4(ifq, icgp, stats_classe_tr, stats_classe_nd):
    """
    Prépare la phrase de synthèse transversale de la section 4.4
    "Vue d'ensemble de qualification".

    Ne recalcule rien — lit uniquement les résultats déjà produits par
    4.1 (ifq), 4.2 (icgp) et 4.3 (stats_classe_tr / stats_classe_nd).

    Règle de seuil propre à 4.4 pour le volet 4.3 (précision géographique) :
    cumul des % classes A+B par couche, seuil à 50%. Si les deux couches
    sont disponibles, la couche la plus faible décide (pas de moyenne).
    Si une seule couche dispose du champ classe, on évalue sur celle-ci
    uniquement. Si aucune, 4.3 est "non évaluable" — exclu de la
    comparaison et jamais traité comme un point faible.

    Ordre fixe de présentation : 4.3, puis 4.2, puis 4.1.

    Retourne un dict :
      {
        "volets_non_satisfaisants": ["4.3 ...", "4.1 ..."],  # noms, ordre fixe
        "phrase_principale": "...",
        "phrase_4_3_non_evaluable": "..." ou None,
    }
    """
    NOM_4_1 = "score global de qualité"
    NOM_4_2 = "connaissance patrimoniale"
    NOM_4_3 = "précision géographique"

    # ── Volet 4.1 — score global ────────────────────────────────────────────
    satisfaisant_4_1 = ifq >= 80

    # ── Volet 4.2 — indice de connaissance patrimoniale ─────────────────────
    satisfaisant_4_2 = (icgp.get("niveau_global") == "Satisfaisant")

    # ── Volet 4.3 — précision géographique (règle propre à 4.4) ────────────
    def _cumul_ab(stats_classe):
        """Cumule les % des classes A et B depuis le tableau 4.3."""
        if not stats_classe.get("disponible"):
            return None
        cumul = sum(
            s["pct"] for s in stats_classe.get("stats", [])
            if s["classe"] in ("A", "B")
        )
        return cumul

    cumul_tr = _cumul_ab(stats_classe_tr)
    cumul_nd = _cumul_ab(stats_classe_nd)

    evaluable_4_3   = (cumul_tr is not None) or (cumul_nd is not None)
    satisfaisant_4_3 = None
    if cumul_tr is not None and cumul_nd is not None:
        # Deux couches disponibles — le maillon faible décide
        satisfaisant_4_3 = (cumul_tr >= 50) and (cumul_nd >= 50)
    elif cumul_tr is not None:
        satisfaisant_4_3 = (cumul_tr >= 50)
    elif cumul_nd is not None:
        satisfaisant_4_3 = (cumul_nd >= 50)
    # Si aucune couche disponible → evaluable_4_3 = False, satisfaisant_4_3 reste None

    # ── Construction de la liste des volets non satisfaisants, ordre fixe ──
    # Ordre : 4.3, puis 4.2, puis 4.1
    volets_non_satisfaisants = []
    if evaluable_4_3 and not satisfaisant_4_3:
        volets_non_satisfaisants.append(NOM_4_3)
    if not satisfaisant_4_2:
        volets_non_satisfaisants.append(NOM_4_2)
    if not satisfaisant_4_1:
        volets_non_satisfaisants.append(NOM_4_1)

    n = len(volets_non_satisfaisants)

    if n == 0:
        phrase_principale = "Les volets évalués sont tous satisfaisants."
    elif n == 1:
        phrase_principale = (
            f"Le volet à améliorer prioritairement est le {volets_non_satisfaisants[0]}."
            if volets_non_satisfaisants[0] == NOM_4_1 else
            f"Le volet à améliorer prioritairement est la {volets_non_satisfaisants[0]}."
        )
    elif n == 2:
        art = lambda v: "le" if v == NOM_4_1 else "la"
        phrase_principale = (
            f"Les volets à améliorer prioritairement sont {art(volets_non_satisfaisants[0])} "
            f"{volets_non_satisfaisants[0]} et {art(volets_non_satisfaisants[1])} "
            f"{volets_non_satisfaisants[1]}."
        )
    else:  # n == 3
        # "de" + "le" se contracte en "du" (la contraction ne s'applique
        # pas à "la", qui reste "de la")
        art_de = lambda v: "du" if v == NOM_4_1 else "de la"
        art_le = lambda v: "le" if v == NOM_4_1 else "la"
        phrase_principale = (
            f"L'ensemble des volets nécessite une amélioration — à commencer par "
            f"{art_le(volets_non_satisfaisants[0])} {volets_non_satisfaisants[0]}, suivie "
            f"{art_de(volets_non_satisfaisants[1])} {volets_non_satisfaisants[1]} ainsi que "
            f"{art_de(volets_non_satisfaisants[2])} {volets_non_satisfaisants[2]}."
        )

    # ── Phrase distincte si 4.3 est non évaluable ───────────────────────────
    phrase_4_3_non_evaluable = None
    if not evaluable_4_3:
        phrase_4_3_non_evaluable = (
            "La précision géographique du levé n'a pas pu être évaluée — "
            "le champ classe de précision n'est pas transmis dans les données."
        )

    return {
        "volets_non_satisfaisants": volets_non_satisfaisants,
        "phrase_principale":        phrase_principale,
        "phrase_4_3_non_evaluable": phrase_4_3_non_evaluable,
    }


def run_quality_attributaire(gdf, champs_config, layer_name):
    """
    Lance les contrôles attributaires dans l'ordre correct :
      1. Contrôles standards (texte, numérique, mixte)
      2. Contraintes conditionnelles (PRIORITAIRES — écrasent les standards)
      3. Cohérence inter-champs
      4. Synthèse

    Le champ commentaire a été retiré de mapping.py (V20) — il n'existe
    donc plus dans champs_config et n'a plus besoin d'être filtré ici.
    """
    champs = dict(champs_config)

    # Champs optionnels — leur absence ne pénalise pas le score qualité
    # Un champ optionnel absent est signalé dans les actions correctives
    # mais ne compte pas comme erreur par objet dans le score attributaire
    CHAMPS_OPTIONNELS = {"diametre_regard", "classe"}

    resultats        = {}
    gdf_enrichi      = gdf.copy()
    objets_en_erreur = set()   # indices uniques — pas de double comptage

    # ── ÉTAPE 1 : contrôles standards ────────────────────────────────────────
    for cle, config in champs.items():
        nom_client = config.get("nom_client")
        label      = config.get("label", cle)
        nom_qualif = cle + "_qualif"

        if nom_client is None or nom_client not in gdf.columns:
            # Champ absent des données client
            resultats[cle] = {
                "label": label, "champ_client": nom_client or "Non renseigné",
                "n_total": len(gdf), "n_null": len(gdf), "n_present": 0,
                "completude": 0.0, "n_invalides": 0, "details": [], "absent": True,
            }
            gdf_enrichi[nom_qualif] = "non"
            # Champs optionnels absents (classe, diametre_regard) :
            # signalés dans les actions correctives mais ne polluent pas le score.
            # Champs obligatoires absents : tous les objets comptent en erreur.
            if cle not in CHAMPS_OPTIONNELS:
                objets_en_erreur.update(gdf.index.tolist())
            continue

        res = controler_champ(gdf[nom_client], config, nom_client)
        resultats[cle] = res
        gdf_enrichi[nom_qualif] = res["qualif_serie"]

        # Collecter les objets en erreur du contrôle standard
        # Règle : la nullité n'est une erreur que si la valeur est attendue.
        # Pour les champs optionnels, la nullité n'est pas une erreur par objet.
        for d in res["details"]:
            objets_en_erreur.add(d["index"])
        if cle not in CHAMPS_OPTIONNELS:
            # Nullité comptée comme erreur uniquement pour les champs obligatoires
            objets_en_erreur.update(gdf.index[_null_mask(gdf[nom_client])].tolist())

    details_supplementaires = []

    # ── ÉTAPE 2 : contraintes conditionnelles (PRIORITAIRES) ─────────────────
    if layer_name == "Tronçon":
        details_cond = _appliquer_contraintes_conditionnelles(
            gdf, champs, gdf_enrichi
        )
        details_supplementaires.extend(details_cond)
        for d in details_cond:
            objets_en_erreur.add(d["index"])

        # Recalculer n_invalides après les corrections conditionnelles
        # pour que les stats par champ soient cohérentes
        for cle in ["diametre", "hauteur", "materiau"]:
            if cle in resultats:
                qcol = cle + "_qualif"
                if qcol in gdf_enrichi.columns:
                    resultats[cle]["n_invalides"] = int(
                        (gdf_enrichi[qcol] == "non").sum()
                    )

        # Ajuster la complétude conditionnelle
        completudes_cond = _calculer_completude_conditionnelle(gdf, champs, layer_name)
        for cle, comp in completudes_cond.items():
            if cle in resultats:
                resultats[cle]["completude"] = comp

    elif layer_name == "Nœud":
        # Cohérence cote TN > cote radier
        details_coh = _appliquer_coherence_cotes(gdf, champs, gdf_enrichi)
        details_supplementaires.extend(details_coh)
        for d in details_coh:
            objets_en_erreur.add(d["index"])

        # Diamètre regard
        details_diam = _appliquer_diametre_regard(gdf, champs, gdf_enrichi)
        details_supplementaires.extend(details_diam)
        for d in details_diam:
            objets_en_erreur.add(d["index"])

    # ── ÉTAPE 3 : recalcul des objets en erreur depuis les _qualif finaux ─────
    # On relit les _qualif après toutes les corrections pour être cohérent.
    # Les champs optionnels (classe, diametre_regard) sont exclus :
    # leur absence ou non-conformité ne dégrade pas le score qualité attributaire.
    COLS_OPTIONNELLES = {c + "_qualif" for c in CHAMPS_OPTIONNELS}
    objets_en_erreur_final = set()
    for col in gdf_enrichi.columns:
        if col.endswith("_qualif") and col not in COLS_OPTIONNELLES:
            objets_en_erreur_final.update(
                gdf_enrichi.index[gdf_enrichi[col] == "non"].tolist()
            )

    # ── ÉTAPE 4 : calculs de synthèse ─────────────────────────────────────────
    completudes = [r["completude"] for r in resultats.values() if not r.get("absent")]
    completude_moyenne = arrondi_pct(np.mean(completudes)) if completudes else 0.0

    n_total = len(gdf)
    n_erreur = len(objets_en_erreur_final)
    taux_conformite = arrondi_pct((1 - n_erreur / n_total) * 100) if n_total > 0 else 0.0

    # Catégorisation erreurs pour donut 2.2
    type_erreurs = {
        "Valeur manquante":           0,
        "Valeur hors plage / format": 0,
        "Caractères spéciaux":        0,
    }
    for res in resultats.values():
        type_erreurs["Valeur manquante"] += res.get("n_null", 0)
        for d in res.get("details", []):
            p = (d.get("probleme") or "").lower()
            if "numérique" in p or "minimum" in p or "maximum" in p or "multiple" in p or "= 0" in p:
                type_erreurs["Valeur hors plage / format"] += 1
            elif "spéciaux" in p or "accents" in p or "conforme" in p:
                type_erreurs["Caractères spéciaux"] += 1
    for d in details_supplementaires:
        p = (d.get("probleme") or "").lower()
        if "absent" in p or "obligatoire" in p:
            type_erreurs["Valeur manquante"] += 1
        elif "incohérent" in p or "non attendue" in p:
            type_erreurs["Valeur hors plage / format"] += 1
    type_erreurs = {k: v for k, v in type_erreurs.items() if v > 0}

    # Taux de conformité par champ (pour section 2.3 — graphe 3 segments)
    # Calculés depuis les données BRUTES du client pour avoir les 3 segments :
    #   - Conforme  : valeurs présentes ET valides (qualif = "oui")
    #   - Invalide  : valeurs présentes ET non valides (présentes mais qualif = "non")
    #   - Vide      : valeurs nulles/absentes dans les données client
    # IMPORTANT : ne pas confondre "null en données" avec "non dans qualif"
    # Les nulls reçoivent "non" dans qualif mais doivent être dans le segment Vide
    for cle, res in resultats.items():
        nom_client_champ = res.get("champ_client")
        total_c = len(gdf)

        if res.get("absent") or not nom_client_champ or nom_client_champ not in gdf.columns:
            # Champ absent → 100% vide
            res["taux_conformite_champ"] = 0.0
            res["taux_invalide_champ"]   = 0.0
            res["taux_null_champ"]       = 100.0
            continue

        # Calculer depuis les données brutes du client
        n_null    = int(res.get("n_null", 0))          # valeurs absentes dans les données
        n_invalide = int(res.get("n_invalides", 0))    # valeurs présentes mais non conformes
        n_conforme = max(0, total_c - n_null - n_invalide)  # valeurs présentes et conformes

        res["taux_conformite_champ"] = arrondi_pct(n_conforme  / total_c * 100)
        res["taux_invalide_champ"]   = arrondi_pct(n_invalide  / total_c * 100)
        res["taux_null_champ"]       = arrondi_pct(n_null      / total_c * 100)

    # Tout champ défini dans CHAMPS_TRONCON / CHAMPS_NOEUD doit apparaître
    # en 2.3, même absent des données client — il s'affiche alors avec
    # 100% non renseigné. Le maître d'ouvrage doit voir l'intégralité des
    # champs attendus, pas seulement ceux qui sont fournis (V20).
    for cle_champ, config_champ in champs_config.items():
        nom_champ = config_champ.get("nom_client")
        if (nom_champ is None or nom_champ not in gdf.columns) and cle_champ not in resultats:
            resultats[cle_champ] = {
                "label":                 config_champ.get("label", cle_champ),
                "champ_client":          nom_champ or "Non renseigné",
                "n_total":               len(gdf),
                "n_null":                len(gdf),
                "n_present":             0,
                "completude":            0.0,
                "n_invalides":           0,
                "details":               [],
                "absent":                True,
                "taux_conformite_champ": 0.0,
                "taux_invalide_champ":   0.0,
                "taux_null_champ":       100.0,
            }

    # Stats conditionnelles pour tableau 2.4
    stats_type, stats_mat = _preparer_stats_conditionnelles(
        gdf, gdf_enrichi, champs, layer_name
    )

    # Stats classe de précision pour section 4.3
    stats_classe = _preparer_stats_classe(gdf, champs_config, layer_name)

    # Intégrer le champ geometrie_qualif dans la couche enrichie
    # uniquement si au moins un objet a une géométrie vide/absente.
    # Ce champ n'apparaît dans le GeoPackage de sortie que si ce cas
    # se présente — pour ne pas alourdir la table pour rien.
    if stats_classe.get("geom_invalide_qualif") is not None:
        gdf_enrichi["geometrie_qualif"] = stats_classe["geom_invalide_qualif"]

    return {
        "layer_name":              layer_name,
        "stats_classe":            stats_classe,
        "n_total":                 n_total,
        "completude_moyenne":      completude_moyenne,
        "taux_conformite":         taux_conformite,
        "n_objets_en_erreur":      n_erreur,
        "champs_results":          resultats,
        "details_supplementaires": details_supplementaires,
        "type_errors":             type_erreurs,
        "gdf_enrichi":             gdf_enrichi,
        "stats_type":              stats_type,
        "stats_materiau":          stats_mat,
    }
