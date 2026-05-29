import streamlit as st
from moviepy import VideoFileClip
import tempfile
import os


st.set_page_config(
    page_title="Video to GIF Converter",
    page_icon="🎞️",
    layout="centered"
)

st.title("🎞️ 동영상 → GIF 변환기")
st.write("동영상 파일을 업로드하고 원하는 구간을 GIF로 변환하세요.")


uploaded_file = st.file_uploader(
    "동영상 파일 업로드",
    type=["mp4", "mov", "avi", "mkv", "webm"]
)

if uploaded_file is not None:
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(uploaded_file.read())
        video_path = temp_video.name

    st.video(video_path)

    try:
        video = VideoFileClip(video_path)
        duration = video.duration

        st.info(f"영상 길이: {duration:.2f}초")

        st.subheader("GIF로 만들 구간 선택")

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

        fps = st.slider(
            "GIF 프레임 수(FPS)",
            min_value=5,
            max_value=30,
            value=12
        )

        width = st.slider(
            "GIF 가로 크기(px)",
            min_value=200,
            max_value=1280,
            value=480,
            step=20
        )

        if end_time <= start_time:
            st.error("끝 시간은 시작 시간보다 커야 합니다.")
        else:
            if st.button("GIF 변환하기"):
                with st.spinner("GIF로 변환 중입니다..."):
                    output_path = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".gif"
                    ).name

                    clip = video.subclipped(start_time, end_time)
                    clip = clip.resized(width=width)

                    clip.write_gif(
                        output_path,
                        fps=fps
                    )

                    st.success("GIF 변환 완료")

                    st.image(output_path)

                    with open(output_path, "rb") as gif_file:
                        st.download_button(
                            label="GIF 다운로드",
                            data=gif_file,
                            file_name="converted.gif",
                            mime="image/gif"
                        )

                    clip.close()

        video.close()

    except Exception as e:
        st.error("변환 중 오류가 발생했습니다.")
        st.code(str(e))

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)