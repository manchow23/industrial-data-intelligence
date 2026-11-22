import json
import logging

import pandas as pd
import plotly.express as px
import streamlit as st

from src.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Industrial Data Intelligence",
    page_icon="🏭",
    layout="wide",
)

# ── SCADA-style dark industrial theme CSS (scoped classes only) ──
st.markdown(
    """
    <style>
    :root {
        --scada-canvas: #0B0F13;
        --scada-surface: #11181E;
        --scada-surface-elev: #161C25;
        --scada-border: #232A34;
        --scada-text: #F1F5F9;
        --scada-muted: #94A3B8;
        --scada-accent: #F59E0B;
        --scada-normal: #10B981;
        --scada-anomaly: #EF4444;
        --scada-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }

    /* Remove excess top padding so the header sits close to the viewport */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    /* Top command bar */
    .scada-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0 0.75rem 0;
        margin-bottom: 0.25rem;
        border-bottom: 1px solid var(--scada-border);
    }
    .scada-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .scada-title {
        font-size: 1.625rem; /* 26px base, scales with browser zoom */
        font-weight: 700;
        color: var(--scada-text);
        margin: 0;
        letter-spacing: -0.01em;
        line-height: 1.25;
    }
    .scada-title-big {
        font-size: 2.5rem; /* ~40px */
        line-height: 1.25;
    }
    .scada-subtitle {
        color: var(--scada-muted);
        font-size: 0.875rem;
        margin: 0.1rem 0 0 0;
        font-weight: 400;
    }
    .scada-status {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.45rem 1rem;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid;
        backdrop-filter: blur(4px);
    }
    .scada-status.connected {
        background: rgba(16, 185, 129, 0.12);
        color: var(--scada-normal);
        border-color: rgba(16, 185, 129, 0.4);
    }
    .scada-status.disconnected {
        background: rgba(239, 68, 68, 0.12);
        color: var(--scada-anomaly);
        border-color: rgba(239, 68, 68, 0.4);
    }
    .scada-status.connecting {
        background: rgba(245, 158, 11, 0.12);
        color: var(--scada-accent);
        border-color: rgba(245, 158, 11, 0.4);
    }
    .scada-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        box-shadow: 0 0 10px currentColor;
    }
    .scada-dot.connected {
        background: var(--scada-normal);
        animation: scada-pulse 2s infinite;
    }
    .scada-dot.disconnected {
        background: var(--scada-anomaly);
    }
    .scada-dot.connecting {
        background: var(--scada-accent);
        animation: scada-pulse 1.5s infinite;
    }
    @keyframes scada-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.45; }
    }

    /* Filter toolbar */
    .scada-toolbar {
        background: var(--scada-surface-elev);
        border: 1px solid var(--scada-border);
        border-radius: 12px;
        padding: 0.7rem 1rem;
        margin: 0.5rem 0 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
        box-shadow: var(--scada-shadow);
    }
    .scada-toolbar-label {
        color: var(--scada-muted);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }

    /* KPI row */
    .scada-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin: 0.5rem 0 0.5rem 0;
    }
    .scada-kpi-card {
        background: var(--scada-surface);
        border: 1px solid var(--scada-border);
        border-radius: 12px;
        padding: 1rem 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
        box-shadow: var(--scada-shadow);
        position: relative;
        overflow: hidden;
    }
    .scada-kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
    }
    .scada-kpi-card.readings::before { background: var(--scada-accent); }
    .scada-kpi-card.anomalies::before { background: var(--scada-anomaly); }
    .scada-kpi-card.rate::before { background: var(--scada-accent); }
    .scada-kpi-card.sensors::before { background: var(--scada-normal); }
    .scada-kpi-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .scada-kpi-icon {
        width: 2.6rem;
        height: 2.6rem;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(245, 158, 11, 0.12);
        color: var(--scada-accent);
        font-size: 1.35rem;
        flex-shrink: 0;
        box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.2);
    }
    .scada-kpi-card.anomalies .scada-kpi-icon {
        background: rgba(239, 68, 68, 0.12);
        color: var(--scada-anomaly);
        box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.2);
    }
    .scada-kpi-card.sensors .scada-kpi-icon {
        background: rgba(16, 185, 129, 0.12);
        color: var(--scada-normal);
        box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.2);
    }
    .scada-kpi-value {
        font-size: 1.75rem; /* ~28px, scales up on larger screens */
        font-weight: 800;
        color: var(--scada-text);
        line-height: 1.15;
        letter-spacing: -0.02em;
    }
    .scada-kpi-label {
        font-size: 0.7rem;
        color: var(--scada-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
    }

    /* Section headings */
    .scada-section {
        margin: 0.6rem 0 0.5rem 0;
    }
    .scada-section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--scada-text);
        margin: 0 0 0.6rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        letter-spacing: -0.01em;
    }

    /* Surface panel for tables */
    .scada-panel {
        background: var(--scada-surface);
        border: 1px solid var(--scada-border);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: var(--scada-shadow);
    }

    /* Two-column lower grid */
    .scada-lower-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin: 0.5rem 0 1.5rem 0;
    }

    /* Footer */
    .scada-footer {
        color: var(--scada-muted);
        font-size: 0.78rem;
        margin-top: 1rem;
        padding-top: 0.75rem;
        border-top: 1px solid var(--scada-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Responsive */
    @media (max-width: 1024px) {
        .scada-kpi-grid { grid-template-columns: repeat(2, 1fr); }
        .scada-lower-grid { grid-template-columns: 1fr; }
        .scada-toolbar { flex-direction: column; align-items: stretch; gap: 0.6rem; }
    }
    @media (max-width: 640px) {
        .scada-kpi-grid { grid-template-columns: 1fr; }
        .scada-title { font-size: 1.25rem; }
        .scada-title-big { font-size: 1.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_anomalies():
    query = """
        SELECT id, sensor_id, timestamp, score,
               is_anomaly, raw_data
        FROM anomalies
        ORDER BY timestamp DESC
    """

    from src.db.pool import get_pool

    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        conn.rollback()
        pool.putconn(conn)

    if not df.empty:
        # Extract value from raw_data JSONB column
        def extract_value(raw):
            if isinstance(raw, dict):
                return raw.get("value")
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    return parsed.get("value")
                except Exception:
                    return None
            return None

        df["value"] = df["raw_data"].apply(extract_value)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


@st.fragment(run_every="5s")
def dashboard():
    if "db_connected" not in st.session_state:
        st.session_state.db_connected = None

    connected = st.session_state.db_connected
    if connected is None:
        status_class = "connecting"
        status_text = "Connecting&hellip;"
        status_dot_class = "connecting"
    elif connected:
        status_class = "connected"
        status_text = "Database Connected"
        status_dot_class = "connected"
    else:
        status_class = "disconnected"
        status_text = "Database Disconnected"
        status_dot_class = "disconnected"

    # ── Top command bar ──
    st.markdown(
        f"""
        <div class="scada-header">
            <div class="scada-brand">
                <div style="font-size:1.5rem;">🏭</div>
                <div>
                    <div class="scada-title scada-title-big">Industrial Data Intelligence</div>
                    <div class="scada-subtitle">Real-time Industrial Sensor Monitoring &amp; Anomaly Detection</div>
                </div>
            </div>
            <div class="scada-status {status_class}">
                <span class="scada-dot {status_dot_class}"></span>
                {status_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Database query + error handling (unchanged logic) ──
    try:
        df = load_anomalies()
        st.session_state.db_connected = True
    except Exception as e:
        st.session_state.db_connected = False
        st.error(f"Database connection failed: {e}")
        if st.button("🔄 Retry Connection", key="retry_main"):
            st.rerun()
        return

    # Show last updated timestamp only after a successful database query
    st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if df.empty:
        st.info("No sensor readings available yet. Start the Kafka producer.")
        return

    # ── Filter toolbar (compact, native columns) ──
    col_refresh, col_sensor, col_threshold = st.columns([1, 2, 3])

    with col_refresh:
        refresh = st.button("🔄 Refresh Data", key="refresh_main")

    if refresh:
        st.rerun()

    # Sensor filter (applies to KPIs, chart, health, recent readings)
    sensors = ["All"] + sorted(df["sensor_id"].unique().tolist())
    with col_sensor:
        selected_sensor = st.selectbox(
            "Filter by Sensor",
            sensors,
            label_visibility="collapsed",
            key="filter_sensor",
        )

    # Anomaly score threshold slider (applies only to anomaly alerts)
    score_min = float(df["score"].min()) if not df.empty else 0.0
    score_max = float(df["score"].max()) if not df.empty else 1.0
    if score_min == score_max:
        score_max = score_min + 1.0
    with col_threshold:
        threshold = st.slider(
            "Anomaly Score Threshold",
            min_value=round(score_min, 3),
            max_value=round(score_max, 3),
            value=round(score_min, 3),
            step=0.001,
            label_visibility="collapsed",
            key="filter_threshold",
            help="Filter anomaly alerts by minimum score threshold",
        )

    # Working view filtered by sensor only (no threshold applied here)
    if selected_sensor != "All":
        df_view = df[df["sensor_id"] == selected_sensor].copy()
    else:
        df_view = df.copy()

    # KPI calculations (based on sensor-filtered data, no threshold)
    total_readings = len(df_view)
    total_anomalies = int(df_view["is_anomaly"].sum())
    anomaly_rate = (
        total_anomalies / total_readings * 100
        if total_readings else 0
    )
    unique_sensors = df_view["sensor_id"].nunique()

    # ── KPI row ──
    st.markdown(
        f"""
        <div class="scada-kpi-grid">
            <div class="scada-kpi-card readings">
                <div class="scada-kpi-row">
                    <div class="scada-kpi-icon">📊</div>
                    <div>
                        <div class="scada-kpi-value">{total_readings:,}</div>
                        <div class="scada-kpi-label">Total Readings</div>
                    </div>
                </div>
            </div>
            <div class="scada-kpi-card anomalies">
                <div class="scada-kpi-row">
                    <div class="scada-kpi-icon">🚨</div>
                    <div>
                        <div class="scada-kpi-value">{total_anomalies:,}</div>
                        <div class="scada-kpi-label">Anomalies Detected</div>
                    </div>
                </div>
            </div>
            <div class="scada-kpi-card rate">
                <div class="scada-kpi-row">
                    <div class="scada-kpi-icon">📈</div>
                    <div>
                        <div class="scada-kpi-value">{anomaly_rate:.2f}%</div>
                        <div class="scada-kpi-label">Anomaly Rate</div>
                    </div>
                </div>
            </div>
            <div class="scada-kpi-card sensors">
                <div class="scada-kpi-row">
                    <div class="scada-kpi-icon">🛰️</div>
                    <div>
                        <div class="scada-kpi-value">{unique_sensors}</div>
                        <div class="scada-kpi-label">Active Sensors</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Main chart (visual anchor, ~420px) ──
    st.markdown('<div class="scada-section"><div class="scada-section-title">📈 Sensor Monitoring</div></div>', unsafe_allow_html=True)

    chart_df = df_view.dropna(subset=["value"]).sort_values("timestamp")
    chart_df = chart_df.tail(500)

    if not chart_df.empty:
        fig = px.scatter(
            chart_df,
            x="timestamp",
            y="value",
            color="is_anomaly",
            symbol="is_anomaly",
            hover_data=["sensor_id", "score"],
            color_discrete_map={True: "#EF4444", False: "#10B981"},
            title="Sensor Readings &amp; Anomaly Detection",
            labels={
                "timestamp": "Time",
                "value": "Sensor Value",
                "is_anomaly": "Status",
            },
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=420,
            font=dict(color="#94A3B8", size=11),
            title=dict(font=dict(size=15, color="#F1F5F9"), x=0.02, xanchor="left"),
            showlegend=True,
            legend=dict(
                title="Status",
                bgcolor="rgba(17, 24, 30, 0.7)",
                bordercolor="#232A34",
                borderwidth=1,
                font=dict(color="#F1F5F9", size=11),
                itemsizing="constant",
                itemwidth=34,
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=1,
            ),
            xaxis=dict(
                type="date",
                tickformat="%b %d %H:%M",
                gridcolor="#1E2530",
                tickfont=dict(color="#94A3B8", size=10),
                title_font=dict(color="#CBD5E1", size=11),
                title_standoff=8,
            ),
            yaxis=dict(
                gridcolor="#1E2530",
                tickfont=dict(color="#94A3B8", size=10),
                title_font=dict(color="#CBD5E1", size=11),
                title_standoff=8,
            ),
            margin=dict(l=10, r=10, t=30, b=10),
            hovermode="closest",
        )
        fig.update_traces(marker=dict(size=6, opacity=0.8))
        st.plotly_chart(fig, use_container_width=True)

    # ── Lower half: two-column data grid ──
    col_health, col_alerts = st.columns([3, 2])

    with col_health:
        st.markdown('<div class="scada-section-title">🏥 Sensor Health Summary</div>', unsafe_allow_html=True)

        health = df_view.groupby("sensor_id").agg(
            readings=("is_anomaly", "size"),
            anomalies=("is_anomaly", "sum"),
            avg_score=("score", "mean"),
        ).reset_index()
        health["anomaly_rate"] = (health["anomalies"] / health["readings"] * 100).round(1)
        health = health.sort_values("anomaly_rate", ascending=False)

        st.dataframe(
            health,
            column_config={
                "sensor_id": "Sensor ID",
                "readings": st.column_config.NumberColumn("Readings"),
                "anomalies": st.column_config.NumberColumn("Anomalies"),
            "avg_score": st.column_config.NumberColumn("Avg Score", format="%.3f"),
            "anomaly_rate": st.column_config.NumberColumn("Anomaly Rate (%)", format="%.1f"),
            },
            hide_index=True,
            use_container_width=True,
        )

    with col_alerts:
        st.markdown('<div class="scada-section-title">🚨 Latest Anomaly Alerts</div>', unsafe_allow_html=True)

        anomalies = (
            df_view[df_view["is_anomaly"] & (df_view["score"] >= threshold)]
            .sort_values("timestamp", ascending=False)
            .head(20)
        )

        if anomalies.empty:
            st.success("No anomalies detected.")
        else:
            display_df = anomalies[
                ["sensor_id", "timestamp", "value", "score"]
            ].copy()
            display_df.columns = [
                "Sensor ID",
                "Timestamp",
                "Sensor Value",
                "Anomaly Score",
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

    # ── Recent readings expander ──
    with st.expander("View latest sensor readings"):
        st.dataframe(
            df_view[
                ["sensor_id", "timestamp", "value", "score", "is_anomaly"]
            ].head(50),
            use_container_width=True,
            hide_index=True,
        )

    # ── Footer ──
    st.markdown(
        f"""
        <div class="scada-footer">
            <span>Data refreshes automatically every 5 seconds &bull; Use Refresh Data to force an immediate refresh</span>
            <span>{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


dashboard()
