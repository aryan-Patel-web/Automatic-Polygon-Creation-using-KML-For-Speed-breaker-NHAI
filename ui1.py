# """
# ui.py  v7  —  Speed Breaker GIS BOQ Tool
# Per-marker heading + lane selector | Visual compass | Real-time preview
# IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
# Run:  streamlit run ui.py
# """

# import streamlit as st
# import tempfile, time, math
# import pandas as pd
# import folium
# from streamlit_folium import st_folium

# from polygon import (
#     parse_kml_markers, run_pipeline, pca_heading,
#     PolygonSpec, MarkerOverride, GeneratedPolygon, MarkerInfo,
#     haversine_distance, forward_bearing, normalise_heading,
#     LANE_PRESETS,
# )

# # ── Page config ───────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="GIS BOQ — Speed Breaker v7",
#     page_icon="🚧", layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ── CSS ───────────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
# html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}

# .banner{background:linear-gradient(135deg,#050d1a 0%,#0d1a2e 50%,#142340 100%);
#   border:1px solid #FFD700;border-radius:16px;padding:22px 30px 16px;
#   margin-bottom:20px;box-shadow:0 4px 28px rgba(255,215,0,.12);}
# .banner h1{color:#FFD700;font-size:1.75rem;font-weight:700;margin:0 0 5px;}
# .banner p{color:#94a3b8;font-size:.87rem;margin:0;}
# .tag{display:inline-block;background:#1e3a5f;color:#60a5fa;border-radius:20px;
#   padding:2px 10px;font-size:.7rem;font-weight:600;margin:5px 4px 0 0;}

# .hdg-panel{background:#06111f;border:2px solid #FFD700;border-radius:12px;
#   padding:14px 16px;margin-bottom:12px;}
# .hdg-panel h4{color:#FFD700;margin:0 0 8px;font-size:.9rem;}

# .stat{background:#0d1a2e;border:1px solid #1e3a5f;border-left:4px solid #FFD700;
#   border-radius:9px;padding:11px 12px;text-align:center;}
# .stat .v{font-size:1.55rem;font-weight:700;color:#FFD700;}
# .stat .l{font-size:.65rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;}

# .mk-card{background:#0d1a2e;border:1px solid #1e3a5f;border-left:3px solid #2563eb;
#   border-radius:8px;padding:10px 13px;margin-bottom:8px;}
# .mk-card.has-hdg{border-left-color:#FF8C00;}
# .mk-card.has-lane{border-left-color:#22c55e;}
# .mk-card.has-both{border-left-color:#FF4444;}
# .mk-card .title{color:#93c5fd;font-weight:600;font-size:.82rem;margin-bottom:4px;}
# .mk-card.has-hdg .title{color:#FF8C00;}
# .mk-card.has-lane .title{color:#22c55e;}
# .mk-card.has-both .title{color:#FF4444;}
# .mk-card .coords{color:#6b7280;font-family:'JetBrains Mono',monospace;font-size:.72rem;}

# .compass-wrap{text-align:center;margin:8px 0 4px;}
# .compass-label{font-size:.72rem;color:#94a3b8;text-align:center;margin-top:4px;}

# .lane-btn{display:inline-block;padding:5px 12px;border-radius:8px;
#   font-size:.78rem;font-weight:700;margin:3px;cursor:pointer;border:2px solid transparent;}
# .lane-1{background:#1a3a1a;color:#4ade80;border-color:#166534;}
# .lane-2{background:#1a2e4a;color:#60a5fa;border-color:#1e40af;}
# .lane-4{background:#2e1a4a;color:#c084fc;border-color:#6b21a8;}
# .lane-6{background:#3a1a1a;color:#f87171;border-color:#991b1b;}

# .ok{background:#052e16;border:1px solid #16a34a;border-radius:7px;
#   padding:8px 12px;color:#86efac;font-size:.8rem;margin:6px 0;}
# .warn{background:#2d1400;border:1px solid #d97706;border-radius:7px;
#   padding:8px 12px;color:#fde68a;font-size:.8rem;margin:6px 0;}
# .info2{background:#06111f;border:1px dashed #1e3a5f;border-radius:7px;
#   padding:8px 12px;color:#94a3b8;font-size:.79rem;margin:6px 0;}

# div[data-testid="stSidebar"]{background:#050d1a;}
# .stButton>button{background:linear-gradient(135deg,#d97706,#b45309);
#   color:#fff;border:none;border-radius:8px;font-weight:600;transition:all .2s;}
# .stButton>button:hover{transform:translateY(-1px);box-shadow:0 4px 14px rgba(217,119,6,.4);}
# </style>
# """, unsafe_allow_html=True)

# # ── Banner ────────────────────────────────────────────────────────────────────
# st.markdown("""
# <div class="banner">
#   <h1>🚧 GIS BOQ Tool — CAP PTBM Speed Breaker v7</h1>
#   <p>Per-marker lane + heading | Visual compass | Real-time preview | BOQ Excel</p>
#   <span class="tag">IIIT Nagpur</span><span class="tag">Dr. Neha Kasture</span>
#   <span class="tag">PWD/NHAI</span><span class="tag">v7 — Per-marker config</span>
# </div>
# """, unsafe_allow_html=True)


