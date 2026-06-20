# =============================================================================
#  charts.py — Génération des graphiques (charte SCE) — V5
#
#  CHANGEMENTS V5 :
#    - Fond transparent sur toutes les figures (facecolor="none")
#    - Pas de texte sous les jauges (redondant avec les labels HTML)
#    - Pas de légende dans les donuts (légende affichée dans le HTML à côté)
#    - Tailles conservées pour la lisibilité
# =============================================================================

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

# --- Palette SCE ---
SCE_PURPLE2 = "#6B4A8A"
SCE_ORANGE  = "#ED7D31"
SCE_ORANGE2 = "#C25E0E"
SCE_TAUPE   = "#8B6F5E"
SCE_TAUPE2  = "#C2A785"
COL_GREEN   = "#4A8050"
COL_RED     = "#A63030"
COL_TRACK   = "#EFEAF2"   # fond gris des jauges


def _save(fig, path):
    """
    Sauvegarde la figure en PNG avec fond transparent.
    Fond transparent = les graphiques s'intègrent dans n'importe quelle
    couleur de fond du template HTML/PDF sans carré blanc visible.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
        facecolor="none",       # fond transparent
        transparent=True,       # confirmation de la transparence
        edgecolor="none"
    )
    plt.close(fig)


def couleur_score(score):
    """
    Retourne la couleur correspondant au niveau de qualité :
      - Rouge   : score < 50%  (qualité faible)
      - Orange  : score 50-80% (qualité moyenne)
      - Vert    : score >= 80% (bonne qualité)
    """
    if score >= 80:
        return COL_GREEN
    elif score >= 50:
        return SCE_ORANGE
    return COL_RED


def jauge_demi_cercle(pct, couleur, path):
    """
    Génère une jauge en demi-cercle (speedomètre).
    Affiche uniquement le pourcentage — pas de texte dessous
    (le label est déjà dans le HTML au-dessus de l'image).

    Paramètres :
      - pct    : valeur entre 0 et 100
      - couleur: couleur de l'arc actif (hex)
      - path   : chemin de sauvegarde PNG
    """
    fig, ax = plt.subplots(
        figsize=(3.2, 1.9),
        subplot_kw=dict(aspect="equal")
    )
    # Fond transparent
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # Arc de fond gris (de π à 0, soit 180°)
    angles_fond = np.linspace(np.pi, 0, 200)
    ax.plot(
        np.cos(angles_fond), np.sin(angles_fond),
        lw=17, color=COL_TRACK, solid_capstyle="round"
    )

    # Arc coloré jusqu'à la valeur (de π jusqu'à l'angle correspondant)
    theta_val = np.pi * (1 - pct / 100)
    angles_val = np.linspace(np.pi, theta_val, 200)
    ax.plot(
        np.cos(angles_val), np.sin(angles_val),
        lw=17, color=couleur, solid_capstyle="round"
    )

    # Pourcentage au centre — seul texte affiché
    ax.text(
        0, 0.12, f"{pct}%",
        ha="center", va="center",
        fontsize=26, fontweight="bold", color=couleur
    )

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.5, 1.25)
    ax.axis("off")
    _save(fig, path)


def donut(labels, valeurs, couleurs, path, texte_centre=None):
    """
    Génère un graphique en donut (anneau).
    Pas de légende interne — la légende est affichée dans le HTML à côté.
    Texte central optionnel (ex: pourcentage de raccordement).

    Paramètres :
      - labels       : liste des libellés (non affichés dans le graphique)
      - valeurs      : liste des valeurs numériques
      - couleurs     : liste des couleurs correspondantes
      - path         : chemin de sauvegarde
      - texte_centre : dict optionnel {"val": "92%", "color": "#...", "sub": "raccordés"}
    """
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # Tracé du donut sans légende
    ax.pie(
        valeurs,
        labels=None,            # pas de labels sur le graphique
        colors=couleurs,
        wedgeprops=dict(width=0.48, edgecolor="white", linewidth=2),
        startangle=90
    )

    # Texte au centre du donut (optionnel)
    # Valeur principale positionnée plus haut pour ne pas toucher l'anneau
    # Sous-titre positionné juste en dessous avec espacement suffisant
    if texte_centre:
        ax.text(
            0, 0.22, texte_centre["val"],
            ha="center", va="center",
            fontsize=20, fontweight="bold",
            color=texte_centre["color"]
        )
        ax.text(
            0, -0.12, texte_centre.get("sub", ""),
            ha="center", va="center",
            fontsize=10, fontweight="bold",
            color=texte_centre["color"]
        )

    ax.set_aspect("equal")
    _save(fig, path)


def barres_horizontales(champs, valeurs, couleurs, path):
    """
    Génère des barres horizontales de complétude par champ.
    Chaque barre représente le % de remplissage réel d'un champ.
    Les noms de champs sont ceux du client (labels du mapping).

    Paramètres :
      - champs  : liste des labels (depuis mapping.py)
      - valeurs : liste des % de complétude réels
      - couleurs: couleur de chaque barre selon le niveau
      - path    : chemin de sauvegarde
    """
    n = len(champs)
    if n == 0:
        return  # rien à afficher

    fig, ax = plt.subplots(figsize=(6.0, max(2.0, n * 0.52)))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    y = np.arange(n)

    # Fond gris représentant 100%
    ax.barh(y, [100] * n, color=COL_TRACK, height=0.6, zorder=1)

    # Barre colorée représentant la complétude réelle
    bars = ax.barh(y, valeurs, color=couleurs, height=0.6, zorder=2)

    # Affichage du % à droite de chaque barre
    for bar, val in zip(bars, valeurs):
        ax.text(
            bar.get_width() + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val}%",
            va="center", ha="left",
            fontsize=10, fontweight="bold",
            color=bar.get_facecolor()
        )

    # Labels des champs (noms lisibles depuis mapping.py)
    ax.set_yticks(y)
    ax.set_yticklabels(champs, fontsize=10)
    ax.set_xlim(0, 118)

    # Masquer les axes superflus
    ax.xaxis.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

    plt.tight_layout()
    _save(fig, path)
