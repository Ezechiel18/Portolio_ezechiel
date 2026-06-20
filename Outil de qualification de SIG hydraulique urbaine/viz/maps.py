# =============================================================================
#  maps.py — Cartes topologiques avec fond OpenStreetMap — V7
#
#  CORRECTION V7 :
#    Les données sont reprojetées en EPSG:3857 avant d'être tracées.
#    contextily attend des données en 3857 pour superposer le fond OSM
#    au bon endroit géographiquement.
#
#    Flux :
#      données en 2154 (depuis quality_spatiale.py)
#        → reprojection en 3857 dans maps.py pour l'affichage
#        → contextily superpose le fond OSM correctement
#        → image PNG générée
#      Les GeoPackages exportés restent en 2154.
# =============================================================================

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

SCE_PURPLE = "#3D2E4A"
SCE_ORANGE = "#ED7D31"
COL_GREEN  = "#4A8050"
COL_RED    = "#A63030"
COL_BG     = "#F0EEE8"

try:
    import contextily as ctx
    CTX_OK = True
except ImportError:
    CTX_OK = False


def _save(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight",
                facecolor=COL_BG, edgecolor="none")
    plt.close(fig)


def _reprojeter_3857(gdf):
    """
    Reprojette en EPSG:3857 pour contextily.
    Si CRS absent : avertissement et retour sans reprojection.
    """
    if gdf.crs is None:
        print("  [AVERTISSEMENT] CRS absent — carte sans fond OSM")
        return gdf
    return gdf.to_crs(epsg=3857)


def _emprise_paysage(gdf_erreurs, gdf_total, marge=0.25):
    """
    Emprise paysage centrée sur les erreurs, en coordonnées 3857.
    Ratio largeur:hauteur = 3:2.
    """
    gdf_ref = gdf_erreurs if not gdf_erreurs.empty else gdf_total
    b  = gdf_ref.total_bounds
    cx = (b[0] + b[2]) / 2
    cy = (b[1] + b[3]) / 2
    dx = (b[2] - b[0]) / 2
    dy = (b[3] - b[1]) / 2
    rayon = max(dx, dy, 200) * (1 + marge)
    return (cx - rayon * 1.5, cx + rayon * 1.5,
            cy - rayon,       cy + rayon)


def _fond_osm(ax, gdf_3857):
    """
    Fond CartoDB Positron — données en 3857 obligatoire.
    """
    if not CTX_OK:
        ax.set_facecolor(COL_BG)
        return
    try:
        ctx.add_basemap(
            ax,
            crs=gdf_3857.crs,
            source=ctx.providers.CartoDB.Positron,
            zoom="auto",
            attribution=False
        )
    except Exception as e:
        print(f"  [INFO] Fond OSM non disponible : {e}")
        ax.set_facecolor(COL_BG)


