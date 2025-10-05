# -*- coding: utf-8 -*- 
# start.py  —  Gantt avec week-end en couleur dédiée (插入周末颜色片段)

import pandas as pd
import plotly.express as px

# ========================
# 1) 数据：5 大行；矩形内 label 极简；hover 用 full_label
#    顺序：Blockout → 低模 → 高模 → UV → 烘焙 → 贴图 → 集成 → 多次评审
#    覆盖合同区间：2025-05-19 → 2025-07-19
# ========================
rows = [
    # —— Préparation ——
    ("Préparation","2025-05-19","2025-05-22","Prépa","Préparation",
     "Formation d'intégration et configuration de l'environnement (Maya/ZBrush/Substance/UE5)","Formation"),
    ("Préparation","2025-05-23","2025-05-24","Prépa","Préparation",
     "Finalisation du pipeline UE5 et des conventions de nommage (FBX/tangentes/préréglages ORM)","Normes"),

    # —— Modèle 1 (arme) ——
    ("Modèle 1 (arme)","2025-05-25","2025-05-28","Modèle 1","Production",
     "Blocage des volumes (proportions/masse)","Blocage"),
    ("Modèle 1 (arme)","2025-05-29","2025-05-29","Modèle 1","Review",
     "Revue des proportions et ajustements","Revue"),
    ("Modèle 1 (arme)","2025-05-30","2025-06-03","Modèle 1","Production",
     "Modèle bas et topologie (Maya)","Bas poly"),
    ("Modèle 1 (arme)","2025-06-04","2025-06-08","Modèle 1","Production",
     "Détails high-poly (ZBrush)","Haut poly"),
     ("Modèle 1 (arme)","2025-06-09","2025-06-11","Modèle 1","Production",
     "Dépliage UV (RizomUV, TD unifiée)","UV"),
    ("Modèle 1 (arme)","2025-06-12","2025-06-12","Modèle 1","Review",
     "Revue des proportions et ajustements","Revue"),
    ("Modèle 1 (arme)","2025-06-12","2025-06-13","Modèle 1","Production",
     "Cuisson (Normals/AO)","Cuisson"),
    ("Modèle 1 (arme)","2025-06-14","2025-06-14","Modèle 1","Review",
     "Revue technique (UV/normales/coutures)","Revue"),
    ("Modèle 1 (arme)","2025-06-15","2025-06-20","Modèle 1","Production",
     "Texturage PBR (Substance)","Texturage"),
    ("Modèle 1 (arme)","2025-06-21","2025-06-22","Modèle 1","Production",
     "Intégration UE5 et vérification des performances","Intégration"),
    ("Modèle 1 (arme)","2025-06-23","2025-06-23","Modèle 1","Review",
     "Revue finale et corrections","Revue"),

    # —— Modèle 2 (arme) ——
    ("Modèle 2 (arme)","2025-06-01","2025-06-03","Modèle 2","Production",
     "Blocage des volumes (proportions/masse)","Blocage"),
    ("Modèle 2 (arme)","2025-06-04","2025-06-04","Modèle 2","Review",
     "Revue des proportions et ajustements","Revue"),
    ("Modèle 2 (arme)","2025-06-05","2025-06-09","Modèle 2","Production",
     "Modèle bas et topologie (Maya)","Bas poly"),
    ("Modèle 2 (arme)","2025-06-10","2025-06-13","Modèle 2","Production",
     "Détails high-poly (ZBrush)","Haut poly"),
    ("Modèle 2 (arme)","2025-06-14","2025-06-16","Modèle 2","Production",
     "Dépliage UV (RizomUV, TD unifiée)","UV"),
    ("Modèle 2 (arme)","2025-06-17","2025-06-18","Modèle 2","Production",
     "Cuisson (Normals/AO)","Cuisson"),
    ("Modèle 2 (arme)","2025-06-19","2025-06-19","Modèle 2","Review",
     "Revue technique (UV/normales/coutures)","Revue"),
    ("Modèle 2 (arme)","2025-06-20","2025-06-25","Modèle 2","Production",
     "Texturage PBR (Substance)","Texturage"),
    ("Modèle 2 (arme)","2025-06-26","2025-06-27","Modèle 2","Production",
     "Intégration UE5 et vérification des performances","Intégration"),
    ("Modèle 2 (arme)","2025-06-28","2025-06-29","Modèle 2","Review",
     "Revue finale et corrections","Revue"),

    # —— Modèle 3 (module de maison) ——
    ("Modèle 3 (module de maison)","2025-06-12","2025-06-16","Maison","Production",
     "Blocage des volumes (murs/portes/fenêtres/toit)","Blocage"),
    ("Modèle 3 (module de maison)","2025-06-17","2025-06-17","Maison","Review",
     "Revue des proportions et ajustements","Revue"),
    ("Modèle 3 (module de maison)","2025-06-18","2025-06-22","Maison","Production",
     "Structure bas-poly (corps et frontières des modules)","Bas poly"),
    ("Modèle 3 (module de maison)","2025-06-23","2025-06-27","Maison","Production",
     "Détails high-poly (briques/veinage bois/éléments)","Haut poly"),
    ("Modèle 3 (module de maison)","2025-06-28","2025-06-30","Maison","Production",
     "UV (Texel Density unifiée)","UV"),
    ("Modèle 3 (module de maison)","2025-07-01","2025-07-02","Maison","Production",
     "Cuisson (normales/AO/courbure)","Cuisson"),
    ("Modèle 3 (module de maison)","2025-07-03","2025-07-03","Maison","Review",
     "Revue technique (UV/normales/coutures)","Revue"),
    ("Modèle 3 (module de maison)","2025-07-04","2025-07-09","Maison","Production",
     "Texturage (couches de matériaux et salissures)","Texturage"),
    ("Modèle 3 (module de maison)","2025-07-10","2025-07-12","Maison","Production",
     "Intégration UE5 (collisions/LOD/Nanite)","Intégration"),
    ("Modèle 3 (module de maison)","2025-07-13","2025-07-14","Maison","Review",
     "Revue finale et corrections","Revue"),

    # —— Clôture ——
    ("Clôture","2025-07-15","2025-07-15","Clôture","Clôture",
     "Export et packaging (FBX/textures/vérif. conventions)","Export"),
    ("Clôture","2025-07-16","2025-07-17","Clôture","Clôture",
     "Auto-vérification finale via checklist","Auto-vérif"),
    ("Clôture","2025-07-18","2025-07-18","Clôture","Review",
     "Revue de livraison finale","Revue"),
    ("Clôture","2025-07-19","2025-07-19","Clôture","Clôture",
     "Archivage et passation (Wiki/conventions/sauvegarde)","Archivage"),
]