# # ── Helper: SVG Compass ───────────────────────────────────────────────────────
# def render_compass(road_hdg: float, size: int = 140) -> str:
#     """
#     Returns an SVG compass showing:
#       🟡 Yellow solid line  = road direction (heading)
#       🟠 Orange dashed line = strip direction (perpendicular)
#     """
#     cx, cy, r = size // 2, size // 2, size // 2 - 10
#     r2 = r - 8

#     road_rad  = math.radians(road_hdg)
#     strip_rad = math.radians(road_hdg + 90)

#     # Road line endpoints
#     rx1 = cx + r2 * math.sin(road_rad);   ry1 = cy - r2 * math.cos(road_rad)
#     rx2 = cx - r2 * math.sin(road_rad);   ry2 = cy + r2 * math.cos(road_rad)

#     # Strip line endpoints
#     sx1 = cx + r2 * math.sin(strip_rad);  sy1 = cy - r2 * math.cos(strip_rad)
#     sx2 = cx - r2 * math.sin(strip_rad);  sy2 = cy + r2 * math.cos(strip_rad)

#     strip_dir = int((road_hdg + 90) % 180)

#     return f"""
# <div class="compass-wrap">
# <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
#   <!-- Outer ring -->
#   <circle cx="{cx}" cy="{cy}" r="{r}" fill="#06111f" stroke="#FFD700" stroke-width="2.5"/>
#   <!-- Tick marks -->
#   {''.join(
#     f'<line x1="{cx+r*math.sin(math.radians(a)):.1f}" y1="{cy-r*math.cos(math.radians(a)):.1f}" '
#     f'x2="{cx+(r-6)*math.sin(math.radians(a)):.1f}" y2="{cy-(r-6)*math.cos(math.radians(a)):.1f}" '
#     f'stroke="#1e3a5f" stroke-width="1.5"/>'
#     for a in range(0, 360, 30)
#   )}
#   <!-- Cardinal labels -->
#   <text x="{cx}" y="14" text-anchor="middle" fill="#94a3b8" font-size="9" font-family="DM Sans">N</text>
#   <text x="{size-8}" y="{cy+4}" text-anchor="middle" fill="#94a3b8" font-size="9" font-family="DM Sans">E</text>
#   <text x="{cx}" y="{size-4}" text-anchor="middle" fill="#94a3b8" font-size="9" font-family="DM Sans">S</text>
#   <text x="8" y="{cy+4}" text-anchor="middle" fill="#94a3b8" font-size="9" font-family="DM Sans">W</text>
#   <!-- Strip direction (orange dashed) -->
#   <line x1="{sx2:.1f}" y1="{sy2:.1f}" x2="{sx1:.1f}" y2="{sy1:.1f}"
#         stroke="#FF8C00" stroke-width="2.5" stroke-dasharray="5 3" stroke-linecap="round"/>
#   <!-- Road direction (yellow solid) -->
#   <line x1="{rx2:.1f}" y1="{ry2:.1f}" x2="{rx1:.1f}" y2="{ry1:.1f}"
#         stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>
#   <!-- Arrow head on road line -->
#   <polygon points="{rx1:.1f},{ry1:.1f} {rx1-5*math.cos(road_rad)-4*math.sin(road_rad):.1f},{ry1+5*math.sin(road_rad)-4*math.cos(road_rad):.1f} {rx1-5*math.cos(road_rad)+4*math.sin(road_rad):.1f},{ry1+5*math.sin(road_rad)+4*math.cos(road_rad):.1f}"
#            fill="#FFD700"/>
#   <!-- Centre dot -->
#   <circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>
#   <!-- Heading text -->
#   <text x="{cx}" y="{size-16}" text-anchor="middle" fill="#FFD700"
#         font-size="11" font-weight="bold" font-family="DM Sans">{road_hdg:.0f}°</text>
#   <!-- Legend -->
#   <line x1="6" y1="{size-20}" x2="18" y2="{size-20}" stroke="#FFD700" stroke-width="3"/>
#   <text x="21" y="{size-16}" fill="#FFD700" font-size="7" font-family="DM Sans">Road</text>
#   <line x1="6" y1="{size-10}" x2="18" y2="{size-10}" stroke="#FF8C00" stroke-width="2"
#         stroke-dasharray="4 2"/>
#   <text x="21" y="{size-6}" fill="#FF8C00" font-size="7" font-family="DM Sans">Strip {strip_dir}°</text>
# </svg>
# </div>
# <div class="compass-label">
#   Road: <b style="color:#FFD700">{road_hdg:.0f}°</b> &nbsp;|&nbsp;
#   Strip: <b style="color:#FF8C00">{strip_dir}°</b>
# </div>
# """