def _credit(ax):
    ax.text(0.99, 0.01, "Fonds de carte : OpenStreetMap",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=5.5, color="#555",
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none", pad=1.5))


def _message_ok(ax, msg):
    ax.set_facecolor("#E8F0E9")
    ax.text(0.5, 0.58, "✓", transform=ax.transAxes,
            ha="center", va="center", fontsize=48, color=COL_GREEN, alpha=0.45)
    ax.text(0.5, 0.32, msg, transform=ax.transAxes,
            ha="center", va="center", fontsize=10, color=COL_GREEN,
            fontweight="bold", multialignment="center")
    ax.axis("off")


def carte_noeuds_connectivite(gdf_noeuds, path):
    """
    Carte nœuds raccordés / non raccordés.
    Données reprojetées en 3857 pour OSM correct.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    fig.patch.set_facecolor(COL_BG)

    non_racco = gdf_noeuds[gdf_noeuds["connecte"] == "non"]
    racco     = gdf_noeuds[gdf_noeuds["connecte"] == "oui"]

    if non_racco.empty:
        _message_ok(ax, "Tous les nœuds\nsont raccordés au réseau")
        ax.set_title("Raccordement des nœuds au réseau",
                     fontsize=9, color=SCE_PURPLE, pad=5, fontweight="bold")
        _save(fig, path)
        return

    # Reprojection en 3857 — nécessaire pour fond OSM au bon endroit
    gdf_3857       = _reprojeter_3857(gdf_noeuds)
    non_racco_3857 = gdf_3857[gdf_3857["connecte"] == "non"]
    racco_3857     = gdf_3857[gdf_3857["connecte"] == "oui"]

    # Emprise en 3857
    xmin, xmax, ymin, ymax = _emprise_paysage(non_racco_3857, gdf_3857)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    # Fond OSM — axes en 3857, alignement correct
    _fond_osm(ax, gdf_3857)

    # Tracé en 3857
    if not racco_3857.empty:
        racco_3857.plot(ax=ax, color=COL_GREEN, markersize=4, alpha=0.5, zorder=2)
    non_racco_3857.plot(ax=ax, color=SCE_ORANGE, markersize=9, alpha=0.9, zorder=3)

    leg = [
        mpatches.Patch(color=COL_GREEN,  label=f"Raccordé ({len(racco)})"),
        mpatches.Patch(color=SCE_ORANGE, label=f"Non raccordé ({len(non_racco)})"),
    ]
    ax.legend(handles=leg, loc="lower right", frameon=True,
              framealpha=0.9, fontsize=7, bbox_to_anchor=(0.99, 0.07))

    ax.set_title(
        f"Raccordement des nœuds au réseau — {len(non_racco)} non raccordé(s)",
        fontsize=9, color=SCE_PURPLE, pad=5, fontweight="bold")

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#ccc")

    _credit(ax)
    plt.tight_layout(pad=0.3)
    _save(fig, path)


def carte_troncons_delimitation(gdf_troncons, path):
    """
    Carte tronçons selon statut de délimitation.
    Données reprojetées en 3857 pour OSM correct.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    fig.patch.set_facecolor(COL_BG)

    ok       = gdf_troncons[gdf_troncons["statut_delimitation"] == "deux_cotes"]
    un       = gdf_troncons[gdf_troncons["statut_delimitation"] == "un_cote_seul"]
    aucun    = gdf_troncons[gdf_troncons["statut_delimitation"] == "non_delimite"]
    problemes = gdf_troncons[gdf_troncons["statut_delimitation"] != "deux_cotes"]

    if problemes.empty:
        _message_ok(ax, "Tous les tronçons sont délimités\naux deux extrémités")
        ax.set_title("Délimitation des tronçons par leurs extrémités",
                     fontsize=9, color=SCE_PURPLE, pad=5, fontweight="bold")
        _save(fig, path)
        return

    # Reprojection en 3857
    gdf_3857   = _reprojeter_3857(gdf_troncons)
    ok_3857    = gdf_3857[gdf_3857["statut_delimitation"] == "deux_cotes"]
    un_3857    = gdf_3857[gdf_3857["statut_delimitation"] == "un_cote_seul"]
    aucun_3857 = gdf_3857[gdf_3857["statut_delimitation"] == "non_delimite"]
    prob_3857  = gdf_3857[gdf_3857["statut_delimitation"] != "deux_cotes"]

    # Emprise en 3857
    xmin, xmax, ymin, ymax = _emprise_paysage(prob_3857, gdf_3857)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    # Fond OSM
    _fond_osm(ax, gdf_3857)

    # Tracé en 3857
    if not ok_3857.empty:
        ok_3857.plot(ax=ax, color=COL_GREEN, linewidth=0.8, alpha=0.4, zorder=2)
    if not un_3857.empty:
        un_3857.plot(ax=ax, color=SCE_ORANGE, linewidth=2.0, alpha=0.9, zorder=3)
    if not aucun_3857.empty:
        aucun_3857.plot(ax=ax, color=COL_RED, linewidth=2.5, alpha=0.9, zorder=4)

    leg = []
    if not ok_3857.empty:
        leg.append(mpatches.Patch(color=COL_GREEN,
                                   label=f"Délimité ({len(ok)})"))
    if not un_3857.empty:
        leg.append(mpatches.Patch(color=SCE_ORANGE,
                                   label=f"1 extrémité libre ({len(un)})"))
    if not aucun_3857.empty:
        leg.append(mpatches.Patch(color=COL_RED,
                                   label=f"2 extrémités libres ({len(aucun)})"))

    ax.legend(handles=leg, loc="lower right", frameon=True,
              framealpha=0.9, fontsize=7, bbox_to_anchor=(0.99, 0.07))

    ax.set_title(
        f"Délimitation des tronçons — {len(problemes)} tronçon(s) à corriger",
        fontsize=9, color=SCE_PURPLE, pad=5, fontweight="bold")

    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#ccc")

    _credit(ax)
    plt.tight_layout(pad=0.3)
    _save(fig, path)
