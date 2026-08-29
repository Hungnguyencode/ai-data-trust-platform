from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from database.repositories.scan_repository import save_full_scan
from src.scoring.score_engine import calculate_data_trust_score
from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box
from src.validation.rule_engine import run_quality_checks

st.set_page_config(
    page_title="Trust Score",
    page_icon="⭐",
    layout="wide",
)

inject_custom_css()


st.markdown(
    """
    <div class="main-title">⭐ Data Trust Score</div>
    <div class="subtitle">Chấm điểm mức độ tin cậy và mức độ sẵn sàng của dataset cho phân tích/AI.</div>
    """,
    unsafe_allow_html=True,
)


if "current_df" not in st.session_state:
    st.warning("Bạn chưa upload dataset. Hãy vào trang Upload Dataset trước.")
    st.stop()


df = st.session_state["current_df"]
profile = st.session_state.get("current_profile")
file_name = st.session_state.get("current_file_name", "Unknown file")
file_type = st.session_state.get("current_file_type", "Unknown type")

if profile is None:
    st.error("Không tìm thấy profile trong session. Hãy upload lại dataset.")
    st.stop()


if "current_quality_report" not in st.session_state:
    quality_report = run_quality_checks(df)
    st.session_state["current_quality_report"] = quality_report
else:
    quality_report = st.session_state["current_quality_report"]

trust_score_report = calculate_data_trust_score(df, quality_report)
st.session_state["current_trust_score_report"] = trust_score_report

overall_score = trust_score_report["overall_score"]
risk_level = trust_score_report["risk_level"]
ai_readiness = trust_score_report["ai_readiness"]
conclusion = trust_score_report["conclusion"]
breakdown_df = trust_score_report["breakdown_df"]
outlier_details_df = trust_score_report["outlier_details_df"]
anomaly_report = trust_score_report.get("anomaly_report", {})


status = "low"
if risk_level == "Medium":
    status = "medium"
elif risk_level == "High":
    status = "high"
elif risk_level == "Critical":
    status = "critical"


st.markdown('<div class="section-title">1. Tổng quan Data Trust Score</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1.4])

with col1:
    render_metric_card(
        "Overall Data Trust Score",
        f"{overall_score}/100",
        "Điểm tổng hợp có trọng số",
        status=status,
    )

with col2:
    render_metric_card(
        "Risk Level",
        risk_level,
        "Mức rủi ro dữ liệu",
        status=status,
    )

with col3:
    render_metric_card(
        "AI Readiness",
        ai_readiness,
        "Mức độ sẵn sàng cho phân tích/AI",
        status=status,
    )


if risk_level == "Low":
    render_recommendation_box(conclusion, level="success")
elif risk_level == "Medium":
    render_recommendation_box(conclusion, level="warning")
else:
    render_recommendation_box(conclusion, level="danger")


st.markdown('<div class="section-title">2. Save scan result</div>', unsafe_allow_html=True)

save_col1, save_col2 = st.columns([1, 3])

with save_col1:
    if st.button("Save full scan to SQL Server"):
        try:
            result = save_full_scan(
                file_name=file_name,
                file_type=file_type,
                df=df,
                profile=profile,
                quality_report=quality_report,
                trust_score_report=trust_score_report,
            )

            st.session_state["last_saved_scan"] = result

            st.success(
                f"Đã lưu full scan. "
                f"dataset_id={result['dataset_id']}, "
                f"scan_id={result['scan_id']}, "
                f"score_id={result['score_id']}, "
                f"issues={result['saved_issues']}"
            )

        except Exception as exc:
            st.error(f"Không thể lưu full scan vào SQL Server: {exc}")

with save_col2:
    st.info(
        "Full scan gồm: dataset metadata, scan run, trust score và toàn bộ quality issues."
    )


st.markdown('<div class="section-title">3. Score Overview</div>', unsafe_allow_html=True)

score_col1, score_col2 = st.columns([1.15, 1])

with score_col1:
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=overall_score,
            title={"text": "Overall Data Trust Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2563eb"},
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 70], "color": "#ffedd5"},
                    {"range": [70, 85], "color": "#fef9c3"},
                    {"range": [85, 100], "color": "#dcfce7"},
                ],
                "threshold": {
                    "line": {"color": "#111827", "width": 4},
                    "thickness": 0.75,
                    "value": overall_score,
                },
            },
        )
    )
    fig_gauge.update_layout(height=380, margin=dict(l=20, r=20, t=70, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with score_col2:
    radar_df = breakdown_df.copy()

    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=radar_df["score"].tolist(),
            theta=radar_df["score_name"].tolist(),
            fill="toself",
            name="Score",
        )
    )

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
            )
        ),
        showlegend=False,
        title="Radar chất lượng dữ liệu",
        height=380,
        margin=dict(l=30, r=30, t=70, b=30),
    )
    st.plotly_chart(fig_radar, use_container_width=True)