# # ── Sidebar ───────────────────────────────────────────────────────────────────
# with st.sidebar:

#     # ── Global Heading ────────────────────────────────────────────────────────
#     st.markdown("## 🧭 Global Road Heading")
#     st.markdown('<div class="hdg-panel"><h4>Default angle for all straight markers</h4>',
#                 unsafe_allow_html=True)

#     use_manual = st.toggle("✏️ Set manually (recommended)", value=True)
#     heading_val = 45
#     if use_manual:
#         heading_val = st.slider("Road Heading (°)", 0, 179, 45, 1,
#                                  help="0=N–S | 45=NE–SW | 90=E–W | 135=SE–NW")
#         st.markdown(render_compass(heading_val, size=140), unsafe_allow_html=True)
#         heading_override = float(heading_val)
#         st.markdown('</div>', unsafe_allow_html=True)
#         st.markdown('<div class="ok">✅ Global heading active</div>', unsafe_allow_html=True)
#     else:
#         heading_override = -1.0
#         use_osm = st.toggle("🌐 Try OSM road data", value=True)
#         st.markdown('</div>', unsafe_allow_html=True)
#         st.markdown('<div class="warn">⚠️ Auto-detect. Set manually if strips wrong angle.</div>',
#                     unsafe_allow_html=True)

#     st.markdown("---")

#     # ── Default Road Config ───────────────────────────────────────────────────
#     st.markdown("## 🛣️ Default Road Config")
#     st.markdown("*(Used for markers without per-marker override)*")

#     default_lanes = st.selectbox(
#         "Default Lane Type",
#         options=[1, 2, 4, 6],
#         index=1,
#         format_func=lambda x: LANE_PRESETS[x]["label"],
#         help="Select the most common road type in your project"
#     )
#     preset = LANE_PRESETS[default_lanes]

#     road_width_m  = st.number_input("Total Road Width (m)", 2.0, 60.0,
#                                      float(preset["road_width"]), 0.5,
#                                      help="Measure in Google Earth Pro: Tools → Ruler")
#     has_sep       = st.toggle("Has Centre Separator", value=preset["has_sep"])
#     sep_w         = 0.0
#     if has_sep and default_lanes > 1:
#         sep_w = st.number_input("Separator Width (m)", 0.0, 10.0,
#                                  float(preset["separator"]), 0.25,
#                                  help="Measure only the centre divider in Google Earth Pro")

#     drv_lw_default = (road_width_m - (sep_w if has_sep and default_lanes > 1 else 0.0)) / default_lanes
#     _auto_gap = round(sep_w + max(0.3, drv_lw_default * 0.10), 2) if has_sep and default_lanes > 1 else 0.0

#     use_manual_gap = st.toggle("Override lane group gap", value=False)
#     lane_gap_m = -1.0
#     if use_manual_gap and default_lanes > 1:
#         lane_gap_m = st.number_input("Lane Group Gap (m)", 0.1, road_width_m/2, _auto_gap, 0.25)
#     elif default_lanes > 1:
#         st.caption(f"↳ Auto gap = {_auto_gap:.2f}m (sep + clearance)")

#     # Road cross-section visual
#     if default_lanes > 1 and road_width_m > 0:
#         tot = road_width_m
#         sp  = sep_w if has_sep else 0
#         lw  = (tot - sp) / default_lanes
#         lanes_html = ""
#         lane_colors = ["#FFD700","#FFA500","#00CC66","#9966FF"]
#         for li in range(default_lanes):
#             c = lane_colors[li % len(lane_colors)]
#             ldir = "→" if li % 2 == 0 else "←"
#             lanes_html += f'<div style="background:{c};flex:1;display:flex;align-items:center;justify-content:center;color:#000;font-size:.68rem;font-weight:700;">L{li+1}{ldir} {lw:.1f}m</div>'
#         sep_html = (f'<div style="background:#4B5563;width:{max(12, int(sp/tot*120))}px;display:flex;'
#                     f'align-items:center;justify-content:center;color:#9CA3AF;font-size:.6rem;">SEP</div>'
#                     if has_sep and default_lanes > 1 else "")
#         # For >2 lanes insert sep in middle
#         half = default_lanes // 2
#         lane_parts = lanes_html.split('</div>')
#         left_lanes  = "".join(lane_parts[:half]) + ("</div>" if lane_parts[:half] else "")
#         right_lanes = "".join(p + "</div>" for p in lane_parts[half:-1])
#         st.markdown(f"""
#         <div style="background:#06111f;border:1px solid #1e3a5f;border-radius:8px;padding:8px 10px;margin-top:6px;">
#           <div style="font-size:.7rem;color:#94a3b8;margin-bottom:5px;">Cross-section preview:</div>
#           <div style="display:flex;height:26px;border-radius:4px;overflow:hidden;">
#             {left_lanes}{sep_html}{right_lanes}
#           </div>
#           <div style="font-size:.7rem;color:#60a5fa;margin-top:4px;">← {road_width_m:.1f}m total →</div>
#         </div>
#         """, unsafe_allow_html=True)

