# ==============================
# 필요한 라이브러리 불러오기
# ==============================

# streamlit은 파이썬으로 웹사이트를 만들 수 있게 해주는 라이브러리입니다.
import streamlit as st

# imageio는 동영상 파일에서 프레임을 읽고,
# 여러 이미지를 GIF로 저장할 때 사용합니다.
import imageio

# tempfile은 임시 파일을 만들 때 사용합니다.
# 업로드한 동영상을 잠깐 저장하기 위해 필요합니다.
import tempfile

# os는 파일 삭제, 파일 존재 여부 확인 등에 사용합니다.
import os

# math는 계산할 때 사용합니다.
import math

# PIL은 이미지 크기를 줄일 때 사용합니다.
from PIL import Image


# ==============================
# Streamlit 페이지 기본 설정
# ==============================

st.set_page_config(
    page_title="Video to GIF Converter",
    page_icon="🎞️",
    layout="centered"
)


# ==============================
# 사이트 제목과 설명
# ==============================

st.title("🎞️ 동영상 → GIF 변환기")

st.write(
    "동영상 파일을 업로드하고 원하는 구간을 선택해서 GIF로 변환할 수 있습니다."
)


# ==============================
# 파일 업로드
# ==============================

uploaded_file = st.file_uploader(
    "동영상 파일 업로드",
    type=["mp4", "mov", "avi", "mkv", "webm"]
)


# ==============================
# 파일이 업로드되었을 때 실행
# ==============================

if uploaded_file is not None:

    # 업로드한 파일의 확장자를 가져옵니다.
    # 예: video.mp4 → .mp4
    file_extension = os.path.splitext(uploaded_file.name)[1]

    # 업로드한 동영상을 임시 파일로 저장합니다.
    # imageio가 동영상을 읽으려면 실제 파일 경로가 필요하기 때문입니다.
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_video:
        temp_video.write(uploaded_file.read())
        video_path = temp_video.name

    # 업로드한 동영상을 화면에서 미리 볼 수 있게 보여줍니다.
    st.video(video_path)

    try:
        # ==============================
        # 동영상 정보 읽기
        # ==============================

        # imageio로 동영상 파일을 읽습니다.
        reader = imageio.get_reader(video_path, "ffmpeg")

        # 동영상의 메타데이터를 가져옵니다.
        metadata = reader.get_meta_data()

        # 원본 영상의 FPS를 가져옵니다.
        # FPS는 1초에 몇 장의 프레임이 있는지를 뜻합니다.
        video_fps = metadata.get("fps", 30)

        # 영상 길이를 가져옵니다.
        # 일부 파일은 duration 정보가 없을 수 있습니다.
        duration = metadata.get("duration", None)

        if duration is None or duration == float("inf"):
            st.warning("영상 길이를 자동으로 읽지 못했습니다. 짧은 영상 위주로 사용해 주세요.")
            duration = 10.0

        st.info(f"영상 길이: 약 {duration:.2f}초")
        st.info(f"원본 FPS: {video_fps:.2f}")


        # ==============================
        # GIF 설정값 입력받기
        # ==============================

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

        width = st.slider(
            "GIF 가로 크기(px)",
            min_value=200,
            max_value=1280,
            value=480,
            step=20
        )

        st.caption("GIF는 길이, FPS, 크기가 커질수록 용량이 빠르게 커집니다.")


        # ==============================
        # 입력값 검사
        # ==============================

        if end_time <= start_time:
            st.error("끝 시간은 시작 시간보다 커야 합니다.")

        elif end_time - start_time > 15:
            st.warning("GIF 구간이 너무 길면 변환이 느리거나 실패할 수 있습니다. 15초 이하를 추천합니다.")

        else:
            # ==============================
            # GIF 변환 버튼
            # ==============================

            if st.button("GIF 변환하기"):

                with st.spinner("GIF로 변환 중입니다..."):

                    # 결과 GIF를 저장할 임시 파일 경로를 만듭니다.
                    output_path = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".gif"
                    ).name

                    # 시작 프레임과 끝 프레임을 계산합니다.
                    start_frame = int(start_time * video_fps)
                    end_frame = int(end_time * video_fps)

                    # 원본 FPS에서 GIF FPS에 맞게 프레임을 건너뛰기 위한 값입니다.
                    # 예: 원본 30fps, GIF 10fps면 3프레임마다 1장씩 사용합니다.
                    frame_step = max(1, int(video_fps / gif_fps))

                    frames = []

                    # 사용할 총 프레임 수를 계산합니다.
                    total_frames = max(1, math.ceil((end_frame - start_frame) / frame_step))

                    # 진행률 표시 바입니다.
                    progress_bar = st.progress(0)

                    # 선택한 구간의 프레임을 읽습니다.
                    for index, frame_number in enumerate(range(start_frame, end_frame, frame_step)):

                        # 특정 번호의 프레임을 가져옵니다.
                        frame = reader.get_data(frame_number)

                        # numpy 배열 형태의 프레임을 PIL 이미지로 변환합니다.
                        image = Image.fromarray(frame)

                        # 원본 비율을 유지하면서 가로 크기를 줄입니다.
                        original_width, original_height = image.size
                        ratio = width / original_width
                        new_height = int(original_height * ratio)

                        image = image.resize((width, new_height))

                        # GIF에 넣을 프레임 목록에 추가합니다.
                        frames.append(image)

                        # 진행률 업데이트
                        progress = min(1.0, (index + 1) / total_frames)
                        progress_bar.progress(progress)

                    # 프레임이 하나도 없으면 오류를 보여줍니다.
                    if len(frames) == 0:
                        st.error("GIF로 만들 프레임을 가져오지 못했습니다.")

                    else:
                        # 프레임들을 GIF 파일로 저장합니다.
                        imageio.mimsave(
                            output_path,
                            frames,
                            format="GIF",
                            fps=gif_fps
                        )

                        st.success("GIF 변환 완료!")

                        # 변환된 GIF 미리보기
                        st.image(output_path)

                        # GIF 다운로드 버튼
                        with open(output_path, "rb") as gif_file:
                            st.download_button(
                                label="GIF 다운로드",
                                data=gif_file,
                                file_name="converted.gif",
                                mime="image/gif"
                            )

        # 동영상 reader를 닫습니다.
        reader.close()

    except Exception as e:
        st.error("변환 중 오류가 발생했습니다.")
        st.code(str(e))

    finally:
        # 임시로 저장한 동영상 파일을 삭제합니다.
        if os.path.exists(video_path):
            os.remove(video_path)