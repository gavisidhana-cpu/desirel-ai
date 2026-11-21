    "रील का टॉपिक लिखें",
    placeholder="उदाहरण: पंजाबी में मोटिवेशनल कोट, या हिंदी में फिटनेस टिप...",
)
bg_video = st.file_uploader(
    "बैकग्राउंड वीडियो अपलोड करें (MP4 - 9:16 Vertical)", type=["mp4"]
)

# भारतीय आवाजें (Punjabi & Hindi)
VOICES = {
    "Punjabi": {
        "Male (पुरुष)": "pa-IN-OjasNeural",
        "Female (महिला)": "pa-IN-VaaniNeural",
    },
    "Hindi": {
        "Male (पुरुष)": "hi-IN-MadhurNeural",
        "Female (महिला)": "hi-IN-SwaraNeural",
    },
}


async def generate_voice(text, voice, output_file):
  communicate = edge_tts.Communicate(text, voice)
  await communicate.save(output_file)


@st.cache_resource
def load_whisper_model():
  return whisper.load_model("base")


if st.button("🚀 तेज AI रील बनाएं (Generate Reel)", use_container_width=True):
  if not api_key or not topic or not bg_video:
    st.error("⚠️ कृपया API Key, टॉपिक और बैकग्राउंड वीडियो तीनों जरूर दें!")
  else:
    try:
      # 1. स्क्रिप्ट जनरेट करें
      with st.spinner("1/3 वायरल स्क्रिप्ट लिखी जा रही है..."):
        client = genai.Client(api_key=api_key)
        prompt = (
            "Write a short, engaging 12-to-15 second Instagram Reel voiceover"
            f" script in {language} about: {topic}. Write in native script"
            " (Gurmukhi for Punjabi, Devanagari for Hindi). Output ONLY the"
            " spoken text, no hashtags, emojis, or scene descriptions."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        script_text = response.text.strip()
        st.info(f"**तैयार स्क्रिप्ट:**\n\n{script_text}")

      # 2. आवाज (Voiceover) बनाएं
      with st.spinner("2/3 तेज AI आवाज (Voiceover) बन रही है..."):
        audio_path = "voiceover.mp3"
        selected_voice = VOICES[language][voice_gender]
        asyncio.run(generate_voice(script_text, selected_voice, audio_path))

      # 3. वीडियो और कैप्शन एडिट करें
      with st.spinner("3/3 वीडियो एडिटिंग और ऑटो-कैप्शन लग रहे हैं..."):
        with open("temp_bg.mp4", "wb") as f:
          f.write(bg_video.read())

        audio = AudioFileClip(audio_path)
        video = VideoFileClip("temp_bg.mp4")

        if video.duration < audio.duration:
          video = video.loop(duration=audio.duration)
        else:
          video = video.subclip(0, audio.duration)

        video = video.set_audio(audio)

        # Whisper से कैप्शन टाइमिंग निकालें
        model = load_whisper_model()
        lang_code = "pa" if language == "Punjabi" else "hi"
        result = model.transcribe(audio_path, language=lang_code)

        caption_clips = []
        for segment in result["segments"]:
          txt_clip = (
              TextClip(
                  segment["text"].strip(),
                  fontsize=45,
                  color="yellow",
                  font="DejaVu-Sans-Bold",
                  stroke_color="black",
                  stroke_width=2,
                  method="caption",
                  size=(video.w * 0.85, None),
              )
              .set_position(("center", "center"))
              .set_start(segment["start"])
              .set_duration(segment["end"] - segment["start"])
          )
          caption_clips.append(txt_clip)

        final_video = CompositeVideoClip([video] + caption_clips)
        output_filename = "final_reel.mp4"
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        st.success("✅ आपकी रील तैयार है!")
        st.video(output_filename)

        with open(output_filename, "rb") as file:
          st.download_button(
              label="⬇️ फाइनल रील डाउनलोड करें (Download MP4)",
              data=file,
              file_name=f"{language.lower()}_reel.mp4",
              mime="video/mp4",
              use_container_width=True,
          )

    except Exception as e:
      st.error(f"कुछ गड़बड़ हुई: {e}")