#     st.markdown("---")

#     # ── Strip Specification ───────────────────────────────────────────────────
#     st.markdown("## 🟨 Strip Specification")
#     strip_mm   = st.number_input("Strip Width (mm)", 5.0, 200.0, 15.0, 5.0,
#                                   help="CAP PTBM thickness: 10mm or 15mm")
#     num_strips = st.number_input("Total Strips (all lanes)", 1, 60, 6, 1)
#     gap_m      = st.number_input("Gap Between Strips (m)", 0.01, 2.0, 0.10, 0.05)

#     use_manual_len = st.toggle("Override strip length", value=False)
#     strip_length_m = drv_lw_default
#     if use_manual_len:
#         strip_length_m = st.number_input("Strip Length (m)", 0.5, road_width_m, round(drv_lw_default, 1), 0.5)

#     spl = int(num_strips) // int(default_lanes)
#     area_one = (strip_mm / 1000.0) * strip_length_m
#     st.info(
#         f"**{int(num_strips)} ÷ {int(default_lanes)} = {spl}/lane**\n\n"
#         f"`CAP PTBM {int(strip_mm)}MM X {int(num_strips)}`\n\n"
#         f"Strip: **{strip_mm}mm × {strip_length_m:.2f}m** | Area: **{area_one:.4f} Sqm**"
#     )


# # ── Main columns ──────────────────────────────────────────────────────────────
# cL, cR = st.columns([1.1, 1.7], gap="large")

# # ── LEFT panel ───────────────────────────────────────────────────────────────
# with cL:
#     st.markdown("### 📂 Upload KML")
#     uploaded = st.file_uploader("KML from Google Earth Pro", type=["kml"])

#     if uploaded:
#         st.success(f"✅ **{uploaded.name}** — {uploaded.size:,} bytes")
#         with tempfile.NamedTemporaryFile(suffix=".kml", delete=False) as tmp:
#             tmp.write(uploaded.read()); tmp_path = tmp.name
#         try:
#             markers = parse_kml_markers(tmp_path)
#             st.session_state.update({"markers": markers, "tmp_kml": tmp_path})
#             if "per_marker_headings" not in st.session_state:
#                 st.session_state["per_marker_headings"] = {}
#             if "per_marker_overrides" not in st.session_state:
#                 st.session_state["per_marker_overrides"] = {}

#             pca_h  = pca_heading(markers)
#             spread = 0.0
#             if len(markers) > 1:
#                 spread = max(
#                     haversine_distance(markers[i].lat, markers[i].lon,
#                                        markers[j].lat, markers[j].lon)
#                     for i in range(len(markers))
#                     for j in range(i+1, min(i+3, len(markers)))
#                 )
#             st.markdown(f"**{len(markers)} markers** | spread ≈ {spread:.1f}m")
#             if pca_h:
#                 st.markdown(f'<div class="ok">🔵 PCA: <b>{pca_h:.1f}°</b></div>', unsafe_allow_html=True)
#             elif spread < 5:
#                 st.markdown('<div class="warn">⚠️ Markers close — use manual heading</div>', unsafe_allow_html=True)
#         except Exception as e:
#             st.error(f"KML error: {e}")

#     # ── Per-Marker Config Table ───────────────────────────────────────────────
#     if "markers" in st.session_state:
#         markers    = st.session_state["markers"]
#         pmh        = st.session_state.get("per_marker_headings", {})
#         pmo_raw    = st.session_state.get("per_marker_overrides", {})

#         st.markdown("---")
#         st.markdown("### 🎯 Per-Marker Configuration")

#         # Legend
#         st.markdown("""
#         <div class="info2">
#         <b>🔵 Blue border</b> = default &nbsp;|&nbsp;
#         <b>🟠 Orange</b> = heading override &nbsp;|&nbsp;
#         <b>🟢 Green</b> = lane override &nbsp;|&nbsp;
#         <b>🔴 Red</b> = both overridden
#         </div>
#         """, unsafe_allow_html=True)

