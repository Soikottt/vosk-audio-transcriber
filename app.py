import json
import os
import urllib.request
import zipfile
from pydub import AudioSegment
import streamlit as st
from vosk import KaldiRecognizer, Model

# Page config
st.set_page_config(page_title="Audio to Text Converter", layout="centered")

st.title("🎙️ Offline Audio to Text Converter")
st.write("MP3 file upload korun ebong browser-e druto text paben.")

MODEL_PATH = "model"

# Auto-download Vosk model if not present (useful for Cloud Deployment)
if not os.path.exists(MODEL_PATH):
  with st.spinner("Vosk Model download hochhe... (Khub druto sesh hobe)"):
    MODEL_URL = (
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    )
    urllib.request.urlretrieve(MODEL_URL, "model.zip")
    with zipfile.ZipFile("model.zip", "r") as zip_ref:
      zip_ref.extractall(".")
    os.rename("vosk-model-small-en-us-0.15", MODEL_PATH)
    if os.path.exists("model.zip"):
      os.remove("model.zip")


@st.cache_resource
def load_vosk_model():
  if not os.path.exists(MODEL_PATH):
    return None
  return Model(MODEL_PATH)


model = load_vosk_model()

if model is None:
  st.error(
      "Error: 'model' folder paowa jayni! Sothik path-e model folder thakbar"
      " nishchoyota dain."
  )
else:
  uploaded_file = st.file_uploader(
      "Apnar MP3 File Upload Korun", type=["mp3", "wav"]
  )

  if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/mp3")

    if st.button("Transcribe Now", type="primary"):
      with st.spinner(
          "Processing audio... Khub druto fast convert hochhe..."
      ):
        # Temporary file save
        with open("temp_input.mp3", "wb") as f:
          f.write(uploaded_file.getbuffer())

        # Convert to 16kHz Mono WAV
        sound = AudioSegment.from_file("temp_input.mp3")
        sound = sound.set_channels(1).set_frame_rate(16000)
        sound.export("temp_processed.wav", format="wav")

        # Transcribe using Vosk
        recognizer = KaldiRecognizer(model, 16000)
        results = []

        with open("temp_processed.wav", "rb") as wf:
          while True:
            # High-speed chunk size
            data = wf.read(32000)
            if len(data) == 0:
              break
            if recognizer.AcceptWaveform(data):
              part = json.loads(recognizer.Result())
              if part.get("text"):
                results.append(part["text"])

        final_part = json.loads(recognizer.FinalResult())
        if final_part.get("text"):
          results.append(final_part["text"])

        full_text = " ".join(results)

        # Cleaning temporary files
        if os.path.exists("temp_input.mp3"):
          os.remove("temp_input.mp3")
        if os.path.exists("temp_processed.wav"):
          os.remove("temp_processed.wav")

      st.success("Completed!")
      st.subheader("Transcription Text:")
      st.text_area("Result", value=full_text, height=250)

      st.download_button(
          label="Download Text File",
          data=full_text,
          file_name="transcription.txt",
          mime="text/plain",
      )