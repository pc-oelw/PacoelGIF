# ==============================
# 필요한 라이브러리 불러오기
# ==============================

# streamlit은 파이썬으로 웹사이트를 만들 수 있게 해주는 라이브러리입니다.
import streamlit as st

# VideoFileClip은 동영상 파일을 불러오고, 자르고, 변환할 때 사용합니다.
#
# 중요:
# Streamlit Cloud에서는 아래처럼 moviepy.editor에서 가져오는 방식이 안정적입니다.
# from moviepy import VideoFileClip 이라고 쓰면 오류가 날 수 있습니다.
from moviepy.editor import VideoFileClip

# tempfile은 임시 파일을 만들 때 사용합니다.
# 사용자가 업로드한 동영상을 잠깐 저장하기 위해 필요합니다.
import tempfile

# os는 파일 삭제, 파일 존재 여부 확인 등에 사용합니다.
import os


# ==============================
# Streamlit 페이지 기본 설정
# ==============================

st.set_page_config(
    page_title="Video to GIF Converter",  # 브라우저 탭에 보이는 제목
    page_icon="🎞️",                      # 브라우저 탭 아이콘
    layout="centered"                    # 화면 레이아웃
)


# ==============================
# 사이트 제목과 설명
# ==============================

st.title("🎞️ 동영상 → GIF 변환기")

st.write(
    "동영상 파일을 업로드한 뒤, 원하는 구간을 선택해서 GIF로 변환할 수 있습니다."
)


# ==============================
# 동영상 파일 업로드
# ==============================

uploaded_file = st.file_uploader(
    "동영상 파일 업로드",
    type=["mp4", "mov", "avi", "mkv", "webm"]
)


# ==============================
# 파일이 업로드되었을 때 실행
# ==============================

if uploaded_file is not None:

    # 사용자가 업로드한 파일은 Streamlit 내부의 UploadedFile 형태입니다.
    # MoviePy는 실제 파일 경로가 있어야 동영상을 읽을 수 있기 때문에,
    # 업로드한 파일을 임시 파일로 저장합니다.
    #
    # delete=False:
    # 임시 파일을 자동으로 삭제하지 않고,
    # 나중에 우리가 직접 삭제하겠다는 뜻입니다.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(uploaded_file.read())
        video_path = temp_video.name

    # 업로드한 동영상을 웹페이지에서 미리보기로 보여줍니다.
    st.video(video_path)

    try:
        # ==============================
        # 동영상 파일 불러오기
        # ==============================

        # MoviePy로 동영상을 불러옵니다.
        video = VideoFileClip(video_path)

        # 동영상 전체 길이를 초 단위로 가져옵니다.
        duration = video.duration

        # 영상 길이를 사용자에게 보여줍니다.
        st.info(f"영상 길이: {duration:.2f}초")


        # ==============================
        # GIF 설정값 입력받기
        # ==============================

        st.subheader("GIF 설정")

        # GIF로 만들 시작 시간을 입력받습니다.
        start_time = st.number_input(
            "시작 시간(초)",
            min_value=0.0,
            max_value=float(duration),
            value=0.0,
            step=0.1
        )

        # GIF로 만들 끝 시간을 입력받습니다.
        #
        # 기본값은 5초입니다.
        # 단, 영상이 5초보다 짧으면 영상 끝까지로 설정합니다.
        end_time = st.number_input(
            "끝 시간(초)",
            min_value=0.1,
            max_value=float(duration),
            value=min(5.0, float(duration)),
            step=0.1
        )

        # FPS는 1초에 몇 장의 이미지가 들어가는지 뜻합니다.
        #
        # FPS가 높으면:
        # - GIF가 더 부드러움
        # - 대신 용량이 커짐
        #
        # FPS가 낮으면:
        # - GIF가 덜 부드러움
        # - 대신 용량이 작아짐
        fps = st.slider(
            "GIF 프레임 수(FPS)",
            min_value=5,
            max_value=30,
            value=12
        )

        # GIF의 가로 크기를 선택합니다.
        #
        # 크기가 클수록:
        # - 화질이 좋아짐
        # - 대신 용량이 커지고 변환 시간이 길어짐
        width = st.slider(
            "GIF 가로 크기(px)",
            min_value=200,
            max_value=1280,
            value=480,
            step=20
        )


        # ==============================
        # 입력값 검사
        # ==============================

        # 끝 시간이 시작 시간보다 작거나 같으면 변환할 수 없습니다.
        if end_time <= start_time:
            st.error("끝 시간은 시작 시간보다 커야 합니다.")

        else:
            # ==============================
            # GIF 변환 버튼
            # ==============================

            if st.button("GIF 변환하기"):

                # 변환 중이라는 표시를 띄웁니다.
                with st.spinner("GIF로 변환 중입니다..."):

                    # 변환된 GIF를 저장할 임시 파일 경로를 만듭니다.
                    output_path = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".gif"
                    ).name

                    # ==============================
                    # 동영상 구간 자르기
                    # ==============================

                    # 사용자가 선택한 시작 시간 ~ 끝 시간만 잘라냅니다.
                    clip = video.subclip(start_time, end_time)

                    # ==============================
                    # GIF 크기 조절
                    # ==============================

                    # 가로 크기를 사용자가 선택한 값으로 변경합니다.
                    # 세로 크기는 원본 비율에 맞게 자동으로 조절됩니다.
                    clip = clip.resize(width=width)

                    # ==============================
                    # GIF 파일로 저장
                    # ==============================

                    # 잘라낸 동영상 클립을 GIF 파일로 저장합니다.
                    clip.write_gif(
                        output_path,
                        fps=fps
                    )

                    # 변환이 완료되었다는 메시지
                    st.success("GIF 변환 완료!")

                    # 변환된 GIF 미리보기
                    st.image(output_path)

                    # ==============================
                    # GIF 다운로드 버튼
                    # ==============================

                    # GIF 파일을 rb 모드로 읽습니다.
                    # rb는 read binary, 즉 바이너리 파일 읽기라는 뜻입니다.
                    with open(output_path, "rb") as gif_file:
                        st.download_button(
                            label="GIF 다운로드",
                            data=gif_file,
                            file_name="converted.gif",
                            mime="image/gif"
                        )

                    # 사용이 끝난 clip을 닫습니다.
                    # 파일 점유를 해제하기 위해 필요합니다.
                    clip.close()

        # 사용이 끝난 원본 영상 객체를 닫습니다.
        video.close()


    except Exception as e:
        # ==============================
        # 오류 처리
        # ==============================

        # 변환 중 오류가 나면 사용자에게 알려줍니다.
        st.error("변환 중 오류가 발생했습니다.")

        # 실제 오류 내용을 보여줍니다.
        # 공부할 때는 오류 내용을 확인하는 게 중요해서 표시합니다.
        st.code(str(e))


    finally:
        # ==============================
        # 임시 파일 삭제
        # ==============================

        # 업로드한 영상을 임시 파일로 저장했기 때문에,
        # 작업이 끝나면 삭제해서 서버 용량을 아낍니다.
        if os.path.exists(video_path):
            os.remove(video_path)