#         # Quick range tool
#         with st.expander("⚡ Quick Range Assignment", expanded=False):
#             rc1, rc2, rc3 = st.columns(3)
#             with rc1:
#                 r_from = st.number_input("From #", 1, len(markers), 1, 1, key="qrf")
#             with rc2:
#                 r_to   = st.number_input("To #",   1, len(markers), min(6, len(markers)), 1, key="qrt")
#             with rc3:
#                 r_hdg  = st.number_input("Heading°", 0, 179, int(heading_val), 1, key="qrh")
#             r_lane = st.selectbox("Lane type for range", [None, 1, 2, 4, 6],
#                                    format_func=lambda x: "— keep default —" if x is None
#                                                          else LANE_PRESETS[x]["label"],
#                                    key="qrl")
#             qc1, qc2 = st.columns(2)
#             with qc1:
#                 if st.button("✅ Apply Range", use_container_width=True):
#                     for mi in range(int(r_from), int(r_to)+1):
#                         pmh[mi] = float(r_hdg)
#                         if r_lane is not None:
#                             preset_r = LANE_PRESETS[r_lane]
#                             pmo_raw[mi] = MarkerOverride(
#                                 num_lanes=r_lane,
#                                 road_width_m=preset_r["road_width"],
#                                 separator_width_m=preset_r["separator"],
#                                 has_separator=preset_r["has_sep"],
#                             )
#                     st.session_state["per_marker_headings"]  = pmh
#                     st.session_state["per_marker_overrides"] = pmo_raw
#                     st.success(f"Applied M{int(r_from)}–{int(r_to)}: {r_hdg}°" +
#                                (f" + {LANE_PRESETS[r_lane]['label']}" if r_lane else ""))
#                     st.rerun()
#             with qc2:
#                 if st.button("🗑️ Clear Range", use_container_width=True):
#                     for mi in range(int(r_from), int(r_to)+1):
#                         pmh.pop(mi, None); pmo_raw.pop(mi, None)
#                     st.session_state["per_marker_headings"]  = pmh
#                     st.session_state["per_marker_overrides"] = pmo_raw
#                     st.rerun()

#         # Individual marker rows
#         for mk in markers:
#             has_h = mk.index in pmh
#             has_l = mk.index in pmo_raw and pmo_raw[mk.index].num_lanes is not None
#             card_cls = ("has-both" if has_h and has_l else
#                         "has-hdg"  if has_h else
#                         "has-lane" if has_l else "")
#             cur_hdg  = pmh.get(mk.index, heading_val if use_manual else 45)
#             cur_ov   = pmo_raw.get(mk.index)
#             cur_lane = cur_ov.num_lanes if cur_ov and cur_ov.num_lanes else default_lanes

#             icon = "🔴" if (has_h and has_l) else ("🟠" if has_h else ("🟢" if has_l else "🔵"))
#             with st.expander(
#                 f"{icon} M{mk.index}. {mk.name[:30]}"
#                 f"{' | ' + str(cur_hdg) + '°' if has_h else ''}"
#                 f"{' | ' + str(cur_lane) + '-lane' if has_l else ''}",
#                 expanded=False
#             ):
#                 ec1, ec2 = st.columns([1.2, 1])

#                 with ec1:
#                     # Heading control
#                     st.markdown("**Road Heading**")
#                     new_hdg = st.slider(
#                         f"Heading M{mk.index}",
#                         0, 179, int(cur_hdg), 1,
#                         key=f"hdg_{mk.index}",
#                         label_visibility="collapsed",
#                         help="Drag to set road heading for this marker"
#                     )
#                     # Lane selector
#                     st.markdown("**Lane Type**")
#                     new_lane = st.selectbox(
#                         f"Lanes M{mk.index}",
#                         options=[None, 1, 2, 4, 6],
#                         index=([None, 1, 2, 4, 6].index(cur_lane)
#                                if cur_lane in [None, 1, 2, 4, 6] else 0),
#                         format_func=lambda x: "— use default —" if x is None
#                                                else LANE_PRESETS[x]["label"],
#                         key=f"lane_{mk.index}",
#                         label_visibility="collapsed",
#                     )
#                     # Apply / clear buttons
#                     bc1, bc2 = st.columns(2)
#                     with bc1:
#                         if st.button(f"📌 Set M{mk.index}", key=f"set_{mk.index}",
#                                      use_container_width=True):
#                             pmh[mk.index] = float(new_hdg)
#                             if new_lane is not None:
#                                 preset_m = LANE_PRESETS[new_lane]
#                                 pmo_raw[mk.index] = MarkerOverride(
#                                     num_lanes=new_lane,
#                                     road_width_m=preset_m["road_width"],
#                                     separator_width_m=preset_m["separator"],
#                                     has_separator=preset_m["has_sep"],
#                                 )
#                             else:
#                                 pmo_raw.pop(mk.index, None)
#                             st.session_state["per_marker_headings"]  = pmh
#                             st.session_state["per_marker_overrides"] = pmo_raw
#                             st.rerun()
#                     with bc2:
#                         if st.button(f"✖ Clear", key=f"clr_{mk.index}",
#                                      use_container_width=True):
#                             pmh.pop(mk.index, None)
#                             pmo_raw.pop(mk.index, None)
#                             st.session_state["per_marker_headings"]  = pmh
#                             st.session_state["per_marker_overrides"] = pmo_raw
#                             st.rerun()

#                 with ec2:
#                     # Live compass for this marker
#                     st.markdown(render_compass(new_hdg, size=130), unsafe_allow_html=True)
#                     lane_lbl = LANE_PRESETS.get(new_lane or default_lanes, {}).get("label", "")
#                     st.markdown(
#                         f'<div style="text-align:center;font-size:.72rem;color:#94a3b8;">'
#                         f'{lane_lbl}</div>',
#                         unsafe_allow_html=True)
#                     st.markdown(
#                         f'<div class="coords" style="font-family:JetBrains Mono,monospace;'
#                         f'font-size:.7rem;color:#6b7280;text-align:center;">'
#                         f'{mk.lat:.5f}<br/>{mk.lon:.5f}</div>',
#                         unsafe_allow_html=True)