# === DataFrame ===
df = pd.DataFrame(rows, columns=["task","start","end","group","phase","full_label","label"])
df["start"] = pd.to_datetime(df["start"])
df["end"]   = pd.to_datetime(df["end"])



# ★ 不再对同日起止做“+8小时”补丁，改为按“日期闭区间”整日切片
def explode_to_days(row):
    start_day = row["start"].normalize()           # 当天 00:00
    end_day   = row["end"].normalize()             # 结束那天 00:00
    # end 视为“含当日”，故构造半开区间 [start_day, end_day + 1 天)
    end_exclusive = end_day + pd.Timedelta(days=1)

    out = []
    day = start_day
    while day < end_exclusive:
        seg_start = day                            # 整日开始
        seg_end   = day + pd.Timedelta(days=1)     # 整日结束（到次日 00:00）
        is_weekend = seg_start.weekday() >= 5      # 5=Sat, 6=Sun
        out.append({
            "task": row["task"],
            "start": seg_start,
            "end": seg_end,
            "group": row["group"],
            "phase2": ("Week-end" if is_weekend else row["phase"]),
            "full_label": row["full_label"],
            "label2": ("" if is_weekend else row["label"]),
        })
        day += pd.Timedelta(days=1)
    return out

segments = []
for _, r in df.iterrows():
    segments.extend(explode_to_days(r))
df2 = pd.DataFrame(segments)
if df2.empty:
    df2 = df.rename(columns={"phase": "phase2", "label": "label2"}).copy()

# ========================
# 3) 画图
# ========================
fig = px.timeline(
    df2,
    x_start="start", x_end="end",
    y="task",
    color="phase2",
    text="label2",
    hover_name="full_label",
    color_discrete_map={
        "Préparation":"#8ecae6",
        "Production":"#ffb703",
        "Review":"#ff6b6b",
        "Clôture":"#219ebc",
        "Week-end":"#8a94a6"  # 周末统一颜色；更淡可用 'rgba(138,148,166,0.45)'
    }
)

# 行序（法文行名）
y_order = ["Préparation","Modèle 1 (arme)","Modèle 2 (arme)","Modèle 3 (module de maison)","Clôture"]
fig.update_yaxes(categoryorder="array", categoryarray=y_order)

# 样式与网格
fig.update_layout(
    title="Stage — Diagramme de Gantt (Week-end coloré)",
    template="plotly_dark",
    height=720,
    margin=dict(l=170, r=40, t=70, b=40),
    legend_title_text="Phase",
    bargap=0.2,
    font=dict(family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif")
)
fig.update_traces(
    texttemplate="%{text}",
    textposition="inside",
    insidetextanchor="middle",
    constraintext="inside",
    marker_line_color="rgba(255,255,255,0.8)",
    marker_line_width=1.2
)

# 每 7 天竖线
xmin, xmax = df2["start"].min(), df2["end"].max()
for dt in pd.date_range(xmin.normalize(), xmax.normalize(), freq="7D"):
    fig.add_vline(x=dt, line=dict(color="#FFFFFF", width=1, dash="dot"))

fig.update_xaxes(
    tickformat="%m/%d",
    dtick="D7",
    showgrid=False,
    range=[xmin - pd.Timedelta(days=2), xmax + pd.Timedelta(days=2)]
)
fig.update_yaxes(tickfont=dict(size=12))

# 展示
fig.show()

# 如在某些环境下 fig.show() 不弹窗，可改用：
# fig.write_html("gantt.html", auto_open=True)
