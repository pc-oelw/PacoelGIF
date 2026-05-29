import streamlit as st
import imageio
import tempfile
import os
import math
from PIL import Image

st.set_page_config(
    page_title="동영상 GIF 변환기",
    page_icon="🎞️",
    layout="centered"
)

if "gif_data" not in st.session_state:
    st.session_state.gif_data = None

if "gif_ready" not in st.session_state:
    st.session_state.gif_ready = False

st.title("GIF 변환기")
st.write("동영상을 업로드하고 원하는 구간을 GIF로 변환하세요.")

uploaded_file = st.file_uploader(
    "동영상 업로드",
    type=["mp4", "mov", "avi", "mkv", "webm"]
)

if uploaded_file is not None:
    current_file_name = uploaded_file.name

    if "last_file_name" not in st.session_state:
        st.session_state.last_file_name = current_file_name

    if st.session_state.last_file_name != current_file_name:
        st.session_state.gif_data = None
        st.session_state.gif_ready = False
        st.session_state.last_file_name = current_file_name

if uploaded_file is not None:
    file_extension = os.path.splitext(uploaded_file.name)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_video:
        temp_video.write(uploaded_file.read())
        video_path = temp_video.name

    st.video(video_path)

    try:
        reader = imageio.get_reader(video_path, "ffmpeg")
        metadata = reader.get_meta_data()

        video_fps = metadata.get("fps", 30)
        duration = metadata.get("duration", None)

        if duration is None or duration == float("inf"):
            st.warning("영상 길이를 자동으로 읽지 못했습니다. 기본값을 10초로 설정합니다.")
            duration = 10.0

        st.info(f"영상 길이: 약 {duration:.2f}초")
        st.info(f"원본 FPS: {video_fps:.2f}")

        st.subheader("GIF 설정")

        start_time = st.number_input(
            "시작 시간(초)",
            min_value=0.0,
            max_value=float(duration),
            value=0.0,
            step=0.1
        )

        end_time = st.number_input(
            "끝 시간(초)",
            min_value=0.1,
            max_value=float(duration),
            value=min(5.0, float(duration)),
            step=0.1
        )

        gif_fps = st.slider(
            "GIF 프레임 수(FPS)",
            min_value=5,
            max_value=30,
            value=12
        )

        st.caption("GIF는 길이와 FPS가 커질수록 용량이 커집니다.")

        if end_time <= start_time:
            st.error("끝 시간은 시작 시간보다 커야 합니다.")

        elif end_time - start_time > 15:
            st.warning("GIF 구간이 너무 길면 변환이 느리거나 실패할 수 있습니다.")

        else:
            if st.button("GIF 변환하기"):
                with st.spinner("GIF로 변환 중..."):
                    output_path = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".gif"
                    ).name

                    start_frame = int(start_time * video_fps)
                    end_frame = int(end_time * video_fps)
                    frame_step = max(1, int(video_fps / gif_fps))

                    frames = []
                    total_frames = max(
                        1,
                        math.ceil((end_frame - start_frame) / frame_step)
                    )

                    progress_bar = st.progress(0)

                    for index, frame_number in enumerate(
                        range(start_frame, end_frame, frame_step)
                    ):
                        frame = reader.get_data(frame_number)
                        image = Image.fromarray(frame)
                        frames.append(image)

                        progress = min(1.0, (index + 1) / total_frames)
                        progress_bar.progress(progress)

                    if len(frames) == 0:
                        st.error("GIF로 만들 프레임을 가져오지 못했습니다.")
                    else:
                        imageio.mimsave(
                            output_path,
                            frames,
                            format="GIF",
                            fps=gif_fps
                        )

                        with open(output_path, "rb") as gif_file:
                            st.session_state.gif_data = gif_file.read()

                        st.session_state.gif_ready = True
                        st.success("GIF 변환 완료")

        reader.close()

    except Exception as e:
        st.error("변환 중 오류가 발생했습니다.")
        st.code(str(e))

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

if st.session_state.gif_ready and st.session_state.gif_data is not None:
    st.subheader("변환 결과")

    st.image(st.session_state.gif_data)

    st.download_button(
        label="GIF 다운로드",
        data=st.session_state.gif_data,
        file_name="converted.gif",
        mime="image/gif"
    )