#         # Override summary
#         if pmh or pmo_raw:
#             st.markdown("---")
#             all_keys = sorted(set(list(pmh.keys()) + list(pmo_raw.keys())))
#             summary  = []
#             for mi in all_keys:
#                 mn = next((m.name[:20] for m in markers if m.index == mi), f"M{mi}")
#                 ov = pmo_raw.get(mi)
#                 summary.append({
#                     "#": mi, "Name": mn,
#                     "Heading": f"{pmh[mi]:.0f}°" if mi in pmh else "—",
#                     "Lane": f"{ov.num_lanes}-lane" if ov and ov.num_lanes else "—",
#                 })
#             st.markdown(f"**{len(all_keys)} overrides active:**")
#             st.dataframe(pd.DataFrame(summary), use_container_width=True,
#                          hide_index=True, height=min(180, 40+36*len(summary)))
#             if st.button("🗑️ Clear ALL overrides", use_container_width=True):
#                 st.session_state["per_marker_headings"]  = {}
#                 st.session_state["per_marker_overrides"] = {}
#                 st.rerun()

#     # ── Generate ──────────────────────────────────────────────────────────────
#     st.markdown("---")
#     st.markdown("### 🚀 Generate")
#     gen = st.button("⚡ Generate Polygons & Export BOQ",
#                     disabled=not uploaded, use_container_width=True)

#     if gen and "tmp_kml" in st.session_state:
#         pmh     = st.session_state.get("per_marker_headings", {})
#         pmo_raw = st.session_state.get("per_marker_overrides", {})

#         spec = PolygonSpec(
#             strip_width_mm          = float(strip_mm),
#             num_strips              = int(num_strips),
#             gap_between_strips_m    = float(gap_m),
#             strip_length_override_m = float(strip_length_m) if use_manual_len else -1.0,
#             num_lanes               = int(default_lanes),
#             road_width_m            = float(road_width_m),
#             separator_width_m       = float(sep_w),
#             has_separator           = bool(has_sep),
#             lane_gap_m              = float(lane_gap_m) if use_manual_gap and default_lanes>1 else -1.0,
#             heading_override        = float(heading_override),
#         )

#         pb = st.progress(0); txt = st.empty()
#         def prog(i, tot, nm):
#             pb.progress(int(i/tot*100)); txt.text(f"{i+1}/{tot}: {nm}")
#         try:
#             ko = st.session_state["tmp_kml"].replace(".kml","_out.kml")
#             xo = st.session_state["tmp_kml"].replace(".kml","_out.xlsx")
#             osm_flag = (not use_manual) and locals().get('use_osm', True)
#             _, pols = run_pipeline(
#                 st.session_state["tmp_kml"], ko, xo, spec,
#                 per_marker_headings=pmh,
#                 per_marker_overrides=pmo_raw,
#                 use_osm=osm_flag,
#                 progress_callback=prog,
#             )
#             pb.progress(100); time.sleep(0.3); pb.empty(); txt.empty()
#             st.session_state.update({
#                 "polygons": pols, "out_kml": ko, "out_excel": xo, "spec": spec})

#             src_c = {}
#             for pg in pols: src_c[pg.heading_source] = src_c.get(pg.heading_source, 0)+1
#             ov_count = sum(1 for pg in pols if pg.heading_source == "per-marker")
#             lc_count = sum(1 for pg in pols if pg.override and pg.override.num_lanes)
#             st.success(f"✅ {len(pols)} markers × {spec.num_strips} strips = "
#                        f"**{sum(len(p.strip_polygons) for p in pols)} polygons**")
#             if ov_count or lc_count:
#                 st.warning(f"🔶 {ov_count} heading overrides | 🟢 {lc_count} lane overrides")
#             st.info("📡 " + " | ".join(f"{k}:{v}" for k,v in src_c.items()))
#         except Exception as e:
#             pb.empty(); txt.empty(); st.error(f"Error: {e}")
#             import traceback; st.code(traceback.format_exc())

#     if "out_kml" in st.session_state:
#         st.markdown("---")
#         st.markdown("### 📥 Download")
#         with open(st.session_state["out_kml"],"rb") as f:
#             st.download_button("⬇️ KML (Google Earth Pro)", f,
#                                "speed_breaker_polygons.kml",
#                                "application/vnd.google-earth.kml+xml",
#                                use_container_width=True)
#         with open(st.session_state["out_excel"],"rb") as f:
#             st.download_button("⬇️ Excel BOQ Report", f,
#                                "speed_breaker_BOQ.xlsx",
#                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                                use_container_width=True)


