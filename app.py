import os
from pathlib import Path
from PIL import Image, ImageDraw
import streamlit as st
import db
import torch

st.set_page_config(page_title="PathPulse", layout="wide")
st.title("PathPulse: AI Road Safety Assistant")

# --- Constants & Paths ---
BASE_DIR = Path(r"P:\archive")
TRAIN_IMAGES_DIR = BASE_DIR / "images" / "train" / "images"
TRAIN_LABELS_DIR = BASE_DIR / "images" / "train" / "labels"

CLASS_NAMES = ['HMV', 'LMV', 'Pedestrian', 'RoadDamages', 'SpeedBump', 'UnsurfacedRoad']
CLASS_COLORS = {
    0: "blue",        # HMV
    1: "cyan",        # LMV
    2: "green",       # Pedestrian
    3: "red",         # RoadDamages
    4: "purple",      # SpeedBump
    5: "orange"       # UnsurfacedRoad
}

@st.cache_data
def get_image_files():
    if TRAIN_IMAGES_DIR.exists():
        files = list(TRAIN_IMAGES_DIR.glob("*.jpg")) + list(TRAIN_IMAGES_DIR.glob("*.png"))
        return sorted(files)
    return []

@st.cache_resource
def load_yolo_model():
    try:
        from ultralytics import YOLO
        model_path = Path("runs/detect/pathpulse_nano/weights/best.pt")
        if model_path.exists():
            return YOLO(str(model_path))
        else:
            return YOLO("yolov8n.pt")  # Fallback base model
    except ImportError:
        st.error("Please install ultralytics (pip install ultralytics)")
        return None

def run_live_inference(image_path, conf_thresh, iou_thresh):
    model = load_yolo_model()
    if model is None:
        return Image.open(image_path).convert("RGB")
        
    # Run prediction
    results = model.predict(source=str(image_path), conf=conf_thresh, iou=iou_thresh)
    
    # Render bounding boxes
    res = results[0]
    im_bgr = res.plot()
    # convert BGR to RGB for PIL
    im_rgb = im_bgr[..., ::-1]
    return Image.fromarray(im_rgb)

image_files = get_image_files()

# Sidebar for file uploads & browsing
with st.sidebar:
    st.header("Model Settings")
    conf_threshold = st.slider("Confidence Threshold", min_value=0.1, max_value=1.0, value=0.5, step=0.05)
    iou_threshold = st.slider("IoU (NMS) Threshold", min_value=0.1, max_value=1.0, value=0.4, step=0.05)
    
    st.divider()

    st.header("Dataset Browser")
    if image_files:
        st.write(f"Found {len(image_files)} training images.")
        image_idx = st.slider("Select Image Index", min_value=0, max_value=len(image_files)-1, value=0)
        selected_img_path = image_files[image_idx]
        st.caption(f"Selected: {selected_img_path.name}")
    else:
        st.warning("Dataset not found at P:\\archive")

    st.divider()
    
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload road images", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.success("Image uploaded successfully!")
        st.info("Inference pipeline integration pending.")

# --- Main View ---

st.header("Live Detection Viewer")
if image_files:
    processed_img = run_live_inference(selected_img_path, conf_threshold, iou_threshold)
    
    col_img1, col_img2, col_img3 = st.columns([1, 6, 1])
    with col_img2:
        st.image(processed_img, caption=f"Live YOLO Inference: {selected_img_path.name}", use_container_width=True)
else:
    st.info("Please ensure the dataset is available at P:\\archive to view images.")

st.divider()

st.header("Analytics Dashboard")

try:
    # Fetch Data
    kpis = db.get_kpis()
    stats_df = db.get_summary_stats()

    # 1. Top Row Metric Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Incidents Detected", value=f"{kpis['total_incidents']:,}")
    with col2:
        st.metric(label="Critical Anomalies (Priority 4-5)", value=f"{kpis['critical_anomalies']:,}", delta="High Severity", delta_color="inverse")
    with col3:
        st.metric(label="Database Status", value="Exasol Online", delta="Connected")

    st.divider()

    # 2. Distribution Chart (Grouped by damage_type)
    st.subheader("Incident Distribution by Damage Type")
    if not stats_df.empty:
        chart_data = stats_df.groupby('damage_type')['total_incidents'].sum().reset_index()
        chart_data = chart_data.set_index('damage_type')
        st.bar_chart(chart_data)
    else:
        st.info("No data available for the chart.")

    st.divider()

    # 3. Live Database Proof Expander
    with st.expander("🔍 Live Database Proof: Recent Exasol Entries", expanded=False):
        st.caption("Displaying the most recent 100 raw records directly from the CIVIC.ROAD_INCIDENTS table.")
        recent_df = db.get_recent_incidents(limit=100)
        st.dataframe(recent_df, use_container_width=True)

except Exception as e:
    st.error(f"Failed to fetch data from Exasol: {e}")