st.markdown('<div class="section-title">4. Score Breakdown</div>', unsafe_allow_html=True)

display_breakdown_df = breakdown_df[
    [
        "score_name",
        "score",
        "weight",
        "weighted_score",
        "raw_value (%)",
        "detail",
        "interpretation",
    ]
]

st.dataframe(display_breakdown_df, use_container_width=True)


st.markdown('<div class="section-title">5. Weighted Contribution</div>', unsafe_allow_html=True)

contribution_df = breakdown_df[["score_name", "score", "weight", "weighted_score"]].copy()

fig_contribution = px.bar(
    contribution_df,
    x="score_name",
    y="weighted_score",
    title="Đóng góp có trọng số của từng nhóm điểm",
    text="weighted_score",
)

fig_contribution.update_traces(textposition="outside")
fig_contribution.update_layout(yaxis_range=[0, max(contribution_df["weighted_score"].max() + 5, 30)])
st.plotly_chart(fig_contribution, use_container_width=True)


st.markdown('<div class="section-title">6. Chi tiết từng nhóm điểm</div>', unsafe_allow_html=True)

for _, row in breakdown_df.iterrows():
    with st.expander(f"{row['score_name']} — {row['score']}/100"):
        c1, c2, c3 = st.columns(3)

        c1.metric("Score", f"{row['score']}/100")
        c2.metric("Weight", row["weight"])
        c3.metric("Weighted Score", row["weighted_score"])

        st.markdown(f"**Raw value:** `{row['raw_value (%)']}%`")
        st.markdown(f"**Chi tiết:** {row['detail']}")
        st.markdown(f"**Ý nghĩa:** {row['interpretation']}")


st.markdown('<div class="section-title">7. Anomaly details</div>', unsafe_allow_html=True)

if not anomaly_report:
    st.info("Chưa có anomaly report.")
else:
    anomaly_summary = anomaly_report["summary"]
    anomaly_summary_df = anomaly_report["summary_df"]
    combined_outlier_rows_df = anomaly_report["combined_outlier_rows_df"]

    a1, a2, a3 = st.columns(3)

    a1.metric("Anomaly rows", anomaly_summary["total_anomaly_rows"])
    a2.metric("Anomaly rate", f"{anomaly_summary['anomaly_rate (%)']}%")
    a3.metric("Anomaly Score", f"{anomaly_summary['anomaly_score']}/100")

    st.dataframe(anomaly_summary_df, use_container_width=True)

    if combined_outlier_rows_df.empty:
        st.success("Không phát hiện dòng bất thường tổng hợp.")
    else:
        st.warning(f"Phát hiện {len(combined_outlier_rows_df)} dòng bất thường tổng hợp.")
        st.dataframe(combined_outlier_rows_df, use_container_width=True)


st.markdown('<div class="section-title">8. Recommendation Box</div>', unsafe_allow_html=True)

if risk_level == "Low":
    render_recommendation_box(
        """
        <b>Khuyến nghị:</b> Dataset đang có điểm tốt. Có thể tiếp tục dùng cho phân tích,
        nhưng vẫn nên kiểm tra thêm privacy risk, drift detection và các rule nghiệp vụ ở các version sau.
        """,
        level="success",
    )
elif risk_level == "Medium":
    render_recommendation_box(
        """
        <b>Khuyến nghị:</b> Dataset có thể dùng cho phân tích sơ bộ.
        Trước khi dùng chính thức, nên xử lý các lỗi có severity Medium/High và kiểm tra outlier.
        """,
        level="warning",
    )
else:
    render_recommendation_box(
        """
        <b>Khuyến nghị:</b> Dataset chưa nên dùng trực tiếp cho AI/ML.
        Cần ưu tiên xử lý missing value, duplicate rows, lỗi kiểu dữ liệu, invalid range và outlier.
        """,
        level="danger",
    )


st.markdown('<div class="section-title">9. Diễn giải kết quả</div>', unsafe_allow_html=True)

st.markdown(
    f"""
- **Overall Data Trust Score:** `{overall_score}/100`
- **Risk Level:** `{risk_level}`
- **AI Readiness:** `{ai_readiness}`

{conclusion}

**Lưu ý:** Điểm hiện tại dựa trên các kiểm tra cơ bản gồm missing value, duplicate rows, lỗi validity, consistency và outlier bằng IQR. Ở các version sau, điểm số sẽ được nâng cấp thêm với privacy risk, drift detection và anomaly detection nâng cao.
"""
)