# # ── RIGHT panel: Map + Stats ──────────────────────────────────────────────────
# with cR:
#     st.markdown("### 🗺️ Satellite Preview")
#     polygons = st.session_state.get("polygons")
#     markers  = st.session_state.get("markers")
#     spec     = st.session_state.get("spec")
#     pmh_d    = st.session_state.get("per_marker_headings", {})

#     if polygons and markers and spec:
#         curv   = {"straight":0,"slight_curve":0,"sharp_curve":0}
#         src_c  = {}
#         ov_mks = []
#         lc_mks = []
#         for pg in polygons:
#             curv[pg.road_curvature] = curv.get(pg.road_curvature,0)+1
#             src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1
#             if pg.heading_source=="per-marker": ov_mks.append(pg.marker.index)
#             if pg.override and pg.override.num_lanes: lc_mks.append(pg.marker.index)

#         # Stats
#         cols = st.columns(5)
#         for col,(v,l) in zip(cols,[
#             (len(polygons),"Markers"),
#             (spec.num_strips,"Strips/mkr"),
#             (len(set(pg.num_lanes_used for pg in polygons)),"Lane types"),
#             (len(ov_mks),"Hdg overrides"),
#             (sum(len(pg.strip_polygons) for pg in polygons),"Total strips"),
#         ]):
#             with col:
#                 st.markdown(f'<div class="stat"><div class="v">{v}</div>'
#                             f'<div class="l">{l}</div></div>', unsafe_allow_html=True)

#         # Source badges
#         src_html = " ".join(
#             f'<span style="background:#1e3a5f;color:#93c5fd;border-radius:10px;'
#             f'padding:2px 8px;font-size:.73rem;font-weight:700;">{k}:{v}</span>'
#             for k,v in src_c.items())
#         st.markdown(f'<div style="margin:7px 0;font-size:.8rem;color:#94a3b8;">'
#                     f'📡 Headings: {src_html}</div>', unsafe_allow_html=True)

#         if ov_mks or lc_mks:
#             parts = []
#             if ov_mks: parts.append(f"🔶 Heading overrides: M{', M'.join(str(i) for i in sorted(ov_mks))}")
#             if lc_mks: parts.append(f"🟢 Lane overrides: M{', M'.join(str(i) for i in sorted(lc_mks))}")
#             st.markdown(f'<div class="warn">{" &nbsp;|&nbsp; ".join(parts)}</div>',
#                         unsafe_allow_html=True)

#         # Map
#         avg_lat = sum(m.lat for m in markers)/len(markers)
#         avg_lon = sum(m.lon for m in markers)/len(markers)
#         fmap = folium.Map(
#             location=[avg_lat, avg_lon], zoom_start=17,
#             tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
#             attr="Google Satellite")
#         folium.TileLayer("OpenStreetMap", name="Street").add_to(fmap)
#         folium.LayerControl().add_to(fmap)

#         LC = ["#FFD700","#FFA500","#00FF88","#AA00FF","#FF4444","#00CCFF"]

#         for pg in polygons:
#             mk = pg.marker
#             is_hdg_ov  = pg.heading_source == "per-marker"
#             is_lane_ov = pg.override and pg.override.num_lanes
#             icon_color = ("red"    if is_hdg_ov and is_lane_ov else
#                           "orange" if is_hdg_ov else
#                           "green"  if is_lane_ov else
#                           {"straight":"blue","slight_curve":"orange","sharp_curve":"red"}.get(pg.road_curvature,"blue"))

#             lane_lbl = LANE_PRESETS.get(pg.num_lanes_used, {}).get("label", f"{pg.num_lanes_used}-Lane")
#             popup = (
#                 f"<b>M{mk.index}: {mk.name}</b><br/>"
#                 f"{'🔶 HDG OVERRIDE<br/>' if is_hdg_ov else ''}"
#                 f"{'🟢 LANE OVERRIDE<br/>' if is_lane_ov else ''}"
#                 f"Heading: <b>{pg.heading_deg:.1f}°</b> [{pg.heading_source}]<br/>"
#                 f"Lane type: <b>{lane_lbl}</b><br/>"
#                 f"Curvature: {pg.road_curvature.replace('_',' ').title()}<br/>"
#                 f"Strips: {len(pg.strip_polygons)}<br/>"
#                 f"{mk.lat:.6f}, {mk.lon:.6f}"
#             )
#             folium.Marker(
#                 [mk.lat, mk.lon],
#                 popup=folium.Popup(popup, max_width=260),
#                 tooltip=f"M{mk.index}: {pg.heading_deg:.0f}°[{pg.heading_source}] {pg.num_lanes_used}L",
#                 icon=folium.Icon(
#                     color=icon_color,
#                     icon='exclamation-circle' if (is_hdg_ov or is_lane_ov) else 'road',
#                     prefix='fa'),
#             ).add_to(fmap)

#             for strip, ln in zip(pg.strip_polygons, pg.lane_assignments):
#                 ll = [[la, lo] for lo, la in strip]
#                 c  = LC[(ln-1) % len(LC)]
#                 folium.Polygon(
#                     locations=ll, color=c, fill=True,
#                     fill_color=c, fill_opacity=0.85, weight=1.5,
#                     tooltip=f"M{mk.index} L{ln} {pg.heading_deg:.0f}° {pg.num_lanes_used}-lane",
#                 ).add_to(fmap)

