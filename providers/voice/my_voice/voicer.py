from gradio_client import Client, handle_file

# 🔥 Your RunPod WebUI URL
API_URL = "https://qughf6g12na7uk-8002.proxy.runpod.net/"

# 🔥 Path to your local reference file
REF_WAV = "ref.wav"

TEXT = "Hello bro. This voice is cloned remotely using my RunPod server."

client = Client(API_URL)

result = client.predict(
    emo_control_method="Same as the voice reference",
    prompt=handle_file(REF_WAV),   # 🔥 voice cloning
    text=TEXT,
    emo_ref_path=handle_file(REF_WAV),
    emo_weight=0.65,
    vec1=0, vec2=0, vec3=0, vec4=0,
    vec5=0, vec6=0, vec7=0, vec8=0,
    emo_text="",
    emo_random=False,
    max_text_tokens_per_segment=120,
    param_16=True,
    param_17=0.8,
    param_18=30,
    param_19=0.8,
    param_20=0,
    param_21=3,
    param_22=10,
    param_23=1500,
    api_name="/gen_single"
)

print("Generated file:", result)

# Save output
if isinstance(result, dict):
    output_path = result["value"]
else:
    output_path = result

print("Audio saved at:", output_path)