#             if len(pg.coordinates) >= 3:
#                 folium.Polygon(
#                     locations=[[la,lo] for lo,la in pg.coordinates],
#                     color="#FF4444", fill=False, weight=2, dash_array="5",
#                 ).add_to(fmap)

#         st_folium(fmap, width="100%", height=460, returned_objects=[])

#         # Legend
#         st.markdown("""
#         <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:.75rem;color:#94a3b8;margin:5px 0;">
#           <span>🟡 Lane 1</span><span>🟠 Lane 2</span><span>🟢 Lane 3</span><span>🟣 Lane 4</span>
#           <span>🔵 Default marker</span><span>🟠 Heading override</span>
#           <span>🟢 Lane override</span><span>🔴 Both override</span>
#         </div>
#         """, unsafe_allow_html=True)

#         # Detail table
#         st.markdown("### 📋 Marker Summary")
#         rows = []
#         for pg in polygons:
#             src_icon = {"per-marker":"🔶","global":"🟡","osm":"🟢",
#                         "pca":"🔵","neighbour":"🔴"}.get(pg.heading_source,"⚪")
#             lane_lbl = LANE_PRESETS.get(pg.num_lanes_used,{}).get("label","")
#             rows.append({
#                 "#":        pg.marker.index,
#                 "Name":     pg.marker.name[:18],
#                 "Hdg°":     f"{pg.heading_deg:.1f}",
#                 "Src":      f"{src_icon} {pg.heading_source}",
#                 "Lanes":    f"{pg.num_lanes_used} ({lane_lbl.split('(')[0].strip()})",
#                 "Curv":     pg.road_curvature.replace("_"," "),
#                 "Strips":   len(pg.strip_polygons),
#                 "Override": ("Hdg+Lane" if (pg.heading_source=="per-marker" and pg.override and pg.override.num_lanes)
#                               else "Hdg" if pg.heading_source=="per-marker"
#                               else "Lane" if pg.override and pg.override.num_lanes
#                               else "—"),
#             })
#         st.dataframe(pd.DataFrame(rows), use_container_width=True,
#                      hide_index=True, height=min(400, 40+36*len(rows)))

#     elif markers:
#         avg_lat = sum(m.lat for m in markers)/len(markers)
#         avg_lon = sum(m.lon for m in markers)/len(markers)
#         pmh_cur = st.session_state.get("per_marker_headings",{})
#         fmap = folium.Map(location=[avg_lat,avg_lon],zoom_start=16,tiles="OpenStreetMap")
#         for mk in markers:
#             has_ov = mk.index in pmh_cur
#             folium.Marker([mk.lat,mk.lon],
#                           tooltip=f"M{mk.index}: {mk.name}" + (f" [{pmh_cur[mk.index]:.0f}°]" if has_ov else ""),
#                           icon=folium.Icon(color='orange' if not has_ov else 'red',icon='map-marker')).add_to(fmap)
#         st_folium(fmap, width="100%", height=360, returned_objects=[])
#         st.info("Set per-marker configs in left panel → Generate")

#     else:
#         st.markdown("""<div style="background:#0d1a2e;border-radius:12px;
#             padding:50px 25px;text-align:center;border:1px dashed #1e3a5f;">
#           <div style="font-size:3rem">🗺️</div>
#           <div style="color:#64748b;margin-top:11px;font-size:.95rem">
#             Upload KML to begin
#           </div>
#         </div>""", unsafe_allow_html=True)

#         st.markdown("### 📖 Workflow")
#         for n, d in [
#             ("1","Export KML markers from Google Earth Pro"),
#             ("2","Upload KML — all markers appear in left panel"),
#             ("3","Set global heading via compass slider (sidebar)"),
#             ("4","Expand each curve marker → set its individual heading via compass"),
#             ("5","For mixed-road projects: set lane type per marker (1/2/4-lane)"),
#             ("6","Use Quick Range to batch-assign straight section markers"),
#             ("7","Click Generate → each marker gets its own correct angle + lane config"),
#             ("8","Download KML (coloured by lane) + Excel BOQ (5 sheets)"),
#         ]:
#             st.markdown(
#                 f'<div style="background:#0d1a2e;border-radius:7px;padding:9px 13px;'
#                 f'margin-bottom:6px;border:1px solid #1e3a5f;">'
#                 f'<span style="color:#FFD700;font-weight:700;margin-right:8px;">Step {n}</span>{d}</div>',
#                 unsafe_allow_html=True)

#         # Preview compass in empty state
#         st.markdown("---")
#         st.markdown("### 🧭 Compass Preview")
#         demo_hdg = st.slider("Try the compass", 0, 179, 45, 1, key="demo_compass")
#         st.markdown(render_compass(demo_hdg, size=160), unsafe_allow_html=True)